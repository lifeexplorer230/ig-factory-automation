"""
Telegram Reporter — отправка отчётов о работе пайплайна в Telegram.

Использование:
    from telegram_reporter import TelegramReporter

    reporter = TelegramReporter()
    reporter.report_pipeline({'success': 3, 'failed': 0, 'skipped': 0})
    reporter.report_daily(pipeline=..., login=..., warmup=..., publish=...)

Standalone:
    python telegram_reporter.py --daily  (отправляет сводку из текущих данных)
"""
import logging
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

logger = logging.getLogger('telegram_reporter')

# ── Форматирование ────────────────────────────────────────────────────────────

_LABELS = {
    'pipeline': '🎬 Генерация контента',
    'login':    '🔐 Логин аккаунтов',
    'warmup':   '🔥 Прогрев аккаунтов',
    'publish':  '📤 Публикация',
}


def format_report(stage: str, stats: dict) -> str:
    """
    Форматировать статистику одного этапа в строку.

    Args:
        stage: 'pipeline' | 'login' | 'warmup' | 'publish'
        stats: {'success': n, 'failed': n, 'skipped': n}

    Returns:
        Отформатированная строка для Telegram.
    """
    label   = _LABELS.get(stage, stage)
    success = stats.get('success', 0)
    failed  = stats.get('failed',  0)
    skipped = stats.get('skipped', 0)

    status = '✅' if failed == 0 else '❌'
    lines  = [f'{status} <b>{label}</b>']
    lines.append(f'   ✔ успешно: {success}')
    if failed:
        lines.append(f'   ✗ ошибок: {failed}')
    if skipped:
        lines.append(f'   ⏭ пропущено: {skipped}')

    return '\n'.join(lines)


def build_daily_summary(pipeline: dict, login: dict,
                         warmup: dict, publish: dict) -> str:
    """
    Собрать итоговую сводку дня из всех этапов.

    Returns:
        Полное сообщение для Telegram (HTML-разметка).
    """
    now   = datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')
    total_failed = (pipeline.get('failed', 0) + login.get('failed', 0) +
                    warmup.get('failed', 0)   + publish.get('failed', 0))

    header = f'📊 <b>Ежедневный отчёт</b> — {now}'
    if total_failed > 0:
        header += f'\n⚠️ Ошибок за день: {total_failed}'

    sections = [
        format_report('pipeline', pipeline),
        format_report('login',    login),
        format_report('warmup',   warmup),
        format_report('publish',  publish),
    ]

    return header + '\n\n' + '\n\n'.join(sections)


# ── Отправка ──────────────────────────────────────────────────────────────────

def send_message(text: str, bot_token: str = '', chat_id: str = '') -> bool:
    """
    Отправить сообщение в Telegram.

    Args:
        text:      Текст сообщения (поддерживает HTML).
        bot_token: Токен бота (по умолчанию из TELEGRAM_BOT_TOKEN).
        chat_id:   ID чата/канала (по умолчанию из TELEGRAM_CHAT_ID).

    Returns:
        True если отправка успешна, False при ошибке.
    """
    token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat  = chat_id  or os.getenv('TELEGRAM_CHAT_ID', '')

    if not token or not chat:
        logger.warning('Telegram не настроен: нет BOT_TOKEN или CHAT_ID')
        return False

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    try:
        resp = requests.post(url, json={
            'chat_id':    chat,
            'text':       text,
            'parse_mode': 'HTML',
        }, timeout=10)
        if not resp.ok:
            logger.error(f'Telegram API ошибка: {resp.status_code} {resp.text[:200]}')
            return False
        return True
    except Exception as e:
        logger.error(f'Ошибка отправки в Telegram: {e}')
        return False


# ── Класс-фасад ───────────────────────────────────────────────────────────────

class TelegramReporter:
    """
    Главный фасад для отчётности.

    Пример:
        reporter = TelegramReporter()
        reporter.report_daily(
            pipeline={'success': 5, 'failed': 0, 'skipped': 0},
            login={'success': 2, 'failed': 0, 'skipped': 8},
            warmup={'success': 1, 'failed': 0, 'skipped': 9},
            publish={'success': 5, 'failed': 0, 'skipped': 0},
        )
    """

    def __init__(self, bot_token: str = '', chat_id: str = ''):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id   = chat_id   or os.getenv('TELEGRAM_CHAT_ID',   '')

    def send(self, text: str) -> bool:
        """Отправить произвольное сообщение."""
        return send_message(text, bot_token=self.bot_token, chat_id=self.chat_id)

    def report_pipeline(self, stats: dict) -> bool:
        """Отправить отчёт этапа генерации контента."""
        return self.send(format_report('pipeline', stats))

    def report_login(self, stats: dict) -> bool:
        """Отправить отчёт этапа логина."""
        return self.send(format_report('login', stats))

    def report_warmup(self, stats: dict) -> bool:
        """Отправить отчёт этапа прогрева."""
        return self.send(format_report('warmup', stats))

    def report_publish(self, stats: dict) -> bool:
        """Отправить отчёт публикации."""
        return self.send(format_report('publish', stats))

    def report_daily(self, pipeline: dict, login: dict,
                     warmup: dict, publish: dict) -> bool:
        """Отправить итоговую сводку дня."""
        text = build_daily_summary(
            pipeline=pipeline,
            login=login,
            warmup=warmup,
            publish=publish,
        )
        return self.send(text)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s — %(message)s',
        datefmt='%H:%M:%S',
    )

    parser = argparse.ArgumentParser(description='Отправить тестовое сообщение в Telegram')
    parser.add_argument('--test',    action='store_true', help='Отправить тестовое сообщение')
    parser.add_argument('--message', help='Отправить произвольное сообщение')
    args = parser.parse_args()

    reporter = TelegramReporter()

    if args.test:
        ok = reporter.send('✅ Telegram Reporter работает! ig-factory-automation.')
        sys.exit(0 if ok else 1)
    elif args.message:
        ok = reporter.send(args.message)
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
