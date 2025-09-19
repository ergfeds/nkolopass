import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import io
import base64

def get_smtp_config():
    """Get SMTP configuration from environment variables"""
    return {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('SMTP_USERNAME', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'from_name': os.getenv('SMTP_FROM_NAME', 'Nkolo Pass'),
        'from_email': os.getenv('SMTP_FROM_EMAIL', ''),
        'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        'email_tickets': os.getenv('EMAIL_TICKETS', 'true').lower() == 'true'
    }

def send_test_email(to_email):
    """Send a test email to verify SMTP configuration"""
    try:
        config = get_smtp_config()
        
        if not all([config['server'], config['username'], config['password']]):
            print("SMTP configuration incomplete")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = to_email
        msg['Subject'] = "Nkolo Pass - SMTP Test Email"
        
        body = f"""
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>This is a test email from your Nkolo Pass bus booking system.</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>SMTP Server: {config['server']}</li>
                <li>Port: {config['port']}</li>
                <li>TLS: {'Enabled' if config['use_tls'] else 'Disabled'}</li>
                <li>From: {config['from_name']} &lt;{config['from_email']}&gt;</li>
            </ul>
            <p>If you received this email, your SMTP configuration is working correctly!</p>
            <p><em>Test sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(config['server'], config['port'])
        if config['use_tls']:
            server.starttls()
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
        
        print(f"Test email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        return False

def generate_ticket_html(booking):
    """Generate HTML ticket content for email"""
    try:
        # Get booking details
        customer = booking.customer
        trip = booking.trip
        route = trip.route
        operator = trip.operator
        
        # Generate QR code data
        qr_data = f"Booking: {booking.booking_reference}\\nRoute: {route.origin} → {route.destination}\\nDate: {trip.departure_time.strftime('%d/%m/%Y %H:%M')}\\nSeats: {', '.join(map(str, booking.get_seat_numbers()))}\\nAmount: {booking.total_amount:.0f} XAF"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bus Ticket - {booking.booking_reference}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .boarding-pass {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #fff;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
                    overflow: hidden;
                    position: relative;
                }}
                .boarding-pass::before {{
                    content: '';
                    position: absolute;
                    left: 70%;
                    top: 0;
                    bottom: 0;
                    width: 2px;
                    background: repeating-linear-gradient(
                        to bottom,
                        #ddd 0px,
                        #ddd 8px,
                        transparent 8px,
                        transparent 16px
                    );
                    z-index: 1;
                }}
                .ticket-header {{
                    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                    color: white;
                    padding: 16px 24px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .airline-info {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                .airline-logo {{
                    width: 40px;
                    height: 40px;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.2rem;
                }}
                .airline-name {{
                    font-size: 1.1rem;
                    font-weight: 600;
                }}
                .ticket-type {{
                    font-size: 0.85rem;
                    opacity: 0.9;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .status-badge {{
                    background: #dcfce7;
                    color: #166534;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
                .main-content {{
                    display: grid;
                    grid-template-columns: 1fr 2px 200px;
                    min-height: 280px;
                }}
                .left-section {{
                    padding: 24px;
                }}
                .right-section {{
                    padding: 24px 20px;
                    background: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    align-items: center;
                }}
                .route-section {{
                    margin-bottom: 24px;
                }}
                .route-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }}
                .city-code {{
                    font-size: 2rem;
                    font-weight: 700;
                    color: #1e40af;
                    letter-spacing: -1px;
                }}
                .city-name {{
                    font-size: 0.85rem;
                    color: #64748b;
                    margin-top: -4px;
                }}
                .route-arrow {{
                    flex: 1;
                    text-align: center;
                    position: relative;
                    margin: 0 16px;
                }}
                .route-line {{
                    height: 2px;
                    background: #e2e8f0;
                    position: relative;
                }}
                .route-line::after {{
                    content: '✈';
                    position: absolute;
                    right: -8px;
                    top: -8px;
                    background: #fff;
                    color: #3b82f6;
                    font-size: 1rem;
                }}
                .flight-info {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 24px;
                }}
                .info-item {{
                    display: flex;
                    flex-direction: column;
                }}
                .info-label {{
                    font-size: 0.75rem;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 4px;
                }}
                .info-value {{
                    font-size: 0.95rem;
                    font-weight: 600;
                    color: #1e293b;
                }}
                .passenger-section {{
                    border-top: 1px solid #e2e8f0;
                    padding-top: 20px;
                }}
                .seat-info {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .seat-number {{
                    font-size: 1.8rem;
                    font-weight: 700;
                    color: #1e40af;
                    margin-bottom: 4px;
                }}
                .seat-label {{
                    font-size: 0.75rem;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .qr-code {{
                    width: 80px;
                    height: 80px;
                    background: #1e293b;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 2rem;
                    margin-bottom: 8px;
                }}
                .booking-ref {{
                    font-size: 0.8rem;
                    font-weight: 600;
                    color: #1e40af;
                    text-align: center;
                }}
                .boarding-info {{
                    background: #f1f5f9;
                    padding: 16px 24px;
                    border-top: 1px solid #e2e8f0;
                }}
                .boarding-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 16px;
                    font-size: 0.85rem;
                }}
                .boarding-item {{
                    text-align: center;
                }}
                .boarding-value {{
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 2px;
                }}
                .boarding-label {{
                    color: #64748b;
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                @media (max-width: 768px) {{
                    .main-content {{
                        grid-template-columns: 1fr;
                        gap: 16px;
                    }}
                    .boarding-pass::before {{
                        display: none;
                    }}
                    .right-section {{
                        background: #fff;
                        border-top: 2px dashed #ddd;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="boarding-pass">
                <!-- Header -->
                <div class="ticket-header">
                    <div class="airline-info">
                        <div class="airline-logo">🚌</div>
                        <div>
                            <div class="airline-name">Nkolo Pass</div>
                            <div class="ticket-type">Bus Ticket</div>
                        </div>
                    </div>
                    <div>
                        <span class="status-badge">Confirmed</span>
                    </div>
                </div>

                <!-- Main Content -->
                <div class="main-content">
                    <!-- Left Section -->
                    <div class="left-section">
                        <!-- Route -->
                        <div class="route-section">
                            <div class="route-header">
                                <div>
                                    <div class="city-code">{route.origin[:3].upper()}</div>
                                    <div class="city-name">{route.origin}</div>
                                </div>
                                <div class="route-arrow">
                                    <div class="route-line"></div>
                                </div>
                                <div style="text-align: right;">
                                    <div class="city-code">{route.destination[:3].upper()}</div>
                                    <div class="city-name">{route.destination}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Trip Info -->
                        <div class="flight-info">
                            <div class="info-item">
                                <div class="info-label">Departure Date</div>
                                <div class="info-value">{trip.departure_time.strftime('%d %b %Y')}</div>
                            </div>
                            
                            <div class="info-item">
                                <div class="info-label">Departure Time</div>
                                <div class="info-value">{trip.departure_time.strftime('%H:%M')}</div>
                            </div>
                            
                            <div class="info-item">
                                <div class="info-label">Passenger</div>
                                <div class="info-value">{customer.name if customer else 'N/A'}</div>
                            </div>
                            
                            <div class="info-item">
                                <div class="info-label">Phone</div>
                                <div class="info-value">{customer.phone if customer else 'N/A'}</div>
                            </div>
                        </div>

                        <!-- Booking Details -->
                        <div class="passenger-section">
                            <div class="flight-info">
                                <div class="info-item">
                                    <div class="info-label">Booking Reference</div>
                                    <div class="info-value" style="color: #1e40af;">{booking.booking_reference}</div>
                                </div>
                                
                                <div class="info-item">
                                    <div class="info-label">Total Amount</div>
                                    <div class="info-value" style="color: #059669;">{booking.total_amount:.0f} XAF</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Section (Stub) -->
                    <div class="right-section">
                        <div class="seat-info">
                            <div class="seat-number">{', '.join(map(str, booking.get_seat_numbers()))}</div>
                            <div class="seat-label">Seat(s)</div>
                        </div>
                        
                        <div class="qr-code">📱</div>
                        
                        <div class="booking-ref">{booking.booking_reference}</div>
                    </div>
                </div>

                <!-- Footer -->
                <div class="boarding-info">
                    <div class="boarding-grid">
                        <div class="boarding-item">
                            <div class="boarding-value">{operator.name}</div>
                            <div class="boarding-label">Operator</div>
                        </div>
                        
                        <div class="boarding-item">
                            <div class="boarding-value">Confirmed</div>
                            <div class="boarding-label">Payment</div>
                        </div>
                        
                        <div class="boarding-item">
                            <div class="boarding-value">{booking.created_at.strftime('%d/%m/%Y')}</div>
                            <div class="boarding-label">Booked</div>
                        </div>
                        
                        <div class="boarding-item">
                            <div class="boarding-value">Standard</div>
                            <div class="boarding-label">Class</div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        print(f"Error generating ticket HTML: {str(e)}")
        return None

def send_ticket_email(booking):
    """Send e-ticket to customer after successful payment"""
    try:
        config = get_smtp_config()
        
        # Check if email tickets are enabled
        if not config['email_tickets']:
            print("Email tickets are disabled")
            return False
        
        # Check if SMTP is configured
        if not all([config['server'], config['username'], config['password']]):
            print("SMTP configuration incomplete")
            return False
        
        # Check if customer has email
        customer = booking.customer
        if not customer or not customer.email:
            print("Customer email not available")
            return False
        
        # Generate ticket HTML
        ticket_html = generate_ticket_html(booking)
        if not ticket_html:
            print("Failed to generate ticket HTML")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = customer.email
        msg['Subject'] = f"Your Bus Ticket - {booking.booking_reference}"
        
        # Email body
        email_body = f"""
        <html>
        <body>
            <h2>Thank you for your booking!</h2>
            <p>Dear {customer.name},</p>
            <p>Your payment has been successfully processed and your bus ticket is ready!</p>
            
            <h3>Booking Details:</h3>
            <ul>
                <li><strong>Booking Reference:</strong> {booking.booking_reference}</li>
                <li><strong>Route:</strong> {booking.trip.route.origin} → {booking.trip.route.destination}</li>
                <li><strong>Date & Time:</strong> {booking.trip.departure_time.strftime('%d/%m/%Y at %H:%M')}</li>
                <li><strong>Seats:</strong> {', '.join(map(str, booking.get_seat_numbers()))}</li>
                <li><strong>Operator:</strong> {booking.trip.operator.name}</li>
                <li><strong>Total Amount:</strong> {booking.total_amount:.0f} XAF</li>
            </ul>
            
            <p><strong>Important:</strong> Please arrive at the departure point at least 30 minutes before departure time.</p>
            
            <p>Your e-ticket is attached to this email. You can also view it online anytime using your booking reference.</p>
            
            <p>Have a safe journey!</p>
            
            <p>Best regards,<br>
            The Nkolo Pass Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(email_body, 'html'))
        
        # Attach ticket as HTML file
        ticket_attachment = MIMEBase('text', 'html')
        ticket_attachment.set_payload(ticket_html.encode('utf-8'))
        encoders.encode_base64(ticket_attachment)
        ticket_attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="ticket_{booking.booking_reference}.html"'
        )
        msg.attach(ticket_attachment)
        
        # Send email
        server = smtplib.SMTP(config['server'], config['port'])
        if config['use_tls']:
            server.starttls()
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
        
        print(f"Ticket email sent successfully to {customer.email}")
        return True
        
    except Exception as e:
        print(f"Error sending ticket email: {str(e)}")
        return False
