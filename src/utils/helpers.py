"""
Helper Utilities Module - Common utility functions.
"""

from typing import List, Optional, Any
import re
from datetime import datetime


def clean_string(value: str) -> str:
    """
    Clean and trim a string value.
    
    Args:
        value: String to clean.
        
    Returns:
        Cleaned string with leading/trailing whitespace removed.
    """
    if not isinstance(value, str):
        return ""
    return value.strip()


def split_batch_numbers(batch_string: str) -> List[str]:
    """
    Split a pipe-delimited batch number string.
    
    Args:
        batch_string: Pipe-delimited batch numbers.
        
    Returns:
        List of individual batch numbers, cleaned and trimmed.
    """
    if not batch_string:
        return []
    
    batches = batch_string.split('|')
    return [clean_string(b) for b in batches if clean_string(b)]


def validate_bag_number(bag_number: Any) -> bool:
    """
    Validate bag number format.
    
    Accepts numeric bag numbers or text values with exactly one leading apostrophe.
    Rejects blank values, multiple apostrophes, and non-numeric content.
    
    Args:
        bag_number: Bag number to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if bag_number is None:
        return False

    if isinstance(bag_number, bool):
        return False

    if isinstance(bag_number, int):
        return bag_number >= 0

    if isinstance(bag_number, float):
        return bag_number.is_integer() and bag_number >= 0

    value = str(bag_number).strip()
    if value == "":
        return False

    # Accept pure numeric Bag_No values from Excel
    if re.fullmatch(r"[0-9]+", value):
        return True

    # Accept values with exactly one leading apostrophe and digits only
    if re.fullmatch(r"'[0-9]+", value):
        return True

    return False


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted duration string (e.g., "1m 23s").
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_datetime(dt: datetime) -> str:
    """
    Format datetime to standard string.
    
    Args:
        dt: Datetime object.
        
    Returns:
        Formatted datetime string.
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def is_valid_excel_file(file_path: str) -> bool:
    """
    Check if file is a valid Excel file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        True if file has Excel extension, False otherwise.
    """
    valid_extensions = ['.xlsx', '.xls', '.xlsm']
    return any(file_path.lower().endswith(ext) for ext in valid_extensions)
