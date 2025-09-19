/**
 * Payment Return Detection System
 * Detects when users return from mobile money apps and checks payment status
 */

class PaymentReturnDetector {
  constructor() {
    this.checkInterval = null;
    this.isActive = false;
    this.init();
  }

  init() {
    // Check if there's a pending booking when page loads
    this.checkPendingBooking();
    
    // Listen for page visibility changes (user returning from another app)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.isActive) {
        console.log('User returned to page, checking payment status...');
        this.checkPaymentStatus();
      }
    });

    // Listen for window focus (user returning to browser)
    window.addEventListener('focus', () => {
      if (this.isActive) {
        console.log('Window focused, checking payment status...');
        this.checkPaymentStatus();
      }
    });
  }

  checkPendingBooking() {
    if (typeof(Storage) === "undefined") return;

    const pendingBookingId = localStorage.getItem('pendingBookingId');
    const pendingBookingTime = localStorage.getItem('pendingBookingTime');

    if (pendingBookingId && pendingBookingTime) {
      const timeElapsed = Date.now() - parseInt(pendingBookingTime);
      const maxAge = 30 * 60 * 1000; // 30 minutes

      // If booking is recent (within 30 minutes), activate monitoring
      if (timeElapsed < maxAge) {
        this.activateMonitoring(pendingBookingId);
      } else {
        // Clean up old booking data
        localStorage.removeItem('pendingBookingId');
        localStorage.removeItem('pendingBookingTime');
      }
    }
  }

  activateMonitoring(bookingId) {
    this.isActive = true;
    this.bookingId = bookingId;
    
    // Show return notification
    this.showReturnNotification();
    
    // Start periodic checking every 15 seconds
    this.checkInterval = setInterval(() => {
      this.checkPaymentStatus();
    }, 15000);
  }

  async checkPaymentStatus() {
    if (!this.bookingId) return;

    try {
      const response = await fetch(`/api/booking-status/${this.bookingId}`);
      const data = await response.json();

      if (data.is_confirmed) {
        // Payment successful - redirect to confirmation
        this.cleanup();
        window.location.href = `/en/booking/confirmation/${this.bookingId}`;
        
      } else if (data.booking_status === 'failed' || data.mesomb_status === 'FAILED') {
        // Payment failed - show notification
        this.cleanup();
        this.showPaymentFailedNotification(data.error_message);
        
      } else {
        // Still pending - continue monitoring
        console.log('Payment still pending:', data.mesomb_status);
      }

    } catch (error) {
      console.error('Error checking payment status:', error);
    }
  }

  showReturnNotification() {
    // Create floating notification
    const notification = document.createElement('div');
    notification.id = 'paymentReturnNotification';
    notification.className = 'alert alert-info position-fixed';
    notification.style.cssText = `
      top: 20px;
      right: 20px;
      z-index: 9999;
      max-width: 350px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      border-radius: 8px;
    `;
    
    notification.innerHTML = `
      <div class="d-flex align-items-center">
        <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
        <div class="flex-grow-1">
          <strong>Checking Payment Status...</strong><br>
          <small>We're verifying your mobile money payment</small>
        </div>
        <button type="button" class="btn-close" onclick="paymentDetector.dismiss()"></button>
      </div>
    `;
    
    document.body.appendChild(notification);
  }

  showPaymentFailedNotification(errorMessage) {
    const notification = document.getElementById('paymentReturnNotification');
    if (notification) {
      notification.className = 'alert alert-danger position-fixed';
      notification.innerHTML = `
        <div class="d-flex align-items-center">
          <i class="fas fa-exclamation-triangle text-danger me-2"></i>
          <div class="flex-grow-1">
            <strong>Payment Failed</strong><br>
            <small>${errorMessage || 'Please try again or contact support'}</small>
          </div>
          <button type="button" class="btn-close" onclick="paymentDetector.dismiss()"></button>
        </div>
      `;
    }
  }

  dismiss() {
    const notification = document.getElementById('paymentReturnNotification');
    if (notification) {
      notification.remove();
    }
    this.cleanup();
  }

  cleanup() {
    this.isActive = false;
    
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    
    // Clean up localStorage
    if (typeof(Storage) !== "undefined") {
      localStorage.removeItem('pendingBookingId');
      localStorage.removeItem('pendingBookingTime');
    }
  }
}

// Initialize the payment return detector
const paymentDetector = new PaymentReturnDetector();

// Export for global access
window.paymentDetector = paymentDetector;
