"""
Content Pipeline — Поток 1: генерация видео и наполнение очереди.

Фазы 1.2–1.5: Nano Banana → Kling AI → Caption → data/queue/

Использование:
    python content_pipeline.py --product "Black Dress" --description "Elegant cotton"
    python content_pipeline.py --batch products.json
    python content_pipeline.py --status    # показать статус очереди

Зависимости:
    - .env: NANO_BANANA_API_KEY, KLING_API_KEY, GOOGLE_DRIVE_CREDENTIALS, CLAUDE_API_KEY
    - data/queue/   — куда кладём готовые JSON с метаданными
    - data/videos/  — куда скачиваем MP4
"""
import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR   = Path(__file__).parent.parent
QUEUE_DIR  = BASE_DIR / 'data' / 'queue'
VIDEOS_DIR = BASE_DIR / 'data' / 'videos'

load_dotenv(BASE_DIR / '.env')
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('pipeline')


# ── Очередь ───────────────────────────────────────────────────────────────────

def queue_status() -> dict:
    """Вернуть статистику очереди."""
    if not QUEUE_DIR.exists():
        return {'total': 0, 'ready_to_post': 0, 'published': 0, 'processing': 0}

    counts: dict[str, int] = {}
    for f in QUEUE_DIR.glob('*.json'):
        data = json.loads(f.read_text())
        if not isinstance(data, dict):
            continue  # пропускаем не-queue файлы (списки и т.п.)
        status = data.get('status', 'unknown')
        counts[status] = counts.get(status, 0) + 1

    return {
        'total':         sum(counts.values()),
        'ready_to_post': counts.get('ready_to_post', 0),
        'published':     counts.get('published', 0),
        'processing':    counts.get('processing', 0),
        'error':         counts.get('error', 0),
    }


def save_to_queue(video_data: dict) -> Path:
    """Сохранить метаданные видео в очередь."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    video_id = video_data.get('video_id') or str(uuid.uuid4())[:8]
    path     = QUEUE_DIR / f"{video_id}.json"

    data = {
        'video_id':    video_id,
        'status':      'ready_to_post',
        'created_at':  datetime.now(timezone.utc).isoformat(),
        **video_data,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info(f"Очередь: сохранено {path.name}")
    return path


# ── Пайплайн одного товара ────────────────────────────────────────────────────

def process_product(
    product_name: str,
    product_description: str,
    model_photo_url: str   = '',
    clothing_photo_url: str = '',
    bg_photo_url: str       = '',
    source_video_url: str   = '',
    dry_run: bool           = False,
) -> dict:
    """
    Полный пайплайн для одного товара.

    Шаги:
      1. Nano Banana — генерация модели в одежде
      2. Kling AI    — создание Reels-видео
      3. Claude      — генерация подписей
      4. Queue       — сохранение метаданных

    Args:
        product_name:        Название товара (например "Black Evening Dress")
        product_description: Краткое описание (материал, фасон, стиль)
        model_photo_url:     URL фото модели
        clothing_photo_url:  URL фото одежды
        bg_photo_url:        URL фото фона
        source_video_url:    URL исходного видео (движение + аудио)
        dry_run:             True = без реальных API-вызовов, возвращает заглушку

    Returns:
        Метаданные видео с полями video_id, video_url, captions, hashtags, mention, status
    """
    logger.info(f"Обработка товара: {product_name}")

    if dry_run:
        return _dry_run_product(product_name)

    # Шаг 1: Nano Banana — модель в одежде
    video_url = _step_nano_banana(
        product_name, model_photo_url, clothing_photo_url, bg_photo_url
    )

    # Шаг 2: Kling AI — Reels видео
    video_url = _step_kling(
        video_url, source_video_url, product_name
    )

    # Шаг 3: Claude — подписи
    captions, hashtags, mention = _step_captions(product_name, product_description)

    video_id = str(uuid.uuid4())[:8]
    return {
        'video_id':    video_id,
        'video_url':   video_url,
        'product':     product_name,
        'captions':    captions,
        'hashtags':    hashtags,
        'mention':     mention,
        'status':      'ready_to_post',
    }


def _step_nano_banana(
    product_name: str,
    model_photo_url: str,
    clothing_photo_url: str,
    bg_photo_url: str,
) -> str:
    """Генерировать модель в одежде через Nano Banana API."""
    from nano_banana_client import NanoBananaClient

    client = NanoBananaClient()
    logger.info("Nano Banana: генерация модели...")

    result = client.generate_model(
        product_name=product_name,
        model_image_url=model_photo_url,
        clothing_image_url=clothing_photo_url,
        background_image_url=bg_photo_url,
    )
    model_id  = result['model_id']
    image_url = client.wait_for_model(model_id)

    logger.info(f"Nano Banana: готово → {image_url}")
    return image_url


def _step_kling(
    image_url: str,
    source_video_url: str,
    product_name: str,
) -> str:
    """Создать Reels-видео через Kling AI."""
    from kling_client import KlingAIClient

    client = KlingAIClient()
    logger.info("Kling AI: создание видео...")

    result = client.create_video(
        image_url=image_url,
        reference_video_url=source_video_url,
        prompt=f"Fashion Reels for {product_name}, 9:16 vertical, smooth movement",
    )
    video_id  = result['video_id']
    video_url = client.wait_for_video(video_id)

    logger.info(f"Kling AI: готово → {video_url}")
    return video_url


def _step_captions(
    product_name: str,
    product_description: str,
) -> tuple[list[str], list[str], str]:
    """Сгенерировать подписи через Claude API."""
    from caption_generator import CaptionGenerator

    gen      = CaptionGenerator()
    mention  = os.getenv('BRAND_MENTION', '@brand')
    hashtags = [
        '#fashion', '#womensfashion', '#ootd', '#style',
        '#outfit', '#fashionista', '#instafashion', '#trendy',
    ]

    logger.info("Claude: генерация подписей...")
    captions = gen.generate_with_fallback(product_name, product_description)
    logger.info(f"Claude: {len(captions)} подписей готово")

    return captions, hashtags, mention


def _dry_run_product(product_name: str) -> dict:
    """Заглушка для dry-run режима."""
    video_id = str(uuid.uuid4())[:8]
    mention  = os.getenv('BRAND_MENTION', '@brand')
    return {
        'video_id':    video_id,
        'video_url':   f'https://example.com/videos/{video_id}.mp4',
        'product':     product_name,
        'captions':    [
            f"Style that speaks for itself ✨ {mention} #fashion #womensfashion #ootd",
            f"Effortless elegance 🖤 {mention} #fashionista #lookbook #styleinspo",
        ],
        'hashtags':    ['#fashion', '#style', '#ootd'],
        'mention':     mention,
        'status':      'ready_to_post',
        'dry_run':     True,
    }


# ── Пакетная обработка ────────────────────────────────────────────────────────

def process_batch(products_file: str, dry_run: bool = False) -> int:
    """
    Обработать список товаров из JSON-файла.

    Формат products.json:
    [
      {
        "name": "Black Evening Dress",
        "description": "Elegant cotton dress, A-line silhouette",
        "model_photo_url": "https://...",
        "clothing_photo_url": "https://...",
        "bg_photo_url": "https://...",
        "source_video_url": "https://..."
      },
      ...
    ]

    Returns:
        Количество успешно обработанных товаров
    """
    path = Path(products_file)
    if not path.exists():
        logger.error(f"Файл не найден: {products_file}")
        return 0

    products = json.loads(path.read_text())
    logger.info(f"Пакет: {len(products)} товаров")

    success = 0
    for i, p in enumerate(products, 1):
        logger.info(f"[{i}/{len(products)}] {p.get('name', '?')}")
        try:
            video_data = process_product(
                product_name=p.get('name', f'Product {i}'),
                product_description=p.get('description', ''),
                model_photo_url=p.get('model_photo_url', ''),
                clothing_photo_url=p.get('clothing_photo_url', ''),
                bg_photo_url=p.get('bg_photo_url', ''),
                source_video_url=p.get('source_video_url', ''),
                dry_run=dry_run,
            )
            save_to_queue(video_data)
            success += 1
        except Exception as e:
            logger.error(f"Ошибка товара '{p.get('name')}': {e}")

    logger.info(f"Пакет: {success}/{len(products)} успешно")
    return success


# ── Google Sheets: задания от оператора ──────────────────────────────────────

def process_task(task: dict, dry_run: bool = False) -> dict:
    """
    Обработать одно задание из Google Sheets.

    Структура задания:
        account              — username аккаунта (например brand_anna)
        clothing_drive_id    — Google Drive ID файла одежды
        source_video_drive_id — Google Drive ID исходного видео (движение + аудио)
        row_index            — номер строки в Sheets (для обновления статуса)

    Поток:
        1. Скачиваем clothing и source_video из Google Drive
        2. Берём model_photo_url из data/accounts/<account>.json
        3. Nano Banana: model_photo + clothing → сгенерированное фото
        4. Kling AI: сгенерированное фото + source_video → видео
        5. Claude: подпись
        6. Сохраняем в data/queue/<account>/

    Returns:
        dict с метаданными видео (video_id, video_url, captions, ...)
    """
    account    = task.get('account', '')
    clothing   = task.get('clothing_drive_id', '')
    src_video  = task.get('source_video_drive_id', '')

    logger.info(f"Задание: аккаунт={account}, одежда={clothing[:8]}..., видео={src_video[:8]}...")

    if dry_run:
        video_id = str(uuid.uuid4())[:8]
        mention  = os.getenv('BRAND_MENTION', '@brand')
        return {
            'video_id':             video_id,
            'video_url':            f'https://example.com/videos/{video_id}.mp4',
            'account':              account,
            'clothing_drive_id':    clothing,
            'source_video_drive_id': src_video,
            'captions': [
                f"Style that speaks for itself ✨ {mention} #fashion #womensfashion #ootd",
                f"Effortless elegance 🖤 {mention} #fashionista #lookbook #styleinspo",
            ],
            'hashtags': ['#fashion', '#style', '#ootd'],
            'mention':  mention,
            'status':   'ready_to_post',
            'dry_run':  True,
        }

    # Загрузить model_photo_url из аккаунта
    accounts_dir = BASE_DIR / 'data' / 'accounts'
    account_file = accounts_dir / f'{account}.json'
    if not account_file.exists():
        raise RuntimeError(
            f'Файл аккаунта не найден: {account_file}. '
            f'Создай data/accounts/{account}.json с полем model_photo_url.'
        )
    account_data    = json.loads(account_file.read_text())
    model_photo_url = account_data.get('model_photo_url', '')
    if not model_photo_url:
        raise RuntimeError(f'model_photo_url пустой в {account_file}')

    from google_drive_client import GoogleDriveClient
    drive = GoogleDriveClient()

    # Скачать одежду и исходное видео из Drive
    clothing_path   = VIDEOS_DIR / f'clothing_{clothing[:8]}.jpg'
    src_video_path  = VIDEOS_DIR / f'srcvideo_{src_video[:8]}.mp4'
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Drive: скачиваем одежду...")
    drive.download_file(clothing, str(clothing_path))

    logger.info("Drive: скачиваем исходное видео...")
    drive.download_file(src_video, str(src_video_path))

    # Генерация через Nano Banana + Kling + Claude
    video_data = process_product(
        product_name        = account,
        product_description = '',
        model_photo_url     = model_photo_url,
        clothing_photo_url  = str(clothing_path),
        source_video_url    = str(src_video_path),
    )
    video_data['account']               = account
    video_data['clothing_drive_id']     = clothing
    video_data['source_video_drive_id'] = src_video
    return video_data


def run_from_sheets(dry_run: bool = False) -> int:
    """
    Читать pending-задания из Google Sheets и генерировать видео.

    Оператор добавляет строки в таблицу:
        account | clothing_drive_id | source_video_drive_id | status=pending

    Этот метод:
        1. Читает все pending строки
        2. Обрабатывает каждую через process_task()
        3. Обновляет статус строки в Sheets (done / error)
        4. Сохраняет видео в data/queue/<account>/

    Returns:
        Количество успешно обработанных заданий
    """
    from google_sheets_client import GoogleSheetsClient
    sheets  = GoogleSheetsClient()
    tasks   = sheets.get_pending_tasks()

    if not tasks:
        logger.info("Нет новых заданий в Google Sheets")
        return 0

    logger.info(f"Заданий из Sheets: {len(tasks)}")
    success = 0

    for i, task in enumerate(tasks, 1):
        account = task.get('account', '?')
        logger.info(f"[{i}/{len(tasks)}] Аккаунт: {account}")
        try:
            sheets.update_task_status(task['row_index'], 'processing')
            video_data = process_task(task, dry_run=dry_run)
            save_to_queue(video_data)
            sheets.update_task_status(
                task['row_index'], 'done',
                video_id=video_data.get('video_id', '')
            )
            success += 1
            logger.info(f"✓ {account}: видео {video_data['video_id']} в очереди")
        except Exception as e:
            logger.error(f"✗ {account}: {e}")
            try:
                sheets.update_task_status(task['row_index'], 'error', error=str(e))
            except Exception:
                pass

    logger.info(f"Sheets: {success}/{len(tasks)} заданий выполнено")
    return success


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Поток 1: генерация видео для Instagram'
    )
    parser.add_argument('--product',     help='Название товара (для теста без Sheets)')
    parser.add_argument('--description', default='', help='Описание товара')
    parser.add_argument('--batch',       help='JSON-файл со списком товаров (для теста)')
    parser.add_argument('--sheets',      action='store_true',
                        help='Читать задания из Google Sheets (основной режим)')
    parser.add_argument('--status',      action='store_true', help='Показать статус очереди')
    parser.add_argument('--dry-run',     dest='dry_run', action='store_true',
                        help='Без реальных API-вызовов')
    args = parser.parse_args()

    if args.status:
        stat = queue_status()
        print(f"\nСтатус очереди:")
        print(f"  Всего:          {stat['total']}")
        print(f"  Готово к постингу: {stat['ready_to_post']}")
        print(f"  Опубликовано:   {stat['published']}")
        print(f"  В обработке:    {stat['processing']}")
        print(f"  Ошибок:         {stat['error']}\n")
        sys.exit(0)

    if args.batch:
        count = process_batch(args.batch, dry_run=args.dry_run)
        sys.exit(0 if count > 0 else 1)

    if args.product:
        try:
            data = process_product(
                product_name=args.product,
                product_description=args.description,
                dry_run=args.dry_run,
            )
            save_to_queue(data)
            print(f"\nГотово: {data['video_id']}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            sys.exit(1)

    parser.print_help()
