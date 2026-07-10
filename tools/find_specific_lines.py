patterns = ['def detect_capitec_summary_sheet', 'def detect_daily_output_sheet', 'def load_workbook', 'def get_worksheet', 'def update_summary_worksheet', 'workbook.save(']

import pathlib

for p in patterns:
    found = False
    for i, line in enumerate(open('src/core/workbook_loader.py','r',encoding='utf-8')):
        if p in line:
            print(p, 'in workbook_loader.py at', i+1)
            found = True
            break
    if not found:
        for i, line in enumerate(open('src/core/summary_updater.py','r',encoding='utf-8')):
            if p in line:
                print(p, 'in summary_updater.py at', i+1)
                found = True
                break
    if not found:
        for i, line in enumerate(open('src/gui/dashboard.py','r',encoding='utf-8')):
            if p in line:
                print(p, 'in dashboard.py at', i+1)
                found = True
                break
    if not found:
        print(p, 'not found')
