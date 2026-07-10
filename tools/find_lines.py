import re

def find_lines(path, patterns):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    results = {}
    for i, line in enumerate(lines, start=1):
        for pat in patterns:
            if pat in line:
                results.setdefault(pat, []).append(i)
    return results

files_and_patterns = {
    'src/gui/dashboard.py': ['def _on_update_summary', 'def _on_start_validation', 'def _run_integration_test'],
    'src/core/summary_reconciliation_engine.py': ['def analyze', 'def _read_summary_rows', 'def _apply_row_calculations'],
    'src/core/summary_updater.py': ['def update_summary_worksheet', 'workbook.save('],
    'src/core/workbook_loader.py': ['def load_workbook', 'def get_worksheet', 'current_file_path']
}

for path, patterns in files_and_patterns.items():
    print('\nFile:', path)
    res = find_lines(path, patterns)
    for pat in patterns:
        lines = res.get(pat)
        if lines:
            for ln in lines:
                print(f"  Pattern '{pat}' found at line {ln}")
        else:
            print(f"  Pattern '{pat}' not found")
