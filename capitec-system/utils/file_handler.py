"""
File Handler Utility Module
Manages file uploads, storage, and retrieval for the Capitec Agent System.
"""

import os
import uuid
from datetime import datetime


def save_uploaded_file(file_storage, upload_dir):
    """
    Save an uploaded file to the specified upload directory.

    Generates a unique filename to prevent collisions and
    ensures the file is saved securely.

    Args:
        file_storage (FileStorage): The uploaded file object from Flask
        upload_dir (str): Directory path where the file should be saved

    Returns:
        str: Absolute path to the saved file

    Raises:
        ValueError: If file_storage is invalid or upload_dir doesn't exist
        IOError: If file cannot be written to disk
    """
    if not file_storage:
        raise ValueError('No file storage object provided')

    if not file_storage.filename:
        raise ValueError('File has no filename')

    # Ensure upload directory exists
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename to prevent collisions
    original_filename = file_storage.filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]

    # Preserve original extension
    _, ext = os.path.splitext(original_filename)
    safe_filename = f"{timestamp}_{unique_id}_{original_filename}"

    # Sanitize filename - remove any path separators
    safe_filename = safe_filename.replace('/', '_').replace('\\', '_')

    # Build full path
    file_path = os.path.join(upload_dir, safe_filename)

    try:
        # Save the file
        file_storage.save(file_path)

        # Verify file was saved
        if not os.path.exists(file_path):
            raise IOError(f'File was not saved to {file_path}')

        return file_path

    except PermissionError:
        raise IOError(f'Permission denied: Cannot write to {upload_dir}')

    except Exception as e:
        raise IOError(f'Failed to save file: {str(e)}')


def get_file_info(file_path):
    """
    Get metadata information about a stored file.

    Args:
        file_path (str): Absolute path to the file

    Returns:
        dict: File metadata including name, size, and modification time
    """
    if not os.path.exists(file_path):
        return None

    stat = os.stat(file_path)
    return {
        'filename': os.path.basename(file_path),
        'size': stat.st_size,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat()
    }


def delete_file(file_path):
    """
    Safely delete a stored file.

    Args:
        file_path (str): Absolute path to the file to delete

    Returns:
        bool: True if file was deleted, False if file doesn't exist
    """
    if not os.path.exists(file_path):
        return False

    os.remove(file_path)
    return True


def cleanup_old_files(upload_dir, max_age_hours=24):
    """
    Remove files older than the specified age from the upload directory.

    Args:
        upload_dir (str): Directory to clean up
        max_age_hours (int): Maximum age of files in hours before deletion

    Returns:
        int: Number of files deleted
    """
    if not os.path.exists(upload_dir):
        return 0

    now = datetime.now()
    deleted_count = 0

    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            file_age = now - datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_age.total_seconds() > max_age_hours * 3600:
                os.remove(file_path)
                deleted_count += 1

    return deleted_count