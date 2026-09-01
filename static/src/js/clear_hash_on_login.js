/** @odoo-module **/

// When the user is on the login page, we clear the URL hash.
// This prevents Odoo from restoring the previous user's session action
// when logging in as a different user (which causes Access Errors).

if (window.location.pathname === '/web/login' || window.location.pathname === '/login') {
    if (window.location.hash) {
        window.history.replaceState(null, null, window.location.pathname + window.location.search);
        console.log('Hospital Management: Cleared URL hash to prevent AccessError on login.');
    }
    // Also clear sessionStorage just in case Odoo stored the action there.
    sessionStorage.removeItem('current_action');
}

