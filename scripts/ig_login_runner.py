"""
Login Runner — последовательный логин всех аккаунтов из data/accounts/.

ВАЖНО: один мобильный прокси → логиним по одному аккаунту, не параллельно.
IP ротируется каждые 30 мин — при необходимости делаем паузу между аккаунтами.

Использование:
    python ig_login_runner.py                        # все аккаунты
    python ig_login_runner.py --account brand_anna   # один аккаунт
    python ig_login_runner.py --dry-run              # без реального ADB

Что делает:
  1. Читает data/accounts/*.json
  2. Пропускает уже залогиненные (есть сессия с logged_in=True)
  3. Для каждого аккаунта:
     a. Находит свободный телефон в MoreLogin
     b. Запускает телефон
     c. Логинится через ig_client.login()
     d. Сохраняет сессию в data/sessions/<username>.json
     e. Останавливает телефон (биллинг по минутам!)
  4. Пауза между аккаунтами (опционально)
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
ACCOUNTS_DIR = BASE_DIR / 'data' / 'accounts'
SESSIONS_DIR = BASE_DIR / 'data' / 'sessions'

load_dotenv(BASE_DIR / '.env')
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('login_runner')


# ── Вспомогательные функции ───────────────────────────────────────────────────

def load_accounts(only: str = '') -> list[dict]:
    """Загрузить все credentials из data/accounts/."""
    if not ACCOUNTS_DIR.exists():
        return []
    result = []
    for f in sorted(ACCOUNTS_DIR.glob('*.json')):
        if f.name.startswith('_'):
            continue  # пропускаем шаблоны (_template.json)
        data = json.loads(f.read_text())
        data['_file'] = str(f)
        result.append(data)
    if only:
        result = [a for a in result if a.get('username') == only]
    return result


def load_session(username: str) -> dict:
    """Загрузить session-файл если существует."""
    path = SESSIONS_DIR / f'{username}.json'
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_session(username: str, data: dict) -> None:
    """Сохранить session-файл."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f'{username}.json'
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info(f'Сессия сохранена: {path.name}')


def is_logged_in(username: str) -> bool:
    """Проверить, залогинен ли уже аккаунт."""
    session = load_session(username)
    return bool(session.get('logged_in'))


# ── Логин одного аккаунта ────────────────────────────────────────────────────

def login_account(account: dict, phone_name: str = '',
                  dry_run: bool = False) -> bool:
    """
    Залогинить один аккаунт.

    Args:
        account:    dict с username, password, totp_secret, model_photo_url
        phone_name: имя телефона в MoreLogin (если пусто — берём любой свободный)
        dry_run:    True = без реального ADB

    Returns:
        True если залогинился успешно
    """
    username = account.get('username', '?')
    logger.info(f'Логин: @{username}')

    if dry_run:
        logger.info(f'[DRY RUN] Симуляция логина @{username}')
        save_session(username, {
            'username':    username,
            'logged_in':   True,
            'phone_name':  phone_name or 'DRY_RUN',
            'model_photo_url': account.get('model_photo_url', ''),
            'logged_in_at': datetime.now(timezone.utc).isoformat(),
            'warmup':      {},
            'published_posts': [],
        })
        return True

    from morelogin_client import MoreLoginClient
    from adb_client import AdbClient
    from ig_client import InstagramClient

    client = MoreLoginClient()

    # Найти телефон
    phones  = client.list_phones()
    stopped = [p for p in phones
               if p.get('envStatus') == 2  # Stop
               and (not phone_name or p.get('envName') == phone_name)]

    if not stopped:
        logger.error(f'Нет свободных телефонов для @{username}')
        return False

    phone    = stopped[0]
    phone_id = phone['id']
    pname    = phone.get('envName', str(phone_id))
    logger.info(f'Используем телефон: {pname}')

    try:
        info = client.get_or_start_phone(phone_id)
        ip   = info.get('host', info.get('ip', '127.0.0.1'))
        port = int(info.get('port', 5555))
        pwd  = info.get('password', '')

        with AdbClient(ip, port, pwd) as adb:
            ig = InstagramClient(adb)
            ig.login(
                username    = account['username'],
                password    = account['password'],
                totp_secret = account.get('totp_secret') or None,
            )

        save_session(username, {
            'username':       username,
            'logged_in':      True,
            'phone_name':     pname,
            'phone_id':       phone_id,
            'model_photo_url': account.get('model_photo_url', ''),
            'logged_in_at':   datetime.now(timezone.utc).isoformat(),
            'warmup':         {},
            'published_posts': [],
        })
        logger.info(f'✓ @{username} залогинен')
        return True

    except Exception as e:
        logger.error(f'✗ Ошибка логина @{username}: {e}')
        save_session(username, {
            'username':  username,
            'logged_in': False,
            'phone_name': pname,
            'status':    'login_failed',
            'error':     str(e),
        })
        return False

    finally:
        # Останавливаем телефон — биллинг по минутам
        try:
            client.stop_phone(phone_id)
            logger.info(f'Телефон {pname} остановлен')
        except Exception as e:
            logger.warning(f'Не удалось остановить телефон: {e}')


# ── Главный runner ────────────────────────────────────────────────────────────

def run(only: str = '', skip_existing: bool = True,
        pause_sec: int = 0, dry_run: bool = False) -> dict:
    """
    Залогинить все аккаунты последовательно.

    Args:
        only:          если задан — логиним только этот username
        skip_existing: пропускать уже залогиненные аккаунты
        pause_sec:     пауза между аккаунтами в секундах (0 = без паузы)
        dry_run:       без реального ADB

    Returns:
        {'success': n, 'skipped': n, 'failed': n}
    """
    accounts = load_accounts(only=only)
    if not accounts:
        logger.warning(
            f'Нет аккаунтов в {ACCOUNTS_DIR}. '
            'Создай data/accounts/<username>.json для каждого аккаунта.'
        )
        return {'success': 0, 'skipped': 0, 'failed': 0}

    logger.info(f'Аккаунтов для логина: {len(accounts)}')

    success = skipped = failed = 0

    for i, account in enumerate(accounts, 1):
        username = account.get('username', '?')
        logger.info(f'[{i}/{len(accounts)}] @{username}')

        if skip_existing and is_logged_in(username):
            logger.info(f'  Пропущен — уже залогинен')
            skipped += 1
            continue

        ok = login_account(account, dry_run=dry_run)
        if ok:
            success += 1
        else:
            failed += 1

        # Пауза между аккаунтами (опционально)
        if pause_sec > 0 and i < len(accounts):
            logger.info(f'Пауза {pause_sec}с перед следующим аккаунтом...')
            time.sleep(pause_sec)

    logger.info(
        f'Итог: {success} залогинено, '
        f'{skipped} пропущено, '
        f'{failed} ошибок'
    )
    return {'success': success, 'skipped': skipped, 'failed': failed}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Последовательный логин всех Instagram-аккаунтов'
    )
    parser.add_argument('--account',  help='Логинить только этот username')
    parser.add_argument('--all',      dest='all_accounts', action='store_true',
                        help='Логинить все, включая уже залогиненные')
    parser.add_argument('--pause',    type=int, default=0,
                        help='Пауза между аккаунтами в секундах (по умолчанию 0)')
    parser.add_argument('--dry-run',  dest='dry_run', action='store_true',
                        help='Без реального ADB — симуляция')
    args = parser.parse_args()

    result = run(
        only          = args.account or '',
        skip_existing = not args.all_accounts,
        pause_sec     = args.pause,
        dry_run       = args.dry_run,
    )
    sys.exit(0 if result['failed'] == 0 else 1)
