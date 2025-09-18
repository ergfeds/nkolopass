// Nkolo Pass - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS (Animate On Scroll) if available
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-out-cubic',
            once: true,
            offset: 100
        });
    }

    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
            this.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenu.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
            }
        });
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed header
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Form validation and submission
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && form.checkValidity()) {
                showButtonLoading(submitBtn);
            }
        });
    });

    // Auto-hide flash messages
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            if (alert.querySelector('.btn-close')) {
                alert.querySelector('.btn-close').click();
            }
        });
    }, 5000);

    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Touch device enhancements
    if (isTouchDevice()) {
        document.body.classList.add('touch-device');
        
        // Add touch feedback to buttons
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('touchstart', function() {
                this.classList.add('btn-active');
            });
            
            btn.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.classList.remove('btn-active');
                }, 150);
            });
        });
    }
});

// Utility functions
function isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

function isMobileDevice() {
    return window.innerWidth <= 768;
}

function showButtonLoading(button) {
    const originalText = button.innerHTML;
    const loadingText = button.getAttribute('data-loading-text') || 'Loading...';
    
    button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
    button.disabled = true;
    
    // Fallback to re-enable button
    setTimeout(function() {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 30000);
}

// Bus search and booking functionality (for future frontend)
function initializeBusSearch() {
    const searchForm = document.getElementById('busSearchForm');
    if (!searchForm) return;
    
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const searchData = {
            origin: formData.get('origin'),
            destination: formData.get('destination'),
            date: formData.get('date'),
            passengers: formData.get('passengers') || 1
        };
        
        searchBuses(searchData);
    });
}

function searchBuses(searchData) {
    showLoading();
    
    fetch('/api/search-buses', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        displaySearchResults(data.trips);
    })
    .catch(error => {
        hideLoading();
        console.error('Search error:', error);
        showAlert('An error occurred while searching. Please try again.', 'error');
    });
}

function displaySearchResults(trips) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;
    
    if (trips.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4>No trips found</h4>
                <p class="text-muted">Try adjusting your search criteria</p>
            </div>
        `;
        return;
    }
    
    resultsContainer.innerHTML = trips.map(trip => `
        <div class="trip-card card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-3">
                        <div class="operator-info">
                            ${trip.operator.logo ? 
                                `<img src="${trip.operator.logo}" alt="${trip.operator.name}" class="operator-logo">` : 
                                `<div class="operator-placeholder"><i class="fas fa-bus"></i></div>`
                            }
                            <h6>${trip.operator.name}</h6>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="trip-route">
                            <div class="departure">
                                <strong>${trip.departure_time}</strong>
                                <div>${trip.route.origin}</div>
                            </div>
                            <div class="route-line">
                                <i class="fas fa-arrow-right"></i>
                            </div>
                            <div class="arrival">
                                <strong>${trip.arrival_time}</strong>
                                <div>${trip.route.destination}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="trip-duration">
                            <i class="fas fa-clock"></i>
                            ${trip.duration}
                        </div>
                        <div class="available-seats">
                            ${trip.available_seats} seats left
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="trip-price">
                            <strong>${trip.price} XAF</strong>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <button class="btn btn-primary" onclick="selectTrip(${trip.id})">
                            Select
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function selectTrip(tripId) {
    // Store selected trip and redirect to seat selection
    sessionStorage.setItem('selectedTrip', tripId);
    window.location.href = '/booking/seats';
}

function showLoading() {
    const loader = document.getElementById('loadingSpinner');
    if (loader) {
        loader.style.display = 'flex';
    }
}

function hideLoading() {
    const loader = document.getElementById('loadingSpinner');
    if (loader) {
        loader.style.display = 'none';
    }
}

function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 start-50 translate-middle-x';
    container.style.zIndex = '1050';
    container.style.marginTop = '20px';
    document.body.appendChild(container);
    return container;
}
