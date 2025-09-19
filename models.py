from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json

db = SQLAlchemy()

class Operator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    logo_url = db.Column(db.String(500))  # URL to logo image
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    locations = db.relationship('OperatorLocation', backref='operator', lazy=True)
    trips = db.relationship('Trip', backref='operator', lazy=True)
    
    def __repr__(self):
        return f'<Operator {self.name}>'

class OperatorLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    location_type = db.Column(db.String(20), default='terminal')  # terminal, office, depot
    is_main_office = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Location {self.city} - {self.operator.name}>'

class BusType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Luxury Coach", "Standard Bus"
    category = db.Column(db.String(20), nullable=False, default='regular')  # 'vip' or 'regular'
    description = db.Column(db.Text)
    amenities = db.Column(db.Text)  # JSON string of amenities
    capacity = db.Column(db.Integer, nullable=False, default=48)
    seat_layout = db.Column(db.Text)  # JSON string for default seat map
    seats_per_row = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_amenities(self):
        if self.amenities:
            return json.loads(self.amenities)
        return []

    def set_amenities(self, amenities_list):
        self.amenities = json.dumps(amenities_list)
    
    def is_vip(self):
        """Check if this bus type is VIP category"""
        return self.category.lower() == 'vip'
    
    def is_regular(self):
        """Check if this bus type is Regular category"""
        return self.category.lower() == 'regular'
    
    def get_seat_layout(self):
        if self.seat_layout:
            return json.loads(self.seat_layout)
        return self.generate_default_layout()
    
    def set_seat_layout(self, layout):
        self.seat_layout = json.dumps(layout)
    
    def generate_default_layout(self):
        """Generate default seat layout based on capacity and seats_per_row"""
        layout = []
        rows = (self.capacity + self.seats_per_row - 1) // self.seats_per_row
        seat_number = 1
        
        for r in range(rows):
            row_list = []
            num_in_row = min(self.seats_per_row, self.capacity - (r * self.seats_per_row))
            for i in range(num_in_row):
                row_list.append({
                    'number': seat_number,
                    'type': 'standard'
                })
                seat_number += 1
            layout.append(row_list)
        
        return layout

    def get_assigned_operator_ids(self):
        """Get list of operator IDs that have this bus type assigned"""
        return [config.operator_id for config in self.operator_configs if config.is_active]
    
    def __repr__(self):
        return f'<BusType {self.name}>'

class OperatorBusType(db.Model):
    """Configuration for each operator's bus types with layouts and capacity"""
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    bus_type_id = db.Column(db.Integer, db.ForeignKey('bus_type.id'), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=48)
    seat_layout = db.Column(db.Text)  # JSON string for seat map
    seats_per_row = db.Column(db.Integer, default=4)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    operator = db.relationship('Operator', backref='bus_type_configs')
    bus_type = db.relationship('BusType', backref='operator_configs')
    
    # Unique constraint to prevent duplicate configurations
    __table_args__ = (db.UniqueConstraint('operator_id', 'bus_type_id', name='unique_operator_bus_type'),)
    
    def get_seat_layout(self):
        if self.seat_layout:
            return json.loads(self.seat_layout)
        return self.generate_default_layout()
    
    def set_seat_layout(self, layout):
        self.seat_layout = json.dumps(layout)
    
    def generate_default_layout(self):
        """Generate default seat layout based on capacity and seats_per_row"""
        layout = []
        rows = (self.capacity + self.seats_per_row - 1) // self.seats_per_row
        seat_number = 1
        
        for r in range(rows):
            row_list = []
            num_in_row = min(self.seats_per_row, self.capacity - (r * self.seats_per_row))
            for i in range(num_in_row):
                row_list.append({
                    'number': seat_number,
                    'type': 'standard'
                })
                seat_number += 1
            layout.append(row_list)
        
        return layout
    
    def __repr__(self):
        return f'<OperatorBusType {self.operator.name} - {self.bus_type.name}>'

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Float)
    estimated_duration = db.Column(db.Integer)  # in minutes
    waypoints = db.Column(db.Text)  # JSON string of intermediate stops
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trips = db.relationship('Trip', backref='route', lazy=True)

    def get_waypoints(self):
        if self.waypoints and self.waypoints.strip():
            try:
                return json.loads(self.waypoints)
            except (json.JSONDecodeError, ValueError):
                return []
        return []

    def set_waypoints(self, waypoints_list):
        self.waypoints = json.dumps(waypoints_list)

    def get_reverse_route(self):
        """Find or create the reverse route (destination → origin)"""
        # Look for existing reverse route
        reverse_route = Route.query.filter_by(
            origin=self.destination,
            destination=self.origin
        ).first()
        
        if reverse_route:
            return reverse_route
        
        # Create reverse route if it doesn't exist
        reverse_route = Route(
            name=f"{self.destination} → {self.origin}",
            origin=self.destination,
            destination=self.origin,
            distance_km=self.distance_km,
            estimated_duration=self.estimated_duration,
            waypoints=self.waypoints,  # Could reverse waypoints if needed
            is_active=True
        )
        
        db.session.add(reverse_route)
        db.session.commit()
        
        return reverse_route

    def __repr__(self):
        return f'<Route {self.origin} → {self.destination}>'

class RouteOperatorAssignment(db.Model):
    __tablename__ = 'route_operator_assignment'
    
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    
    # Pricing per seat for different bus types
    regular_seat_price = db.Column(db.Float, nullable=False, default=0)  # Price per seat for regular buses
    vip_seat_price = db.Column(db.Float, nullable=False, default=0)     # Price per seat for VIP buses
    
    # Trip frequency configuration
    trips_per_day = db.Column(db.Integer, default=3)  # How many trips this operator runs per day on this route
    departure_times = db.Column(db.Text)  # JSON array of departure times like ["08:00", "14:00", "20:00"]
    
    # Location-specific details
    pickup_location_id = db.Column(db.Integer, db.ForeignKey('operator_location.id'))
    dropoff_location_id = db.Column(db.Integer, db.ForeignKey('operator_location.id'))
    
    # Service details
    is_active = db.Column(db.Boolean, default=True)
    service_days = db.Column(db.String(20), default='1234567')  # Days of week (1=Monday, 7=Sunday)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    route = db.relationship('Route', backref='operator_assignments')
    operator = db.relationship('Operator', backref='route_assignments')
    pickup_location = db.relationship('OperatorLocation', foreign_keys=[pickup_location_id])
    dropoff_location = db.relationship('OperatorLocation', foreign_keys=[dropoff_location_id])
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('route_id', 'operator_id', name='unique_route_operator'),)
    
    def get_seat_price_for_bus_type(self, bus_type_name):
        """Get seat price based on bus type (VIP or Regular)"""
        if bus_type_name and bus_type_name.lower() == 'vip':
            return self.vip_seat_price
        return self.regular_seat_price
    
    def get_departure_times(self):
        """Get list of departure times"""
        if self.departure_times:
            return json.loads(self.departure_times)
        # Default times based on trips_per_day
        if self.trips_per_day == 1:
            return ["14:00"]
        elif self.trips_per_day == 2:
            return ["08:00", "18:00"]
        elif self.trips_per_day == 3:
            return ["08:00", "14:00", "20:00"]
        elif self.trips_per_day == 4:
            return ["06:00", "10:00", "14:00", "18:00"]
        else:
            # Generate times evenly distributed
            times = []
            start_hour = 6
            end_hour = 22
            interval = (end_hour - start_hour) / self.trips_per_day
            for i in range(self.trips_per_day):
                hour = int(start_hour + (i * interval))
                times.append(f"{hour:02d}:00")
            return times
    
    def set_departure_times(self, times_list):
        """Set departure times from list"""
        self.departure_times = json.dumps(times_list)
    
    def get_service_days_list(self):
        """Convert service_days string to list of day numbers"""
        return [int(d) for d in self.service_days if d.isdigit()]
    
    def set_service_days_list(self, days_list):
        """Set service_days from list of day numbers"""
        self.service_days = ''.join(str(d) for d in sorted(days_list) if 1 <= d <= 7)
    
    def __repr__(self):
        return f'<RouteAssignment {self.operator.name} on {self.route.name}>'

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    seat_price = db.Column(db.Float, nullable=False)  # Price per seat
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, departed, arrived, cancelled
    
    # Virtual bus identifier (e.g., "VIP-1", "REG-2") - for display purposes
    virtual_bus_id = db.Column(db.String(20))
    
    # Foreign Keys
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    bus_type_id = db.Column(db.Integer, db.ForeignKey('bus_type.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='trip', lazy=True)
    bus_type = db.relationship('BusType', backref='trips')
    
    @property
    def operator_bus_type_config(self):
        """Get the operator's bus type configuration"""
        return OperatorBusType.query.filter_by(
            operator_id=self.operator_id,
            bus_type_id=self.bus_type_id
        ).first()
    
    @property
    def seat_layout(self):
        """Get seat layout from operator's bus type configuration"""
        config = self.operator_bus_type_config
        return config.get_seat_layout() if config else []
    
    @property
    def route_assignment(self):
        """Get the route operator assignment for pricing"""
        return RouteOperatorAssignment.query.filter_by(
            route_id=self.route_id,
            operator_id=self.operator_id
        ).first()
    
    def get_seat_price(self):
        """Get the current seat price for this trip"""
        return self.seat_price

    def get_booked_seats(self):
        """Get list of booked seat numbers for this trip"""
        booked_seats = []
        for booking in self.bookings:
            if booking.seat_numbers:
                try:
                    seats = json.loads(booking.seat_numbers)
                    booked_seats.extend(seats)
                except:
                    pass
        return booked_seats

    def get_available_seat_count(self):
        """Get count of available seats"""
        return self.available_seats - len(self.get_booked_seats())

    def __repr__(self):
        return f'<Trip {self.route.origin}→{self.route.destination} {self.departure_time}>'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=False)
    seat_numbers = db.Column(db.Text)  # JSON string of selected seats
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded, cancelled
    payment_reference = db.Column(db.String(100))  # Payment gateway transaction ID
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_seat_numbers(self):
        if self.seat_numbers:
            # Handle integer case (single seat number)
            if isinstance(self.seat_numbers, int):
                return [str(self.seat_numbers)]
            
            # Handle string cases
            if isinstance(self.seat_numbers, str):
                try:
                    # Try to parse as JSON first
                    result = json.loads(self.seat_numbers)
                    # If result is a list, return it
                    if isinstance(result, list):
                        return [str(s) for s in result]
                    # If result is an int/string, wrap in list
                    return [str(result)]
                except (json.JSONDecodeError, TypeError, ValueError):
                    # If not JSON, assume it's comma-separated string
                    return [s.strip() for s in self.seat_numbers.split(',') if s.strip()]
        return []

    def set_seat_numbers(self, seats_list):
        self.seat_numbers = json.dumps(seats_list)

    def __repr__(self):
        return f'<Booking {self.booking_reference}>'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    id_number = db.Column(db.String(50))  # National ID or passport
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True)

    def get_full_name(self):
        """Return the customer's full name"""
        return self.name
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class SeatBlock(db.Model):
    """Temporary seat blocking to prevent double booking during payment process"""
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    seat_numbers = db.Column(db.Text, nullable=False)  # JSON string of seat numbers
    session_id = db.Column(db.String(100), nullable=False)  # Browser session ID
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Relationships
    trip = db.relationship('Trip', backref='seat_blocks')
    
    def __init__(self, trip_id, seat_numbers, session_id, duration_minutes=6):
        self.trip_id = trip_id
        self.seat_numbers = json.dumps(seat_numbers) if isinstance(seat_numbers, list) else seat_numbers
        self.session_id = session_id
        self.blocked_at = datetime.utcnow()
        self.expires_at = self.blocked_at + timedelta(minutes=duration_minutes)
    
    def get_seat_numbers(self):
        """Get list of blocked seat numbers"""
        if self.seat_numbers:
            try:
                return json.loads(self.seat_numbers)
            except:
                return []
        return []
    
    def is_expired(self):
        """Check if the block has expired"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def cleanup_expired(cls):
        """Remove all expired seat blocks"""
        expired_blocks = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for block in expired_blocks:
            db.session.delete(block)
        db.session.commit()
        return len(expired_blocks)
    
    @classmethod
    def get_blocked_seats_for_trip(cls, trip_id, exclude_session=None):
        """Get all currently blocked seats for a trip"""
        # Clean up expired blocks first
        cls.cleanup_expired()
        
        query = cls.query.filter(
            cls.trip_id == trip_id,
            cls.expires_at > datetime.utcnow()
        )
        
        if exclude_session:
            query = query.filter(cls.session_id != exclude_session)
        
        blocks = query.all()
        blocked_seats = []
        for block in blocks:
            blocked_seats.extend(block.get_seat_numbers())
        
        return blocked_seats
    
    @classmethod
    def block_seats(cls, trip_id, seat_numbers, session_id):
        """Block seats for a session"""
        # Remove any existing blocks for this session
        existing_blocks = cls.query.filter_by(
            trip_id=trip_id,
            session_id=session_id
        ).all()
        
        for block in existing_blocks:
            db.session.delete(block)
        
        # Create new block
        new_block = cls(trip_id, seat_numbers, session_id)
        db.session.add(new_block)
        db.session.commit()
        
        return new_block
    
    def __repr__(self):
        return f'<SeatBlock Trip:{self.trip_id} Seats:{self.get_seat_numbers()} Session:{self.session_id}>'
