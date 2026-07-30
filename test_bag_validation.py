#!/usr/bin/env python3
"""
Test script to verify multiple bag number validation.
"""

from src.utils.helpers import validate_bag_number, split_batch_numbers

def test_validate_bag_number():
    """Test individual bag number validation."""
    print("Testing individual bag number validation...")
    
    # Valid cases
    assert validate_bag_number("2301") == True, "Numeric bag should be valid"
    assert validate_bag_number("'2303") == True, "Apostrophe prefixed bag should be valid"
    assert validate_bag_number(2301) == True, "Integer bag should be valid"
    assert validate_bag_number(0) == True, "Zero should be valid"
    
    # Invalid cases
    assert validate_bag_number("") == False, "Empty string should be invalid"
    assert validate_bag_number(None) == False, "None should be invalid"
    assert validate_bag_number("'2303'") == False, "Double apostrophe should be invalid"
    assert validate_bag_number("AB123") == False, "Non-numeric should be invalid"
    assert validate_bag_number("'AB123") == False, "Apostrophe with letters should be invalid"
    
    print("✓ Individual bag number validation tests passed!")


def test_split_batch_numbers():
    """Test splitting bag numbers by pipe delimiter."""
    print("\nTesting split_batch_numbers...")
    
    # Multiple bag numbers
    result = split_batch_numbers("2301 | 2303")
    assert result == ["2301", "2303"], f"Expected ['2301', '2303'], got {result}"
    
    # Single bag number
    result = split_batch_numbers("2301")
    assert result == ["2301"], f"Expected ['2301'], got {result}"
    
    # With spaces
    result = split_batch_numbers(" 2301 | 2303 ")
    assert result == ["2301", "2303"], f"Expected ['2301', '2303'], got {result}"
    
    # Empty parts should be filtered
    result = split_batch_numbers("2301 || 2303")
    assert result == ["2301", "2303"], f"Expected ['2301', '2303'], got {result}"
    
    # Apostrophe prefixed
    result = split_batch_numbers("'2301 | '2303")
    assert result == ["'2301", "'2303"], f"Expected [\"'2301\", \"'2303\"], got {result}"
    
    print("✓ Split batch numbers tests passed!")


def test_multiple_bag_validation():
    """Test validation of multiple bag numbers in one field."""
    print("\nTesting multiple bag number validation...")
    
    # Valid multiple bag numbers
    bag_string = "2301 | 2303"
    bag_numbers = split_batch_numbers(bag_string)
    invalid_bags = [bag for bag in bag_numbers if not validate_bag_number(bag)]
    assert invalid_bags == [], f"Expected no invalid bags, got {invalid_bags}"
    
    # Mixed valid/invalid
    bag_string = "2301 | ABC"
    bag_numbers = split_batch_numbers(bag_string)
    invalid_bags = [bag for bag in bag_numbers if not validate_bag_number(bag)]
    assert invalid_bags == ["ABC"], f"Expected ['ABC'], got {invalid_bags}"
    
    # All invalid
    bag_string = "ABC | XYZ"
    bag_numbers = split_batch_numbers(bag_string)
    invalid_bags = [bag for bag in bag_numbers if not validate_bag_number(bag)]
    assert invalid_bags == ["ABC", "XYZ"], f"Expected ['ABC', 'XYZ'], got {invalid_bags}"
    
    print("✓ Multiple bag number validation tests passed!")


if __name__ == "__main__":
    test_validate_bag_number()
    test_split_batch_numbers()
    test_multiple_bag_validation()
    print("\n" + "="*50)
    print("ALL TESTS PASSED!")
    print("="*50)