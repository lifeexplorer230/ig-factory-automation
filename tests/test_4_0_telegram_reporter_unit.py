"""
Unit-тесты telegram_reporter.py — без реального Telegram API.

TDD: тест написан до скрипта.
Проверяем: format_report, send_message (mock), build_pipeline_report, build_daily_summary.
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# ── Блок 1: format_report ────────────────────────────────────────────────────

class TestFormatReport:
    """format_report() форматирует статистику в читаемый текст."""

    def test_pipeline_report_has_counts(self):
        """Отчёт pipeline содержит количество видео."""
        import telegram_reporter as tr
        report = tr.format_report('pipeline', {
            'success': 3,
            'failed':  1,
            'skipped': 0,
        })
        assert '3' in report
        assert '1' in report

    def test_login_report_shows_success(self):
        """Отчёт логина содержит результат."""
        import telegram_reporter as tr
        report = tr.format_report('login', {
            'success': 5,
            'failed':  0,
            'skipped': 2,
        })
        assert '5' in report

    def test_warmup_report_shows_result(self):
        """Отчёт прогрева содержит данные."""
        import telegram_reporter as tr
        report = tr.format_report('warmup', {
            'success': 8,
            'failed':  2,
            'skipped': 0,
        })
        assert '8' in report

    def test_publish_report_shows_result(self):
        """Отчёт публикации содержит данные."""
        import telegram_reporter as tr
        report = tr.format_report('publish', {
            'success': 10,
            'failed':  0,
            'skipped': 0,
        })
        assert '10' in report

    def test_report_is_string(self):
        """format_report возвращает строку."""
        import telegram_reporter as tr
        result = tr.format_report('login', {'success': 1, 'failed': 0, 'skipped': 0})
        assert isinstance(result, str)

    def test_report_not_empty(self):
        """format_report не возвращает пустую строку."""
        import telegram_reporter as tr
        result = tr.format_report('publish', {'success': 0, 'failed': 0, 'skipped': 0})
        assert len(result) > 0


# ── Блок 2: build_daily_summary ──────────────────────────────────────────────

class TestBuildDailySummary:
    """build_daily_summary() собирает итоговый отчёт дня."""

    def test_summary_contains_all_sections(self):
        """Сводка содержит данные по всем этапам."""
        import telegram_reporter as tr
        summary = tr.build_daily_summary(
            pipeline={'success': 5, 'failed': 0, 'skipped': 0},
            login={'success': 2, 'failed': 0, 'skipped': 8},
            warmup={'success': 1, 'failed': 0, 'skipped': 9},
            publish={'success': 5, 'failed': 0, 'skipped': 0},
        )
        assert isinstance(summary, str)
        assert len(summary) > 10

    def test_summary_shows_failures_prominently(self):
        """При ошибках — они явно отражены в сводке."""
        import telegram_reporter as tr
        summary = tr.build_daily_summary(
            pipeline={'success': 3, 'failed': 2, 'skipped': 0},
            login={'success': 0, 'failed': 1, 'skipped': 0},
            warmup={'success': 0, 'failed': 0, 'skipped': 0},
            publish={'success': 3, 'failed': 0, 'skipped': 0},
        )
        # Хоть одна из ошибок должна отразиться в тексте
        assert '2' in summary or '1' in summary

    def test_summary_all_zeros_no_crash(self):
        """Нулевые данные не вызывают исключение."""
        import telegram_reporter as tr
        summary = tr.build_daily_summary(
            pipeline={'success': 0, 'failed': 0, 'skipped': 0},
            login={'success': 0, 'failed': 0, 'skipped': 0},
            warmup={'success': 0, 'failed': 0, 'skipped': 0},
            publish={'success': 0, 'failed': 0, 'skipped': 0},
        )
        assert isinstance(summary, str)


# ── Блок 3: send_message ─────────────────────────────────────────────────────

class TestSendMessage:
    """send_message() отправляет сообщение в Telegram."""

    def test_send_calls_requests_post(self, monkeypatch):
        """send_message делает POST запрос к Telegram API."""
        import telegram_reporter as tr
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {'ok': True}
        with patch('telegram_reporter.requests.post', return_value=mock_response) as mock_post:
            tr.send_message('Test message', bot_token='test_token', chat_id='123')
        mock_post.assert_called_once()

    def test_send_returns_true_on_success(self, monkeypatch):
        """При успешной отправке возвращает True."""
        import telegram_reporter as tr
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {'ok': True}
        with patch('telegram_reporter.requests.post', return_value=mock_response):
            result = tr.send_message('Hello', bot_token='t', chat_id='c')
        assert result is True

    def test_send_returns_false_on_error(self):
        """При ошибке сети возвращает False (не бросает исключение)."""
        import telegram_reporter as tr
        with patch('telegram_reporter.requests.post', side_effect=Exception('network error')):
            result = tr.send_message('Hello', bot_token='t', chat_id='c')
        assert result is False

    def test_send_uses_env_credentials_by_default(self, monkeypatch):
        """Без явных параметров использует BOT_TOKEN и CHAT_ID из env."""
        import telegram_reporter as tr
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'env_token')
        monkeypatch.setenv('TELEGRAM_CHAT_ID', 'env_chat')
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {'ok': True}
        with patch('telegram_reporter.requests.post', return_value=mock_response) as mock_post:
            tr.send_message('Test')
        # Проверяем что URL содержит env_token
        call_args = mock_post.call_args
        assert 'env_token' in str(call_args)


# ── Блок 4: TelegramReporter (класс/фасад) ───────────────────────────────────

class TestTelegramReporter:
    """TelegramReporter — главный фасад для отчётности."""

    def test_reporter_init_with_env(self, monkeypatch):
        """Инициализируется из переменных окружения."""
        import telegram_reporter as tr
        monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'tok')
        monkeypatch.setenv('TELEGRAM_CHAT_ID', 'cid')
        reporter = tr.TelegramReporter()
        assert reporter.bot_token == 'tok'
        assert reporter.chat_id == 'cid'

    def test_reporter_init_with_args(self):
        """Инициализируется с явными параметрами."""
        import telegram_reporter as tr
        reporter = tr.TelegramReporter(bot_token='my_token', chat_id='my_chat')
        assert reporter.bot_token == 'my_token'

    def test_report_pipeline_calls_send(self):
        """report_pipeline() вызывает send_message."""
        import telegram_reporter as tr
        reporter = tr.TelegramReporter(bot_token='t', chat_id='c')
        with patch.object(reporter, 'send', return_value=True) as mock_send:
            reporter.report_pipeline({'success': 3, 'failed': 0, 'skipped': 0})
        mock_send.assert_called_once()

    def test_report_daily_calls_send(self):
        """report_daily() вызывает send_message."""
        import telegram_reporter as tr
        reporter = tr.TelegramReporter(bot_token='t', chat_id='c')
        with patch.object(reporter, 'send', return_value=True) as mock_send:
            reporter.report_daily(
                pipeline={'success': 1, 'failed': 0, 'skipped': 0},
                login={'success': 1, 'failed': 0, 'skipped': 0},
                warmup={'success': 1, 'failed': 0, 'skipped': 0},
                publish={'success': 1, 'failed': 0, 'skipped': 0},
            )
        mock_send.assert_called_once()

    def test_reporter_no_crash_if_not_configured(self, monkeypatch):
        """Без токена reporter не бросает исключение при инициализации."""
        import telegram_reporter as tr
        monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
        monkeypatch.delenv('TELEGRAM_CHAT_ID', raising=False)
        reporter = tr.TelegramReporter()
        assert reporter is not None
