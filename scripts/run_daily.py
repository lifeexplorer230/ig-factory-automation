"""
Daily Runner — главный ежедневный оркестратор.

Последовательность:
  1. Поток 1: content_pipeline.run_from_sheets() — генерация нового контента
  2. Поток 2а: ig_login_runner.run()             — логин новых аккаунтов
  3. Поток 2б: ig_warmup_runner.run()            — прогрев аккаунтов
  4. Поток 3: multi_account_publisher.run()      — публикация готового контента
  5. Telegram-отчёт с итогами всех этапов

Использование:
    python run_daily.py              # реальный запуск
    python run_daily.py --dry-run    # симуляция (без ADB и API)
    python run_daily.py --skip-pipeline   # пропустить генерацию (только публикация)
    python run_daily.py --only-pipeline   # только генерация
"""
import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / '.env')

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('run_daily')

# ── Импорты модулей (с защитой от ошибок импорта) ────────────────────────────

from content_pipeline    import run_from_sheets
from ig_login_runner     import run as login_run
from ig_warmup_runner    import run as warmup_run
from multi_account_publisher import run as publisher_run
from telegram_reporter   import TelegramReporter

reporter = TelegramReporter()

# ── Главная функция ───────────────────────────────────────────────────────────

def run_daily(dry_run: bool = False,
              skip_pipeline: bool = False,
              only_pipeline: bool = False) -> dict:
    """
    Запустить полный ежедневный цикл.

    Args:
        dry_run:        Симуляция — без реального ADB и API.
        skip_pipeline:  Пропустить генерацию контента (только login/warmup/publish).
        only_pipeline:  Только генерация контента (без login/warmup/publish).

    Returns:
        dict с ключами pipeline, login, warmup, publish — каждый {success, failed, skipped}.
    """
    start_time = time.time()
    logger.info(f'=== Daily Run started (dry_run={dry_run}) ===')

    result = {
        'pipeline': {'success': 0, 'failed': 0, 'skipped': 0},
        'login':    {'success': 0, 'failed': 0, 'skipped': 0},
        'warmup':   {'success': 0, 'failed': 0, 'skipped': 0},
        'publish':  {'success': 0, 'failed': 0, 'skipped': 0},
    }

    # ── Поток 1: Генерация контента ──────────────────────────────────────────
    if not skip_pipeline:
        logger.info('--- Поток 1: Генерация контента ---')
        try:
            count = run_from_sheets(dry_run=dry_run)
            result['pipeline']['success'] = count
            logger.info(f'Pipeline: {count} видео добавлено в очередь')
        except Exception as e:
            logger.error(f'Pipeline ошибка: {e}')
            result['pipeline']['failed'] = 1

    if only_pipeline:
        _finalize(result, start_time, dry_run)
        return result

    # ── Поток 2а: Логин новых аккаунтов ──────────────────────────────────────
    logger.info('--- Поток 2а: Логин аккаунтов ---')
    try:
        login_stats = login_run(skip_existing=True, dry_run=dry_run)
        result['login'] = login_stats
        logger.info(f'Login: {login_stats}')
    except Exception as e:
        logger.error(f'Login ошибка: {e}')
        result['login']['failed'] = 1

    # ── Поток 2б: Прогрев аккаунтов ──────────────────────────────────────────
    logger.info('--- Поток 2б: Прогрев аккаунтов ---')
    try:
        warmup_stats = warmup_run(skip_warmed=True, dry_run=dry_run)
        result['warmup'] = warmup_stats
        logger.info(f'Warmup: {warmup_stats}')
    except Exception as e:
        logger.error(f'Warmup ошибка: {e}')
        result['warmup']['failed'] = 1

    # ── Поток 3: Публикация ───────────────────────────────────────────────────
    logger.info('--- Поток 3: Публикация ---')
    try:
        published = publisher_run(dry_run=dry_run)
        result['publish']['success'] = published
        logger.info(f'Published: {published} постов')
    except Exception as e:
        logger.error(f'Publisher ошибка: {e}')
        result['publish']['failed'] = 1

    _finalize(result, start_time, dry_run)
    return result


def _finalize(result: dict, start_time: float, dry_run: bool) -> None:
    """Подвести итог и отправить Telegram-отчёт."""
    elapsed = time.time() - start_time
    logger.info(
        f'=== Daily Run завершён за {elapsed:.0f}с ==='
        f' pipeline={result["pipeline"]}'
        f' login={result["login"]}'
        f' warmup={result["warmup"]}'
        f' publish={result["publish"]}'
    )
    if not dry_run:
        reporter.report_daily(
            pipeline=result['pipeline'],
            login=result['login'],
            warmup=result['warmup'],
            publish=result['publish'],
        )
    else:
        logger.info('[DRY RUN] Telegram-отчёт не отправлен')
        reporter.report_daily(
            pipeline=result['pipeline'],
            login=result['login'],
            warmup=result['warmup'],
            publish=result['publish'],
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Ежедневный запуск: pipeline → login → warmup → publish → Telegram'
    )
    parser.add_argument('--dry-run',       dest='dry_run',       action='store_true',
                        help='Симуляция без реального ADB и API')
    parser.add_argument('--skip-pipeline', dest='skip_pipeline', action='store_true',
                        help='Пропустить генерацию контента')
    parser.add_argument('--only-pipeline', dest='only_pipeline', action='store_true',
                        help='Только генерация (без login/warmup/publish)')
    args = parser.parse_args()

    result = run_daily(
        dry_run       = args.dry_run,
        skip_pipeline = args.skip_pipeline,
        only_pipeline = args.only_pipeline,
    )

    total_failed = sum(v.get('failed', 0) for v in result.values())
    sys.exit(0 if total_failed == 0 else 1)
