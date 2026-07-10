import sys
sys.path.insert(0, 'c:/Users/Obedbosh/Music/OBED BOSHIELO/Capitec-Reconciliation-System')
from types import FrameType
calls=[]

FILTERS = ['src\\gui\\dashboard.py','src\\core\\summary_reconciliation_engine.py','src\\core\\summary_updater.py','src\\core\\workbook_loader.py','openpyxl']

def should_trace(filename):
    if not filename:
        return False
    fn = filename.replace('/', '\\')
    return any(p in fn for p in FILTERS)


def tracefunc(frame, event, arg):
    if event != 'call':
        return tracefunc
    code = frame.f_code
    filename = code.co_filename
    if should_trace(filename):
        calls.append((filename, code.co_name, frame.f_lineno))
    return tracefunc


if __name__ == '__main__':
    sys.settrace(tracefunc)
    try:
        from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
        from src.core.summary_updater import SummaryWorksheetUpdater
        engine = SummaryReconciliationEngine()
        analysis = engine.analyze('sample_files/sample_valid.xlsx')
        loader = engine.loader
        updater = SummaryWorksheetUpdater()
        result = updater.update_summary_worksheet(analysis, loader)
        print('UpdateResult:', result)
    finally:
        sys.settrace(None)
        print('\nTraced call sequence:')
        for i, (fn, name, ln) in enumerate(calls, 1):
            print(f"{i}. {fn} :: {name}() @ line {ln}")
        saved = any('save' in name and 'openpyxl' in fn for (fn, name, ln) in calls)
        print('\nWorkbook.save() called:', saved)
