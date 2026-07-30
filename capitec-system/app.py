from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import sys

# Add modules and utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from modules.validation_engine import validate_file
from utils.file_handler import save_uploaded_file

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf', 'doc', 'docx'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def main_dashboard():
    """Main dashboard with department cards"""
    return render_template('main_dashboard.html')


@app.route('/service-center')
def service_center():
    """Service center dashboard with file upload and validation"""
    return render_template('service_center.html')


@app.route('/api/validate', methods=['POST'])
def api_validate():
    """API endpoint to validate uploaded files"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file provided'
            }), 400

        file = request.files['file']

        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400

        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save uploaded file
        try:
            file_path = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to save file: {str(e)}'
            }), 500

        # Run validation
        try:
            result = validate_file(file_path)
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Validation failed: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500


@app.route('/fake-payment', methods=['POST'])
def fake_payment():
    """Fake payment endpoint for testing card payments"""
    return jsonify({
        'status': 'success',
        'message': 'Payment processed'
    }), 200


@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'status': 'error',
        'message': 'File is too large. Maximum size is 16MB.'
    }), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)