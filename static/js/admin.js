// Nkolo Pass - Modern Admin Panel JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize dropdowns explicitly
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });

    // Initialize DataTables with mobile-first responsive design
    if ($.fn.DataTable) {
        // Initialize only tables not already initialised
        $('table').each(function() {
            const $t = $(this);
            if ($.fn.dataTable.isDataTable($t)) return;
            $t.DataTable({
                responsive: true,
                pageLength: 25,
                order: [[ 0, "desc" ]],
                language: {
                    search: "_INPUT_",
                    searchPlaceholder: "Search...",
                    lengthMenu: "_MENU_ entries per page",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    infoEmpty: "No entries found",
                    infoFiltered: "(filtered from _MAX_ total entries)",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                },
                dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                     '<"row"<"col-sm-12"tr>>' +
                     '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
                drawCallback: function() {
                    // Re-initialize tooltips after table redraw
                    $('[data-bs-toggle="tooltip"]').tooltip();
                }
            });
        });
    }

    // Mobile menu enhancements
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('mobile-menu-open');
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
                if (navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                    document.body.classList.remove('mobile-menu-open');
                }
            }
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation enhancements
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            } else {
                // Defer disabling the submit button so the browser can proceed with submission
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    setTimeout(function() { showLoading(submitBtn); }, 0);
                }
            }
            form.classList.add('was-validated');
        });
    });

    // Note: loading state is now triggered from the form 'submit' handler above

    // File upload preview
    document.querySelectorAll('input[type="file"]').forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewId = input.getAttribute('data-preview');
                    if (previewId) {
                        const preview = document.getElementById(previewId);
                        if (preview) {
                            preview.src = e.target.result;
                            preview.style.display = 'block';
                        }
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Card hover effects for touch devices
    if ('ontouchstart' in window) {
        document.querySelectorAll('.card').forEach(function(card) {
            card.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            });
            
            card.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.classList.remove('touch-active');
                }, 300);
            });
        });
    }
});

// Loading state function
function showLoading(button) {
    const originalText = button.innerHTML;
    const loadingText = button.getAttribute('data-loading-text') || 'Loading...';
    
    button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
    button.disabled = true;
    
    // Re-enable after 30 seconds as fallback
    setTimeout(function() {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 30000);
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '11';
    document.body.appendChild(container);
    return container;
}

// Utility functions for mobile
function isMobile() {
    return window.innerWidth <= 768;
}

function isTouch() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

// Responsive table helper
function makeTableResponsive() {
    const tables = document.querySelectorAll('.table:not(.table-responsive *)');
    tables.forEach(function(table) {
        if (!table.closest('.table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}

// Initialize responsive tables
document.addEventListener('DOMContentLoaded', makeTableResponsive);

// Seat map functionality (for bus management)
function initializeSeatMap(busId, seatLayout) {
    const seatMapContainer = document.getElementById('seatMap');
    if (!seatMapContainer) return;
    
    seatMapContainer.innerHTML = '';
    
    seatLayout.forEach(function(row, rowIndex) {
        const rowElement = document.createElement('div');
        rowElement.className = 'seat-row';
        
        row.forEach(function(seat) {
            const seatElement = document.createElement('div');
            seatElement.className = `seat ${seat.status || 'available'}`;
            seatElement.textContent = seat.number;
            seatElement.setAttribute('data-seat', seat.number);
            
            seatElement.addEventListener('click', function() {
                if (!this.classList.contains('booked')) {
                    this.classList.toggle('selected');
                    updateSelectedSeats();
                }
            });
            
            rowElement.appendChild(seatElement);
        });
        
        seatMapContainer.appendChild(rowElement);
    });
}

function updateSelectedSeats() {
    const selectedSeats = document.querySelectorAll('.seat.selected');
    const seatNumbers = Array.from(selectedSeats).map(seat => seat.getAttribute('data-seat'));
    
    const seatInput = document.getElementById('selectedSeats');
    if (seatInput) {
        seatInput.value = seatNumbers.join(',');
    }
    
    // Update seat count and total price if applicable
    const seatCount = document.getElementById('seatCount');
    if (seatCount) {
        seatCount.textContent = seatNumbers.length;
    }
}
