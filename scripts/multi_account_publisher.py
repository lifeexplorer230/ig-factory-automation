"""
Multi Account Publisher — публикует видео из очереди на Instagram аккаунты.

Поток 3: когда Поток 1 (контент) и Поток 2 (аккаунты) готовы.

Использование:
    python multi_account_publisher.py              # одна публикация
    python multi_account_publisher.py --all        # все готовые видео
    python multi_account_publisher.py --dry-run    # без реальной публикации

Зависимости:
    - data/queue/*.json       — видео со статусом 'ready_to_post'
    - data/sessions/*.json    — залогиненные аккаунты (logged_in=True)
    - data/accounts/*.json    — credentials (username, password, totp_secret)
    - .env                    — MORELOGIN_APP_ID, MORELOGIN_APP_SECRET, BRAND_MENTION
"""
import argparse
import json
import logging
import os
import sys
import random
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR     = Path(__file__).parent.parent
QUEUE_DIR    = BASE_DIR / 'data' / 'queue'
SESSIONS_DIR = BASE_DIR / 'data' / 'sessions'
ACCOUNTS_DIR = BASE_DIR / 'data' / 'accounts'
VIDEOS_DIR   = BASE_DIR / 'data' / 'videos'

load_dotenv(BASE_DIR / '.env')
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('publisher')


# ── Очередь ───────────────────────────────────────────────────────────────────

def get_ready_videos() -> list[dict]:
    """Вернуть список видео со статусом ready_to_post."""
    if not QUEUE_DIR.exists():
        return []
    result = []
    for f in sorted(QUEUE_DIR.glob('*.json')):
        data = json.loads(f.read_text())
        if data.get('status') == 'ready_to_post':
            data['_queue_file'] = str(f)
            result.append(data)
    return result


def mark_as_published(queue_file: str, post_url: str) -> None:
    """Обновить статус видео в очереди на 'published'."""
    path = Path(queue_file)
    data = json.loads(path.read_text())
    data['status']       = 'published'
    data['post_url']     = post_url
    data['published_at'] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info(f"Очередь обновлена: {path.name} → published")


# ── Сессии / аккаунты ────────────────────────────────────────────────────────

def get_logged_in_sessions() -> list[dict]:
    """Вернуть список залогиненных аккаунтов."""
    if not SESSIONS_DIR.exists():
        return []
    result = []
    for f in SESSIONS_DIR.glob('*.json'):
        data = json.loads(f.read_text())
        if data.get('logged_in') and data.get('status') not in ('banned', 'action_block'):
            data['_session_file'] = str(f)
            result.append(data)
    return result


def get_account_credentials(username: str) -> dict:
    """Загрузить credentials аккаунта по username."""
    if not ACCOUNTS_DIR.exists():
        return {}
    for f in ACCOUNTS_DIR.glob('*.json'):
        data = json.loads(f.read_text())
        if data.get('username') == username:
            return data
    return {}


def save_published_post(session: dict, post_info: dict) -> None:
    """Добавить запись об опубликованном посте в session-файл."""
    path = Path(session['_session_file'])
    data = json.loads(path.read_text())
    posts = data.setdefault('published_posts', [])
    posts.append(post_info)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info(f"Сессия обновлена: {path.name} (+1 пост)")


# ── Подпись ───────────────────────────────────────────────────────────────────

def build_caption(video_data: dict) -> str:
    """
    Собрать подпись для поста.

    Выбирает случайный вариант из captions, добавляет @mention и хештеги.
    Если captions пустой — формирует минимальную подпись.
    """
    captions  = video_data.get('captions', [])
    mention   = video_data.get('mention', os.getenv('BRAND_MENTION', '@brand'))
    hashtags  = video_data.get('hashtags', ['#fashion', '#style'])

    if captions:
        caption = random.choice(captions)
    else:
        caption = f"New collection ✨ {mention} {' '.join(hashtags)}"

    # Убедиться что mention и hashtags присутствуют
    if mention not in caption:
        caption = f"{caption} {mention}"
    if not any(h in caption for h in hashtags):
        caption = f"{caption} {' '.join(hashtags[:5])}"

    return caption


# ── Публикация ────────────────────────────────────────────────────────────────

def publish_one(video: dict, session: dict, dry_run: bool = False) -> dict:
    """
    Опубликовать одно видео на один аккаунт.

    Returns:
        dict с полями: video_id, post_url, caption, published_at, account
    """
    username = session.get('username', '?')
    video_id = video.get('video_id', '?')
    caption  = build_caption(video)

    logger.info(f"Публикация: @{username} ← {video_id}")
    logger.info(f"Подпись: {caption[:80]}...")

    if dry_run:
        logger.info("[DRY RUN] Реальная публикация пропущена")
        return {
            'video_id':     video_id,
            'post_url':     'https://www.instagram.com/p/DRY_RUN/',
            'caption':      caption,
            'published_at': datetime.now(timezone.utc).isoformat(),
            'account':      username,
        }

    # Получаем ADB-параметры из сессии
    phone_ip   = session.get('phone_ip')
    phone_port = session.get('phone_port', 5555)
    password   = session.get('adb_password', '')

    if not phone_ip:
        # Запустить телефон через MoreLogin
        phone_ip, phone_port, password = _start_phone(session)

    from adb_client import AdbClient
    from ig_client  import InstagramClient

    video_path = _resolve_video_path(video)
    post_url   = None

    with AdbClient(phone_ip, phone_port, password) as adb:
        ig = InstagramClient(adb)

        # Логин (если сессия ещё не активна)
        creds = get_account_credentials(username)
        if creds:
            ig.login(
                username    = creds['username'],
                password    = creds['password'],
                totp_secret = creds.get('totp_secret'),
            )

        # Публикация
        post_url = ig.post_image(video_path)

    post_url = post_url or 'https://www.instagram.com/  (URL не определён)'

    return {
        'video_id':     video_id,
        'post_url':     post_url,
        'caption':      caption,
        'published_at': datetime.now(timezone.utc).isoformat(),
        'account':      username,
    }


def _start_phone(session: dict) -> tuple[str, int, str]:
    """
    Запустить телефон в MoreLogin и вернуть (ip, port, password).

    Использует phone_name из session-файла для поиска телефона.
    """
    from morelogin_client import MoreLoginClient

    client     = MoreLoginClient()
    phone_name = session.get('phone_name')

    if not phone_name:
        raise RuntimeError(
            f"phone_name не задан в сессии {session.get('username')}. "
            "Невозможно запустить телефон."
        )

    phones = client.list_phones()
    phone  = next((p for p in phones if p.get('envName') == phone_name), None)

    if not phone:
        raise RuntimeError(f"Телефон '{phone_name}' не найден в MoreLogin")

    logger.info(f"Запуск телефона: {phone_name} (id={phone['id']})")
    info = client.get_or_start_phone(phone['id'])

    ip       = info.get('host', info.get('ip', '127.0.0.1'))
    port     = int(info.get('port', 5555))
    password = info.get('password', '')

    logger.info(f"Телефон готов: {ip}:{port}")
    return ip, port, password


def _resolve_video_path(video: dict) -> str:
    """
    Найти локальный путь к видео-файлу.

    Пробует:
    1. video_local_path из метаданных
    2. data/videos/<video_id>.mp4
    3. video_url как-есть (если локальный путь)
    """
    if video.get('video_local_path') and Path(video['video_local_path']).exists():
        return video['video_local_path']

    local = VIDEOS_DIR / f"{video.get('video_id', 'video')}.mp4"
    if local.exists():
        return str(local)

    url = video.get('video_url', '')
    if url and not url.startswith('http'):
        return url

    raise RuntimeError(
        f"Не могу найти локальный файл видео {video.get('video_id')}. "
        f"video_url={url}. "
        "Скачай видео в data/videos/ перед публикацией."
    )


# ── Оркестратор ───────────────────────────────────────────────────────────────

def run(publish_all: bool = False, dry_run: bool = False) -> int:
    """
    Главная функция публикации.

    Args:
        publish_all: True = публиковать все готовые видео, False = только одно
        dry_run:     True = симуляция без реальных запросов

    Returns:
        Количество успешных публикаций
    """
    videos   = get_ready_videos()
    sessions = get_logged_in_sessions()

    if not videos:
        logger.warning("Очередь пуста — нет видео со статусом ready_to_post")
        logger.warning("Запусти content_pipeline.py для генерации контента.")
        return 0

    if not sessions:
        logger.warning("Нет залогиненных аккаунтов")
        logger.warning("Запусти ig-warmup.py для логина аккаунтов.")
        return 0

    logger.info(f"Очередь: {len(videos)} видео | Аккаунты: {len(sessions)}")

    # Если publish_all — берём все видео, иначе одно
    to_publish = videos if publish_all else videos[:1]
    success    = 0

    for video in to_publish:
        # Выбираем следующий аккаунт (ротация)
        session = _pick_session(sessions, video)

        try:
            post_info = publish_one(video, session, dry_run=dry_run)

            # Сохраняем результат
            save_published_post(session, post_info)
            if not dry_run:
                mark_as_published(video['_queue_file'], post_info['post_url'])

            logger.info(
                f"✓ Опубликовано: @{session['username']} "
                f"→ {post_info['post_url']}"
            )
            success += 1

        except Exception as e:
            logger.error(
                f"✗ Ошибка публикации {video.get('video_id')} "
                f"на @{session.get('username')}: {e}"
            )

    logger.info(f"Итог: {success}/{len(to_publish)} успешно")
    return success


def _pick_session(sessions: list[dict], video: dict) -> dict:
    """
    Выбрать аккаунт для публикации.

    Избегает аккаунтов, которые уже публиковали это видео.
    """
    video_id = video.get('video_id')
    # Фильтруем аккаунты, которые уже публиковали это видео
    available = [
        s for s in sessions
        if not any(
            p.get('video_id') == video_id
            for p in s.get('published_posts', [])
        )
    ]
    if not available:
        logger.warning(f"Все аккаунты уже публиковали {video_id}, берём любой")
        available = sessions

    return random.choice(available)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Публикация видео из очереди на Instagram аккаунты'
    )
    parser.add_argument(
        '--all', dest='publish_all', action='store_true',
        help='Опубликовать все готовые видео (по умолчанию — только одно)'
    )
    parser.add_argument(
        '--dry-run', dest='dry_run', action='store_true',
        help='Симуляция без реальной публикации'
    )
    args = parser.parse_args()

    count = run(publish_all=args.publish_all, dry_run=args.dry_run)
    sys.exit(0 if count > 0 else 1)
