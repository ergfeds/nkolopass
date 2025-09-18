# config.py - Additional configuration settings
# This file contains additional configuration options

import os

# Application Configuration
APP_NAME = 'Nkolo Pass'
APP_VERSION = '1.0.0'

# File Upload Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Session Configuration
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = False
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

# Cache Configuration
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

# Email Configuration (if needed)
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'app.log'

# Security Configuration
SECRET_KEY_MIN_LENGTH = 32
PASSWORD_MIN_LENGTH = 8

# Business Rules
MAX_SEATS_PER_BOOKING = 5
BOOKING_TIMEOUT_MINUTES = 15
PAYMENT_TIMEOUT_MINUTES = 30

# API Rate Limiting
API_RATE_LIMIT = '100 per hour'
API_RATE_LIMIT_STORAGE_URL = 'memory://'
