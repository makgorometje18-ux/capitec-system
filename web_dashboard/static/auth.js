/**
 * Authentication JavaScript for Capitec CDRS
 * Handles login, logout, password management
 */

// API endpoints
const API_ENDPOINTS = {
    login: '/api/auth/login',
    logout: '/api/auth/logout',
    changePassword: '/api/auth/change-password',
    forgotPassword: '/api/auth/forgot-password',
    firstLogin: '/api/auth/first-login'
};

// Current auth state
let currentUser = null;
let tempPassword = null;
let selectedRole = '';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
});

function initializeAuth() {
    // Setup login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Setup first login form
    const firstLoginForm = document.getElementById('firstLoginForm');
    if (firstLoginForm) {
        firstLoginForm.addEventListener('submit', handleFirstLogin);
    }

    // Setup forgot password form
    const forgotPasswordForm = document.getElementById('forgotPasswordForm');
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener('submit', handleForgotPassword);
    }

    // Setup password expired form
    const passwordExpiredForm = document.getElementById('passwordExpiredForm');
    if (passwordExpiredForm) {
        passwordExpiredForm.addEventListener('submit', handlePasswordExpired);
    }

    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const expired = urlParams.get('expired');
    const firstLogin = urlParams.get('first_login');

    if (expired === 'true') {
        showPasswordExpired();
    } else if (firstLogin === 'true') {
        showFirstLogin();
    }
}

// ================================================================
// ROLE SELECTOR
// ================================================================

function selectRole(role) {
    // Update visual state of role cards
    document.querySelectorAll('.role-card').forEach(card => {
        card.classList.remove('selected');
    });
    const selectedCard = document.querySelector(`.role-card[data-role="${role}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    selectedRole = role;
    document.getElementById('userFields').style.display = 'block';
    document.getElementById('passwordSection').style.display = 'block';
    document.getElementById('loginBtn').style.display = 'block';
    document.getElementById('loginPassword').focus();
    document.getElementById('loginPassword').value = '';
    
    if (role === 'ADMIN') {
        document.getElementById('usernameSection').style.display = 'none';
    } else {
        document.getElementById('usernameSection').style.display = 'block';
        document.getElementById('loginUsername').value = '';
        document.getElementById('loginUsername').focus();
    }
}

function cancelLogin() {
    document.querySelectorAll('.role-card').forEach(card => {
        card.classList.remove('selected');
    });
    document.getElementById('userFields').style.display = 'none';
    document.getElementById('passwordSection').style.display = 'none';
    document.getElementById('loginBtn').style.display = 'none';
    document.getElementById('usernameSection').style.display = 'none';
    document.getElementById('loginError').classList.add('d-none');
    selectedRole = '';
}

function showManualLogin() {
    document.getElementById('roleButtons').style.display = 'none';
    cancelLogin();
    document.getElementById('userFields').style.display = 'block';
    document.getElementById('usernameSection').style.display = 'block';
    document.getElementById('passwordSection').style.display = 'block';
    document.getElementById('loginBtn').style.display = 'block';
    selectedRole = null;
}

function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// ================================================================
// FORM HANDLERS
// ================================================================

async function handleLogin(e) {
    e.preventDefault();
    
    let username;
    if (selectedRole === 'ADMIN') {
        username = 'ADMIN';
    } else if (selectedRole === 'STAFF') {
        username = document.getElementById('loginUsername').value.trim().toUpperCase();
    } else {
        username = document.getElementById('loginUsername').value.trim().toUpperCase();
    }
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    const errorText = document.getElementById('loginErrorText');
    const submitBtn = document.getElementById('loginBtn');
    
    // Hide previous errors
    errorDiv.classList.add('d-none');
    
    // Validate inputs
    if (!username || !password) {
        showError(errorDiv, errorText, 'Please enter your username and password');
        return;
    }

    // Disable button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';

    try {
        const response = await fetch(API_ENDPOINTS.login, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser = {
                username: data.username,
                role: data.role
            };

            if (data.must_change_password) {
                // User logged in with temporary password - must change it
                window.location.href = '/login?first_login=true&username=' + encodeURIComponent(username);
            } else if (data.first_login) {
                window.location.href = '/login?first_login=true&username=' + encodeURIComponent(username);
            } else {
                window.location.href = '/';
            }
        } else {
            if (data.expired) {
                showError(errorDiv, errorText, data.error);
                setTimeout(() => {
                    window.location.href = '/login?expired=true';
                }, 2000);
            } else {
                showError(errorDiv, errorText, data.error || 'Invalid username or password');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
            }
        }
    } catch (error) {
        showError(errorDiv, errorText, 'Network error. Please try again.');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
    }
}

async function handleFirstLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('firstLoginUsername').value.trim();
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    const errorDiv = document.getElementById('firstLoginError');
    const errorText = document.getElementById('firstLoginErrorText');
    const submitBtn = document.getElementById('firstLoginBtn');
    
    errorDiv.classList.add('d-none');
    
    if (!username || !newPassword || !confirmPassword) {
        showError(errorDiv, errorText, 'Please fill in all fields');
        return;
    }

    if (newPassword !== confirmPassword) {
        showError(errorDiv, errorText, 'Passwords do not match');
        return;
    }

    if (newPassword.length < 8) {
        showError(errorDiv, errorText, 'Password must be at least 8 characters');
        return;
    }

    if (!/[A-Z]/.test(newPassword)) {
        showError(errorDiv, errorText, 'Password must contain at least one uppercase letter');
        return;
    }

    if (!/[0-9]/.test(newPassword)) {
        showError(errorDiv, errorText, 'Password must contain at least one number');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating password...';

    try {
        const response = await fetch(API_ENDPOINTS.firstLogin, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, new_password: newPassword })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Password created successfully! Redirecting...', 'success', 1500);
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            showError(errorDiv, errorText, data.error || 'Failed to create password');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check"></i> Create Password';
        }
    } catch (error) {
        showError(errorDiv, errorText, 'Network error. Please try again.');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-check"></i> Create Password';
    }
}

async function handleForgotPassword(e) {
    e.preventDefault();
    
    const username = document.getElementById('forgotUsername').value.trim();
    const errorDiv = document.getElementById('forgotPasswordError');
    const errorText = document.getElementById('forgotPasswordErrorText');
    const successDiv = document.getElementById('forgotPasswordSuccess');
    const successText = document.getElementById('forgotPasswordSuccessText');
    const submitBtn = document.getElementById('forgotPasswordBtn');
    
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    if (!username) {
        showError(errorDiv, errorText, 'Please enter your username');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';

    try {
        const response = await fetch(API_ENDPOINTS.forgotPassword, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        const data = await response.json();

        if (response.ok) {
            tempPassword = data.temporary_password;
            successText.innerHTML = `
                Password reset successfully!<br>
                <strong>Your temporary password is: <code>${tempPassword}</code></strong><br>
                <small>Copy this password and use it to login. You will be prompted to change it.</small>
            `;
            successDiv.classList.remove('d-none');
            document.getElementById('forgotUsername').value = '';
            setTimeout(() => {
                showLogin();
                successDiv.classList.add('d-none');
            }, 8000);
        } else {
            showError(errorDiv, errorText, data.error || 'Password reset failed');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Reset Password';
        }
    } catch (error) {
        showError(errorDiv, errorText, 'Network error. Please try again.');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Reset Password';
    }
}

async function handlePasswordExpired(e) {
    e.preventDefault();
    
    const username = document.getElementById('expiredUsername').value.trim();
    const newPassword = document.getElementById('expiredNewPassword').value;
    const errorDiv = document.getElementById('passwordExpiredError');
    const errorText = document.getElementById('passwordExpiredErrorText');
    const submitBtn = document.getElementById('passwordExpiredBtn');
    
    errorDiv.classList.add('d-none');
    
    if (!username || !newPassword) {
        showError(errorDiv, errorText, 'Please fill in all fields');
        return;
    }

    if (newPassword.length < 8) {
        showError(errorDiv, errorText, 'Password must be at least 8 characters');
        return;
    }

    if (!/[A-Z]/.test(newPassword)) {
        showError(errorDiv, errorText, 'Password must contain at least one uppercase letter');
        return;
    }

    if (!/[0-9]/.test(newPassword)) {
        showError(errorDiv, errorText, 'Password must contain at least one number');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';

    try {
        const response = await fetch(API_ENDPOINTS.changePassword, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_password: newPassword, new_password: newPassword })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Password reset successfully! Please login.', 'success', 2000);
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            showError(errorDiv, errorText, data.error || 'Password reset failed');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sync"></i> Reset Password';
        }
    } catch (error) {
        showError(errorDiv, errorText, 'Network error. Please try again.');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-sync"></i> Reset Password';
    }
}

// ================================================================
// UI NAVIGATION
// ================================================================

function showLogin() {
    hideAllSections();
    const loginSection = document.getElementById('loginSection');
    if (loginSection) {
        loginSection.classList.add('active');
    }
}

function showForgotPassword() {
    hideAllSections();
    const forgotSection = document.getElementById('forgotPasswordSection');
    if (forgotSection) {
        forgotSection.classList.add('active');
    }
}

function showFirstLogin() {
    hideAllSections();
    const firstLoginSection = document.getElementById('firstLoginSection');
    if (firstLoginSection) {
        firstLoginSection.classList.add('active');
    }
    
    // Auto-fill username from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const username = urlParams.get('username');
    const usernameField = document.getElementById('firstLoginUsername');
    if (username && usernameField) {
        usernameField.value = username;
        usernameField.readOnly = true;
    }
}

function showPasswordExpired() {
    hideAllSections();
    const passwordExpiredSection = document.getElementById('passwordExpiredSection');
    if (passwordExpiredSection) {
        passwordExpiredSection.classList.add('active');
    }
}

function hideAllSections() {
    document.querySelectorAll('.auth-section').forEach(section => {
        section.classList.remove('active');
    });
}

// ================================================================
// UTILITY FUNCTIONS
// ================================================================

function showError(errorDiv, errorText, message) {
    if (errorDiv && errorText) {
        errorText.textContent = message;
        errorDiv.classList.remove('d-none');
    }
}

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast ' + type;
    
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <div style="padding:1rem;display:flex;align-items:center;gap:1rem;">
            <i class="fas ${icons[type] || icons.info}"></i>
            <span>${message}</span>
            <button type="button" onclick="document.getElementById('${toastId}').remove()" style="background:none;border:none;cursor:pointer;font-size:1.2rem;opacity:0.7;margin-left:auto;">&times;</button>
        </div>
    `;
    
    container.appendChild(toast);
    
    if (duration > 0) {
        setTimeout(() => {
            const el = document.getElementById(toastId);
            if (el) {
                el.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => el.remove(), 300);
            }
        }, duration);
    }
}