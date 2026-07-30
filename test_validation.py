import requests
import os

# Test the running server
base_url = 'http://localhost:5000'
sample_file = 'sample_files/sample_valid.xlsx'

print('Testing validation system...')
print('Sample file exists:', os.path.exists(sample_file))

if os.path.exists(sample_file):
    print('Testing with', sample_file)
    print('File size:', os.path.getsize(sample_file), 'bytes')
    
    # Test file upload
    with open(sample_file, 'rb') as f:
        files = {'file': f}
        response = requests.post(f'{base_url}/api/validate/upload', files=files)
    
    print('Status:', response.status_code)
    if response.status_code == 200:
        result = response.json()
        print('✓ Validation completed!')
        print('Passed:', result.get('passed'))
        print('Errors:', result.get('error_count'))
        print('Warnings:', result.get('warning_count'))
        print('Duration:', result.get('duration_seconds'), 's')
    else:
        print('✗ Request failed')
        print('Response:', response.text)
else:
    print('ERROR: Sample file not found at', sample_file)