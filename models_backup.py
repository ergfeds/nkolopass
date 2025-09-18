from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='admin')  # admin, super_admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Operator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)  # e.g., "VIP001"
    description = db.Column(db.Text)
    logo = db.Column(db.String(200))  # path to logo file
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.Text)  # Main/Head office address
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    buses = db.relationship('Bus', backref='operator', lazy=True, cascade='all, delete-orphan')
    trips = db.relationship('Trip', backref='operator', lazy=True)
    locations = db.relationship('OperatorLocation', backref='operator', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Operator {self.name}>'

class OperatorLocation(db.Model):
    """Operator locations/offices in different cities"""
    __tablename__ = 'operator_location'
    
    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    contact_phone = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    landmark = db.Column(db.String(200))  # Nearby landmark for easy finding
    gps_coordinates = db.Column(db.String(50))  # Optional GPS coordinates
    is_active = db.Column(db.Boolean, default=True)
    is_main_office = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint - one location per city per operator
    __table_args__ = (db.UniqueConstraint('operator_id', 'city', name='unique_operator_city'),)
    
    def __repr__(self):
        return f'<OperatorLocation {self.operator.name} - {self.city}>'

class BusType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # VIP, Regular
    description = db.Column(db.Text)
    base_price_multiplier = db.Column(db.Float, default=1.0)  # Price multiplier for this type
    amenities = db.Column(db.Text)  # JSON string of amenities
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    buses = db.relationship('Bus', backref='bus_type', lazy=True)

    def get_amenities(self):
        if self.amenities:
            return json.loads(self.amenities)
        return []

    def set_amenities(self, amenities_list):
        self.amenities = json.dumps(amenities_list)

class BusModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., VIP Coach 2025
    description = db.Column(db.Text)  # Added description field
    model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    capacity = db.Column(db.Integer, nullable=False)
    seats_per_row = db.Column(db.Integer, default=4)
    seat_layout = db.Column(db.Text)  # JSON string representing canonical layout
    bus_type_id = db.Column(db.Integer, db.ForeignKey('bus_type.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bus_type = db.relationship('BusType', backref='bus_models')
    buses = db.relationship('Bus', backref='bus_model', lazy=True)

    def get_seat_layout(self):
        if self.seat_layout:
            return json.loads(self.seat_layout)
        # fallback default based on capacity and seats_per_row
        layout = []
        rows = (self.capacity + self.seats_per_row - 1) // self.seats_per_row
        labels_map = {2: ['A','B'],3:['A','B','C'],4:['A','B','C','D'],5:['A','B','C','D','E']}
        labels = labels_map.get(self.seats_per_row, ['A','B','C','D'])
        seat_number = 1
        for r in range(rows):
            row_list = []
            num_in_row = min(self.seats_per_row, self.capacity - (r * self.seats_per_row))
            for i in range(num_in_row):
                row_list.append({'number': seat_number, 'position': labels[i], 'type': 'standard'})
                seat_number += 1
            layout.append(row_list)
        return layout

    def set_seat_layout(self, layout):
        self.seat_layout = json.dumps(layout)
    
    def generate_default_layout(self):
        """Generate default seat layout based on capacity and seats_per_row"""
        layout = []
        rows = (self.capacity + self.seats_per_row - 1) // self.seats_per_row
        labels_map = {2: ['A','B'], 3: ['A','B','C'], 4: ['A','B','C','D'], 5: ['A','B','C','D','E']}
        labels = labels_map.get(self.seats_per_row, ['A','B','C','D'])
        seat_number = 1
        
        for r in range(rows):
            row_list = []
            num_in_row = min(self.seats_per_row, self.capacity - (r * self.seats_per_row))
            for i in range(num_in_row):
                row_list.append({
                    'number': seat_number, 
                    'position': labels[i], 
                    'type': 'standard'
                })
                seat_number += 1
            layout.append(row_list)
        
        return layout

class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    model = db.Column(db.String(50))
    year = db.Column(db.Integer)
    capacity = db.Column(db.Integer, nullable=True)  # Made nullable - now comes from BusModel
    seat_layout = db.Column(db.Text)  # JSON string for seat map
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    bus_type_id = db.Column(db.Integer, db.ForeignKey('bus_type.id'), nullable=False)
    bus_model_id = db.Column(db.Integer, db.ForeignKey('bus_model.id'))
    batch_id = db.Column(db.String(50))  # Batch ID for bulk operations
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trips = db.relationship('Trip', backref='bus', lazy=True)
    
    # Properties to get data from linked BusModel
    @property
    def effective_capacity(self):
        """Get capacity from BusModel if linked, otherwise from direct capacity field"""
        if self.bus_model_id and self.bus_model:
            return self.bus_model.capacity
        return self.capacity or 0
    
    @property
    def effective_bus_type(self):
        """Get bus type from BusModel if linked, otherwise from direct bus_type_id"""
        if self.bus_model_id and self.bus_model:
            return self.bus_model.bus_type
        return BusType.query.get(self.bus_type_id)

    def get_seat_layout(self):
        if self.seat_layout:
            return json.loads(self.seat_layout)
        return self.generate_default_layout()

    def set_seat_layout(self, layout):
        self.seat_layout = json.dumps(layout)

    def generate_default_layout(self):
        """Generate default seat layout based on effective capacity"""
        # If linked to BusModel, use its layout
        if self.bus_model_id and self.bus_model:
            return self.bus_model.get_seat_layout()
        
        # Otherwise generate based on direct capacity
        capacity = self.effective_capacity
        rows = (capacity + 3) // 4  # 4 seats per row typically
        layout = []
        seat_number = 1
        
        for row in range(rows):
            row_seats = []
            seats_in_row = min(4, capacity - (row * 4))
            for seat in range(seats_in_row):
                row_seats.append({
                    'number': seat_number,
                    'position': ['A', 'B', 'C', 'D'][seat],
                    'type': 'standard'
                })
                seat_number += 1
            layout.append(row_seats)
        
        return layout

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Float)
    estimated_duration = db.Column(db.Integer)  # in minutes
    waypoints = db.Column(db.Text)  # JSON string of intermediate stops
    base_price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trips = db.relationship('Trip', backref='route', lazy=True)

    def get_waypoints(self):
        if self.waypoints:
            return json.loads(self.waypoints)
        return []

    def set_waypoints(self, waypoints_list):
        self.waypoints = json.dumps(waypoints_list)

    def __repr__(self):
        return f'<Route {self.origin} → {self.destination}>'

class RouteOperatorAssignment(db.Model):
    __tablename__ = 'route_operator_assignment'
    
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.id'), nullable=False)
    
    # Pricing for different bus types
    regular_price = db.Column(db.Float)  # Price for regular buses
    vip_price = db.Column(db.Float)     # Price for VIP buses
    
    # Location-specific details
    pickup_location_id = db.Column(db.Integer, db.ForeignKey('operator_location.id'))  # Where passengers board
    dropoff_location_id = db.Column(db.Integer, db.ForeignKey('operator_location.id'))  # Where passengers alight
    
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
    
    def get_price_for_bus_type(self, bus_type_name):
        """Get price based on bus type (VIP or Regular)"""
        if bus_type_name and bus_type_name.lower() == 'vip':
            return self.vip_price or self.regular_price
        return self.regular_price
    
    def get_service_days_list(self):
        """Convert service_days string to list of day numbers"""
        return [int(d) for d in self.service_days if d.isdigit()]
    
    def set_service_days_list(self, days_list):
        """Set service_days from list of day numbers"""
        self.service_days = ''.join(str(d) for d in sorted(days_list) if 1 <= d <= 7)
    
    def __repr__(self):
        return f'<RouteAssignment {self.operator.name} on {self.route.name}>'

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
        labels_map = {2: ['A','B'], 3: ['A','B','C'], 4: ['A','B','C','D'], 5: ['A','B','C','D','E']}
        labels = labels_map.get(self.seats_per_row, ['A','B','C','D'])
        seat_number = 1
        
        for r in range(rows):
            row_list = []
            num_in_row = min(self.seats_per_row, self.capacity - (r * self.seats_per_row))
            for i in range(num_in_row):
                row_list.append({
                    'number': seat_number, 
                    'position': labels[i], 
                    'type': 'standard'
                })
                seat_number += 1
            layout.append(row_list)
        
        return layout
    
    def __repr__(self):
        return f'<OperatorBusType {self.operator.name} - {self.bus_type.name}>'

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, departed, arrived, cancelled
    
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

    def calculate_price(self):
        """Calculate trip price based on route base price and bus type multiplier"""
        base_price = self.route.base_price
        multiplier = self.bus_type.base_price_multiplier
        return base_price * multiplier

    def get_booked_seats(self):
        """Get list of booked seat numbers for this trip"""
        booked_seats = []
        for booking in self.bookings:
            if booking.status in ['confirmed', 'paid']:
                booked_seats.extend(booking.get_seat_numbers())
        return booked_seats

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=False)
    id_number = db.Column(db.String(20))  # National ID or passport
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=False)
    seat_numbers = db.Column(db.Text)  # JSON string of selected seats
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, paid, cancelled
    payment_method = db.Column(db.String(50))
    payment_reference = db.Column(db.String(100))
    
    # Foreign Keys
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_seat_numbers(self):
        if self.seat_numbers:
            return json.loads(self.seat_numbers)
        return []

    def set_seat_numbers(self, seats):
        self.seat_numbers = json.dumps(seats)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    qr_code = db.Column(db.String(200))  # Path to QR code image
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    
    # Foreign Key
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    booking = db.relationship('Booking', backref='tickets', lazy=True)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_setting(key, default=None):
        setting = SiteSettings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set_setting(key, value, description=None):
        setting = SiteSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SiteSettings(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()

class NotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(100))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(100))
    smtp_password = db.Column(db.String(200))
    smtp_use_tls = db.Column(db.Boolean, default=True)
    from_email = db.Column(db.String(120))
    from_name = db.Column(db.String(100), default='Nkolo Pass')
    
    # Notification templates
    booking_confirmation_template = db.Column(db.Text)
    booking_cancellation_template = db.Column(db.Text)
    trip_reminder_template = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
