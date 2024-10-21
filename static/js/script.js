// Function to validate that password and confirm password fields match
function validatePassword() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const errorElement = document.getElementById('password-error');

    if (password !== confirmPassword) {
        errorElement.textContent = "Passwords do not match!";
        return false; // Prevent form submission
    }

    errorElement.textContent = ""; // Clear error message if passwords match
    return true; // Allow form submission
}



