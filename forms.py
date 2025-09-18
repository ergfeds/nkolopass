from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField, PasswordField, DateTimeField, DateField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, URL
from wtforms.widgets import TextArea, CheckboxInput, ListWidget

class OperatorForm(FlaskForm):
    name = StringField('Operator Name', validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('Operator Code', validators=[DataRequired(), Length(min=2, max=10)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    logo_url = StringField('Logo URL', validators=[Optional(), URL(message='Please enter a valid URL')])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address')
    is_active = BooleanField('Active', default=True)

# Multi-checkbox widget for operator selection
class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class BusTypeForm(FlaskForm):
    name = StringField('Bus Type Name', validators=[DataRequired(), Length(min=2, max=50)])
    category = SelectField('Bus Category', validators=[DataRequired()], 
                          choices=[('regular', 'Regular Bus'), ('vip', 'VIP Bus')], 
                          default='regular')
    description = TextAreaField('Description')
    capacity = IntegerField('Total Capacity', validators=[DataRequired(), NumberRange(min=10, max=80)], default=48)
    seats_per_row = SelectField('Seat Configuration', validators=[DataRequired()], coerce=int, 
                               choices=[(2, '1x1 (2 seats per row)'), (3, '2x1 (3 seats per row)'), (4, '2x2 (4 seats per row)'), (5, '3x2 (5 seats per row)')], 
                               default=4)
    assigned_operators = MultiCheckboxField('Assign to Operators', coerce=int)

class BulkBusForm(FlaskForm):
    # Bus Model Information
    model_name = StringField('Bus Model Name', validators=[DataRequired(), Length(min=2, max=100)])
    model_description = TextAreaField('Model Description')
    capacity = IntegerField('Total Capacity (Seats)', validators=[DataRequired(), NumberRange(min=10, max=100)], default=40)
    seats_per_row = IntegerField('Seats Per Row', validators=[DataRequired(), NumberRange(min=2, max=5)], default=4)
    bus_type_id = SelectField('Bus Type', validators=[DataRequired()], coerce=int)
    
    # Agency Assignment
    operator_assignments = MultiCheckboxField('Select Agencies', coerce=int, validators=[DataRequired()], choices=[])
    quantity_per_operator = IntegerField('Buses Per Selected Agency', validators=[DataRequired(), NumberRange(min=1, max=50)], default=1)
    
    # Plate Number Configuration
    region_code = SelectField('Region Code', choices=[
        ('LT', 'LT - Littoral'),
        ('CE', 'CE - Centre'),
        ('AD', 'AD - Adamawa'),
        ('EN', 'EN - East'),
        ('ES', 'ES - Far North'),
        ('NO', 'NO - North'),
        ('NW', 'NW - Northwest'),
        ('OU', 'OU - West'),
        ('SU', 'SU - South'),
        ('SW', 'SW - Southwest')
    ], validators=[DataRequired()], default='LT')
    
    starting_number = IntegerField('Starting Number (e.g., 1000)', validators=[DataRequired(), NumberRange(min=1, max=9999)], default=1000)
    suffix_pattern = SelectField('Suffix Pattern', choices=[
        ('sequential', 'Sequential (AA, AB, AC...)'),
        ('random', 'Random Letters')
    ], validators=[DataRequired()], default='sequential')

class BusForm(FlaskForm):
    plate_number = StringField('Plate Number', validators=[DataRequired(), Length(min=2, max=20)])
    model = StringField('Bus Model', validators=[Optional(), Length(max=50)])
    year = IntegerField('Year', validators=[Optional(), NumberRange(min=1990, max=2030)])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=10, max=100)])
    operator_id = SelectField('Operator', validators=[DataRequired()], coerce=int)
    bus_type_id = SelectField('Bus Type', validators=[DataRequired()], coerce=int)
    bus_model_id = SelectField('Bus Model (Optional)', coerce=int, validators=[Optional()])
    is_active = BooleanField('Active', default=True)

class BusModelForm(FlaskForm):
    name = StringField('Model Name', validators=[DataRequired(), Length(min=2, max=100)])
    model = StringField('Manufacturer/Model', validators=[Optional(), Length(max=50)])
    year = IntegerField('Year', validators=[Optional(), NumberRange(min=1990, max=2035)])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=10, max=100)])
    seats_per_row = IntegerField('Seats per row', validators=[DataRequired(), NumberRange(min=2, max=5)])
    bus_type_id = SelectField('Bus Type', validators=[DataRequired()], coerce=int)
    layout_style = SelectField('Layout Style', choices=[('standard','Standard'),('luxury','Luxury'),('minibus','Minibus')])

class BulkAssignForm(FlaskForm):
    bus_model_id = SelectField('Bus Model', validators=[DataRequired()], coerce=int)
    operator_ids = SelectField('Operators', coerce=int)

class RouteForm(FlaskForm):
    name = StringField('Route Name', validators=[DataRequired(), Length(min=2, max=100)])
    origin = StringField('Origin', validators=[DataRequired(), Length(min=2, max=100)])
    destination = StringField('Destination', validators=[DataRequired(), Length(min=2, max=100)])
    distance_km = FloatField('Distance (KM)', validators=[Optional(), NumberRange(min=1)])
    estimated_duration = IntegerField('Estimated Duration (minutes)', validators=[DataRequired(), NumberRange(min=30)])
    waypoints = TextAreaField('Waypoints', validators=[Optional()])
    is_active = BooleanField('Active', default=True)

class RouteOperatorAssignmentForm(FlaskForm):
    route_id = SelectField('Route', validators=[DataRequired()], coerce=int)
    operator_assignments = MultiCheckboxField('Select Operators', choices=[])
    regular_price = FloatField('Regular Bus Price (FCFA)', validators=[DataRequired()], default=0)
    vip_price = FloatField('VIP Bus Price (FCFA)', validators=[Optional()])
    
    # Location selection
    pickup_location_id = SelectField('Pickup Location', validators=[Optional()], coerce=int, choices=[])
    dropoff_location_id = SelectField('Dropoff Location', validators=[Optional()], coerce=int, choices=[])
    
    # Service days
    monday = BooleanField('Monday', default=True)
    tuesday = BooleanField('Tuesday', default=True)
    wednesday = BooleanField('Wednesday', default=True)
    thursday = BooleanField('Thursday', default=True)
    friday = BooleanField('Friday', default=True)
    saturday = BooleanField('Saturday', default=True)
    sunday = BooleanField('Sunday', default=True)
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    def get_selected_days(self):
        """Get list of selected day numbers (1=Monday, 7=Sunday)"""
        days = []
        if self.monday.data: days.append(1)
        if self.tuesday.data: days.append(2)
        if self.wednesday.data: days.append(3)
        if self.thursday.data: days.append(4)
        if self.friday.data: days.append(5)
        if self.saturday.data: days.append(6)
        if self.sunday.data: days.append(7)
        return days

class BulkRouteAssignmentForm(FlaskForm):
    """Form for assigning multiple operators to a route with individual pricing"""
    route_id = SelectField('Route', validators=[DataRequired()], coerce=int)
    operator_assignments = MultiCheckboxField('Select Operators', choices=[])
    
    # Default pricing (can be overridden per operator)
    default_regular_price = FloatField('Default Regular Price (FCFA)', validators=[DataRequired()], default=0)
    default_vip_price = FloatField('Default VIP Price (FCFA)', validators=[Optional()])
    
    # Service days for all assignments
    monday = BooleanField('Monday', default=True)
    tuesday = BooleanField('Tuesday', default=True)
    wednesday = BooleanField('Wednesday', default=True)
    thursday = BooleanField('Thursday', default=True)
    friday = BooleanField('Friday', default=True)
    saturday = BooleanField('Saturday', default=True)
    sunday = BooleanField('Sunday', default=True)
    
    notes = TextAreaField('Notes (applies to all assignments)', validators=[Optional()])
    
    def get_selected_days(self):
        """Get list of selected day numbers (1=Monday, 7=Sunday)"""
        days = []
        if self.monday.data: days.append(1)
        if self.tuesday.data: days.append(2)
        if self.wednesday.data: days.append(3)
        if self.thursday.data: days.append(4)
        if self.friday.data: days.append(5)
        if self.saturday.data: days.append(6)
        if self.sunday.data: days.append(7)
        return days

class TripForm(FlaskForm):
    departure_time = DateTimeField('Departure Time', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    arrival_time = DateTimeField('Arrival Time', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=100)])
    route_id = SelectField('Route', validators=[DataRequired()], coerce=int)
    bus_id = SelectField('Bus', validators=[DataRequired()], coerce=int)
    operator_id = SelectField('Operator', validators=[DataRequired()], coerce=int)

class TripGenerationForm(FlaskForm):
    # Route and Operator Selection
    route_id = SelectField('Route', validators=[DataRequired()], coerce=int)
    operator_id = SelectField('Operator/Agency', validators=[DataRequired()], coerce=int)
    
    # Date Range
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    
    # Pricing
    regular_price = FloatField('Regular Seat Price (FCFA)', validators=[DataRequired(), NumberRange(min=100)], default=3000)
    vip_price = FloatField('VIP Seat Price (FCFA)', validators=[DataRequired(), NumberRange(min=100)], default=5000)
    
    # Trip Frequency
    trips_per_day = IntegerField('Trips Per Day', validators=[DataRequired(), NumberRange(min=1, max=20)], default=3)
    
    # Schedule Configuration
    schedule_type = SelectField('Schedule Type', choices=[
        ('interval', 'Interval-based (evenly distributed)'),
        ('manual', 'Manual departure times')
    ], default='interval', validators=[DataRequired()])
    
    # Interval-based scheduling
    first_departure = StringField('First Departure Time (HH:MM)', validators=[DataRequired()], default='06:00')
    last_departure = StringField('Last Departure Time (HH:MM)', validators=[DataRequired()], default='20:00')
    interval_minutes = IntegerField('Interval Between Trips (minutes)', validators=[Optional(), NumberRange(min=30, max=720)], default=120)
    
    # Manual times (alternative to interval)
    departure_times = StringField('Departure Times (comma-separated, e.g., 08:00, 14:00, 20:00)', 
                                validators=[Optional()], 
                                default='06:00, 14:00, 20:00')
    
    # Bidirectional Trip Generation
    generate_return_trips = BooleanField('Generate Return Trips (Opposite Direction)', default=False)
    return_trip_delay = IntegerField('Return Trip Delay (minutes)', validators=[Optional(), NumberRange(min=30, max=480)], default=60)
    
    # Service days
    monday = BooleanField('Monday', default=True)
    tuesday = BooleanField('Tuesday', default=True)
    wednesday = BooleanField('Wednesday', default=True)
    thursday = BooleanField('Thursday', default=True)
    friday = BooleanField('Friday', default=True)
    saturday = BooleanField('Saturday', default=True)
    sunday = BooleanField('Sunday', default=True)
    
    def get_selected_days(self):
        """Get list of selected day numbers (1=Monday, 7=Sunday)"""
        days = []
        if self.monday.data: days.append(1)
        if self.tuesday.data: days.append(2)
        if self.wednesday.data: days.append(3)
        if self.thursday.data: days.append(4)
        if self.friday.data: days.append(5)
        if self.saturday.data: days.append(6)
        if self.sunday.data: days.append(7)
        return days

class OperatorLocationForm(FlaskForm):
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=100)])
    address = TextAreaField('Full Address', validators=[DataRequired()], 
                          render_kw={'rows': 3, 'placeholder': 'Enter complete address including street, neighborhood, etc.'})
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    landmark = StringField('Nearby Landmark', validators=[Optional(), Length(max=200)], 
                         render_kw={'placeholder': 'e.g., Near Central Market, Behind Total Station'})
    gps_coordinates = StringField('GPS Coordinates', validators=[Optional(), Length(max=50)], 
                                render_kw={'placeholder': 'e.g., 4.0511, 9.7679 (optional)'})
    is_main_office = BooleanField('Main Office', default=False)
    is_active = BooleanField('Active', default=True)

class CustomerForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=8, max=20)])
    id_number = StringField('ID Number', validators=[Optional(), Length(max=20)])

class BookingForm(FlaskForm):
    trip_id = SelectField('Trip', validators=[DataRequired()], coerce=int)
    customer_id = SelectField('Customer', validators=[DataRequired()], coerce=int)
    seat_numbers = StringField('Seat Numbers (comma-separated)', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Credit/Debit Card')
    ], validators=[DataRequired()])

class AdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin')
    ], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)

