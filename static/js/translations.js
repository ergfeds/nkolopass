// Bilingual translation system
const translations = {
    en: {
        // Payment
        'payment.secure': 'Secure Payment',
        'payment.mobile_money': 'Mobile Money',
        'payment.card_payment': 'Card Payment',
        'payment.processing': 'Processing payment...',
        'payment.success': 'Payment successful!',
        'payment.failed': 'Payment failed',
        // Navigation
        'nav.home': 'Home',
        'nav.search': 'Search Trips',
        'nav.retrieve': 'Retrieve Ticket',
        'nav.bookings': 'My Bookings',
        'nav.contact': 'Contact',
        'nav.login': 'Login',
        'nav.register': 'Register',
        'nav.logout': 'Logout',
        
        // Homepage Hero
        'hero.title': "Cameroon's #1 Bus Booking Platform",
        'hero.subtitle': 'Book your bus tickets online with ease',
        'hero.search_button': 'Search buses',
        
        // Search
        'search.from': 'From',
        'search.to': 'To',
        'search.from_placeholder': 'Departure city',
        'search.to_placeholder': 'Arrival city',
        'search.operator': 'Operator',
        'search.date': 'Date',
        'search.search_buses': 'Search Buses',
        'search.today': 'Today',
        'search.tomorrow': 'Tomorrow',
        'search.select_route_first': 'Select a route first',
        'search.select_operator': 'Choose an operator',
        
        // Trips
        'trips.upcoming': 'Upcoming Departures',
        'trips.view_all': 'View All Trips',
        
        // Search Results
        'page.search_results_title': 'Search Results - Nkolo Pass',
        'search.modify_search': 'Modify Search',
        'search.filters': 'Filters',
        'search.filter_all': 'All',
        'search.filter_vip': 'VIP',
        'search.filter_regular': 'Regular',
        'search.filter_morning': 'Morning (6AM-12PM)',
        'search.filter_afternoon': 'Afternoon (12PM-6PM)',
        'search.filter_evening': 'Evening (6PM-12AM)',
        'search.trips_available': 'trips available',
        'search.no_results': 'No trips found',
        'search.no_results_desc': 'Try modifying your search criteria',
        'search.new_search': 'New Search',
        
        // Features
        'features.title': 'Why Choose Us?',
        'features.secure': 'Secure Booking',
        'features.secure_desc': 'Safe and secure online payment',
        'features.operators': 'Multiple Operators',
        'features.operators_desc': 'Choose from different operators',
        'features.support': '24/7 Support',
        'features.support_desc': 'Customer service available 24/7',
        'features.easy': 'Easy Refunds',
        'features.easy_desc': 'Quick and hassle-free refunds',
        
        // Trip Results
        'trips.title': 'Available Trips',
        'trips.no_results': 'No trips found for your search',
        'trips.departure': 'Departure',
        'trips.arrival': 'Arrival',
        'trips.duration': 'Duration',
        'trips.seats_available': 'Seats Available',
        'trips.price': 'Price',
        'trips.select_seats': 'Select Seats',
        'trips.sold_out': 'Sold Out',
        'trips.departing_soon': 'Departing Soon',
        
        // Booking
        'booking.select_seats': 'Select Your Seats',
        'booking.passenger_details': 'Passenger Details',
        'booking.payment': 'Payment',
        'booking.confirm': 'Confirm Booking',
        'booking.total': 'Total Amount',
        
        // Seat Selection
        'seat.driver': 'Driver',
        'seat.available': 'Available',
        'seat.selected': 'Selected',
        'seat.occupied': 'Occupied',
        'seat.selection_summary': 'Selection Summary',
        'seat.selected_seats': 'Selected seats:',
        'seat.no_seats_selected': 'No seats selected',
        'seat.seat_count': 'Number of seats:',
        'seat.price_per_seat': 'Price per seat:',
        'seat.total': 'Total:',
        'seat.continue': 'Continue',
        
        // Passenger Details
        'page.passenger_details_title': 'Passenger Details - Nkolo Pass',
        'progress.seats_selected': '✓ Seat Selection',
        'progress.passenger_details': '2. Passenger Details',
        'passenger.contact_info': 'Contact Information',
        'passenger.full_name': 'Full Name *',
        'passenger.email': 'Email *',
        'passenger.email_note': 'Ticket will be sent to this address',
        'passenger.phone': 'Phone *',
        'passenger.phone_note': 'For ticket retrieval',
        'passenger.passenger_details': 'Passenger Details',
        
        // Footer
        'footer.about': 'About Us',
        'footer.terms': 'Terms & Conditions',
        'footer.privacy': 'Privacy Policy',
        'footer.contact': 'Contact Us',
        'footer.rights': 'All rights reserved',
        'footer.tagline': 'Your trusted travel partner',
        
        // Homepage Hero
        'hero.title': "Cameroon's #1 Bus Booking Platform",
        'hero.subtitle': 'Book your bus tickets online with ease',
        'hero.search_button': 'Search buses',
        
        // Search Form
        'search.from': 'From',
        'search.from_placeholder': 'Departure city',
        'search.to': 'To',
        'search.to_placeholder': 'Arrival city',
        'search.date': 'Date of Journey',
        'search.operator': 'Operator',
        'search.select_operator': 'Select operator',
        'search.select_route_first': 'Please select a route first',
        'search.today': 'Today',
        'search.tomorrow': 'Tomorrow',
        'search.search_buses': 'Search Buses',
        
        // Features
        'features.title': 'Why Choose Us?',
        'features.secure': 'Secure Booking',
        'features.secure_desc': 'Safe and secure online payment',
        'features.operators': 'Multiple Operators',
        'features.operators_desc': 'Choose from various bus operators',
        'features.support': '24/7 Support',
        'features.support_desc': 'Round the clock customer support',
        'features.easy': 'Easy Refunds',
        'features.easy_desc': 'Quick and hassle-free refunds',
        
        // Trip Results
        'trips.title': 'Available Trips',
        'trips.no_results': 'No trips found for your search',
        'trips.departure': 'Departure',
        'trips.arrival': 'Arrival',
        'trips.duration': 'Duration',
        'trips.seats_available': 'Seats Available',
        'trips.price': 'Price',
        'trips.select_seats': 'Select Seats',
        'trips.sold_out': 'Sold Out',
        'trips.departing_soon': 'Departing Soon',
        
        // Booking
        'booking.select_seats': 'Select Your Seats',
        'booking.passenger_details': 'Passenger Details',
        'booking.payment': 'Payment',
        'booking.confirm': 'Confirm Booking',
        'booking.total': 'Total Amount',
        
        // Seat Selection
        'seat.driver': 'Driver',
        'seat.available': 'Available',
        'seat.selected': 'Selected',
        'seat.occupied': 'Occupied',
        'seat.selection_summary': 'Selection Summary',
        'seat.selected_seats': 'Selected seats:',
        'seat.no_seats_selected': 'No seats selected',
        'seat.seat_count': 'Number of seats:',
        'seat.price_per_seat': 'Price per seat:',
        'seat.total': 'Total:',
        'seat.continue': 'Continue',
        
        // Footer
        'footer.about': 'About Us',
        'footer.terms': 'Terms & Conditions',
        'footer.privacy': 'Privacy Policy',
        'footer.contact': 'Contact Us',
        'footer.rights': 'All rights reserved'
    },
    
    fr: {
        // Payment
        'payment.secure': 'Paiement Sécurisé',
        'payment.mobile_money': 'Mobile Money',
        'payment.card_payment': 'Paiement par Carte',
        'payment.processing': 'Traitement du paiement...',
        'payment.success': 'Paiement réussi!',
        'payment.failed': 'Échec du paiement',
        
        // Navigation
        'nav.home': 'Accueil',
        'nav.search': 'Rechercher des Voyages',
        'nav.retrieve': 'Récupérer Billet',
        'nav.bookings': 'Mes Réservations',
        'nav.contact': 'Contact',
        'nav.login': 'Connexion',
        'nav.register': "S'inscrire",
        'nav.logout': 'Déconnexion',
        
        // Homepage Hero
        'hero.title': "La Plateforme #1 de Réservation de Bus au Cameroun",
        'hero.subtitle': 'Réservez vos billets de bus en ligne facilement',
        'hero.search_button': 'Rechercher des bus',
        
        // Search Form
        'search.from': 'De',
        'search.from_placeholder': 'Ville de départ',
        'search.to': 'À',
        'search.to_placeholder': "Ville d'arrivée",
        'search.date': 'Date du Voyage',
        'search.operator': 'Opérateur',
        'search.select_operator': 'Sélectionner un opérateur',
        'search.select_route_first': "Veuillez d'abord sélectionner un itinéraire",
        'search.today': "Aujourd'hui",
        'search.tomorrow': 'Demain',
        'search.search_buses': 'Rechercher des Bus',
        
        // Features
        'features.title': 'Pourquoi Nous Choisir?',
        'features.secure': 'Réservation Sécurisée',
        'features.secure_desc': 'Paiement en ligne sûr et sécurisé',
        'features.operators': 'Plusieurs Opérateurs',
        'features.operators_desc': "Choisissez parmi différents opérateurs de bus",
        'features.support': 'Support 24/7',
        'features.support_desc': 'Service client disponible 24h/24',
        'features.easy': 'Remboursements Faciles',
        'features.easy_desc': 'Remboursements rapides et sans tracas',
        
        // Trip Results
        'trips.title': 'Voyages Disponibles',
        'trips.no_results': 'Aucun voyage trouvé pour votre recherche',
        'trips.departure': 'Départ',
        'trips.arrival': 'Arrivée',
        'trips.duration': 'Durée',
        'trips.seats_available': 'Sièges Disponibles',
        'trips.price': 'Prix',
        'trips.select_seats': 'Sélectionner les Sièges',
        'trips.sold_out': 'Complet',
        'trips.departing_soon': 'Départ Imminent',
        
        // Booking
        'booking.select_seats': 'Sélectionnez Vos Sièges',
        'booking.passenger_details': 'Détails des Passagers',
        'booking.payment': 'Paiement',
        'booking.confirm': 'Confirmer la Réservation',
        'booking.total': 'Montant Total',
        
        // Seat Selection
        'seat.driver': 'Chauffeur',
        'seat.available': 'Disponible',
        'seat.selected': 'Sélectionné',
        'seat.occupied': 'Occupé',
        'seat.selection_summary': 'Résumé de la sélection',
        'seat.selected_seats': 'Sièges sélectionnés:',
        'seat.no_seats_selected': 'Aucun siège sélectionné',
        'seat.seat_count': 'Nombre de sièges:',
        'seat.price_per_seat': 'Prix par siège:',
        'seat.total': 'Total:',
        'seat.continue': 'Continuer',
        
        // Passenger Details
        'page.passenger_details_title': 'Détails des Passagers - Nkolo Pass',
        'progress.seats_selected': '✓ Sélection des sièges',
        'progress.passenger_details': '2. Détails des passagers',
        'passenger.contact_info': 'Informations de Contact',
        'passenger.full_name': 'Nom complet *',
        'passenger.email': 'Email *',
        'passenger.email_note': 'Le billet sera envoyé à cette adresse',
        'passenger.phone': 'Téléphone *',
        'passenger.phone_note': 'Pour la récupération du billet',
        'passenger.passenger_details': 'Détails des Passagers',
        
        // Trips
        'trips.upcoming': 'Prochains Départs',
        'trips.view_all': 'Voir tous les voyages',
        
        // Search Results
        'page.search_results_title': 'Résultats de Recherche - Nkolo Pass',
        'search.modify_search': 'Modifier la recherche',
        'search.filters': 'Filtres',
        'search.filter_all': 'Tous',
        'search.filter_vip': 'VIP',
        'search.filter_regular': 'Regular',
        'search.filter_morning': 'Matin (06h-12h)',
        'search.filter_afternoon': 'Après-midi (12h-18h)',
        'search.filter_evening': 'Soir (18h-00h)',
        'search.trips_available': 'voyages disponibles',
        'search.no_results': 'Aucun voyage trouvé',
        'search.no_results_desc': 'Essayez de modifier vos critères de recherche',
        'search.new_search': 'Nouvelle recherche',
        
        // Footer
        'footer.about': 'À Propos',
        'footer.terms': 'Conditions Générales',
        'footer.privacy': 'Politique de Confidentialité',
        'footer.contact': 'Nous Contacter',
        'footer.rights': 'Tous droits réservés',
        'footer.tagline': 'Votre partenaire de voyage de confiance'
    }
};

// Language Manager
class LanguageManager {
    constructor() {
        // Get language from URL instead of localStorage
        this.currentLang = this.getLanguageFromURL();
        this.init();
    }
    
    getLanguageFromURL() {
        const pathParts = window.location.pathname.split('/');
        if (pathParts[1] === 'en' || pathParts[1] === 'fr') {
            return pathParts[1];
        }
        return 'fr'; // Default language
    }
    
    init() {
        // Apply translations on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.updatePageLanguage();
            this.setupLanguageSwitcher();
        });
    }
    
    setupLanguageSwitcher() {
        const switchers = document.querySelectorAll('[data-lang-switch]');
        switchers.forEach(switcher => {
            switcher.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = switcher.dataset.langSwitch;
                this.switchLanguageURL(lang);
            });
        });
    }
    
    switchLanguageURL(lang) {
        if (lang !== this.currentLang && translations[lang]) {
            // Get current path without language prefix
            const currentPath = window.location.pathname;
            const pathParts = currentPath.split('/');
            
            // Remove current language prefix if exists
            if (pathParts[1] === 'en' || pathParts[1] === 'fr') {
                pathParts.splice(1, 1);
            }
            
            // Add new language prefix
            const newPath = `/${lang}${pathParts.join('/')}`;
            const queryString = window.location.search;
            
            // Redirect to new URL
            window.location.href = newPath + queryString;
        }
    }
    
    switchLanguage(lang) {
        // For backward compatibility and direct language switching
        if (lang !== this.currentLang && translations[lang]) {
            this.currentLang = lang;
            this.updatePageLanguage();
            this.updateActiveSwitcher();
            
            // Trigger custom event for other components
            window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
        }
    }
    
    updatePageLanguage() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.dataset.i18n;
            const translation = this.translate(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.placeholder) {
                    element.placeholder = translation;
                }
            } else {
                element.textContent = translation;
            }
        });
        
        // Update all elements with data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.dataset.i18nPlaceholder;
            element.placeholder = this.translate(key);
        });
        
        // Update document language
        document.documentElement.lang = this.currentLang;
    }
    
    updateActiveSwitcher() {
        // Update active state of language switchers
        document.querySelectorAll('[data-lang-switch]').forEach(switcher => {
            if (switcher.dataset.langSwitch === this.currentLang) {
                switcher.classList.add('active');
                switcher.style.background = '#2563eb';
                switcher.style.color = 'white';
            } else {
                switcher.classList.remove('active');
                switcher.style.background = 'transparent';
                switcher.style.color = '#6b7280';
            }
        });
    }
    
    translate(key) {
        return translations[this.currentLang][key] || key;
    }
    
    getCurrentLanguage() {
        return this.currentLang;
    }
}

// Initialize language manager
const langManager = new LanguageManager();

// Export for use in other scripts
window.langManager = langManager;
window.__ = (key) => langManager.translate(key);
