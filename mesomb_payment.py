import hashlib
import hmac
import time
import os
from datetime import datetime
from flask import current_app
from pymesomb.operations import PaymentOperation
from pymesomb.utils import RandomGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MesombPayment:
    """MesomB Payment Gateway Integration using Official SDK with Best Practices"""
    
    def __init__(self, application_key=None, access_key=None, secret_key=None):
        # Use environment variables if not provided
        self.application_key = application_key or os.getenv('MESOMB_APPLICATION_KEY')
        self.access_key = access_key or os.getenv('MESOMB_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('MESOMB_SECRET_KEY')
        
        if not all([self.application_key, self.access_key, self.secret_key]):
            raise ValueError("MeSomb credentials not found. Please set MESOMB_APPLICATION_KEY, MESOMB_ACCESS_KEY, and MESOMB_SECRET_KEY in environment variables.")
        
        self.client = PaymentOperation(
            self.application_key,
            self.access_key, 
            self.secret_key
        )
        
    def collect_payment(self, amount, payer_phone, service, customer_data, booking_reference, products=None):
        """
        Collect payment from customer using MesomB API with improved patterns
        
        Args:
            amount (float): Payment amount in XAF
            payer_phone (str): Customer's phone number
            service (str): Payment service: MTN, ORANGE, or AIRTEL
            customer_data (dict): Customer information
            booking_reference (str): Unique booking reference
            products (list): Optional product information
            
        Returns:
            dict: Payment response with transaction details and debug info
        """
        
        try:
            print(f"\n=== Processing Bus Booking Payment ===")
            print(f"Amount: {amount} XAF, Phone: {payer_phone}, Service: {service}")
            
            # Validate amount (minimum 100 XAF)
            amount = float(amount)
            if amount < 100:
                return {
                    "success": False,
                    "error": "Amount cannot be less than 100 XAF"
                }
            
            # Format phone number to local format
            formatted_phone = self._format_phone_number(payer_phone)
            if not formatted_phone:
                return {
                    "success": False,
                    "error": "Invalid phone number format. Should be 6XXXXXXXX for Cameroon"
                }
            
            # Validate service
            if service.upper() not in ['MTN', 'ORANGE', 'AIRTEL']:
                return {
                    "success": False,
                    "error": "Invalid service. Must be MTN, ORANGE, or AIRTEL"
                }
            
            # Generate unique transaction ID using timestamp pattern
            trx_id = f"BUS{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Prepare structured payment data
            payment_data = {
                'amount': amount,
                'service': service.upper(),
                'payer': formatted_phone,
                'trx_id': trx_id,
                'nonce': RandomGenerator.nonce(),
                'mode': 'synchronous',  # Use synchronous mode for immediate response
                'fees': True,
                'currency': 'XAF',
                'customer': {
                    'phone': customer_data.get('phone', formatted_phone),
                    'first_name': customer_data.get('name', '').split()[0] if customer_data.get('name') else 'Customer',
                    'last_name': ' '.join(customer_data.get('name', '').split()[1:]) if len(customer_data.get('name', '').split()) > 1 else 'User'
                },
                'location': {
                    'town': 'Douala',
                    'region': 'Littoral', 
                    'country': 'Cameroon'
                },
                'products': products or [{
                    'id': f'TRIP-{booking_reference}',
                    'name': f'Bus Ticket - {booking_reference}',
                    'category': 'Transportation',
                    'quantity': 1,
                    'amount': amount
                }]
            }
            
            print("Sending request to MeSomb API...")
            
            # Make the payment request
            response = self.client.make_collect(**payment_data)
            
            print(f"\n=== MeSomb API Response ===")
            print(f"Response type: {type(response)}")
            
            # Get the response data using the pattern from your test implementation
            response_data = getattr(response, '_data', {})
            
            # If _data is empty, try to get response as dict
            if not response_data and hasattr(response, '__dict__'):
                response_data = vars(response).get('_data', {})
            
            print("Response data:", response_data)
            
            # Get transaction details
            transaction = response_data.get('transaction', {})
            mesomb_status = transaction.get('status', '').upper()
            
            print(f"MeSomb Transaction Status: {mesomb_status}")
            
            # Handle based on official MeSomb transaction statuses
            if mesomb_status == 'SUCCESS':
                # FINAL STATUS: Transaction completed successfully
                return {
                    'status': 'success',
                    'mesomb_status': 'SUCCESS',
                    'message': 'Payment completed successfully',
                    'transaction_id': transaction.get('pk'),
                    'trx_id': trx_id,
                    'amount': transaction.get('amount', amount),
                    'fees': transaction.get('fees', 0),
                    'service': transaction.get('service', service),
                    'reference': transaction.get('reference'),
                    'fin_trx_id': transaction.get('fin_trx_id'),
                    'transaction': transaction,
                    'debug': {
                        'request': payment_data,
                        'response': response_data
                    }
                }
            elif mesomb_status == 'FAILED':
                # FINAL STATUS: Transaction failed
                error_msg = transaction.get('message') or response_data.get('message', 'Payment failed')
                return {
                    'status': 'error',
                    'mesomb_status': 'FAILED',
                    'message': f'Payment failed: {error_msg}',
                    'trx_id': trx_id,
                    'transaction_id': transaction.get('pk'),
                    'debug': {
                        'request': payment_data,
                        'response': response_data
                    }
                }
            elif mesomb_status == 'PENDING':
                # INTERMEDIATE STATUS: Transaction is processing
                return {
                    'status': 'pending',
                    'mesomb_status': 'PENDING',
                    'message': 'Payment is being processed. Please check your phone and approve the transaction.',
                    'trx_id': trx_id,
                    'transaction_id': transaction.get('pk'),
                    'debug': {
                        'request': payment_data,
                        'response': response_data
                    }
                }
            elif mesomb_status == 'CANCELED':
                # INTERMEDIATE STATUS: Transaction was canceled
                return {
                    'status': 'error',
                    'mesomb_status': 'CANCELED',
                    'message': 'Payment was canceled. Please try again.',
                    'trx_id': trx_id,
                    'transaction_id': transaction.get('pk'),
                    'debug': {
                        'request': payment_data,
                        'response': response_data
                    }
                }
            elif mesomb_status == 'ERRORED':
                # INTERMEDIATE STATUS: Transaction encountered an error
                error_msg = transaction.get('message') or 'Transaction encountered an error'
                return {
                    'status': 'error',
                    'mesomb_status': 'ERRORED',
                    'message': f'Payment error: {error_msg}',
                    'trx_id': trx_id,
                    'transaction_id': transaction.get('pk'),
                    'debug': {
                        'request': payment_data,
                        'response': response_data
                    }
                }
            else:
                # Unknown or missing status
                return {
                    'status': 'error',
                    'mesomb_status': mesomb_status or 'UNKNOWN',
                    'message': f'Unknown payment status: {mesomb_status}. Please contact support.',
                    'trx_id': trx_id,
                    'transaction_id': transaction.get('pk'),
                    'debug': {
                        'request': payment_data,
                        'response': response_data
                    }
                }
                
        except Exception as e:
            error_msg = f"Payment processing error: {str(e)}"
            print(f"Exception in collect_payment: {error_msg}")
            
            return {
                'status': 'error',
                'message': error_msg,
                'debug': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            }
    
    def check_transaction_status(self, transaction_id):
        """
        Check the status of a transaction
        Note: This would require a status endpoint from MesomB API
        For now, this is a placeholder that can be extended when the status endpoint is available
        
        Args:
            transaction_id (str): Transaction ID to check
            
        Returns:
            dict: Transaction status information
        """
        
        # TODO: Implement actual status check when MesomB provides status endpoint
        # For now, return a placeholder response
        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": "PENDING",  # Would be SUCCESS, FAILED, or PENDING
            "message": "Status check not yet implemented - use webhooks for real-time updates"
        }
    
    def verify_webhook_signature(self, payload, signature_header, webhook_secret=None):
        """
        Verify webhook signature from MesomB
        
        Args:
            payload (str): Raw webhook payload
            signature_header (str): Signature from webhook header
            webhook_secret (str): Webhook secret (defaults to secret_key)
            
        Returns:
            bool: True if signature is valid
        """
        
        if not webhook_secret:
            webhook_secret = self.secret_key
        
        try:
            # Expected format: "sha256=<signature>"
            if signature_header.startswith('sha256='):
                provided_signature = signature_header[7:]
            else:
                provided_signature = signature_header
            
            # Compute expected signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Secure comparison
            return hmac.compare_digest(expected_signature, provided_signature)
            
        except Exception as e:
            print(f"Webhook signature verification error: {str(e)}")
            return False
    
    def _format_phone_number(self, phone):
        """
        Format phone number to local Cameroon format (6XXXXXXXX)
        
        Args:
            phone (str): Phone number in various formats
            
        Returns:
            str: Formatted phone number or None if invalid
        """
        
        if not phone:
            return None
        
        # Remove all non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if phone.startswith('237'):
            phone = phone[3:]  # Remove country code
        elif phone.startswith('+237'):
            phone = phone[4:]  # Remove country code with +
        
        # Validate Cameroon mobile format (should start with 6 and be 9 digits)
        if len(phone) == 9 and phone.startswith('6'):
            return phone
        
        return None
    
    def get_supported_services(self):
        """
        Get list of supported payment services
        
        Returns:
            list: Supported services
        """
        return ['MTN', 'ORANGE', 'AIRTEL']
    
    def format_amount(self, amount):
        """
        Format amount for display
        
        Args:
            amount (float): Amount to format
            
        Returns:
            str: Formatted amount string
        """
        return f"{amount:,.0f} XAF"


    def process_webhook(self, webhook_data):
        """
        Process webhook data from MeSomb for payment status updates
        
        Args:
            webhook_data (dict): Webhook payload from MeSomb
            
        Returns:
            dict: Processed webhook information
        """
        try:
            print(f"\n=== Processing MeSomb Webhook ===")
            print(f"Webhook data: {webhook_data}")
            
            event = webhook_data.get('event')
            transaction = webhook_data.get('transaction', {})
            
            if event == 'transaction.updated':
                status = transaction.get('status')
                trx_id = transaction.get('trxID')
                amount = transaction.get('amount')
                service = transaction.get('service')
                
                print(f"Transaction {trx_id} status updated to: {status}")
                
                return {
                    'success': True,
                    'event': event,
                    'transaction_id': transaction.get('pk'),
                    'trx_id': trx_id,
                    'status': status,
                    'amount': amount,
                    'service': service,
                    'message': f'Transaction {trx_id} status updated to {status}'
                }
            else:
                return {
                    'success': True,
                    'event': event,
                    'message': f'Webhook event {event} received'
                }
                
        except Exception as e:
            print(f"Webhook processing error: {str(e)}")
            return {
                'success': False,
                'error': f'Webhook processing error: {str(e)}'
            }


def get_mesomb_client():
    """Get configured MesomB client instance using environment variables"""
    try:
        return MesombPayment()
    except ValueError as e:
        # Fallback to Flask config if environment variables not found
        if current_app:
            return MesombPayment(
                application_key=current_app.config.get('MESOMB_APPLICATION_KEY'),
                access_key=current_app.config.get('MESOMB_ACCESS_KEY'),
                secret_key=current_app.config.get('MESOMB_SECRET_KEY')
            )
        else:
            raise e
