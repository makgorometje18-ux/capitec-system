import sys
import os
sys.path.insert(0, os.path.abspath(''))
from types import FrameType
from typing import List, Tuple

TARGET_FILE = os.path.abspath('src/core/summary_reconciliation_engine.py')
# Line numbers of interest (from previous grep)
ASSIGN_LINES = {114, 115, 116}
BUILD_DIFF_START = 419
BUILD_DIFF_END = 456

captures: List[Tuple[int, dict]] = []
build_diffs: List[Tuple[int, dict]] = []

def tracefunc(frame: FrameType, event: str, arg):
    if event not in ('line', 'call', 'return'):
        return tracefunc
    code = frame.f_code
    filename = os.path.abspath(code.co_filename)
    lineno = frame.f_lineno
    if filename == TARGET_FILE:
        # capture when entering _build_summary_differences (call) or lines in range
        opname = code.co_name
        if event == 'call' and opname == '_build_summary_differences':
            print(f"ENTER {_short(opname)} at line {lineno}")
        if event == 'line':
            if lineno in ASSIGN_LINES:
                print(f"LINE {lineno} executed in {opname}")
                # copy locals
                locs = frame.f_locals.copy()
                captures.append((lineno, locs))
            if BUILD_DIFF_START <= lineno <= BUILD_DIFF_END:
                print(f"BUILD_DIFF LINE {lineno} in {opname}")
                build_diffs.append((lineno, frame.f_locals.copy()))
        if event == 'return' and opname == '_build_summary_differences':
            print(f"RETURN {_short(opname)} at line {lineno}, returning value type={type(arg)}")
    return tracefunc


def _short(name):
    return name

if __name__ == '__main__':
    prod_path = r'C:/Users/Obedbosh/OneDrive - myidemia/Documents/capitec/CAPITEC DAILY ORDERS REPORT JULY 2026.xlsx'
    if not os.path.exists(prod_path):
        print('Production workbook not found:', prod_path)
        sys.exit(2)

    sys.settrace(tracefunc)
    try:
        from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
        eng = SummaryReconciliationEngine()
        analysis = eng.analyze(prod_path)
    finally:
        sys.settrace(None)

    print('\n--- Captures at assign lines ---')
    for lineno, locs in captures:
        print(f'Line {lineno} locals:')
        for k,v in locs.items():
            try:
                print('  ',k,':',repr(v))
            except Exception:
                print('  ',k,': <unrepr>')

    print('\n--- Build diffs trace (subset) ---')
    for lineno, locs in build_diffs[:50]:
        print(f'Line {lineno} locals keys: {list(locs.keys())}')

    print('\n--- Final analysis fields ---')
    print('differences length =', len(getattr(analysis,'differences', [])))
    for d in getattr(analysis,'differences', []):
        print('  ', d.metric_name, d.existing_value, d.calculated_value, d.difference, d.status)
    print('has_changes =', analysis.has_changes)
    print('changes_count =', analysis.changes_count)
