"""T-P3-16: main.py の ENABLE_SCHEDULER 分岐"""
from unittest.mock import MagicMock

import pytest

import main


@pytest.fixture
def mocks(monkeypatch):
    m = {
        "init_db": MagicMock(),
        "init_user": MagicMock(),
        "check_and_run_batch": MagicMock(),
        "scheduler": MagicMock(),
    }
    for name, mock in m.items():
        monkeypatch.setattr(main, name, mock)
    return m


def test_tc_16_1_unset_enables_scheduler(monkeypatch, mocks):
    monkeypatch.delenv("ENABLE_SCHEDULER", raising=False)
    main.startup_event()
    mocks["scheduler"].start.assert_called_once()
    mocks["check_and_run_batch"].assert_called_once()


def test_tc_16_2_false_disables_scheduler(monkeypatch, mocks):
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    main.startup_event()
    mocks["scheduler"].start.assert_not_called()
    mocks["check_and_run_batch"].assert_not_called()


@pytest.mark.parametrize("value", ["False", "FALSE"])
def test_tc_16_3_false_case_insensitive(monkeypatch, mocks, value):
    monkeypatch.setenv("ENABLE_SCHEDULER", value)
    main.startup_event()
    mocks["scheduler"].start.assert_not_called()
    mocks["check_and_run_batch"].assert_not_called()


@pytest.mark.parametrize("value", ["true", "1", ""])
def test_tc_16_4_other_values_enable_scheduler(monkeypatch, mocks, value):
    monkeypatch.setenv("ENABLE_SCHEDULER", value)
    main.startup_event()
    mocks["scheduler"].start.assert_called_once()
    mocks["check_and_run_batch"].assert_called_once()


def test_tc_16_5_false_startup_then_shutdown_no_error(monkeypatch, mocks):
    from apscheduler.schedulers import SchedulerNotRunningError

    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    # 未起動のスケジューラを shutdown した場合と同じ例外を仕込み、呼ばれないことを確認する
    mocks["scheduler"].shutdown.side_effect = SchedulerNotRunningError()
    main.startup_event()
    main.shutdown_event()
    mocks["scheduler"].shutdown.assert_not_called()


def test_tc_16_6_false_still_initializes_db_and_user(monkeypatch, mocks):
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    main.startup_event()
    mocks["init_db"].assert_called_once()
    mocks["init_user"].assert_called_once()
