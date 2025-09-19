# MesomB Payment Gateway Setup Guide

## Overview
Your bus booking system now uses MesomB payment gateway instead of Fapshi. MesomB supports MTN Mobile Money, Orange Money, and Airtel Money in Cameroon.

## Configuration Steps

### 1. Get MesomB Credentials
1. Visit [MesomB Dashboard](https://mesomb.hachther.com/)
2. Create an account or log in
3. Get your credentials:
   - `application_key`
   - `access_key` 
   - `secret_key`

### 2. Update Configuration
Edit `app.py` and replace the placeholder values:

```python
# MesomB Payment Configuration
MESOMB_APPLICATION_KEY = 'your_actual_application_key_here'
MESOMB_ACCESS_KEY = 'your_actual_access_key_here'
MESOMB_SECRET_KEY = 'your_actual_secret_key_here'
MESOMB_BASE_URL = 'https://mesomb.hachther.com'  # Use sandbox URL for testing
```

### 3. Environment Variables (Recommended)
For production, use environment variables instead of hardcoding:

```python
import os

MESOMB_APPLICATION_KEY = os.getenv('MESOMB_APPLICATION_KEY', 'your_default_key')
MESOMB_ACCESS_KEY = os.getenv('MESOMB_ACCESS_KEY', 'your_default_key')
MESOMB_SECRET_KEY = os.getenv('MESOMB_SECRET_KEY', 'your_default_key')
```

### 4. Webhook Configuration
Configure webhook URL in your MesomB dashboard:
- Webhook URL: `https://yourdomain.com/api/mesomb-webhook`
- Events: `transaction.updated`

## Features Implemented

### Payment Flow
1. **Service Selection**: Users can choose MTN, Orange, or Airtel
2. **Phone Validation**: Validates Cameroon mobile format (6XXXXXXXX)
3. **Real-time Processing**: Uses MesomB's collect API
4. **Status Tracking**: Supports both synchronous and asynchronous flows

### Webhook Support
- Secure signature verification
- Automatic booking confirmation
- Real-time status updates

### Error Handling
- Network timeouts
- Invalid phone numbers
- Insufficient funds
- Provider-specific errors

## Testing

### Test Phone Numbers
Use MesomB's test phone numbers for development:
- MTN Test: `670000000`
- Orange Test: `690000000`
- Airtel Test: `650000000`

### Test Amounts
- Minimum: 100 XAF
- Test amounts: 100, 500, 1000 XAF

## API Endpoints

### Payment Processing
- `POST /booking/payment` - Process payment with MesomB

### Webhook Handler
- `POST /api/mesomb-webhook` - Handle MesomB notifications

### Status Check
- `GET /booking/status/<booking_id>` - Check payment status
- `GET /api/payment-status/<booking_id>` - AJAX status endpoint

## Supported Services

1. **MTN Mobile Money**
   - Service code: `MTN`
   - Phone format: `6XXXXXXXX`

2. **Orange Money**
   - Service code: `ORANGE`
   - Phone format: `6XXXXXXXX`

3. **Airtel Money**
   - Service code: `AIRTEL`
   - Phone format: `6XXXXXXXX`

## Security Features

- HMAC-SHA256 webhook signature verification
- Phone number validation
- Secure credential handling
- Request nonce generation
- Replay attack prevention

## Troubleshooting

### Common Issues

1. **Invalid Credentials**
   - Check application_key, access_key, secret_key
   - Verify account status in MesomB dashboard

2. **Phone Number Errors**
   - Ensure format is 6XXXXXXXX (9 digits starting with 6)
   - Remove country codes (+237 or 237)

3. **Webhook Issues**
   - Verify webhook URL is accessible
   - Check signature verification
   - Ensure HTTPS for production

4. **Payment Failures**
   - Check minimum amount (100 XAF)
   - Verify service availability
   - Check customer account balance

### Debug Mode
Enable debug logging in `mesomb_payment.py` by adding:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Checklist

- [ ] Replace test credentials with production keys
- [ ] Use HTTPS for webhook URL
- [ ] Set up proper error logging
- [ ] Configure environment variables
- [ ] Test all payment services (MTN, Orange, Airtel)
- [ ] Verify webhook signature validation
- [ ] Set up monitoring and alerts

## Support

- MesomB Documentation: [API Docs](https://mesomb.hachther.com/api/docs)
- MesomB Support: Contact through dashboard
- Integration Issues: Check logs in `mesomb_payment.py`

## Migration Notes

### From Fapshi to MesomB
- All Fapshi code has been removed
- Database schema remains compatible
- Booking flow enhanced with service selection
- Webhook endpoint changed from `/api/fapshi-webhook` to `/api/mesomb-webhook`

### Key Improvements
- Multiple payment services (MTN, Orange, Airtel)
- Better error handling and validation
- Enhanced webhook security
- Improved user interface
- Real-time status updates
