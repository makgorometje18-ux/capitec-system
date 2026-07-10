import sys
import threading
from types import FrameType
from typing import List, Tuple

calls: List[Tuple[str,str,int]] = []

FILTER_PATHS = [
    'src\\gui\\dashboard.py',
    'src\\core\\summary_reconciliation_engine.py',
    'src\\core\\summary_updater.py',
    'src\\core\\workbook_loader.py',
    'openpyxl',
]

def should_trace(filename: str) -> bool:
    if not filename:
        return False
    fn = filename.replace('/', '\\')
    for p in FILTER_PATHS:
        if p in fn:
            return True
    return False


def tracefunc(frame: FrameType, event: str, arg):
    if event != 'call':
        return tracefunc
    code = frame.f_code
    filename = code.co_filename
    if should_trace(filename):
        calls.append((filename, code.co_name, frame.f_lineno))
    return tracefunc


def run_update():
    # Import here so trace captures imports if needed
    from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
    from src.core.summary_updater import SummaryWorksheetUpdater

    engine = SummaryReconciliationEngine()
    analysis = engine.analyze('sample_files/sample_valid.xlsx')
    loader = engine.loader
    updater = SummaryWorksheetUpdater()
    result = updater.update_summary_worksheet(analysis, loader)
    print('UpdateResult:', result)


if __name__ == '__main__':
    sys.settrace(tracefunc)
    try:
        run_update()
    finally:
        sys.settrace(None)
        print('\nTraced call sequence:')
        for i, (fn, name, ln) in enumerate(calls, 1):
            print(f"{i}. {fn} :: {name}() @ line {ln}")
        # Print whether openpyxl save was called
        saved = any('save' in name and 'openpyxl' in fn for (fn,name,ln) in calls)
        print('\nWorkbook.save() called:', saved)
