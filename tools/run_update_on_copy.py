import shutil
import tempfile
import os
import sys
sys.path.insert(0, os.path.abspath(''))
from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
from src.core.summary_updater import SummaryWorksheetUpdater

orig = 'sample_files/sample_valid.xlsx'
if not os.path.exists(orig):
    print('Sample file not found:', orig)
    sys.exit(2)

fd, temp_path = tempfile.mkstemp(suffix='.xlsx', prefix='sample_valid_copy_')
os.close(fd)
shutil.copyfile(orig, temp_path)
print('Copied to', temp_path)

engine = SummaryReconciliationEngine()
analysis = engine.analyze(temp_path)
loader = engine.loader
updater = SummaryWorksheetUpdater()
result = updater.update_summary_worksheet(analysis, loader)
print('UpdateResult.success=', result.success)
print('Updated fields:', result.updated_fields)
print('Skipped fields:', result.skipped_fields)
print('Failed fields:', result.failed_fields)
print('Saved path (loader.current_file_path)=', getattr(loader, 'current_file_path', None))

# cleanup
try:
    os.remove(temp_path)
    print('Removed temp copy')
except Exception as e:
    print('Failed to remove temp copy:', e)
