// Toggle Password Visibility
document.addEventListener('DOMContentLoaded', function() {
    
    // Toggle Password
    const togglePassword = document.getElementById('togglePassword');
    if (togglePassword) {
        togglePassword.addEventListener('change', function() {
            const passwordField = document.getElementById('password');
            if (passwordField) {
                passwordField.type = this.checked ? 'text' : 'password';
            }
        });
    }
    
    // NOTE: Removed confirm dialog for cancel buttons
    // Custom modal popups are now used instead in my_bookings.html and admin pages
    
});