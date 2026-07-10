import pytest

from src.core.reconciliation_engine import BatchResult, ReconciliationAnalysis, reconcile
from src.models.models import CommercialBatch


class DummyDailyRecord:
    def __init__(self, batch_number, card_type, branch, waybill, bag):
        self.batch_number = batch_number
        self.card_type = card_type
        self.branch = branch
        self.waybill = waybill
        self.bag = bag


def test_reconcile_detects_matched_batch():
    commercial_batches = [CommercialBatch('BATCH001', 'SIM', 100, None, 2)]
    daily_records = [DummyDailyRecord('BATCH001', 'SIM', 'BR001', 'WB001', "'00001")]

    result = reconcile(commercial_batches, daily_records)

    assert len(result.matched) == 1
    assert result.matched[0].batch_number == 'BATCH001'
    assert result.matched[0].status == 'MATCHED'
    assert result.matched[0].issues == []
    assert result.missing == []
    assert result.extra == []
    assert result.duplicates == []
    assert result.mismatches == []


def test_reconcile_detects_duplicate_daily_batches():
    commercial_batches = [CommercialBatch('BATCH001', 'SIM', 100, None, 2)]
    daily_records = [
        DummyDailyRecord('BATCH001', 'SIM', 'BR001', 'WB001', "'00001"),
        DummyDailyRecord('BATCH001', 'SIM', 'BR001', 'WB001', "'00001"),
    ]

    result = reconcile(commercial_batches, daily_records)

    assert len(result.duplicates) == 1
    assert result.duplicates[0].status == 'DUPLICATE'
    assert 'duplicate daily output entries' in result.duplicates[0].issues
    assert result.matched == []
    assert result.extra == []
    assert result.missing == []
    assert result.mismatches == []


def test_reconcile_detects_missing_batch():
    commercial_batches = [CommercialBatch('BATCH001', 'SIM', 100, None, 2)]
    daily_records = []

    result = reconcile(commercial_batches, daily_records)

    assert len(result.missing) == 1
    assert result.missing[0].batch_number == 'BATCH001'
    assert result.missing[0].status == 'MISSING'
    assert result.extra == []
    assert result.duplicates == []
    assert result.mismatches == []
    assert result.matched == []


def test_reconcile_detects_extra_batch():
    commercial_batches = []
    daily_records = [DummyDailyRecord('BATCH001', 'SIM', 'BR001', 'WB001', "'00001")]

    result = reconcile(commercial_batches, daily_records)

    assert len(result.extra) == 1
    assert result.extra[0].batch_number == 'BATCH001'
    assert result.extra[0].status == 'EXTRA'
    assert result.matched == []
    assert result.missing == []
    assert result.duplicates == []
    assert result.mismatches == []


def test_reconcile_detects_field_mismatch_and_quantity_issue():
    commercial_batches = [CommercialBatch('BATCH001', 'SIM', 200, None, 2)]
    daily_records = [DummyDailyRecord('BATCH001', 'SIM', 'BR001', 'WB002', "'00001")]

    result = reconcile(commercial_batches, daily_records)

    assert len(result.mismatches) == 1
    mismatch = result.mismatches[0]
    assert mismatch.batch_number == 'BATCH001'
    assert mismatch.status == 'MISMATCH'
    assert any('card_type mismatch' in issue for issue in mismatch.issues) or any('quantity mismatch' in issue for issue in mismatch.issues)
    assert result.extra == []
    assert result.duplicates == []
    assert result.missing == []
    assert result.matched == []
