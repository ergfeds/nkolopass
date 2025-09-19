from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from functools import wraps
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'nkolo-pass-secret-key-change-in-production')

# MesomB Payment Configuration
MESOMB_APPLICATION_KEY = os.getenv('MESOMB_APPLICATION_KEY')
MESOMB_ACCESS_KEY = os.getenv('MESOMB_ACCESS_KEY')
MESOMB_SECRET_KEY = os.getenv('MESOMB_SECRET_KEY')
MESOMB_BASE_URL = os.getenv('MESOMB_BASE_URL', 'https://mesomb.hachther.com')

app.config['MESOMB_APPLICATION_KEY'] = MESOMB_APPLICATION_KEY
app.config['MESOMB_ACCESS_KEY'] = MESOMB_ACCESS_KEY
app.config['MESOMB_SECRET_KEY'] = MESOMB_SECRET_KEY
app.config['MESOMB_BASE_URL'] = MESOMB_BASE_URL

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///nkolo_pass.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Timezone Configuration - Set to Cameroon timezone
app.config['TIMEZONE'] = 'Africa/Douala'  # Cameroon timezone (WAT)

def get_cameroon_time():
    """Get current time in Cameroon timezone"""
    cameroon_tz = pytz.timezone(app.config['TIMEZONE'])
    return datetime.now(cameroon_tz)

def get_cameroon_time_utc():
    """Get current Cameroon time converted to UTC for database storage"""
    cameroon_time = get_cameroon_time()
    return cameroon_time.astimezone(pytz.UTC).replace(tzinfo=None)

# i18n / Localization (URL-based)
app.config['LANGUAGES'] = ['en', 'fr']
app.config['BABEL_DEFAULT_LOCALE'] = 'fr'

# Ensure upload directory exists (with error handling for production)
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
except (OSError, PermissionError) as e:
    print(f"Warning: Could not create upload directories: {e}")
    # In production, directories might already exist or be read-only
    pass

# Initialize database
from models import db

db.init_app(app)

# Import models and routes
from models import *
from admin_routes import admin_bp
from user_routes import user_bp

# Register blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp)

# Initialize database tables
with app.app_context():
    db.create_all()
    
    # Create default bus types if not exist
    if not BusType.query.first():
        vip_type = BusType(
            name='VIP',
            description='Premium bus with enhanced comfort and amenities',
            base_price_multiplier=1.5
        )
        vip_type.set_amenities(['Air Conditioning', 'WiFi', 'Reclining Seats', 'Entertainment System', 'Refreshments'])
        
        regular_type = BusType(
            name='Regular',
            description='Standard bus service with basic amenities',
            base_price_multiplier=1.0
        )
        regular_type.set_amenities(['Air Conditioning', 'Comfortable Seats'])
        
        db.session.add(vip_type)
        db.session.add(regular_type)
        db.session.commit()
        print("Default bus types created")
    
    print("Database initialized successfully!")

def get_locale():
    """Select locale from the first path segment like /en/..., /fr/..."""
    path = request.path.strip('/').split('/')
    if path and path[0] in app.config.get('LANGUAGES', []):
        return path[0]
    return app.config.get('BABEL_DEFAULT_LOCALE', 'fr')

# Initialize Babel (Flask-Babel v3 style)
babel = Babel(app, locale_selector=get_locale)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    # Redirect bare root to default language user homepage
    default_lang = app.config.get('BABEL_DEFAULT_LOCALE', 'fr')
    return redirect(f'/{default_lang}/')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}

@app.route('/api/contact-settings')
def contact_settings_api():
    """API endpoint to get contact widget settings"""
    from flask import jsonify
    
    # Get contact settings from environment variables
    settings = {
        'phone': os.getenv('SUPPORT_PHONE', ''),
        'email': os.getenv('SUPPORT_EMAIL', ''),
        'whatsapp': os.getenv('WHATSAPP_NUMBER', ''),
        'business_hours': os.getenv('BUSINESS_HOURS', '24/7'),
        'enabled': os.getenv('CONTACT_WIDGET_ENABLED', 'true').lower() == 'true',
        'position': os.getenv('CONTACT_WIDGET_POSITION', 'bottom-right')
    }
    
    # Only return enabled settings with values
    if not settings['enabled']:
        return jsonify({'enabled': False})
    
    # Filter out empty values
    filtered_settings = {k: v for k, v in settings.items() if v}
    
    return jsonify(filtered_settings)

# Add context processor for global template variables
@app.context_processor
def inject_globals():
    # current language detected from URL
    path_parts = request.path.strip('/').split('/')
    current_language = path_parts[0] if path_parts and path_parts[0] in app.config['LANGUAGES'] else app.config.get('BABEL_DEFAULT_LOCALE', 'fr')

    def switch_language_url(target_lang: str):
        """Return current path with the leading language segment replaced by target_lang"""
        # Preserve query string
        path = request.path
        parts = path.strip('/').split('/')
        if parts and parts[0] in app.config['LANGUAGES']:
            parts[0] = target_lang
            new_path = '/' + '/'.join(parts)
        else:
            new_path = f'/{target_lang}{"/" if path == "/" else path}'
        if request.query_string:
            new_path += f'?{request.query_string.decode()}'
        return new_path

    return {
        'site_name': 'Nkolo Pass',
        'current_year': datetime.now().year,
        'supported_languages': app.config['LANGUAGES'],
        'current_language': current_language,
        'switch_language_url': switch_language_url,
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
