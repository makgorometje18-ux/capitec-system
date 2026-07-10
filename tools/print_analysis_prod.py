import sys, os
sys.path.insert(0, os.path.abspath(''))
prod_path = r'C:/Users/Obedbosh/OneDrive - myidemia/Documents/capitec/CAPITEC DAILY ORDERS REPORT JULY 2026.xlsx'
if not os.path.exists(prod_path):
    print('Production workbook not found:', prod_path)
    sys.exit(2)

from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
eng = SummaryReconciliationEngine()
analysis = eng.analyze(prod_path)
print('Summary sheet:', analysis.summary_worksheet_name)
print('Differences count:', len(analysis.differences))
for d in analysis.differences:
    print(d.metric_name, 'existing=', d.existing_value, 'calc=', d.calculated_value, 'diff=', d.difference, 'status=', d.status)
print('has_changes=', analysis.has_changes)
print('changes_count=', analysis.changes_count)
