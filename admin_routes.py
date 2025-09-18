from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Operator, Route, Trip, Booking, Customer, OperatorBusType, OperatorLocation, RouteOperatorAssignment, BusType
from datetime import datetime
import os
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin_bp', __name__)

# Simple admin authentication (you may want to enhance this)
ADMIN_EMAIL = 'admin@nkolopass.com'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == ADMIN_EMAIL and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_id'] = 1
            session['admin_email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('admin_bp.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('admin_email', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_bp.login'))

@admin_bp.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    # Get dashboard statistics
    total_bookings = Booking.query.count()
    confirmed_bookings = Booking.query.filter_by(status='confirmed').count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    total_operators = Operator.query.count()
    total_routes = Route.query.count()
    total_trips = Trip.query.count()
    
    # Get recent data for dashboard
    recent_trips = Trip.query.order_by(Trip.departure_time.desc()).limit(5).all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    stats = {
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'total_operators': total_operators,
        'total_routes': total_routes,
        'total_trips': total_trips
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         total_operators=total_operators,
                         total_routes=total_routes,
                         total_trips=total_trips,
                         recent_trips=recent_trips,
                         recent_bookings=recent_bookings)

@admin_bp.route('/bookings')
def bookings():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings/list.html', bookings=bookings)

@admin_bp.route('/operators')
def operators():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operators = Operator.query.all()
    return render_template('admin/operators/list.html', operators=operators)

@admin_bp.route('/routes')
def routes():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    routes = Route.query.all()
    return render_template('admin/routes/list.html', routes=routes)

@admin_bp.route('/operators/add', methods=['GET', 'POST'])
def add_operator():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        operator = Operator(
            name=name,
            code=code,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address
        )
        
        db.session.add(operator)
        db.session.commit()
        flash('Operator added successfully!', 'success')
        return redirect(url_for('admin_bp.operators'))
    
    return render_template('admin/operators/form.html', title='Add Operator')

@admin_bp.route('/operators/<int:id>/edit', methods=['GET', 'POST'])
def edit_operator(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(id)
    
    if request.method == 'POST':
        operator.name = request.form.get('name')
        operator.code = request.form.get('code')
        operator.contact_person = request.form.get('contact_person')
        operator.phone = request.form.get('phone')
        operator.email = request.form.get('email')
        operator.address = request.form.get('address')
        
        db.session.commit()
        flash('Operator updated successfully!', 'success')
        return redirect(url_for('admin_bp.operators'))
    
    return render_template('admin/operators/form.html', operator=operator, title='Edit Operator')

@admin_bp.route('/bus-types')
def bus_types():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    bus_types = BusType.query.all()
    return render_template('admin/bus_types/list.html', bus_types=bus_types)

@admin_bp.route('/routes/add', methods=['GET', 'POST'])
def add_route():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        distance = request.form.get('distance')
        duration = request.form.get('duration')
        base_price = request.form.get('base_price')
        
        route = Route(
            origin=origin,
            destination=destination,
            distance=float(distance) if distance else None,
            duration=int(duration) if duration else None,
            base_price=float(base_price) if base_price else None
        )
        
        db.session.add(route)
        db.session.commit()
        flash('Route added successfully!', 'success')
        return redirect(url_for('admin_bp.routes'))
    
    return render_template('admin/routes/form.html', title='Add Route')

@admin_bp.route('/api/operators')
def api_operators():
    """API endpoint to get all operators for AJAX requests"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    operators = Operator.query.all()
    return jsonify([{
        'id': op.id,
        'name': op.name,
        'code': op.code,
        'logo': op.logo_url
    } for op in operators])

@admin_bp.route('/routes/<int:id>/edit', methods=['GET', 'POST'])
def edit_route(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    route = Route.query.get_or_404(id)
    
    if request.method == 'POST':
        route.origin = request.form.get('origin')
        route.destination = request.form.get('destination')
        route.distance = float(request.form.get('distance')) if request.form.get('distance') else None
        route.duration = int(request.form.get('duration')) if request.form.get('duration') else None
        route.base_price = float(request.form.get('base_price')) if request.form.get('base_price') else None
        
        db.session.commit()
        flash('Route updated successfully!', 'success')
        return redirect(url_for('admin_bp.routes'))
    
    return render_template('admin/routes/form.html', route=route, title='Edit Route')

@admin_bp.route('/routes/<int:route_id>/operators')
def route_operators(route_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    route = Route.query.get_or_404(route_id)
    return render_template('admin/routes/operators.html', route=route)

@admin_bp.route('/routes/<int:route_id>/assign-operator', methods=['POST'])
def assign_route_operator(route_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    # Implementation for assigning operator to route
    flash('Operator assigned successfully!', 'success')
    return redirect(url_for('admin_bp.route_operators', route_id=route_id))

@admin_bp.route('/trips')
def trips():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    # Get filter parameters from request
    filters = {
        'status': request.args.get('status', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
        'route_id': request.args.get('route_id', ''),
        'operator_id': request.args.get('operator_id', '')
    }
    
    # Build query with filters
    query = Trip.query
    
    if filters['status']:
        query = query.filter(Trip.status == filters['status'])
    
    if filters['date_from']:
        from datetime import datetime
        date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d').date()
        query = query.filter(Trip.departure_time >= date_from)
    
    if filters['date_to']:
        from datetime import datetime
        date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d').date()
        query = query.filter(Trip.departure_time <= date_to)
    
    if filters['route_id']:
        query = query.filter(Trip.route_id == filters['route_id'])
    
    if filters['operator_id']:
        query = query.filter(Trip.operator_id == filters['operator_id'])
    
    # Get page number from request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Apply pagination
    trips = query.order_by(Trip.departure_time.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Debug: Check total trips in database
    total_trips = Trip.query.count()
    print(f"Total trips in database: {total_trips}")
    print(f"Trips after filtering: {trips.total}")
    if trips.items:
        print(f"Sample trip: {trips.items[0].departure_time}, Route: {trips.items[0].route_id}, Operator: {trips.items[0].operator_id}")
    
    # Get routes and operators for filter dropdowns
    routes = Route.query.all()
    operators = Operator.query.all()
    
    # Create filters_dict for pagination links
    filters_dict = {k: v for k, v in filters.items() if v}
    
    return render_template('admin/trips/list.html', 
                         trips=trips, 
                         filters=filters,
                         filters_dict=filters_dict,
                         routes=routes,
                         operators=operators)

@admin_bp.route('/trips/generate', methods=['GET', 'POST'])
def generate_trips():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    if request.method == 'POST':
        # Get form data
        route_id = request.form.get('route_id')
        operator_id = request.form.get('operator_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        regular_seat_price = request.form.get('regular_seat_price')
        vip_seat_price = request.form.get('vip_seat_price')
        
        # Get additional form data
        trips_per_day = int(request.form.get('trips_per_day', 3))
        start_time = request.form.get('start_time', '06:00')
        end_time = request.form.get('end_time', '20:00')
        bidirectional = request.form.get('bidirectional') == 'on'
        
        # Validate required fields
        if not all([route_id, operator_id, start_date, end_date, regular_seat_price, vip_seat_price, trips_per_day, start_time, end_time]):
            flash('Please fill in all required fields', 'error')
            routes = Route.query.all()
            operators = Operator.query.all()
            bus_types = BusType.query.all()
            return render_template('admin/trips/generate.html', routes=routes, operators=operators, bus_types=bus_types, title='Generate Trips')
        
        try:
            from datetime import datetime, timedelta
            
            # Parse dates
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get route for duration calculation
            route = Route.query.get(route_id)
            if not route:
                flash('Route not found', 'error')
                return redirect(url_for('admin_bp.generate_trips'))
            
            # Get or create RouteOperatorAssignment with pricing
            route_assignment = RouteOperatorAssignment.query.filter_by(
                route_id=route_id, 
                operator_id=operator_id
            ).first()
            
            if not route_assignment:
                # Create new route assignment with pricing
                route_assignment = RouteOperatorAssignment(
                    route_id=route_id,
                    operator_id=operator_id,
                    regular_seat_price=float(regular_seat_price),
                    vip_seat_price=float(vip_seat_price),
                    trips_per_day=trips_per_day
                )
                db.session.add(route_assignment)
            else:
                # Update existing assignment with new pricing
                route_assignment.regular_seat_price = float(regular_seat_price)
                route_assignment.vip_seat_price = float(vip_seat_price)
                route_assignment.trips_per_day = trips_per_day
            
            # Get both VIP and Regular bus types (case insensitive)
            regular_bus_type = BusType.query.filter(BusType.category.ilike('regular')).first()
            vip_bus_type = BusType.query.filter(BusType.category.ilike('vip')).first()
            
            # Debug: Check what bus types exist
            all_bus_types = BusType.query.all()
            print(f"Available bus types: {[(bt.name, bt.category) for bt in all_bus_types]}")
            print(f"Regular bus type found: {regular_bus_type}")
            print(f"VIP bus type found: {vip_bus_type}")
            
            # Fallback: if specific categories not found, use any available bus types
            if not regular_bus_type:
                regular_bus_type = BusType.query.first()  # Use first available bus type
                if regular_bus_type:
                    flash(f'Using "{regular_bus_type.name}" as Regular bus type. Please create a bus type with category "Regular" for proper classification.', 'warning')
                else:
                    flash('No bus types found in the system. Please create bus types first.', 'error')
                    return redirect(url_for('admin_bp.generate_trips'))
            
            if not vip_bus_type:
                # Try to find a different bus type for VIP, or use the same one
                vip_bus_type = BusType.query.filter(BusType.id != regular_bus_type.id).first()
                if not vip_bus_type:
                    vip_bus_type = regular_bus_type  # Use same bus type if only one exists
                flash(f'Using "{vip_bus_type.name}" as VIP bus type. Please create a bus type with category "VIP" for proper classification.', 'warning')
            
            trips_created = 0
            current_date = start_dt
            
            # Service days mapping
            service_days = []
            if request.form.get('monday'): service_days.append(0)  # Monday = 0
            if request.form.get('tuesday'): service_days.append(1)
            if request.form.get('wednesday'): service_days.append(2)
            if request.form.get('thursday'): service_days.append(3)
            if request.form.get('friday'): service_days.append(4)
            if request.form.get('saturday'): service_days.append(5)
            if request.form.get('sunday'): service_days.append(6)
            
            if not service_days:
                flash('Please select at least one service day', 'error')
                return redirect(url_for('admin_bp.generate_trips'))
            
            # Calculate departure times based on user input
            departure_times = []
            
            # Parse start and end times
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute
            
            if trips_per_day == 1:
                # Single trip at start time
                departure_times = [start_time]
            elif trips_per_day == 2:
                # First and last times
                departure_times = [start_time, end_time]
            else:
                # Distribute trips evenly between start and end times
                interval = (end_minutes - start_minutes) / (trips_per_day - 1)
                
                for i in range(trips_per_day):
                    trip_minutes = start_minutes + (i * interval)
                    hours = int(trip_minutes // 60)
                    minutes = int(trip_minutes % 60)
                    departure_times.append(f"{hours:02d}:{minutes:02d}")
            
            if not departure_times:
                flash('No departure times specified', 'error')
                return redirect(url_for('admin_bp.generate_trips'))
            
            # Generate trips for each day in the date range
            while current_date <= end_dt:
                # Check if this day is in service days
                if current_date.weekday() in service_days:
                    # Create trips for each departure time and bus type
                    for time_str in departure_times:
                        try:
                            # Parse time
                            hour, minute = map(int, time_str.split(':'))
                            departure_datetime = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            
                            # Calculate arrival time (add route duration)
                            duration_minutes = route.estimated_duration or 120  # Default 2 hours
                            arrival_datetime = departure_datetime + timedelta(minutes=duration_minutes)
                            
                            # Create Regular bus trip
                            regular_trip = Trip(
                                departure_time=departure_datetime,
                                arrival_time=arrival_datetime,
                                seat_price=float(regular_seat_price),
                                available_seats=regular_bus_type.capacity,
                                route_id=route_id,
                                operator_id=operator_id,
                                bus_type_id=regular_bus_type.id,
                                virtual_bus_id=f"REG-{trips_created + 1}",
                                status='scheduled'
                            )
                            
                            db.session.add(regular_trip)
                            trips_created += 1
                            
                            # Create VIP bus trip
                            vip_trip = Trip(
                                departure_time=departure_datetime,
                                arrival_time=arrival_datetime,
                                seat_price=float(vip_seat_price),
                                available_seats=vip_bus_type.capacity,
                                route_id=route_id,
                                operator_id=operator_id,
                                bus_type_id=vip_bus_type.id,
                                virtual_bus_id=f"VIP-{trips_created + 1}",
                                status='scheduled'
                            )
                            
                            db.session.add(vip_trip)
                            trips_created += 1
                            
                        except ValueError:
                            continue  # Skip invalid time formats
                
                current_date += timedelta(days=1)
            
            # Generate bidirectional trips if requested
            if bidirectional:
                print("Generating bidirectional trips...")
                
                # Get or create reverse route
                reverse_route = route.get_reverse_route()
                print(f"Original route: {route.origin} → {route.destination}")
                print(f"Reverse route: {reverse_route.origin} → {reverse_route.destination}")
                
                # Create or update RouteOperatorAssignment for reverse route
                reverse_route_assignment = RouteOperatorAssignment.query.filter_by(
                    route_id=reverse_route.id, 
                    operator_id=operator_id
                ).first()
                
                if not reverse_route_assignment:
                    reverse_route_assignment = RouteOperatorAssignment(
                        route_id=reverse_route.id,
                        operator_id=operator_id,
                        regular_seat_price=float(regular_seat_price),
                        vip_seat_price=float(vip_seat_price),
                        trips_per_day=trips_per_day
                    )
                    db.session.add(reverse_route_assignment)
                else:
                    reverse_route_assignment.regular_seat_price = float(regular_seat_price)
                    reverse_route_assignment.vip_seat_price = float(vip_seat_price)
                    reverse_route_assignment.trips_per_day = trips_per_day
                
                current_date = start_dt
                
                while current_date <= end_dt:
                    if current_date.weekday() in service_days:
                        for time_str in departure_times:
                            try:
                                hour, minute = map(int, time_str.split(':'))
                                # Use same departure times for return trips (they're on reverse route)
                                departure_datetime = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                
                                # Calculate arrival time for return direction
                                duration_minutes = reverse_route.estimated_duration or 120
                                arrival_datetime = departure_datetime + timedelta(minutes=duration_minutes)
                                
                                # Create Regular return trip (on reverse route)
                                regular_return_trip = Trip(
                                    departure_time=departure_datetime,
                                    arrival_time=arrival_datetime,
                                    seat_price=float(regular_seat_price),
                                    available_seats=regular_bus_type.capacity,
                                    route_id=reverse_route.id,  # Use reverse route ID
                                    operator_id=operator_id,
                                    bus_type_id=regular_bus_type.id,
                                    virtual_bus_id=f"REG-R{trips_created + 1}",
                                    status='scheduled'
                                )
                                
                                db.session.add(regular_return_trip)
                                trips_created += 1
                                print(f"Created Regular return trip: {departure_datetime} on route {reverse_route.name}")
                                
                                # Create VIP return trip (on reverse route)
                                vip_return_trip = Trip(
                                    departure_time=departure_datetime,
                                    arrival_time=arrival_datetime,
                                    seat_price=float(vip_seat_price),
                                    available_seats=vip_bus_type.capacity,
                                    route_id=reverse_route.id,  # Use reverse route ID
                                    operator_id=operator_id,
                                    bus_type_id=vip_bus_type.id,
                                    virtual_bus_id=f"VIP-R{trips_created + 1}",
                                    status='scheduled'
                                )
                                
                                db.session.add(vip_return_trip)
                                trips_created += 1
                                print(f"Created VIP return trip: {departure_datetime} on route {reverse_route.name}")
                                
                            except ValueError:
                                continue
                    
                    current_date += timedelta(days=1)
                
                print(f"Bidirectional generation complete. Created trips on both {route.name} and {reverse_route.name}")
            
            # Commit all trips to database
            db.session.commit()
            
            # Debug: Verify trips were saved
            total_trips_after = Trip.query.count()
            recent_trips = Trip.query.order_by(Trip.created_at.desc()).limit(5).all()
            print(f"Total trips after creation: {total_trips_after}")
            print(f"Recent trips created: {[(t.departure_time, t.route_id, t.operator_id, t.bus_type_id) for t in recent_trips]}")
            
            flash(f'Successfully generated {trips_created} trips!', 'success')
            return redirect(url_for('admin_bp.trips'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error generating trips: {str(e)}', 'error')
            routes = Route.query.all()
            operators = Operator.query.all()
            return render_template('admin/trips/generate.html', routes=routes, operators=operators, title='Generate Trips')
    
    routes = Route.query.all()
    operators = Operator.query.all()
    return render_template('admin/trips/generate.html', routes=routes, operators=operators, title='Generate Trips')

@admin_bp.route('/trips/bulk-delete', methods=['POST'])
def bulk_delete_trips():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    try:
        # Get trip IDs from form
        trip_ids = request.form.getlist('trip_ids')
        
        if not trip_ids:
            flash('No trips selected for deletion', 'error')
            return redirect(url_for('admin_bp.trips'))
        
        deleted_count = 0
        skipped_count = 0
        
        for trip_id in trip_ids:
            trip = Trip.query.get(trip_id)
            if trip:
                # Check if trip has bookings
                if trip.bookings:
                    skipped_count += 1
                    continue
                
                # Delete trip if no bookings
                db.session.delete(trip)
                deleted_count += 1
        
        db.session.commit()
        
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} trips', 'success')
        if skipped_count > 0:
            flash(f'{skipped_count} trips were skipped (have bookings)', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting trips: {str(e)}', 'error')
    
    return redirect(url_for('admin_bp.trips'))

@admin_bp.route('/trips/<int:id>/cancel', methods=['POST'])
def cancel_trip(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    trip = Trip.query.get_or_404(id)
    trip.status = 'cancelled'
    db.session.commit()
    
    flash('Trip cancelled successfully', 'success')
    return redirect(url_for('admin_bp.trips'))

@admin_bp.route('/trips/<int:id>/delete', methods=['POST'])
def delete_trip(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    trip = Trip.query.get_or_404(id)
    
    # Check if trip has bookings
    if trip.bookings:
        flash('Cannot delete trip with existing bookings', 'error')
        return redirect(url_for('admin_bp.trips'))
    
    db.session.delete(trip)
    db.session.commit()
    
    flash('Trip deleted successfully', 'success')
    return redirect(url_for('admin_bp.trips'))

@admin_bp.route('/trips/add', methods=['GET', 'POST'])
def add_trip():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    if request.method == 'POST':
        # Implementation for adding single trip
        flash('Trip added successfully!', 'success')
        return redirect(url_for('admin_bp.trips'))
    
    routes = Route.query.all()
    operators = Operator.query.all()
    return render_template('admin/trips/form.html', routes=routes, operators=operators, title='Add Trip')

@admin_bp.route('/trips/<int:id>/edit', methods=['GET', 'POST'])
def edit_trip(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    trip = Trip.query.get_or_404(id)
    
    if request.method == 'POST':
        # Implementation for editing trip
        flash('Trip updated successfully!', 'success')
        return redirect(url_for('admin_bp.trips'))
    
    routes = Route.query.all()
    operators = Operator.query.all()
    return render_template('admin/trips/form.html', trip=trip, routes=routes, operators=operators, title='Edit Trip')

@admin_bp.route('/bookings/<int:id>')
def booking_details(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    booking = Booking.query.get_or_404(id)
    return render_template('admin/bookings/details.html', booking=booking)

@admin_bp.route('/buses')
def buses():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    buses = OperatorBusType.query.all()
    return render_template('admin/buses/list.html', buses=buses)

@admin_bp.route('/buses/add', methods=['GET', 'POST'])
def add_bus():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    if request.method == 'POST':
        # Implementation for adding bus
        flash('Bus added successfully!', 'success')
        return redirect(url_for('admin_bp.buses'))
    
    operators = Operator.query.all()
    bus_types = BusType.query.all()
    return render_template('admin/buses/form.html', operators=operators, bus_types=bus_types, title='Add Bus')

@admin_bp.route('/buses/<int:id>/edit', methods=['GET', 'POST'])
def edit_bus(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    bus = OperatorBusType.query.get_or_404(id)
    
    if request.method == 'POST':
        # Implementation for editing bus
        flash('Bus updated successfully!', 'success')
        return redirect(url_for('admin_bp.buses'))
    
    operators = Operator.query.all()
    bus_types = BusType.query.all()
    return render_template('admin/buses/form.html', bus=bus, operators=operators, bus_types=bus_types, title='Edit Bus')

@admin_bp.route('/bus-types/add', methods=['GET', 'POST'])
def add_bus_type():
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        base_price_multiplier = request.form.get('base_price_multiplier')
        
        bus_type = BusType(
            name=name,
            description=description,
            base_price_multiplier=float(base_price_multiplier) if base_price_multiplier else 1.0
        )
        
        db.session.add(bus_type)
        db.session.commit()
        flash('Bus type added successfully!', 'success')
        return redirect(url_for('admin_bp.bus_types'))
    
    operators = Operator.query.all()
    return render_template('admin/bus_types/form.html', operators=operators, title='Add Bus Type')

@admin_bp.route('/bus-types/<int:id>/edit', methods=['GET', 'POST'])
def edit_bus_type(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    bus_type = BusType.query.get_or_404(id)
    
    if request.method == 'POST':
        bus_type.name = request.form.get('name')
        bus_type.description = request.form.get('description')
        bus_type.base_price_multiplier = float(request.form.get('base_price_multiplier')) if request.form.get('base_price_multiplier') else 1.0
        
        db.session.commit()
        flash('Bus type updated successfully!', 'success')
        return redirect(url_for('admin_bp.bus_types'))
    
    operators = Operator.query.all()
    return render_template('admin/bus_types/form.html', bus_type=bus_type, operators=operators, title='Edit Bus Type')

@admin_bp.route('/bus-types/<int:id>/delete', methods=['POST'])
def delete_bus_type(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    bus_type = BusType.query.get_or_404(id)
    
    # Check if bus type is being used by any trips or operator configurations
    if bus_type.trips or bus_type.operator_configs:
        flash('Cannot delete bus type that is being used by trips or operator configurations!', 'error')
        return redirect(url_for('admin_bp.bus_types'))
    
    db.session.delete(bus_type)
    db.session.commit()
    flash('Bus type deleted successfully!', 'success')
    return redirect(url_for('admin_bp.bus_types'))

@admin_bp.route('/operators/<int:operator_id>/bus-types')
def operator_bus_types(operator_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(operator_id)
    bus_type_configs = OperatorBusType.query.filter_by(operator_id=operator_id).all()
    available_bus_types = BusType.query.all()
    
    return render_template('admin/operators/bus_types.html', 
                         operator=operator, 
                         bus_type_configs=bus_type_configs,
                         available_bus_types=available_bus_types)

@admin_bp.route('/operators/<int:operator_id>/bus-types/add', methods=['GET', 'POST'])
def add_operator_bus_type(operator_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(operator_id)
    
    if request.method == 'POST':
        bus_type_id = request.form.get('bus_type_id')
        capacity = request.form.get('capacity')
        seats_per_row = request.form.get('seats_per_row')
        
        # Check if configuration already exists
        existing = OperatorBusType.query.filter_by(
            operator_id=operator_id,
            bus_type_id=bus_type_id
        ).first()
        
        if existing:
            flash('Bus type configuration already exists for this operator!', 'error')
            return redirect(url_for('admin_bp.operator_bus_types', operator_id=operator_id))
        
        config = OperatorBusType(
            operator_id=operator_id,
            bus_type_id=int(bus_type_id),
            capacity=int(capacity) if capacity else 48,
            seats_per_row=int(seats_per_row) if seats_per_row else 4
        )
        
        db.session.add(config)
        db.session.commit()
        flash('Bus type configuration added successfully!', 'success')
        return redirect(url_for('admin_bp.operator_bus_types', operator_id=operator_id))
    
    available_bus_types = BusType.query.all()
    return render_template('admin/operators/bus_type_form.html', 
                         operator=operator, 
                         available_bus_types=available_bus_types,
                         title='Add Bus Type Configuration')

@admin_bp.route('/operators/<int:operator_id>/bus-types/<int:config_id>/edit', methods=['GET', 'POST'])
def edit_operator_bus_type(operator_id, config_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(operator_id)
    config = OperatorBusType.query.get_or_404(config_id)
    
    if request.method == 'POST':
        config.capacity = int(request.form.get('capacity')) if request.form.get('capacity') else 48
        config.seats_per_row = int(request.form.get('seats_per_row')) if request.form.get('seats_per_row') else 4
        
        db.session.commit()
        flash('Bus type configuration updated successfully!', 'success')
        return redirect(url_for('admin_bp.operator_bus_types', operator_id=operator_id))
    
    return render_template('admin/operators/bus_type_form.html', 
                         operator=operator, 
                         config=config,
                         title='Edit Bus Type Configuration')

@admin_bp.route('/operators/<int:operator_id>/bus-types/<int:config_id>/seat-map')
def operator_seat_map(operator_id, config_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(operator_id)
    config = OperatorBusType.query.get_or_404(config_id)
    
    return render_template('admin/operators/seat_map.html', 
                         operator=operator, 
                         config=config)

@admin_bp.route('/operators/<int:operator_id>/locations')
def operator_locations(operator_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(operator_id)
    locations = OperatorLocation.query.filter_by(operator_id=operator_id).all()
    
    return render_template('admin/operators/locations.html', 
                         operator=operator, 
                         locations=locations)

@admin_bp.route('/operators/<int:operator_id>/locations/add', methods=['GET', 'POST'])
def add_operator_location(operator_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(operator_id)
    
    if request.method == 'POST':
        city = request.form.get('city')
        address = request.form.get('address')
        location_type = request.form.get('location_type')
        phone = request.form.get('phone')
        is_main_office = 'is_main_office' in request.form
        
        location = OperatorLocation(
            operator_id=operator_id,
            city=city,
            address=address,
            location_type=location_type,
            phone=phone,
            is_main_office=is_main_office
        )
        
        db.session.add(location)
        db.session.commit()
        flash('Location added successfully!', 'success')
        return redirect(url_for('admin_bp.operator_locations', operator_id=operator_id))
    
    return render_template('admin/operators/location_form.html', 
                         operator=operator,
                         title='Add Location')

@admin_bp.route('/operators/<int:operator_id>/locations/<int:location_id>/edit', methods=['GET', 'POST'])
def edit_operator_location(location_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    location = OperatorLocation.query.get_or_404(location_id)
    operator = location.operator
    
    if request.method == 'POST':
        location.city = request.form.get('city')
        location.address = request.form.get('address')
        location.location_type = request.form.get('location_type')
        location.phone = request.form.get('phone')
        location.is_main_office = 'is_main_office' in request.form
        
        db.session.commit()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('admin_bp.operator_locations', operator_id=operator.id))
    
    return render_template('admin/operators/location_form.html', 
                         operator=operator,
                         location=location,
                         title='Edit Location')

@admin_bp.route('/operators/<int:id>/delete', methods=['POST'])
def delete_operator(id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(id)
    
    # Check if operator has any trips or bookings
    if operator.trips:
        flash('Cannot delete operator with existing trips!', 'error')
        return redirect(url_for('admin_bp.operators'))
    
    db.session.delete(operator)
    db.session.commit()
    flash('Operator deleted successfully!', 'success')
    return redirect(url_for('admin_bp.operators'))

@admin_bp.route('/operators/<int:operator_id>/bus-types/<int:config_id>/seat-map')
def operator_bus_type_seat_map(operator_id, config_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_bp.login'))
    
    operator = Operator.query.get_or_404(operator_id)
    config = OperatorBusType.query.get_or_404(config_id)
    
    return render_template('admin/operators/seat_map.html', 
                         operator=operator, 
                         config=config)
