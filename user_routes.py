from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, g
from models import db, Operator, Route, Trip, Booking, Customer, OperatorBusType, OperatorLocation, RouteOperatorAssignment, BusType, SeatBlock
from mesomb_payment import get_mesomb_client
from datetime import datetime, timedelta
import json
from functools import wraps
from jinja2 import TemplateNotFound

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

# Helper to render language-specific booking templates with fallback
def render_booking_template(lang: str, template_name: str, **context):
    """Try to render booking/<lang>/<template>.html, fallback to booking/<template>.html"""
    lang_template = f"booking/{lang}/{template_name}"
    default_template = f"booking/{template_name}"
    try:
        return render_template(lang_template, **context)
    except TemplateNotFound:
        return render_template(default_template, **context)

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
    
    # Extract unique cities for from and to dropdowns
    from_cities = list(set([r.origin for r in routes]))
    to_cities = list(set([r.destination for r in routes]))
    
    # Sort alphabetically
    from_cities.sort()
    to_cities.sort()
    
    return jsonify({
        'from': from_cities,
        'to': to_cities
    })

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
    
    # Validate agency is required
    if not operator_id:
        return jsonify({'trips': [], 'error': 'Please select an agency'}), 400
    
    # Prevent same origin and destination
    if from_city == to_city:
        return jsonify({'trips': [], 'error': 'Origin and destination cannot be the same'}), 400
    
    # Parse the date first
    try:
        date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'trips': [], 'error': 'Invalid date format'}), 400
    
    # Get current time in Cameroon timezone using app configuration
    from app import get_cameroon_time, get_cameroon_time_utc
    current_time_cameroon = get_cameroon_time()
    current_time_utc = get_cameroon_time_utc()
    
    # Add 30 minutes buffer for booking cutoff
    booking_cutoff = current_time_utc + timedelta(minutes=30)
    
    print(f"Current time (Cameroon): {current_time_cameroon}")
    print(f"Current time (UTC): {current_time_utc}")
    print(f"Booking cutoff (UTC): {booking_cutoff}")
    print(f"Search date: {date_obj}")
    print(f"Current date (UTC): {current_time_utc.date()}")
    
    # Don't allow searching for past dates
    if date_obj < current_time_utc.date():
        return jsonify({'trips': [], 'message': 'Cannot search for trips in the past'})
    
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
    
    # For today's trips, use booking cutoff time; for future dates, use start of day
    if date_obj == current_time_utc.date():
        # Today's trips - exclude those departing within 30 minutes
        min_departure_time = booking_cutoff
        print(f"Today's search - minimum departure time: {min_departure_time}")
    else:
        # Future dates - show all trips from start of day
        min_departure_time = start_datetime
        print(f"Future date search - minimum departure time: {min_departure_time}")
    
    # Build query with required operator and exclude trips departing too soon
    query = Trip.query.filter(
        Trip.route_id == route.id,
        Trip.operator_id == operator_id,  # Operator is now required
        Trip.departure_time >= min_departure_time,
        Trip.departure_time <= end_datetime,
        Trip.status == 'scheduled'
    )
    
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
            'amenities': trip.bus_type.get_amenities() if trip.bus_type else [],
            'virtual_bus_id': trip.virtual_bus_id,
            'seat_price': float(trip.seat_price),
            'available_seats': trip.available_seats,
            'total_seats': config.capacity if config else trip.available_seats,
            'status': trip.status,
            'stops': route.get_waypoints() if route else []
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
    
    # Get blocked seats (excluding current session)
    session_id = session.get('session_id', '')
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    blocked_seats = SeatBlock.get_blocked_seats_for_trip(trip_id, exclude_session=session_id)
    
    # Combine booked and blocked seats
    unavailable_seats = list(set(booked_seats + blocked_seats))
    
    # Compute seating config numbers for template (avoid complex Jinja in JS)
    seats_per_row = (config.seats_per_row if config else (trip.bus_type.seats_per_row if trip.bus_type else 4))
    total_seats = (config.capacity if config else (trip.bus_type.capacity if trip.bus_type else 40))

    # Build seat_layout identical to admin structure
    if config and config.get_seat_layout():
        seat_layout = config.get_seat_layout()
    elif trip.bus_type and trip.bus_type.get_seat_layout():
        seat_layout = trip.bus_type.get_seat_layout()
    else:
        # Generate simple default
        seat_layout = []
        rows = (total_seats + seats_per_row - 1) // seats_per_row
        seat_num = 1
        for r in range(rows):
            row = []
            seats_in_row = min(seats_per_row, total_seats - (r * seats_per_row))
            for s in range(seats_in_row):
                row.append({'number': seat_num, 'position': chr(65 + s), 'type': 'standard'})
                seat_num += 1
            seat_layout.append(row)

    return render_booking_template(
        g.language,
        'seat_selection.html',
        trip=trip,
        config=config,
        booked_seats=unavailable_seats,  # Include both booked and blocked seats
        seat_layout=seat_layout,
        seats_per_row=seats_per_row,
        total_seats=total_seats,
        language=g.language
    )

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
    
    return render_booking_template(g.language, 'passenger_details.html',
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
            
            # Send email ticket after successful payment
            try:
                from email_utils import send_ticket_email
                send_ticket_email(booking)
            except Exception as e:
                print(f"Error sending ticket email: {str(e)}")
                # Don't fail the booking if email fails
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
    
    return render_booking_template(g.language, 'payment_new.html',
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
            
            # Send email ticket after confirmation
            try:
                from email_utils import send_ticket_email
                send_ticket_email(booking)
            except Exception as e:
                print(f"Error sending ticket email: {str(e)}")
            
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
    return render_booking_template(g.language, 'status_check.html', booking=booking)

@user_bp.route('/<lang>/booking/payment-tracking/<int:booking_id>')
@language_required
def payment_tracking(lang, booking_id):
    """Enhanced payment tracking page with real-time status updates"""
    booking = Booking.query.get_or_404(booking_id)
    return render_booking_template(g.language, 'payment_tracking.html', booking=booking)

@user_bp.route('/<lang>/booking/confirmation/<int:booking_id>')
@language_required
def booking_confirmation(lang, booking_id):
    """Booking confirmation page with ticket options"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure booking is confirmed
    if booking.status != 'confirmed':
        flash('This booking is not yet confirmed.', 'warning')
        return redirect(url_for('user.payment_status_check', lang=g.language, booking_id=booking.id))
    
    return render_booking_template(g.language, 'confirmation.html', booking=booking)

@user_bp.route('/<lang>/booking/payment-status/<int:booking_id>')
@language_required
def payment_status_check(lang, booking_id):
    """Payment status checking page for users who left and returned"""
    booking = Booking.query.get_or_404(booking_id)
    
    # If already confirmed, redirect to confirmation page
    if booking.status == 'confirmed':
        return redirect(url_for('user.booking_confirmation', lang=g.language, booking_id=booking.id))
    
    return render_booking_template(g.language, 'payment_status.html', booking=booking)

# Removed old download_ticket route - now handled by view_ticket with download functionality

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
    """Store selected seats in session and block them temporarily"""
    data = request.json
    trip_id = data.get('trip_id')
    seats = data.get('seats', [])
    
    if not trip_id or not seats:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Verify seats are available
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404
    
    # Get session ID
    session_id = session.get('session_id', '')
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    # Get already booked seats
    bookings = Booking.query.filter_by(trip_id=trip_id, status='confirmed').all()
    booked_seats = []
    for booking in bookings:
        booked_seats.extend(booking.get_seat_numbers())
    
    # Get blocked seats (excluding current session)
    blocked_seats = SeatBlock.get_blocked_seats_for_trip(trip_id, exclude_session=session_id)
    
    # Check if any selected seat is already booked or blocked
    unavailable_seats = set(booked_seats + blocked_seats)
    for seat in seats:
        if seat in unavailable_seats:
            return jsonify({'error': f'Seat {seat} is no longer available'}), 400
    
    # Block the selected seats for 6 minutes
    try:
        SeatBlock.block_seats(trip_id, seats, session_id)
    except Exception as e:
        return jsonify({'error': 'Failed to reserve seats. Please try again.'}), 500
    
    # Store in session
    session['selected_seats'] = seats
    session['trip_id'] = trip_id
    
    # Get language from request headers or default to French
    lang = request.headers.get('Accept-Language', 'fr')
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    
    return jsonify({
        'success': True, 
        'redirect': url_for('user.passenger_details', lang=lang),
        'blocked_until': (datetime.utcnow() + timedelta(minutes=6)).isoformat(),
        'message': 'Seats reserved for 6 minutes'
    })

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
    """API endpoint to check payment status for AJAX calls with intelligent status checking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # For pending payments, only check for SUCCESS - don't mark as failed prematurely
    if (booking.payment_status == 'pending' and booking.payment_reference and 
        booking.created_at and (datetime.utcnow() - booking.created_at).total_seconds() > 20):
        
        try:
            from mesomb_payment import get_mesomb_client
            mesomb = get_mesomb_client()
            
            # Try to get updated status from MeSomb - focus on SUCCESS detection
            status_result = mesomb.check_transaction_status(booking.payment_reference)
            
            if status_result and isinstance(status_result, dict):
                mesomb_status = status_result.get('status', '').upper()
                
                # ONLY update if we get a SUCCESS - let MeSomb handle failures via webhooks
                if mesomb_status == 'SUCCESS':
                    booking.payment_status = 'paid'
                    booking.status = 'confirmed'
                    db.session.commit()
                    print(f"✅ Payment SUCCESS detected for booking {booking.id}")
                # For any other status (PENDING, FAILED, etc.), keep current status
                # Let the 120-second window complete naturally
                
        except Exception as e:
            print(f"MeSomb status check error (non-critical): {str(e)}")
            # Continue with current booking status - errors are non-critical
    
    # Determine status message and actions based on current booking status
    status_info = {
        'booking_id': booking.id,
        'payment_status': booking.payment_status,
        'booking_status': booking.status,
        'payment_reference': booking.payment_reference,
        'total_amount': booking.total_amount,
        'is_confirmed': booking.status == 'confirmed',
        'created_at': booking.created_at.isoformat() if booking.created_at else None,
        'time_elapsed': int((datetime.utcnow() - booking.created_at).total_seconds()) if booking.created_at else 0
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

@user_bp.route('/api/booking-status/<int:booking_id>')
def api_booking_status(booking_id):
    """API endpoint to check booking payment status - for AJAX polling"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # If already confirmed, return success
        if booking.status == 'confirmed':
            return jsonify({
                'booking_status': 'confirmed',
                'payment_status': 'paid',
                'is_confirmed': True,
                'mesomb_status': 'SUCCESS',
                'message': 'Payment confirmed successfully'
            })
        
        # If payment reference exists, check with MeSomb
        if booking.payment_reference:
            try:
                from mesomb_payment import get_mesomb_client
                mesomb = get_mesomb_client()
                
                # Check transaction status with MeSomb
                status_result = mesomb.check_transaction_status(booking.payment_reference)
                
                if status_result and status_result.get('success'):
                    mesomb_status = status_result.get('status', 'UNKNOWN')
                    
                    if mesomb_status == 'SUCCESS':
                        # Update booking to confirmed
                        booking.payment_status = 'paid'
                        booking.status = 'confirmed'
                        
                        # Update available seats
                        trip = Trip.query.get(booking.trip_id)
                        if trip:
                            seat_count = len(booking.get_seat_numbers())
                            trip.available_seats -= seat_count
                        
                        # Send email ticket after confirmation
                        try:
                            from email_utils import send_ticket_email
                            send_ticket_email(booking)
                        except Exception as e:
                            print(f"Error sending ticket email: {str(e)}")
                        
                        db.session.commit()
                        
                        return jsonify({
                            'booking_status': 'confirmed',
                            'payment_status': 'paid',
                            'is_confirmed': True,
                            'mesomb_status': 'SUCCESS',
                            'message': 'Payment confirmed successfully'
                        })
                    
                    elif mesomb_status == 'FAILED':
                        # Payment failed
                        booking.payment_status = 'failed'
                        booking.status = 'failed'
                        db.session.commit()
                        
                        return jsonify({
                            'booking_status': 'failed',
                            'payment_status': 'failed',
                            'is_confirmed': False,
                            'mesomb_status': 'FAILED',
                            'message': 'Payment failed',
                            'error_message': status_result.get('message', 'Payment was not successful')
                        })
                    
                    else:
                        # Still pending
                        return jsonify({
                            'booking_status': booking.status,
                            'payment_status': booking.payment_status,
                            'is_confirmed': False,
                            'mesomb_status': mesomb_status,
                            'message': 'Payment is still being processed'
                        })
                
                else:
                    # Error checking status
                    return jsonify({
                        'booking_status': booking.status,
                        'payment_status': booking.payment_status,
                        'is_confirmed': False,
                        'mesomb_status': 'UNKNOWN',
                        'message': 'Unable to verify payment status',
                        'error_message': 'Could not connect to payment provider'
                    })
                    
            except Exception as e:
                print(f"Error checking MeSomb status: {str(e)}")
                return jsonify({
                    'booking_status': booking.status,
                    'payment_status': booking.payment_status,
                    'is_confirmed': False,
                    'mesomb_status': 'ERROR',
                    'message': 'Error checking payment status',
                    'error_message': str(e)
                })
        
        else:
            # No payment reference yet
            return jsonify({
                'booking_status': booking.status,
                'payment_status': booking.payment_status,
                'is_confirmed': False,
                'mesomb_status': 'PENDING',
                'message': 'Waiting for payment initiation'
            })
            
    except Exception as e:
        print(f"Error in booking status API: {str(e)}")
        return jsonify({
            'error': True,
            'message': 'Error checking booking status',
            'error_message': str(e)
        }), 500

@user_bp.route('/api/contact-settings')
def api_contact_settings():
    """API endpoint to get contact settings for the widget"""
    import os
    
    contact_settings = {}
    env_path = '.env'
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key in ['SUPPORT_PHONE', 'SUPPORT_EMAIL', 'WHATSAPP_NUMBER', 'BUSINESS_HOURS', 'CONTACT_WIDGET_ENABLED']:
                        contact_settings[key.lower()] = value
    
    # Only return settings if widget is enabled
    widget_enabled = contact_settings.get('contact_widget_enabled', 'true').lower() == 'true'
    
    if not widget_enabled:
        return jsonify({'enabled': False})
    
    return jsonify({
        'enabled': True,
        'phone': contact_settings.get('support_phone', ''),
        'email': contact_settings.get('support_email', ''),
        'whatsapp': contact_settings.get('whatsapp_number', ''),
        'business_hours': contact_settings.get('business_hours', '24/7')
    })

# My Bookings Management
@user_bp.route('/<lang>/my-bookings')
@language_required
def my_bookings_search(lang):
    """My bookings page with search functionality"""
    search_query = request.args.get('search', '').strip()
    booking_ref = request.args.get('ref', '').strip()
    verify_input = request.args.get('verify', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    bookings = []
    
    # Search by phone/email or booking reference
    if search_query or booking_ref:
        query = Booking.query.join(Customer).join(Trip).join(Route).join(Operator)
        
        if booking_ref:
            # Search by booking reference with optional verification
            query = query.filter(Booking.booking_reference.ilike(f'%{booking_ref}%'))
            
            if verify_input:
                # Additional verification with phone or email
                query = query.filter(
                    db.or_(
                        Customer.phone.ilike(f'%{verify_input}%'),
                        Customer.email.ilike(f'%{verify_input}%')
                    )
                )
        elif search_query:
            # Search by phone or email
            query = query.filter(
                db.or_(
                    Customer.phone.ilike(f'%{search_query}%'),
                    Customer.email.ilike(f'%{search_query}%')
                )
            )
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(Booking.status == status_filter)
        
        # Order by creation date (newest first)
        bookings = query.order_by(Booking.created_at.desc()).all()
    
    return render_booking_template(
        g.language,
        'my_bookings.html',
        bookings=bookings,
        now=datetime.utcnow()
    )

# Individual ticket view
@user_bp.route('/<lang>/booking/ticket/<int:booking_id>')
@language_required
def view_ticket(lang, booking_id):
    """View individual ticket in POS style"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        print(f"DEBUG: Found booking {booking.id} - {booking.booking_reference}")
        print(f"DEBUG: Booking status: {booking.status}")
        print(f"DEBUG: Trip: {booking.trip.route.origin} -> {booking.trip.route.destination}")
        
        # Try direct template rendering first for debugging
        try:
            return render_template('booking/ticket.html', 
                                 booking=booking, 
                                 current_language=g.language,
                                 site_name="Nkolo Pass")
        except Exception as template_error:
            print(f"Template error: {str(template_error)}")
            return render_booking_template(
                g.language,
                'ticket.html',
                booking=booking
            )
    except Exception as e:
        print(f"ERROR in view_ticket: {str(e)}")
        flash(f'Error loading ticket: {str(e)}', 'error')
        return redirect(url_for('user.my_bookings_search', lang=g.language))

# Seat change functionality
@user_bp.route('/<lang>/booking/change-seats/<int:booking_id>')
@language_required
def change_seats(lang, booking_id):
    """Change seats for existing booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify booking is confirmed and trip hasn't departed
    if booking.status != 'confirmed':
        flash('Only confirmed bookings can be modified', 'error')
        return redirect(url_for('user.my_bookings_search', lang=g.language))
    
    if booking.trip.departure_time <= datetime.utcnow():
        flash('Cannot modify bookings for past trips', 'error')
        return redirect(url_for('user.my_bookings_search', lang=g.language))
    
    # Get current seat layout and booked seats
    trip = booking.trip
    config = OperatorBusType.query.filter_by(
        operator_id=trip.operator_id,
        bus_type_id=trip.bus_type_id
    ).first()
    
    # Get booked seats (excluding current booking)
    other_bookings = Booking.query.filter(
        Booking.trip_id == trip.id,
        Booking.status == 'confirmed',
        Booking.id != booking.id
    ).all()
    
    booked_seats = []
    for other_booking in other_bookings:
        booked_seats.extend(other_booking.get_seat_numbers())
    
    # Get blocked seats
    session_id = session.get('session_id', '')
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    blocked_seats = SeatBlock.get_blocked_seats_for_trip(trip.id, exclude_session=session_id)
    unavailable_seats = list(set(booked_seats + blocked_seats))
    
    # Build seat layout
    seats_per_row = (config.seats_per_row if config else (trip.bus_type.seats_per_row if trip.bus_type else 4))
    total_seats = (config.capacity if config else (trip.bus_type.capacity if trip.bus_type else 40))
    
    if config and config.get_seat_layout():
        seat_layout = config.get_seat_layout()
    elif trip.bus_type and trip.bus_type.get_seat_layout():
        seat_layout = trip.bus_type.get_seat_layout()
    else:
        # Generate simple default
        seat_layout = []
        rows = (total_seats + seats_per_row - 1) // seats_per_row
        seat_num = 1
        for r in range(rows):
            row = []
            seats_in_row = min(seats_per_row, total_seats - (r * seats_per_row))
            for s in range(seats_in_row):
                row.append({'number': seat_num, 'position': chr(65 + s), 'type': 'standard'})
                seat_num += 1
            seat_layout.append(row)
    
    return render_booking_template(
        g.language,
        'change_seats.html',
        booking=booking,
        trip=trip,
        config=config,
        booked_seats=unavailable_seats,
        current_seats=booking.get_seat_numbers(),
        seat_layout=seat_layout,
        seats_per_row=seats_per_row,
        total_seats=total_seats
    )

# Trip change functionality
@user_bp.route('/<lang>/booking/change-trip/<int:booking_id>')
@language_required
def change_trip(lang, booking_id):
    """Change trip for existing booking (same operator, same price)"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify booking is confirmed and trip hasn't departed
    if booking.status != 'confirmed':
        flash('Only confirmed bookings can be modified', 'error')
        return redirect(url_for('user.my_bookings_search', lang=g.language))
    
    if booking.trip.departure_time <= datetime.utcnow():
        flash('Cannot modify bookings for past trips', 'error')
        return redirect(url_for('user.my_bookings_search', lang=g.language))
    
    # Find alternative trips (same operator, same route, same price, future dates)
    alternative_trips = Trip.query.filter(
        Trip.operator_id == booking.trip.operator_id,
        Trip.route_id == booking.trip.route_id,
        Trip.seat_price == booking.trip.seat_price,
        Trip.departure_time > datetime.utcnow(),
        Trip.id != booking.trip.id
    ).order_by(Trip.departure_time.asc()).all()
    
    # Filter trips with enough available seats
    available_trips = []
    required_seats = len(booking.get_seat_numbers())
    
    for trip in alternative_trips:
        # Count booked seats
        trip_bookings = Booking.query.filter_by(trip_id=trip.id, status='confirmed').all()
        booked_count = sum(len(b.get_seat_numbers()) for b in trip_bookings)
        
        # Get trip capacity
        config = OperatorBusType.query.filter_by(
            operator_id=trip.operator_id,
            bus_type_id=trip.bus_type_id
        ).first()
        
        capacity = (config.capacity if config else (trip.bus_type.capacity if trip.bus_type else 40))
        available_seats = capacity - booked_count
        
        if available_seats >= required_seats:
            available_trips.append({
                'trip': trip,
                'available_seats': available_seats
            })
    
    return render_booking_template(
        g.language,
        'change_trip.html',
        booking=booking,
        alternative_trips=available_trips,
        required_seats=required_seats
    )

# API endpoints for seat and trip changes
@user_bp.route('/<lang>/api/change-seats', methods=['POST'])
@language_required
def api_change_seats(lang):
    """API endpoint to process seat changes"""
    try:
        data = request.json
        booking_id = data.get('booking_id')
        new_seats = data.get('new_seats', [])
        
        if not booking_id or not new_seats:
            return jsonify({'success': False, 'message': 'Invalid data'}), 400
        
        booking = Booking.query.get_or_404(booking_id)
        
        # Verify booking can be modified
        if booking.status != 'confirmed':
            return jsonify({'success': False, 'message': 'Only confirmed bookings can be modified'}), 400
        
        if booking.trip.departure_time <= datetime.utcnow() + timedelta(hours=2):
            return jsonify({'success': False, 'message': 'Cannot modify bookings less than 2 hours before departure'}), 400
        
        # Check if new seats are available
        other_bookings = Booking.query.filter(
            Booking.trip_id == booking.trip.id,
            Booking.status == 'confirmed',
            Booking.id != booking.id
        ).all()
        
        booked_seats = []
        for other_booking in other_bookings:
            booked_seats.extend(other_booking.get_seat_numbers())
        
        # Check availability
        for seat in new_seats:
            if seat in booked_seats:
                return jsonify({'success': False, 'message': f'Seat {seat} is no longer available'}), 400
        
        # Update booking with new seats
        booking.seat_numbers = json.dumps(new_seats)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Seats changed successfully',
            'new_seats': new_seats
        })
        
    except Exception as e:
        print(f"Error changing seats: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@user_bp.route('/<lang>/api/change-trip', methods=['POST'])
@language_required
def api_change_trip(lang):
    """API endpoint to process trip changes"""
    try:
        data = request.json
        booking_id = data.get('booking_id')
        new_trip_id = data.get('new_trip_id')
        
        if not booking_id or not new_trip_id:
            return jsonify({'success': False, 'message': 'Invalid data'}), 400
        
        booking = Booking.query.get_or_404(booking_id)
        new_trip = Trip.query.get_or_404(new_trip_id)
        
        # Verify booking can be modified
        if booking.status != 'confirmed':
            return jsonify({'success': False, 'message': 'Only confirmed bookings can be modified'}), 400
        
        if booking.trip.departure_time <= datetime.utcnow() + timedelta(hours=2):
            return jsonify({'success': False, 'message': 'Cannot modify bookings less than 2 hours before departure'}), 400
        
        # Verify new trip is valid (same operator, route, price)
        if (new_trip.operator_id != booking.trip.operator_id or
            new_trip.route_id != booking.trip.route_id or
            new_trip.seat_price != booking.trip.seat_price):
            return jsonify({'success': False, 'message': 'Invalid trip selection'}), 400
        
        # Check if seats are available on new trip
        required_seats = len(booking.get_seat_numbers())
        new_trip_bookings = Booking.query.filter_by(trip_id=new_trip.id, status='confirmed').all()
        booked_count = sum(len(b.get_seat_numbers()) for b in new_trip_bookings)
        
        # Get trip capacity
        config = OperatorBusType.query.filter_by(
            operator_id=new_trip.operator_id,
            bus_type_id=new_trip.bus_type_id
        ).first()
        
        capacity = (config.capacity if config else (new_trip.bus_type.capacity if new_trip.bus_type else 40))
        available_seats = capacity - booked_count
        
        if available_seats < required_seats:
            return jsonify({'success': False, 'message': 'Not enough seats available on selected trip'}), 400
        
        # Update booking with new trip
        booking.trip_id = new_trip.id
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Trip changed successfully',
            'new_trip_date': new_trip.departure_time.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        print(f"Error changing trip: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# Booking Management Verification Route
@user_bp.route('/<lang>/manage-booking')
@language_required
def manage_booking_verify(lang):
    """Verify booking reference and redirect to management interface"""
    booking_ref = request.args.get('ref', '').strip()
    verify_input = request.args.get('verify', '').strip()
    
    if not booking_ref or not verify_input:
        flash('Please provide both booking reference and phone/email for verification', 'error')
        return redirect(url_for('index', lang=g.language))
    
    # Find booking by reference
    booking = Booking.query.filter_by(booking_reference=booking_ref).first()
    
    if not booking:
        flash('Booking reference not found', 'error')
        return redirect(url_for('index', lang=g.language))
    
    # Verify phone or email matches
    customer = booking.customer
    if not customer:
        flash('Booking verification failed', 'error')
        return redirect(url_for('index', lang=g.language))
    
    # Check if verify_input matches phone or email
    phone_match = customer.phone and verify_input in customer.phone
    email_match = customer.email and verify_input.lower() in customer.email.lower()
    
    if not (phone_match or email_match):
        flash('Phone number or email does not match our records', 'error')
        return redirect(url_for('index', lang=g.language))
    
    # Verification successful - redirect to booking management
    return render_booking_template(
        g.language,
        'booking_management.html',
        booking=booking,
        now=datetime.utcnow()
    )
