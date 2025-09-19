# Nkolo Pass - Bus Booking System

A modern, multilingual bus booking platform for Cameroon built with Flask.

## 🚀 Deployment on Namecheap

### Prerequisites
- Namecheap shared hosting with Python support
- Domain name configured

### Configuration Steps

1. **Upload Files**
   - Upload all project files to your public_html directory
   - Ensure proper file permissions (755 for directories, 644 for files)

2. **Python Configuration**
   - Python Version: 3.13
   - Application Root: /public_html/your-app-directory
   - Application URL: https://yourdomain.com
   - Application Startup File: app.py
   - WSGI Callable Object: app

3. **Environment Variables**
   Set these in Namecheap's control panel:

   ```
   FLASK_SECRET_KEY=your-secret-key-here
   MESOMB_APPLICATION_KEY=your-mesomb-application-key
   MESOMB_ACCESS_KEY=your-mesomb-access-key
   MESOMB_SECRET_KEY=your-mesomb-secret-key
   MESOMB_BASE_URL=https://mesomb.hachther.com
   SUPPORT_PHONE=+237 6727714394
   SUPPORT_EMAIL=nkolopass@gmail.com
   WHATSAPP_NUMBER=+237 6727714394
   BUSINESS_HOURS=24/7
   CONTACT_WIDGET_ENABLED=true
   ```

4. **Database**
   - SQLite database will be created automatically
   - Database file: nkolo_pass.db

### File Structure
```
your-app-directory/
├── app.py                 # Main application
├── models.py             # Database models
├── admin_routes.py       # Admin panel routes
├── user_routes.py        # User-facing routes
├── mesomb_payment.py     # Payment integration
├── email_utils.py        # Email utilities
├── passenger_wsgi.py     # WSGI configuration
├── config.py            # Additional configuration
├── .htaccess            # Apache configuration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── templates/           # HTML templates
├── static/              # CSS, JS, images
└── instance/            # SQLite database (created automatically)
```

### Testing
After deployment, test these URLs:
- Homepage: https://yourdomain.com/
- Health Check: https://yourdomain.com/health
- Admin Panel: https://yourdomain.com/admin/

### Support
For issues, check:
- Namecheap error logs
- Application logs in the instance directory
- Database file permissions

## Features
- ✅ Multilingual support (English/French)
- ✅ MeSomb payment integration
- ✅ Real-time seat selection
- ✅ Mobile Money payments
- ✅ Email notifications
- ✅ Admin dashboard
- ✅ Booking management

## Technologies
- Flask 2.3.3
- SQLAlchemy 2.0
- Bootstrap 5
- MeSomb Payment Gateway
- SQLite Database
