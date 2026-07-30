/**
 * Capitec Agent System - Main JavaScript
 * Handles file upload, validation API calls, and UI updates
 */

(function() {
    'use strict';

    // DOM Elements
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    const validateBtn = document.getElementById('validateBtn');
    const resetBtn = document.getElementById('resetBtn');
    const resultSection = document.getElementById('resultSection');
    const resultStatus = document.getElementById('resultStatus');
    const resultMessage = document.getElementById('resultMessage');
    const loadingSection = document.getElementById('loadingSection');

    /**
     * Update file name display when a file is selected
     */
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                const file = this.files[0];
                fileName.textContent = file.name;
                validateBtn.disabled = false;
            } else {
                fileName.textContent = 'No file selected';
                validateBtn.disabled = true;
            }
        });
    }

    /**
     * Handle form submission - upload and validate file
     */
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Validate file selection
            if (!fileInput.files || fileInput.files.length === 0) {
                showResult('error', 'Please select a file to validate.');
                return;
            }

            const file = fileInput.files[0];

            // Validate file size (16MB max)
            const maxSize = 16 * 1024 * 1024; // 16MB
            if (file.size > maxSize) {
                showResult('error', 'File is too large. Maximum size is 16MB.');
                return;
            }

            // Show loading state
            showLoading(true);
            hideResult();

            // Prepare form data
            const formData = new FormData();
            formData.append('file', file);

            try {
                // Send file to validation API
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    body: formData
                });

                // Parse response
                const data = await response.json();

                // Hide loading state
                showLoading(false);

                // Display result
                if (response.ok) {
                    showResult(data.status, data.message);
                } else {
                    showResult('error', data.message || 'Validation failed. Please try again.');
                }

            } catch (error) {
                // Hide loading state
                showLoading(false);

                // Display error
                showResult('error', 'Network error. Please check your connection and try again.');
                console.error('Upload error:', error);
            }
        });
    }

    /**
     * Handle reset button - clear form and results
     */
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            // Reset form
            uploadForm.reset();
            fileName.textContent = 'No file selected';
            validateBtn.disabled = true;

            // Hide results and loading
            hideResult();
            showLoading(false);
        });
    }

    /**
     * Show validation result
     * @param {string} status - 'success' or 'error'
     * @param {string} message - Result message to display
     */
    function showResult(status, message) {
        if (!resultSection || !resultStatus || !resultMessage) return;

        resultSection.style.display = 'block';
        resultStatus.textContent = status === 'success' ? 'Success' : 'Error';
        resultStatus.className = 'result-status ' + (status === 'success' ? 'success' : 'error');
        resultMessage.textContent = message;

        // Scroll to result
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /**
     * Hide validation result
     */
    function hideResult() {
        if (resultSection) {
            resultSection.style.display = 'none';
        }
    }

    /**
     * Show or hide loading spinner
     * @param {boolean} show - Whether to show loading
     */
    function showLoading(show) {
        if (loadingSection) {
            loadingSection.style.display = show ? 'block' : 'none';
        }
        if (validateBtn) {
            validateBtn.disabled = show;
        }
    }

    /**
     * Payment Form Handling
     */
    const paymentForm = document.getElementById('paymentForm');
    const payBtn = document.getElementById('payBtn');
    const paymentMessage = document.getElementById('paymentMessage');
    const cardNumber = document.getElementById('cardNumber');
    const expiryDate = document.getElementById('expiryDate');
    const cvv = document.getElementById('cvv');

    /**
     * Auto-format card number with spaces every 4 digits
     */
    if (cardNumber) {
        cardNumber.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 16) value = value.slice(0, 16);
            this.value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
        });
    }

    /**
     * Auto-format expiry date with slash
     */
    if (expiryDate) {
        expiryDate.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 4) value = value.slice(0, 4);
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2);
            }
            this.value = value;
        });
    }

    /**
     * Allow only digits for CVV
     */
    if (cvv) {
        cvv.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '');
        });
    }

    /**
     * Handle payment form submission
     */
    if (paymentForm) {
        paymentForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Show processing state
            payBtn.disabled = true;
            payBtn.innerHTML = '<span class="spinner-small"></span> Processing payment...';
            paymentMessage.style.display = 'none';

            // Simulate 2-second processing delay
            await new Promise(resolve => setTimeout(resolve, 2000));

            try {
                // Call fake payment API
                const response = await fetch('/fake-payment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        card_number: cardNumber.value.replace(/\s/g, ''),
                        expiry: expiryDate.value,
                        cvv: cvv.value
                    })
                });

                const data = await response.json();

                // Show success message
                paymentMessage.textContent = 'Payment Successful';
                paymentMessage.className = 'payment-message payment-success';
                paymentMessage.style.display = 'block';

                // Reset button
                payBtn.disabled = false;
                payBtn.innerHTML = '<span class="btn-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1v8m0 0l-3-3m3 3l3-3M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg></span> Pay Now';

                // Reset form fields
                paymentForm.reset();

            } catch (error) {
                paymentMessage.textContent = 'Payment failed. Please try again.';
                paymentMessage.className = 'payment-message payment-error';
                paymentMessage.style.display = 'block';

                payBtn.disabled = false;
                payBtn.innerHTML = '<span class="btn-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1v8m0 0l-3-3m3 3l3-3M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg></span> Pay Now';

                console.error('Payment error:', error);
            }
        });
    }

})();
