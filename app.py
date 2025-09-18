from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Use environment variables for production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nkolo-pass-secret-key-change-in-production')

# MesomB Payment Configuration - Use environment variables
MESOMB_APPLICATION_KEY = os.environ.get('MESOMB_APPLICATION_KEY', '544e29bff5c61dc2d2759b34b3fb60649c915519')
MESOMB_ACCESS_KEY = os.environ.get('MESOMB_ACCESS_KEY', '09576120-d5dd-4ae9-9de7-46e6e79effaa')
MESOMB_SECRET_KEY = os.environ.get('MESOMB_SECRET_KEY', 'a12d1f8f-dedc-4749-bab5-affa9d98d73c')
MESOMB_BASE_URL = os.environ.get('MESOMB_BASE_URL', 'https://mesomb.hachther.com')

app.config['MESOMB_APPLICATION_KEY'] = MESOMB_APPLICATION_KEY
app.config['MESOMB_ACCESS_KEY'] = MESOMB_ACCESS_KEY
app.config['MESOMB_SECRET_KEY'] = MESOMB_SECRET_KEY
app.config['MESOMB_BASE_URL'] = MESOMB_BASE_URL

# Database configuration - Use PostgreSQL in production if DATABASE_URL is set
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Handle both postgres:// and postgresql:// URLs
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/nkolo_pass.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)

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
    return render_template('index.html')

@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_bp.dashboard'))

# Add context processor for global template variables
@app.context_processor
def inject_globals():
    return {
        'site_name': 'Nkolo Pass',
        'current_year': datetime.now().year
    }

def init_database():
    """Initialize database and create default data"""
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
        print("Admin login: email='admin@nkolopass.com', password='admin123'")

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
