"""
Warmup Runner — последовательный прогрев всех аккаунтов из data/sessions/.

ВАЖНО: один мобильный прокси → прогреваем по одному аккаунту, не параллельно.

Использование:
    python ig_warmup_runner.py                        # все аккаунты
    python ig_warmup_runner.py --account brand_anna   # один аккаунт
    python ig_warmup_runner.py --dry-run              # без реального ADB

Что делает:
  1. Читает data/sessions/*.json (только logged_in=True, без банов)
  2. Пропускает уже прогретые (reels_watched >= 25)
  3. Для каждого аккаунта:
     a. Запускает телефон в MoreLogin
     b. Запускает ig_client.warmup_reels()
     c. Обновляет session файл со статистикой прогрева
     d. Останавливает телефон
  4. Пауза между аккаунтами
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR     = Path(__file__).parent.parent
SESSIONS_DIR = BASE_DIR / 'data' / 'sessions'

load_dotenv(BASE_DIR / '.env')
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('warmup_runner')

# Минимум рилов для считается "прогрет"
MIN_REELS = 25


# ── Вспомогательные функции ───────────────────────────────────────────────────

def load_sessions(only: str = '') -> list[dict]:
    """Загрузить залогиненные сессии из data/sessions/."""
    if not SESSIONS_DIR.exists():
        return []
    result = []
    for f in sorted(SESSIONS_DIR.glob('*.json')):
        data = json.loads(f.read_text())
        if not data.get('logged_in'):
            continue
        if data.get('status') in ('banned', 'action_block'):
            logger.warning(f'Пропуск {f.name}: статус {data["status"]}')
            continue
        data['_session_file'] = str(f)
        result.append(data)
    if only:
        result = [s for s in result if s.get('username') == only]
    return result


def is_warmed_up(session: dict) -> bool:
    """Проверить, достаточно ли прогрет аккаунт."""
    watched = session.get('warmup', {}).get('reels_watched', 0)
    return watched >= MIN_REELS


def update_session(session: dict, warmup_stats: dict) -> None:
    """Обновить session-файл со статистикой прогрева."""
    path = Path(session['_session_file'])
    data = json.loads(path.read_text())

    # Накапливаем суммарную статистику
    existing      = data.get('warmup', {})
    total_reels   = existing.get('reels_watched', 0) + warmup_stats.get('reels_watched', 0)
    total_likes   = existing.get('likes', 0) + warmup_stats.get('likes', 0)
    total_elapsed = existing.get('elapsed_sec', 0) + warmup_stats.get('elapsed', 0)

    data['warmup'] = {
        'reels_watched': total_reels,
        'likes':         total_likes,
        'elapsed_sec':   round(total_elapsed, 1),
        'last_run_at':   datetime.now(timezone.utc).isoformat(),
        'runs_count':    existing.get('runs_count', 0) + 1,
    }

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info(
        f'Сессия обновлена: {path.name} '
        f'(всего: {total_reels} рилов, {total_likes} лайков)'
    )


# ── Прогрев одного аккаунта ───────────────────────────────────────────────────

def warmup_account(session: dict, dry_run: bool = False) -> bool:
    """
    Прогреть один аккаунт.

    Args:
        session:  dict из session-файла (с _session_file)
        dry_run:  True = без реального ADB

    Returns:
        True если прогрев прошёл успешно
    """
    username = session.get('username', '?')
    logger.info(f'Прогрев: @{username}')

    if dry_run:
        logger.info(f'[DRY RUN] Симуляция прогрева @{username}')
        update_session(session, {
            'reels_watched': MIN_REELS,
            'likes':         5,
            'elapsed':       280.0,
        })
        return True

    from morelogin_client import MoreLoginClient
    from adb_client import AdbClient
    from ig_client import InstagramClient

    client     = MoreLoginClient()
    phone_name = session.get('phone_name', '')
    phone_id   = session.get('phone_id')

    # Найти телефон по имени или ID
    if not phone_id:
        phones  = client.list_phones()
        matched = [p for p in phones if p.get('envName') == phone_name]
        if not matched:
            logger.error(f'Телефон "{phone_name}" не найден для @{username}')
            return False
        phone_id = matched[0]['id']

    try:
        _, adb_info = client.get_or_start_phone(phone_name)
        ip   = adb_info.get('adbIp', '127.0.0.1')
        port = int(adb_info.get('adbPort', 5555))
        pwd  = adb_info.get('adbPassword', '')

        with AdbClient(ip, port, pwd) as adb:
            ig           = InstagramClient(adb)
            warmup_stats = ig.warmup_reels()

        update_session(session, warmup_stats)
        logger.info(
            f'✓ @{username}: '
            f'{warmup_stats["reels_watched"]} рилов, '
            f'{warmup_stats["likes"]} лайков, '
            f'{warmup_stats["elapsed"]:.0f}с'
        )
        return True

    except Exception as e:
        logger.error(f'✗ Ошибка прогрева @{username}: {e}')
        return False

    finally:
        try:
            client.power_off(int(phone_id))
            logger.info(f'Телефон остановлен')
        except Exception as e:
            logger.warning(f'Не удалось остановить телефон: {e}')


# ── Главный runner ────────────────────────────────────────────────────────────

def run(only: str = '', skip_warmed: bool = True,
        pause_sec: int = 30, dry_run: bool = False) -> dict:
    """
    Прогреть все аккаунты последовательно.

    Args:
        only:        если задан — прогревать только этот username
        skip_warmed: пропускать уже прогретые (>= 25 рилов)
        pause_sec:   пауза между аккаунтами (30с по умолчанию)
        dry_run:     без реального ADB

    Returns:
        {'success': n, 'skipped': n, 'failed': n}
    """
    sessions = load_sessions(only=only)
    if not sessions:
        logger.warning(
            f'Нет залогиненных сессий в {SESSIONS_DIR}. '
            'Сначала запусти ig_login_runner.py.'
        )
        return {'success': 0, 'skipped': 0, 'failed': 0}

    logger.info(f'Сессий для прогрева: {len(sessions)}')

    success = skipped = failed = 0

    for i, session in enumerate(sessions, 1):
        username = session.get('username', '?')
        logger.info(f'[{i}/{len(sessions)}] @{username}')

        if skip_warmed and is_warmed_up(session):
            watched = session.get('warmup', {}).get('reels_watched', 0)
            logger.info(f'  Пропущен — уже прогрет ({watched} рилов)')
            skipped += 1
            continue

        ok = warmup_account(session, dry_run=dry_run)
        if ok:
            success += 1
        else:
            failed += 1

        if pause_sec > 0 and i < len(sessions):
            logger.info(f'Пауза {pause_sec}с перед следующим аккаунтом...')
            time.sleep(pause_sec)

    logger.info(
        f'Итог: {success} прогрето, '
        f'{skipped} пропущено, '
        f'{failed} ошибок'
    )
    return {'success': success, 'skipped': skipped, 'failed': failed}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Последовательный прогрев всех Instagram-аккаунтов'
    )
    parser.add_argument('--account',  help='Прогревать только этот username')
    parser.add_argument('--all',      dest='all_accounts', action='store_true',
                        help='Прогревать все, включая уже прогретые')
    parser.add_argument('--pause',    type=int, default=30,
                        help='Пауза между аккаунтами в секундах (по умолчанию 30)')
    parser.add_argument('--dry-run',  dest='dry_run', action='store_true',
                        help='Без реального ADB — симуляция')
    args = parser.parse_args()

    result = run(
        only         = args.account or '',
        skip_warmed  = not args.all_accounts,
        pause_sec    = args.pause,
        dry_run      = args.dry_run,
    )
    sys.exit(0 if result['failed'] == 0 else 1)
