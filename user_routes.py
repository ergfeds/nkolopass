from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, g
from models import db, Route, Trip, Booking, BusType, Operator, RouteOperatorAssignment, OperatorBusType, Customer
from mesomb_payment import get_mesomb_client
from datetime import datetime, timedelta
import json
from functools import wraps

user_bp = Blueprint('user', __name__)

# Language configuration
SUPPORTED_LANGUAGES = ['en', 'fr']
DEFAULT_LANGUAGE = 'fr'

def get_language_from_url():
    """Extract language from URL path"""
    path_parts = request.path.strip('/').split('/')
    if path_parts and path_parts[0] in SUPPORTED_LANGUAGES:
        return path_parts[0]
    return DEFAULT_LANGUAGE

def language_required(f):
    """Decorator to handle language routing"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract language from URL
        g.language = get_language_from_url()
        
        # Check if URL has language prefix
        path_parts = request.path.strip('/').split('/')
        if not path_parts or path_parts[0] not in SUPPORTED_LANGUAGES:
            # Redirect to language-prefixed URL
            new_path = f"/{DEFAULT_LANGUAGE}{request.path}"
            if request.query_string:
                new_path += f"?{request.query_string.decode()}"
            return redirect(new_path)
        
        return f(*args, **kwargs)
    return decorated_function

# Root redirect to default language
@user_bp.route('/')
def root_redirect():
    """Redirect root to default language"""
    return redirect(f'/{DEFAULT_LANGUAGE}/')

# Language-aware routes
@user_bp.route('/<lang>/')
@language_required
def index(lang):
    """Homepage with search form"""
    return render_template('index.html', language=g.language)

@user_bp.route('/<lang>/search')
@language_required
def search_results(lang):
    """Display search results"""
    # Get search parameters from URL
    from_city = request.args.get('from')
    to_city = request.args.get('to')
    operator_id = request.args.get('operator')
    travel_date = request.args.get('date')
    
    # Get operator name if operator_id is provided
    operator_name = None
    if operator_id:
        operator = Operator.query.get(operator_id)
        operator_name = operator.name if operator else None
    
    return render_template('search_results.html',
                         from_city=from_city,
                         to_city=to_city,
                         operator_id=operator_id,
                         operator_name=operator_name,
                         travel_date=travel_date,
                         language=g.language)

# API Routes
@user_bp.route('/api/routes')
def api_routes():
    """Get all active routes for search form"""
    routes = Route.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'origin': r.origin,
        'destination': r.destination,
        'distance_km': r.distance_km,
        'estimated_duration': r.estimated_duration
    } for r in routes])

@user_bp.route('/api/upcoming-trips')
def api_upcoming_trips():
    """Get upcoming trips from different agencies"""
    from datetime import datetime
    
    # Get trips for the next 7 days
    now = datetime.now()
    end_date = now + timedelta(days=7)
    
    trips = Trip.query.filter(
        Trip.departure_time >= now,
        Trip.departure_time <= end_date,
        Trip.status == 'scheduled',
        Trip.available_seats > 0
    ).order_by(Trip.departure_time).limit(12).all()
    
    trip_list = []
    seen_routes = set()  # To ensure variety from different routes
    
    for trip in trips:
        route_key = f"{trip.route.origin}-{trip.route.destination}"
        if route_key not in seen_routes or len(trip_list) < 6:
            seen_routes.add(route_key)
            trip_list.append({
                'id': trip.id,
                'route': f"{trip.route.origin} → {trip.route.destination}",
                'from': trip.route.origin,
                'to': trip.route.destination,
                'operator': trip.operator.name,
                'bus_type': trip.bus_type.category if trip.bus_type else 'regular',
                'departure_time': trip.departure_time.strftime('%H:%M'),
                'departure_date': trip.departure_time.strftime('%Y-%m-%d'),
                'date': trip.departure_time.strftime('%d/%m'),
                'price': f"{trip.seat_price:,.0f}",
                'available_seats': trip.available_seats
            })
    
    return jsonify(trip_list)

@user_bp.route('/api/route-operators')
def api_route_operators():
    """Get operators for a specific route"""
    from_city = request.args.get('from')
    to_city = request.args.get('to')
    
    if not from_city or not to_city:
        return jsonify([])
    
    # Find the route
    route = Route.query.filter_by(
        origin=from_city,
        destination=to_city,
        is_active=True
    ).first()
    
    if not route:
        # If no direct route found, return all active operators as fallback
        # This ensures users can still search even if route assignments aren't set up
        operators = Operator.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': op.id,
            'name': op.name,
            'code': op.code,
            'logo_url': op.logo_url
        } for op in operators])
    
    # Get operators assigned to this route
    assignments = RouteOperatorAssignment.query.filter_by(
        route_id=route.id,
        is_active=True
    ).all()
    
    operators = []
    for assignment in assignments:
        if assignment.operator.is_active:
            operators.append({
                'id': assignment.operator.id,
                'name': assignment.operator.name,
                'code': assignment.operator.code,
                'logo_url': assignment.operator.logo_url
            })
    
    # If no operators are assigned to this route, return all active operators
    if not operators:
        all_operators = Operator.query.filter_by(is_active=True).all()
        operators = [{
            'id': op.id,
            'name': op.name,
            'code': op.code,
            'logo_url': op.logo_url
        } for op in all_operators]
    
    return jsonify(operators)

@user_bp.route('/api/search-trips')
def api_search_trips():
    """Search for available trips"""
    from_city = request.args.get('from')
    to_city = request.args.get('to')
    operator_id = request.args.get('operator', type=int)
    travel_date = request.args.get('date')
    
    print(f"\n=== Trip Search Debug ===")
    print(f"From: {from_city}, To: {to_city}, Operator: {operator_id}, Date: {travel_date}")
    
    # Validate required parameters
    if not from_city or not to_city or not travel_date:
        return jsonify({'trips': [], 'error': 'Missing required parameters: from, to, date'}), 400
    
    # Make operator optional for broader search
    # if not operator_id:
    #     return jsonify({'trips': [], 'error': 'Please select an operator'}), 400
    
    # Parse the date
    try:
        date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'trips': [], 'error': 'Invalid date format'}), 400
    
    # Find the route
    route = Route.query.filter_by(
        origin=from_city,
        destination=to_city,
        is_active=True
    ).first()
    
    print(f"Direct route found: {route}")
    
    if not route:
        # Check for reverse route (for return trips)
        route = Route.query.filter_by(
            origin=to_city,
            destination=from_city,
            is_active=True
        ).first()
        print(f"Reverse route found: {route}")
        
        if not route:
            # Debug: Show all available routes
            all_routes = Route.query.filter_by(is_active=True).all()
            print(f"Available routes: {[(r.origin, r.destination) for r in all_routes]}")
            return jsonify({'trips': [], 'message': 'No route found between these cities'})
    
    # Get trips for this route and date
    start_datetime = datetime.combine(date_obj, datetime.min.time())
    end_datetime = datetime.combine(date_obj, datetime.max.time())
    
    # Build query - make operator optional
    query = Trip.query.filter(
        Trip.route_id == route.id,
        Trip.departure_time >= start_datetime,
        Trip.departure_time <= end_datetime,
        Trip.status == 'scheduled'
    )
    
    # Add operator filter if specified
    if operator_id:
        query = query.filter(Trip.operator_id == operator_id)
    
    trips = query.order_by(Trip.departure_time).all()
    
    print(f"Found {len(trips)} trips for route {route.id} on {travel_date}")
    if trips:
        print(f"Sample trip: {trips[0].departure_time}, Operator: {trips[0].operator_id}")
    
    # Format trips for response
    trip_list = []
    for trip in trips:
        # Get operator info for each trip
        trip_operator = Operator.query.get(trip.operator_id)
        
        # Get bus type configuration
        config = OperatorBusType.query.filter_by(
            operator_id=trip.operator_id,
            bus_type_id=trip.bus_type_id
        ).first()
        
        trip_list.append({
            'id': trip.id,
            'departure_time': trip.departure_time.isoformat(),
            'arrival_time': trip.arrival_time.isoformat(),
            'from_city': route.origin,
            'to_city': route.destination,
            'operator_name': trip_operator.name if trip_operator else 'Unknown',
            'operator_logo': trip_operator.logo_url if trip_operator else '',
            'bus_type_name': trip.bus_type.name if trip.bus_type else 'Standard',
            'bus_type_category': trip.bus_type.category if trip.bus_type else 'regular',
            'virtual_bus_id': trip.virtual_bus_id,
            'seat_price': float(trip.seat_price),
            'available_seats': trip.available_seats,
            'total_seats': config.capacity if config else trip.available_seats,
            'status': trip.status
        })
    
    return jsonify({
        'trips': trip_list,
        'total_trips': len(trip_list),
        'route': {
            'from': from_city,
            'to': to_city,
            'distance': route.distance_km,
            'duration': route.estimated_duration
        }
    })

@user_bp.route('/<lang>/booking/seats')
@language_required
def select_seats(lang):
    """Seat selection page"""
    trip_id = request.args.get('trip', type=int)
    if not trip_id:
        flash('Trip not found', 'error')
        return redirect(url_for('user.index', lang=g.language))
    
    # Get trip with route and operator info
    trip = db.session.query(Trip).join(Route).join(Operator).filter(
        Trip.id == trip_id
    ).first()
    
    # Get operator bus type configuration for seat layout
    config = OperatorBusType.query.filter_by(
        operator_id=trip.operator_id,
        bus_type_id=trip.bus_type_id
    ).first()
    
    # Get booked seats
    bookings = Booking.query.filter_by(trip_id=trip_id, status='confirmed').all()
    booked_seats = []
    for booking in bookings:
        booked_seats.extend(booking.get_seat_numbers())
    
    return render_template('booking/seat_selection.html', 
                         trip=trip, 
                         config=config,
                         booked_seats=booked_seats,
                         language=g.language)

@user_bp.route('/<lang>/booking/passenger-details', methods=['GET', 'POST'])
@language_required
def passenger_details(lang):
    """Passenger details form"""
    if 'selected_seats' not in session or 'trip_id' not in session:
        flash('Please select seats first', 'error')
        return redirect(url_for('user.index', lang=g.language))
    
    if request.method == 'POST':
        # Store passenger details in session
        session['passenger_details'] = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'passengers': request.form.getlist('passengers')
        }
        return redirect(url_for('user.payment', lang=g.language))
    
    trip = Trip.query.get_or_404(session['trip_id'])
    selected_seats = session['selected_seats']
    total_amount = len(selected_seats) * trip.seat_price
    
    return render_template('booking/passenger_details.html',
                         trip=trip,
                         selected_seats=selected_seats,
                         total_amount=total_amount)

@user_bp.route('/<lang>/booking/payment', methods=['GET', 'POST'])
@language_required
def payment(lang):
    """Payment page with MesomB integration"""
    if 'passenger_details' not in session:
        flash('Please provide passenger details first', 'error')
        return redirect(url_for('user.index', lang=g.language))
    
    if request.method == 'POST':
        from mesomb_payment import get_mesomb_client
        
        # Get form data
        payment_service = request.form.get('payment_service', 'MTN')
        payment_phone = request.form.get('payment_phone', '')
        
        # Create customer
        customer_data = session['passenger_details']
        customer = Customer.query.filter_by(email=customer_data['email']).first()
        
        if not customer:
            customer = Customer(
                name=customer_data['name'],
                email=customer_data['email'],
                phone=customer_data['phone']
            )
            db.session.add(customer)
            db.session.flush()
        
        # Create booking with pending status
        trip = Trip.query.get(session['trip_id'])
        selected_seats = session.get('selected_seats', [])
        if selected_seats and isinstance(selected_seats[0], dict):
            seat_list = [str(seat) if not isinstance(seat, dict) else str(seat.get('number', seat)) for seat in selected_seats]
        else:
            seat_list = [str(seat) for seat in selected_seats]
            
        booking_reference = generate_booking_reference()
        total_amount = len(seat_list) * trip.seat_price
        
        booking = Booking(
            booking_reference=booking_reference,
            trip_id=session['trip_id'],
            customer_id=customer.id,
            seat_numbers=','.join(seat_list),
            total_amount=total_amount,
            payment_status='pending',
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Use customer phone if payment phone not provided
        if not payment_phone:
            payment_phone = customer_data['phone']
        
        # Initialize MesomB payment
        mesomb = get_mesomb_client()
        
        # Prepare product information
        products = [{
            'id': f'BUS_TICKET_{booking_reference}',
            'name': f'Bus Ticket: {trip.route.origin} to {trip.route.destination}',
            'category': 'Transportation',
            'quantity': len(seat_list),
            'amount': total_amount
        }]
        
        # Process payment
        try:
            payment_result = mesomb.collect_payment(
                amount=total_amount,
                payer_phone=payment_phone,
                service=payment_service,
                customer_data=customer_data,
                booking_reference=booking_reference,
                products=products
            )
            
            # Check payment result status
            print(f"Payment result: {payment_result}")
            
            # Ensure payment_result is a dict
            if not isinstance(payment_result, dict):
                flash('Payment processing error. Please try again.', 'error')
                return redirect(url_for('user.payment', lang=g.language, booking_id=booking.id))
            
        except Exception as e:
            print(f"Payment processing exception: {str(e)}")
            flash('Payment processing error. Please try again.', 'error')
            return redirect(url_for('user.payment', lang=g.language, booking_id=booking.id))
        
        # Handle different MeSomb payment statuses
        mesomb_status = payment_result.get('mesomb_status', '').upper()
        payment_status = payment_result.get('status')
        
        print(f"Processing payment result - Status: {payment_status}, MeSomb Status: {mesomb_status}")
        
        if mesomb_status == 'SUCCESS':
            # FINAL STATUS: Payment completed successfully - ONLY confirm booking here
            booking.payment_reference = payment_result.get('transaction_id') or payment_result.get('trx_id')
            booking.payment_method = payment_result.get('service', 'Mobile Money')
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            
            # Update available seats
            trip.available_seats -= len(seat_list)
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'mesomb_status': 'SUCCESS',
                    'message': 'Payment completed successfully! Your booking is confirmed.',
                    'booking_id': booking.id,
                    'redirect_url': url_for('user.booking_confirmation', lang=g.language, booking_id=booking.id)
                })
            else:
                flash('Payment successful! Your booking has been confirmed.', 'success')
                return redirect(url_for('user.booking_confirmation', lang=g.language, booking_id=booking.id))
                
        elif mesomb_status == 'PENDING':
            # INTERMEDIATE STATUS: Payment is processing - DO NOT confirm booking yet
            booking.payment_reference = payment_result.get('transaction_id') or payment_result.get('trx_id')
            booking.payment_status = 'pending'
            booking.status = 'pending'
            db.session.commit()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'pending',
                    'mesomb_status': 'PENDING',
                    'message': payment_result.get('message', 'Payment is being processed. Please check your phone.'),
                    'booking_id': booking.id
                }), 202
            else:
                flash('Payment is being processed. Please check your phone to approve the transaction.', 'info')
                return redirect(url_for('user.check_booking_status', lang=g.language, booking_id=booking.id))
                
        elif mesomb_status in ['FAILED', 'CANCELED', 'ERRORED']:
            # FINAL/INTERMEDIATE ERROR STATUSES: Payment failed
            booking.payment_status = 'failed'
            booking.status = 'failed'
            db.session.commit()
            
            error_msg = payment_result.get('message', f'Payment {mesomb_status.lower()}. Please try again.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'mesomb_status': mesomb_status,
                    'message': error_msg,
                    'booking_id': booking.id
                }), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('user.payment', lang=g.language, booking_id=booking.id))
                
        else:
            # Unknown or missing MeSomb status - DO NOT confirm booking
            booking.payment_status = 'unknown'
            booking.status = 'pending'
            db.session.commit()
            
            warning_msg = f'Payment status unclear ({mesomb_status}). Please contact support if payment was deducted.'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'pending',
                    'mesomb_status': mesomb_status or 'UNKNOWN',
                    'message': warning_msg,
                    'booking_id': booking.id
                }), 202
            else:
                flash(warning_msg, 'warning')
                return redirect(url_for('user.check_booking_status', lang=g.language, booking_id=booking.id))
    
    trip = Trip.query.get_or_404(session['trip_id'])
    selected_seats = session['selected_seats']
    passenger_details = session['passenger_details']
    total_amount = len(selected_seats) * trip.seat_price
    
    return render_template('booking/payment_new.html',
                         trip=trip,
                         selected_seats=selected_seats,
                         passenger_details=passenger_details,
                         total_amount=total_amount,
                         booking_id=session.get('booking_id'))

@user_bp.route('/booking/payment-success/<int:booking_id>')
def payment_success(booking_id):
    """Handle payment success from MesomB"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify payment status if not already confirmed
    if booking.status != 'confirmed':
        from mesomb_payment import get_mesomb_client
        
        mesomb = get_mesomb_client()
        status_result = mesomb.check_transaction_status(booking.payment_reference)
        
        if status_result.get('status') == 'SUCCESS':
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            
            # Update available seats
            trip = Trip.query.get(booking.trip_id)
            seat_count = len(booking.get_seat_numbers())
            trip.available_seats -= seat_count
            
            db.session.commit()
    
    flash('Payment successful! Your booking has been confirmed.', 'success')
    return redirect(url_for('user.booking_confirmation', booking_id=booking.id))

@user_bp.route('/<lang>/booking/status/<int:booking_id>')
@language_required
def check_booking_status(lang, booking_id):
    """Check and update booking payment status with MesomB"""
    booking = Booking.query.get_or_404(booking_id)
    
    # If already confirmed, redirect to confirmation page
    if booking.status == 'confirmed':
        return redirect(url_for('user.booking_confirmation', lang=g.language, booking_id=booking.id))
    
    # Check payment status with MesomB
    if booking.payment_reference:
        from mesomb_payment import get_mesomb_client
        
        mesomb = get_mesomb_client()
        status_result = mesomb.check_transaction_status(booking.payment_reference)
        
        if status_result.get('success') and status_result.get('status') == 'SUCCESS':
            # Update booking to confirmed
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            
            # Update available seats
            trip = Trip.query.get(booking.trip_id)
            seat_count = len(booking.get_seat_numbers())
            trip.available_seats -= seat_count
            
            db.session.commit()
            
            flash('Payment confirmed! Your booking is complete.', 'success')
            return redirect(url_for('user.booking_confirmation', lang=g.language, booking_id=booking.id))
    
    # Payment still pending or failed
    return render_template('booking/status_check.html', booking=booking)

@user_bp.route('/<lang>/booking/payment-tracking/<int:booking_id>')
@language_required
def payment_tracking(lang, booking_id):
    """Enhanced payment tracking page with real-time status updates"""
    booking = Booking.query.get_or_404(booking_id)
    return render_template('booking/payment_tracking.html', booking=booking)

@user_bp.route('/<lang>/booking/confirmation/<int:booking_id>')
@language_required
def booking_confirmation(lang, booking_id):
    """Booking confirmation page with ticket options"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure booking is confirmed
    if booking.status != 'confirmed':
        flash('This booking is not yet confirmed.', 'warning')
        return redirect(url_for('user.check_booking_status', lang=g.language, booking_id=booking.id))
    
    return render_template('booking/confirmation.html', booking=booking)

@user_bp.route('/<lang>/booking/ticket/<int:booking_id>')
@language_required
def download_ticket(lang, booking_id):
    """Download ticket as PDF"""
    booking = Booking.query.get_or_404(booking_id)
    # TODO: Generate PDF ticket
    return jsonify({'message': 'Ticket generation coming soon'})

@user_bp.route('/<lang>/bookings')
@language_required
def my_bookings(lang):
    """User's booking history"""
    # For now, get bookings by email from session
    # In production, implement proper user authentication
    email = session.get('user_email')
    if not email:
        flash('Please login to view your bookings', 'info')
        return redirect(url_for('user.index', lang=g.language))
    
    customer = Customer.query.filter_by(email=email).first()
    if not customer:
        bookings = []
    else:
        bookings = Booking.query.filter_by(customer_id=customer.id).order_by(Booking.created_at.desc()).all()
    
    return render_template('bookings/my_bookings.html', bookings=bookings)

# Utility functions
def generate_booking_reference():
    """Generate unique booking reference"""
    import random
    import string
    while True:
        ref = 'NKP' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Booking.query.filter_by(booking_reference=ref).first():
            return ref

# Session management for seat selection
@user_bp.route('/api/select-seats', methods=['POST'])
def api_select_seats():
    """Store selected seats in session"""
    data = request.json
    trip_id = data.get('trip_id')
    seats = data.get('seats', [])
    
    if not trip_id or not seats:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Verify seats are available
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404
    
    # Get already booked seats
    bookings = Booking.query.filter_by(trip_id=trip_id, status='confirmed').all()
    booked_seats = []
    for booking in bookings:
        booked_seats.extend(booking.get_seat_numbers())
    
    # Check if any selected seat is already booked
    for seat in seats:
        if seat in booked_seats:
            return jsonify({'error': f'Seat {seat} is already booked'}), 400
    
    # Store in session
    session['selected_seats'] = seats
    session['trip_id'] = trip_id
    
    # Get language from request headers or default to French
    lang = request.headers.get('Accept-Language', 'fr')
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    
    return jsonify({'success': True, 'redirect': url_for('user.passenger_details', lang=lang)})

# Language preference
@user_bp.route('/api/set-language', methods=['POST'])
def set_language():
    """Set user's language preference"""
    lang = request.json.get('language', 'fr')
    session['language'] = lang
    return jsonify({'success': True, 'language': lang})

# Ticket retrieval
@user_bp.route('/retrieve-ticket')
def retrieve_ticket_page():
    """Ticket retrieval page"""
    return render_template('booking/retrieve_ticket.html')

@user_bp.route('/api/retrieve-tickets')
def api_retrieve_tickets():
    """API to retrieve tickets by phone, email, or reference"""
    method = request.args.get('method')
    value = request.args.get('value')
    
    if not method or not value:
        return jsonify({'tickets': []})
    
    tickets = []
    
    if method == 'phone':
        # Find customer by phone
        customer = Customer.query.filter_by(phone=value).first()
        if customer:
            bookings = Booking.query.filter_by(
                customer_id=customer.id,
                status='confirmed'
            ).order_by(Booking.created_at.desc()).all()
            
            for booking in bookings:
                tickets.append({
                    'id': booking.id,
                    'reference': booking.booking_reference,
                    'route': f"{booking.trip.route.origin} → {booking.trip.route.destination}",
                    'date': booking.trip.departure_time.strftime('%d/%m/%Y'),
                    'time': booking.trip.departure_time.strftime('%H:%M'),
                    'seats': booking.get_seat_numbers(),
                    'amount': booking.total_amount
                })
    
    elif method == 'email':
        # Find customer by email
        customer = Customer.query.filter_by(email=value).first()
        if customer:
            bookings = Booking.query.filter_by(
                customer_id=customer.id,
                status='confirmed'
            ).order_by(Booking.created_at.desc()).all()
            
            for booking in bookings:
                tickets.append({
                    'id': booking.id,
                    'reference': booking.booking_reference,
                    'route': f"{booking.trip.route.origin} → {booking.trip.route.destination}",
                    'date': booking.trip.departure_time.strftime('%d/%m/%Y'),
                    'time': booking.trip.departure_time.strftime('%H:%M'),
                    'seats': booking.get_seat_numbers(),
                    'amount': booking.total_amount
                })
    
    elif method == 'reference':
        # Find booking by reference
        booking = Booking.query.filter_by(
            booking_reference=value.upper(),
            status='confirmed'
        ).first()
        
        if booking:
            tickets.append({
                'id': booking.id,
                'reference': booking.booking_reference,
                'route': f"{booking.trip.route.origin} → {booking.trip.route.destination}",
                'date': booking.trip.departure_time.strftime('%d/%m/%Y'),
                'time': booking.trip.departure_time.strftime('%H:%M'),
                'seats': booking.get_seat_numbers(),
                'amount': booking.total_amount
            })
    
    return jsonify({'tickets': tickets})

# MesomB webhook handler
@user_bp.route('/api/mesomb-webhook', methods=['POST'])
def mesomb_webhook():
    """Handle MesomB payment webhook notifications"""
    try:
        from mesomb_payment import get_mesomb_client
        
        # Get webhook data
        webhook_data = request.get_json()
        raw_body = request.get_data(as_text=True)
        signature_header = request.headers.get('X-Mesomb-Signature', '')
        
        if not webhook_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Verify webhook signature
        mesomb = get_mesomb_client()
        if not mesomb.verify_webhook_signature(raw_body, signature_header):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Extract transaction details
        event = webhook_data.get('event')
        transaction = webhook_data.get('transaction', {})
        meta = webhook_data.get('meta', {})
        
        transaction_id = transaction.get('pk') or meta.get('pk')
        status = transaction.get('status') or meta.get('status')
        
        if not transaction_id:
            return jsonify({'error': 'Missing transaction ID'}), 400
        
        # Find booking by payment reference
        booking = Booking.query.filter_by(payment_reference=transaction_id).first()
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Update booking based on payment status
        if status == 'SUCCESS':
            # Payment successful - confirm booking
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            booking.payment_method = transaction.get('service', 'Mobile Money')
            
            # Update available seats
            trip = Trip.query.get(booking.trip_id)
            if trip:
                seat_count = len(booking.get_seat_numbers())
                trip.available_seats -= seat_count
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Booking confirmed',
                'booking_id': booking.id
            }), 200
            
        elif status == 'FAILED':
            # Payment failed
            booking.payment_status = 'failed'
            booking.status = 'cancelled'
            db.session.commit()
            
            return jsonify({
                'status': 'failed',
                'message': 'Payment failed',
                'booking_id': booking.id
            }), 200
            
        else:
            # Other status (PENDING, etc.)
            return jsonify({
                'status': 'received',
                'message': f'Status {status} received',
                'booking_id': booking.id
            }), 200
            
    except Exception as e:
        print(f"MesomB webhook error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/api/payment-status/<int:booking_id>')
def api_payment_status(booking_id):
    """API endpoint to check payment status for AJAX calls"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Determine status message and actions based on MeSomb status
    status_info = {
        'booking_id': booking.id,
        'payment_status': booking.payment_status,
        'booking_status': booking.status,
        'payment_reference': booking.payment_reference,
        'total_amount': booking.total_amount,
        'is_confirmed': booking.status == 'confirmed'
    }
    
    # Add MeSomb-specific status information based on official statuses
    if booking.payment_status == 'paid' and booking.status == 'confirmed':
        # FINAL STATUS: SUCCESS - Booking confirmed
        status_info.update({
            'mesomb_status': 'SUCCESS',
            'status_message': 'Paiement confirmé avec succès. Votre réservation est validée.',
            'can_retry': False,
            'next_action': 'view_ticket',
            'is_final': True
        })
    elif booking.payment_status == 'failed':
        # FINAL STATUS: FAILED - Payment definitively failed
        status_info.update({
            'mesomb_status': 'FAILED',
            'status_message': 'Paiement échoué définitivement. Veuillez réessayer avec un nouveau paiement.',
            'can_retry': True,
            'next_action': 'retry_payment',
            'is_final': True
        })
    elif booking.payment_status == 'pending':
        # INTERMEDIATE STATUS: PENDING - Still processing
        status_info.update({
            'mesomb_status': 'PENDING',
            'status_message': 'Paiement en cours de traitement. Vérifiez votre téléphone et approuvez la transaction.',
            'can_retry': True,
            'next_action': 'wait_or_retry',
            'is_final': False
        })
    elif booking.payment_status == 'unknown':
        # Unknown status - needs investigation
        status_info.update({
            'mesomb_status': 'UNKNOWN',
            'status_message': 'Statut du paiement inconnu. Contactez le support si le montant a été débité.',
            'can_retry': True,
            'next_action': 'contact_support',
            'is_final': False
        })
    else:
        # Default case
        status_info.update({
            'mesomb_status': 'UNKNOWN',
            'status_message': f'Statut non reconnu: {booking.payment_status}',
            'can_retry': True,
            'next_action': 'contact_support',
            'is_final': False
        })
    
    return jsonify(status_info)
