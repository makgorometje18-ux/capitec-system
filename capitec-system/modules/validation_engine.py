"""
Validation Engine Module
Handles file validation logic for the Capitec Agent System.
"""

import os
import json
from datetime import datetime


def validate_file(file_path):
    """
    Validate an uploaded file.

    Performs basic validation checks:
    - File exists at the given path
    - File is not empty
    - File has a valid extension

    Args:
        file_path (str): Absolute path to the uploaded file

    Returns:
        dict: JSON-serializable validation result with status and message
    """
    result = {
        'status': 'error',
        'message': 'Validation failed',
        'timestamp': datetime.utcnow().isoformat(),
        'filename': os.path.basename(file_path) if file_path else None
    }

    try:
        # Check if file exists
        if not file_path:
            result['message'] = 'No file path provided'
            return result

        if not os.path.exists(file_path):
            result['message'] = f'File not found: {file_path}'
            return result

        # Check if file is empty
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            result['message'] = 'File is empty'
            return result

        # Check file extension
        allowed_extensions = {'.xlsx', '.xls', '.csv', '.pdf', '.doc', '.docx'}
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in allowed_extensions:
            result['message'] = f'File type "{ext}" is not supported. Allowed types: {", ".join(allowed_extensions)}'
            return result

        # Validation passed
        result['status'] = 'success'
        result['message'] = 'Validation completed'
        result['file_size'] = file_size
        result['file_extension'] = ext.lower()

        return result

    except PermissionError:
        result['message'] = f'Permission denied: Unable to access file {file_path}'
        return result

    except Exception as e:
        result['message'] = f'Validation error: {str(e)}'
        return result


def validate_file_batch(file_paths):
    """
    Validate multiple files in batch.

    Args:
        file_paths (list): List of file paths to validate

    Returns:
        dict: Batch validation results
    """
    results = []
    for file_path in file_paths:
        result = validate_file(file_path)
        results.append(result)

    return {
        'status': 'success' if all(r['status'] == 'success' for r in results) else 'partial',
        'total': len(results),
        'success_count': sum(1 for r in results if r['status'] == 'success'),
        'error_count': sum(1 for r in results if r['status'] == 'error'),
        'results': results
    }