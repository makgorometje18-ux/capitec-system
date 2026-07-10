import sys, os
sys.path.insert(0, os.path.abspath(''))
prod_path = r'C:/Users/Obedbosh/OneDrive - myidemia/Documents/capitec/CAPITEC DAILY ORDERS REPORT JULY 2026.xlsx'
if not os.path.exists(prod_path):
    print('Production workbook not found:', prod_path)
    sys.exit(2)

from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
eng = SummaryReconciliationEngine()
analysis = eng.analyze(prod_path)

print('--- existing_summary_values (repr) ---')
for k,v in analysis.existing_summary_values.items():
    print('KEY:', repr(k))
    print('VALUE:', repr(v))
    print('-----')

print('\n--- summary of keys ---')
print(list(analysis.existing_summary_values.keys()))

print('\n--- calculated_summary_values ---')
print(analysis.calculated_summary_values)
