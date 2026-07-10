import openpyxl
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
from src.gui.dashboard import build_summary_update_preview_text

wb = openpyxl.Workbook()
wb.remove(wb.active)
ws = wb.create_sheet('CAPITEC SUMMARY FILE REPORT')
ws.append(['Files received','Total quantity received','Current Quantity In Stock','Current Quantity Dispatched','Comment'])
ws.append(['P_001_BANK',1000,500,200,'Bank card file'])
ws.append(['C-Connect batch 1',800,300,100,'SIM file batch'])

path = Path(tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False).name)
wb.save(path)
engine = SummaryReconciliationEngine()
analysis = engine.analyze(str(path))
print('summary_rows count', len(analysis.summary_rows))
for row in analysis.summary_rows:
    print('row', row.row_number, row.item_name, row.quantity_in_stock, row.quantity_dispatched, row.new_quantity_in_stock, row.new_quantity_dispatched, row.changes_required)
print('---PREVIEW---')
print(build_summary_update_preview_text(analysis))
