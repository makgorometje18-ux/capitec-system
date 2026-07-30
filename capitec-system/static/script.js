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

})();