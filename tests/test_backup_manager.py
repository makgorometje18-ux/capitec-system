import openpyxl
from pathlib import Path

from src.core.backup_manager import BackupManager
from src.models.models import Workbook


def test_create_backup_creates_file(tmp_path):
    workbook_path = tmp_path / "sample_workbook.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DAILY OUTPUT FILE 03-07-2026"
    wb.save(workbook_path)

    workbook_model = Workbook(
        file_path=str(workbook_path),
        file_name=workbook_path.name,
        file_size=workbook_path.stat().st_size,
        worksheets=[ws.title],
        is_valid=True,
    )

    backup_dir = tmp_path / "backups"
    manager = BackupManager(backup_folder=str(backup_dir))

    success = manager.create_backup(workbook_model)

    assert success is True
    backups = list(backup_dir.glob("*.bak"))
    assert len(backups) == 1
    assert backups[0].stem.startswith(workbook_path.stem)
    assert backups[0].suffix == ".bak"
    assert backups[0].exists()
