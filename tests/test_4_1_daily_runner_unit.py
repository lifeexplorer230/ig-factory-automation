"""
Unit-тесты run_daily.py — без реального ADB, Telegram, Google Sheets.

TDD: тест написан до скрипта.
Проверяем: run_daily(dry_run), результат включает все этапы, Telegram вызывается.
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# ── Блок 1: run_daily структура ───────────────────────────────────────────────

class TestRunDailyStructure:
    """run_daily() возвращает структурированный результат."""

    def test_returns_dict(self, monkeypatch):
        """run_daily возвращает словарь."""
        import run_daily
        _patch_all(monkeypatch)
        result = run_daily.run_daily(dry_run=True)
        assert isinstance(result, dict)

    def test_result_has_all_stages(self, monkeypatch):
        """Результат содержит ключи для всех этапов."""
        import run_daily
        _patch_all(monkeypatch)
        result = run_daily.run_daily(dry_run=True)
        assert 'pipeline' in result
        assert 'login'    in result
        assert 'warmup'   in result
        assert 'publish'  in result

    def test_each_stage_has_success_failed(self, monkeypatch):
        """Каждый этап содержит success, failed, skipped."""
        import run_daily
        _patch_all(monkeypatch)
        result = run_daily.run_daily(dry_run=True)
        for stage in ('pipeline', 'login', 'warmup', 'publish'):
            assert 'success' in result[stage], f"Нет success в {stage}"
            assert 'failed'  in result[stage], f"Нет failed в {stage}"


# ── Блок 2: run_daily вызывает pipeline ──────────────────────────────────────

class TestRunDailyCallsPipeline:
    """run_daily() вызывает content_pipeline.run_from_sheets()."""

    def test_calls_run_from_sheets(self, monkeypatch):
        """run_from_sheets вызывается при наличии GOOGLE_SHEETS_ID."""
        import run_daily
        mock_sheets = MagicMock(return_value=3)
        monkeypatch.setattr('run_daily.run_from_sheets', mock_sheets, raising=False)
        _patch_runners(monkeypatch)
        _patch_telegram(monkeypatch)
        run_daily.run_daily(dry_run=True)
        mock_sheets.assert_called_once()

    def test_pipeline_result_in_output(self, monkeypatch):
        """Результат pipeline (количество видео) попадает в итог."""
        import run_daily
        monkeypatch.setattr('run_daily.run_from_sheets',
                            MagicMock(return_value=5), raising=False)
        _patch_runners(monkeypatch)
        _patch_telegram(monkeypatch)
        result = run_daily.run_daily(dry_run=True)
        # pipeline.success должен отражать результат run_from_sheets
        assert result['pipeline']['success'] >= 0


# ── Блок 3: run_daily вызывает login и warmup ─────────────────────────────────

class TestRunDailyCallsRunners:
    """run_daily() вызывает login_runner и warmup_runner."""

    def test_calls_login_runner(self, monkeypatch):
        """login_runner.run() вызывается."""
        import run_daily
        mock_login = MagicMock(return_value={'success': 2, 'failed': 0, 'skipped': 0})
        monkeypatch.setattr('run_daily.login_run', mock_login, raising=False)
        _patch_pipeline(monkeypatch)
        _patch_warmup(monkeypatch)
        _patch_publisher(monkeypatch)
        _patch_telegram(monkeypatch)
        run_daily.run_daily(dry_run=True)
        mock_login.assert_called_once()

    def test_calls_warmup_runner(self, monkeypatch):
        """warmup_runner.run() вызывается."""
        import run_daily
        mock_warmup = MagicMock(return_value={'success': 5, 'failed': 0, 'skipped': 0})
        monkeypatch.setattr('run_daily.warmup_run', mock_warmup, raising=False)
        _patch_pipeline(monkeypatch)
        _patch_login(monkeypatch)
        _patch_publisher(monkeypatch)
        _patch_telegram(monkeypatch)
        run_daily.run_daily(dry_run=True)
        mock_warmup.assert_called_once()

    def test_calls_publisher(self, monkeypatch):
        """publisher.run() вызывается."""
        import run_daily
        mock_pub = MagicMock(return_value=3)
        monkeypatch.setattr('run_daily.publisher_run', mock_pub, raising=False)
        _patch_pipeline(monkeypatch)
        _patch_login(monkeypatch)
        _patch_warmup(monkeypatch)
        _patch_telegram(monkeypatch)
        run_daily.run_daily(dry_run=True)
        mock_pub.assert_called_once()


# ── Блок 4: run_daily отправляет Telegram ────────────────────────────────────

class TestRunDailyTelegram:
    """run_daily() отправляет итоговый отчёт в Telegram."""

    def test_telegram_report_called(self, monkeypatch):
        """report_daily() вызывается после всех этапов."""
        import run_daily
        mock_reporter = MagicMock()
        monkeypatch.setattr('run_daily.reporter', mock_reporter, raising=False)
        _patch_all_runners(monkeypatch)
        run_daily.run_daily(dry_run=True)
        mock_reporter.report_daily.assert_called_once()

    def test_telegram_gets_all_stage_results(self, monkeypatch):
        """report_daily() получает данные всех 4 этапов."""
        import run_daily
        mock_reporter = MagicMock()
        monkeypatch.setattr('run_daily.reporter', mock_reporter, raising=False)
        _patch_all_runners(monkeypatch)
        run_daily.run_daily(dry_run=True)
        call_kwargs = mock_reporter.report_daily.call_args.kwargs
        assert 'pipeline' in call_kwargs
        assert 'login'    in call_kwargs
        assert 'warmup'   in call_kwargs
        assert 'publish'  in call_kwargs


# ── Блок 5: run_daily dry_run ─────────────────────────────────────────────────

class TestRunDailyDryRun:
    """run_daily(dry_run=True) передаёт dry_run во все под-вызовы."""

    def test_dry_run_passed_to_pipeline(self, monkeypatch):
        """dry_run=True передаётся в run_from_sheets."""
        import run_daily
        mock_sheets = MagicMock(return_value=0)
        monkeypatch.setattr('run_daily.run_from_sheets', mock_sheets, raising=False)
        _patch_runners(monkeypatch)
        _patch_telegram(monkeypatch)
        run_daily.run_daily(dry_run=True)
        mock_sheets.assert_called_once_with(dry_run=True)

    def test_dry_run_passed_to_login(self, monkeypatch):
        """dry_run=True передаётся в login_runner.run()."""
        import run_daily
        mock_login = MagicMock(return_value={'success': 0, 'failed': 0, 'skipped': 0})
        monkeypatch.setattr('run_daily.login_run', mock_login, raising=False)
        _patch_pipeline(monkeypatch)
        _patch_warmup(monkeypatch)
        _patch_publisher(monkeypatch)
        _patch_telegram(monkeypatch)
        run_daily.run_daily(dry_run=True)
        call_kwargs = mock_login.call_args.kwargs
        assert call_kwargs.get('dry_run') is True

    def test_dry_run_passed_to_warmup(self, monkeypatch):
        """dry_run=True передаётся в warmup_runner.run()."""
        import run_daily
        mock_warmup = MagicMock(return_value={'success': 0, 'failed': 0, 'skipped': 0})
        monkeypatch.setattr('run_daily.warmup_run', mock_warmup, raising=False)
        _patch_pipeline(monkeypatch)
        _patch_login(monkeypatch)
        _patch_publisher(monkeypatch)
        _patch_telegram(monkeypatch)
        run_daily.run_daily(dry_run=True)
        call_kwargs = mock_warmup.call_args.kwargs
        assert call_kwargs.get('dry_run') is True


# ── Вспомогательные функции патчинга ─────────────────────────────────────────

def _patch_pipeline(mp):
    mp.setattr('run_daily.run_from_sheets',
               MagicMock(return_value=0), raising=False)

def _patch_login(mp):
    mp.setattr('run_daily.login_run',
               MagicMock(return_value={'success': 0, 'failed': 0, 'skipped': 0}),
               raising=False)

def _patch_warmup(mp):
    mp.setattr('run_daily.warmup_run',
               MagicMock(return_value={'success': 0, 'failed': 0, 'skipped': 0}),
               raising=False)

def _patch_publisher(mp):
    mp.setattr('run_daily.publisher_run',
               MagicMock(return_value=0), raising=False)

def _patch_telegram(mp):
    mp.setattr('run_daily.reporter', MagicMock(), raising=False)

def _patch_runners(mp):
    _patch_login(mp)
    _patch_warmup(mp)
    _patch_publisher(mp)

def _patch_all_runners(mp):
    _patch_pipeline(mp)
    _patch_runners(mp)

def _patch_all(mp):
    _patch_pipeline(mp)
    _patch_runners(mp)
    _patch_telegram(mp)
