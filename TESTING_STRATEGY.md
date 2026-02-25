# 🧪 Стратегия тестирования (TDD — Test-Driven Development)

> Сначала пишем тест, потом скрипт. Тест = критерий завершения фазы.

---

## 🎯 Принцип TDD для этого проекта

```
1. Напиши тест (критерий завершения)
   ↓
2. Запусти тест (он падает)
   ↓
3. Напиши скрипт
   ↓
4. Запусти тест (он проходит)
   ↓
5. Документируй результат
   ↓
6. Переходи к следующей фазе
```

---

## 📊 ПОТОК 1: КОНТЕНТ-ФАБРИКА (Тесты)

### Фаза 1.1: Подготовка (Критерий: все ключи получены)

**Тест: `test_1_1_api_keys.py`**
```python
import os
import pytest

class TestPhase11APIKeys:
    """Фаза 1.1: Проверяем, что все API ключи получены"""
    
    def test_nano_banana_key_exists(self):
        """Тест: API ключ Nano Banana есть"""
        assert os.getenv('NANO_BANANA_API_KEY'), "NANO_BANANA_API_KEY не установлен"
    
    def test_kling_ai_key_exists(self):
        """Тест: API ключ Kling AI есть"""
        assert os.getenv('KLING_API_KEY'), "KLING_API_KEY не установлен"
    
    def test_google_drive_credentials_exist(self):
        """Тест: Google Drive credentials есть"""
        assert os.path.exists(os.getenv('GOOGLE_DRIVE_CREDENTIALS')), \
            "Google Drive credentials файл не найден"
    
    def test_nano_banana_api_connection(self):
        """Тест: Можем подключиться к Nano Banana API"""
        from nano_banana_client import NanoBananaClient
        client = NanoBananaClient(os.getenv('NANO_BANANA_API_KEY'))
        assert client.api_key, "Nano Banana клиент не инициализирован"
    
    def test_kling_ai_api_connection(self):
        """Тест: Можем подключиться к Kling AI API"""
        from kling_client import KlingAIClient
        client = KlingAIClient(os.getenv('KLING_API_KEY'))
        assert client.api_key, "Kling AI клиент не инициализирован"
    
    def test_google_drive_connection(self):
        """Тест: Можем подключиться к Google Drive"""
        from google_drive_client import GoogleDriveClient
        client = GoogleDriveClient(os.getenv('GOOGLE_DRIVE_CREDENTIALS'))
        assert client.drive, "Google Drive клиент не инициализирован"
    
    def test_folder_structure_created(self):
        """Тест: Структура папок в Google Drive создана"""
        import json
        config = json.load(open('/home/roma/config.json'))
        required_folders = ['donors', 'references', 'models', 'videos', 'queue']
        for folder in required_folders:
            assert folder in config['drive_folders'], f"Папка {folder} не найдена в конфиге"
```

**Критерий завершения 1.1:**
- ✅ Все тесты проходят
- ✅ Все API ключи в `.env`
- ✅ Все клиенты инициализированы
- ✅ Структура Google Drive создана

---

### Фаза 1.2: Тест на 1 товаре (Критерий: 1 видео создано)

**Тест: `test_1_2_single_video.py`**
```python
import pytest
import os
from pathlib import Path

class TestPhase12SingleVideo:
    """Фаза 1.2: Генерируем 1 видео от товара до публикации"""
    
    def test_nano_banana_model_generation(self):
        """Тест: Nano Banana генерирует модель в 5 ракурсах"""
        from nano_banana_client import NanoBananaClient
        
        client = NanoBananaClient(os.getenv('NANO_BANANA_API_KEY'))
        
        # Используем тестовый товар
        result = client.generate_model(
            prompt="Красивая женщина, 25 лет, в чёрном платье",
            reference_image_url="https://example.com/reference.jpg",
            clothing_image_url="https://example.com/dress.jpg"
        )
        
        assert result['status'] == 'completed', f"Модель не сгенерирована: {result}"
        assert 'model_id' in result, "model_id отсутствует в результате"
        assert len(result['images']) == 5, f"Должно быть 5 ракурсов, получено {len(result['images'])}"
    
    def test_kling_ai_video_creation(self, nano_banana_model_id):
        """Тест: Kling AI создаёт видео из модели"""
        from kling_client import KlingAIClient
        
        client = KlingAIClient(os.getenv('KLING_API_KEY'))
        
        result = client.create_video(
            image_urls=[
                "https://example.com/front.jpg",
                "https://example.com/left_45.jpg",
                "https://example.com/right_45.jpg"
            ],
            reference_video_url="https://example.com/ref.mp4",
            duration=20
        )
        
        assert result['status'] == 'processing' or result['status'] == 'completed', \
            f"Видео не создаётся: {result}"
        assert 'video_id' in result, "video_id отсутствует в результате"
        
        # Ждём завершения
        final_result = client.wait_for_video(result['video_id'])
        assert final_result['status'] == 'completed', "Видео не завершилось"
    
    def test_video_quality(self, video_path):
        """Тест: Видео имеет приемлемое качество"""
        import subprocess
        
        # Проверяем длительность видео
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1', 
             video_path],
            capture_output=True,
            text=True
        )
        
        duration = float(result.stdout.strip())
        assert 15 <= duration <= 30, f"Длительность видео {duration}s, должна быть 15-30s"
    
    def test_caption_generation(self):
        """Тест: Генерируем подпись к видео"""
        from caption_generator import CaptionGenerator
        
        generator = CaptionGenerator(os.getenv('CLAUDE_API_KEY'))
        
        captions = generator.generate_captions(
            product_name="Чёрное платье",
            product_description="Элегантное платье из хлопка"
        )
        
        assert len(captions) >= 5, f"Должно быть минимум 5 вариантов подписей, получено {len(captions)}"
        assert all(len(c) > 0 for c in captions), "Некоторые подписи пусты"
        assert all('@' in captions[0] for _ in [1]), "Упоминание аккаунта отсутствует"
    
    def test_metadata_saved(self):
        """Тест: Метаданные видео сохранены в JSON"""
        import json
        
        metadata_path = '/data/queue/test_video.json'
        assert os.path.exists(metadata_path), f"Файл метаданных не найден: {metadata_path}"
        
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        required_fields = ['video_id', 'video_url', 'captions', 'hashtags', 'mention', 'status']
        for field in required_fields:
            assert field in metadata, f"Поле {field} отсутствует в метаданных"
        
        assert metadata['status'] == 'ready_to_post', "Статус должен быть ready_to_post"

# Fixtures
@pytest.fixture
def nano_banana_model_id():
    """Фикстура: ID сгенерированной модели"""
    from nano_banana_client import NanoBananaClient
    client = NanoBananaClient(os.getenv('NANO_BANANA_API_KEY'))
    result = client.generate_model(...)
    return result['model_id']

@pytest.fixture
def video_path():
    """Фикстура: Путь к созданному видео"""
    return '/data/videos/test_video.mp4'
```

**Критерий завершения 1.2:**
- ✅ Модель сгенерирована в 5 ракурсах
- ✅ Видео создано (15-30 сек)
- ✅ Видна одежда и черты лица
- ✅ Подписи готовы (5+ вариантов)
- ✅ Метаданные в JSON
- ✅ Все тесты проходят

---

### Фаза 1.3: Масштаб на 10 товаров (Критерий: 10 видео в очереди)

**Тест: `test_1_3_batch_videos.py`**
```python
import pytest
import os
import json
from pathlib import Path

class TestPhase13BatchVideos:
    """Фаза 1.3: Генерируем 10 видео"""
    
    def test_batch_processing(self):
        """Тест: Обрабатываем 10 товаров без ошибок"""
        from content_pipeline import ContentPipeline
        
        pipeline = ContentPipeline()
        
        # Используем 10 тестовых товаров
        test_products = [
            {'id': f'test_{i:03d}', 'name': f'Товар {i}'}
            for i in range(1, 11)
        ]
        
        results = []
        for product in test_products:
            try:
                result = pipeline.process_donor_item(product)
                results.append(result)
            except Exception as e:
                pytest.fail(f"Ошибка при обработке товара {product['id']}: {str(e)}")
        
        assert len(results) == 10, f"Обработано {len(results)} товаров, ожидалось 10"
        assert all(r['status'] == 'success' for r in results), "Некоторые товары обработаны с ошибкой"
    
    def test_queue_has_10_videos(self):
        """Тест: В очереди 10 видео"""
        queue_dir = Path('/data/queue')
        video_files = list(queue_dir.glob('*.json'))
        
        assert len(video_files) >= 10, f"В очереди {len(video_files)} видео, ожидалось >= 10"
    
    def test_processing_time(self):
        """Тест: Время обработки 10 видео < 2 часов"""
        import time
        from content_pipeline import ContentPipeline
        
        pipeline = ContentPipeline()
        test_products = [{'id': f'test_{i:03d}'} for i in range(1, 11)]
        
        start_time = time.time()
        for product in test_products:
            pipeline.process_donor_item(product)
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 7200, f"Обработка заняла {elapsed_time}s, должна быть < 7200s (2 часа)"
    
    def test_no_duplicate_videos(self):
        """Тест: Нет дубликатов видео в очереди"""
        queue_dir = Path('/data/queue')
        video_ids = []
        
        for file in queue_dir.glob('*.json'):
            with open(file) as f:
                metadata = json.load(f)
                video_ids.append(metadata['video_id'])
        
        assert len(video_ids) == len(set(video_ids)), "Найдены дубликаты видео"
    
    def test_all_videos_have_metadata(self):
        """Тест: Все видео имеют полные метаданные"""
        queue_dir = Path('/data/queue')
        required_fields = ['video_id', 'video_url', 'captions', 'hashtags', 'mention', 'status']
        
        for file in queue_dir.glob('*.json'):
            with open(file) as f:
                metadata = json.load(f)
            
            for field in required_fields:
                assert field in metadata, f"Поле {field} отсутствует в {file}"

**Критерий завершения 1.3:**
- ✅ 10 видео в очереди
- ✅ Время обработки < 2 часов
- ✅ Нет дубликатов
- ✅ Все видео имеют метаданные
- ✅ Все тесты проходят
```

---

## 📊 ПОТОК 2: INSTAGRAM-ФАБРИКА (Тесты)

### Фаза 2.1: Подготовка (Критерий: 5 телефонов готово)

**Тест: `test_2_1_phones_ready.py`**
```python
import pytest
import os

class TestPhase21PhonesReady:
    """Фаза 2.1: Проверяем, что 5 виртуальных телефонов готовы"""
    
    def test_morelogin_credentials(self):
        """Тест: MoreLogin credentials есть"""
        assert os.getenv('MORELOGIN_API_KEY'), "MORELOGIN_API_KEY не установлен"
        assert os.getenv('MORELOGIN_APP_ID'), "MORELOGIN_APP_ID не установлен"
        assert os.getenv('MORELOGIN_APP_SECRET'), "MORELOGIN_APP_SECRET не установлен"
    
    def test_5_phones_created(self):
        """Тест: 5 телефонов созданы в MoreLogin"""
        from morelogin_client import MoreLoginClient
        
        client = MoreLoginClient(os.getenv('MORELOGIN_API_KEY'))
        phones = client.list_phones()
        
        assert len(phones) >= 5, f"Создано {len(phones)} телефонов, ожидалось >= 5"
    
    def test_5_proxies_added(self):
        """Тест: 5 прокси добавлены"""
        from morelogin_client import MoreLoginClient
        
        client = MoreLoginClient(os.getenv('MORELOGIN_API_KEY'))
        proxies = client.list_proxies()
        
        assert len(proxies) >= 5, f"Добавлено {len(proxies)} прокси, ожидалось >= 5"
    
    def test_instagram_installed_on_all_phones(self):
        """Тест: Instagram установлен на всех 5 телефонах"""
        from morelogin_client import MoreLoginClient
        
        client = MoreLoginClient(os.getenv('MORELOGIN_API_KEY'))
        phones = client.list_phones()[:5]
        
        for phone in phones:
            apps = client.list_apps(phone['id'])
            assert any(app['name'] == 'instagram' for app in apps), \
                f"Instagram не установлен на телефоне {phone['id']}"
    
    def test_adb_accessible_on_all_phones(self):
        """Тест: ADB доступен на всех 5 телефонах"""
        from morelogin_client import MoreLoginClient
        
        client = MoreLoginClient(os.getenv('MORELOGIN_API_KEY'))
        phones = client.list_phones()[:5]
        
        for phone in phones:
            adb_status = client.check_adb(phone['id'])
            assert adb_status['connected'], f"ADB не доступен на телефоне {phone['id']}"

**Критерий завершения 2.1:**
- ✅ 5 телефонов созданы
- ✅ 5 прокси добавлены
- ✅ Instagram установлен на всех
- ✅ ADB доступен на всех
- ✅ Все тесты проходят
```

---

### Фаза 2.4: Прогрев (Критерий: 5 аккаунтов прогреты)

**Тест: `test_2_4_warmup.py`**
```python
import pytest
import os
import json

class TestPhase24Warmup:
    """Фаза 2.4: Проверяем, что аккаунты прогреты"""
    
    def test_5_accounts_logged_in(self):
        """Тест: 5 аккаунтов залогинены"""
        logged_in_accounts = 0
        
        for i in range(1, 6):
            account_id = f'account_{i:03d}'
            session_file = f'/data/sessions/{account_id}.json'
            
            if os.path.exists(session_file):
                with open(session_file) as f:
                    session = json.load(f)
                    if session.get('logged_in'):
                        logged_in_accounts += 1
        
        assert logged_in_accounts >= 5, f"Залогинено {logged_in_accounts} аккаунтов, ожидалось >= 5"
    
    def test_no_bans(self):
        """Тест: Нет банов аккаунтов"""
        banned_accounts = 0
        
        for i in range(1, 6):
            account_id = f'account_{i:03d}'
            status_file = f'/data/accounts/{account_id}_status.json'
            
            if os.path.exists(status_file):
                with open(status_file) as f:
                    status = json.load(f)
                    if status.get('status') == 'banned':
                        banned_accounts += 1
        
        assert banned_accounts == 0, f"Забанено {banned_accounts} аккаунтов"
    
    def test_warmup_completed(self):
        """Тест: Прогрев завершён на всех аккаунтах"""
        from ig_warmup import WarmupManager
        
        manager = WarmupManager()
        
        for i in range(1, 6):
            account_id = f'account_{i:03d}'
            warmup_status = manager.get_warmup_status(account_id)
            
            assert warmup_status['completed'], f"Прогрев не завершён для {account_id}"
            assert warmup_status['reels_watched'] >= 25, \
                f"Просмотрено {warmup_status['reels_watched']} рилов, ожидалось >= 25"
    
    def test_accounts_visible_in_instagram(self):
        """Тест: Аккаунты видны в Instagram"""
        from ig_checker import InstagramChecker
        
        checker = InstagramChecker()
        
        for i in range(1, 6):
            account_id = f'account_{i:03d}'
            is_visible = checker.check_account_visible(account_id)
            
            assert is_visible, f"Аккаунт {account_id} не видно в Instagram"

**Критерий завершения 2.4:**
- ✅ 5 аккаунтов залогинены
- ✅ 0 банов
- ✅ Прогрев завершён (25+ рилов просмотрено)
- ✅ Аккаунты видны в Instagram
- ✅ Все тесты проходят
```

---

## 📊 ПОТОК 3: ПУБЛИКАЦИЯ (Тесты)

### Фаза 3.1: Первая публикация (Критерий: видео опубликовано)

**Тест: `test_3_1_first_publication.py`**
```python
import pytest
import os
import json
from datetime import datetime

class TestPhase31FirstPublication:
    """Фаза 3.1: Проверяем первую публикацию"""
    
    def test_video_published_successfully(self):
        """Тест: Видео успешно опубликовано"""
        from multi_account_publisher import MultiAccountPublisher
        
        publisher = MultiAccountPublisher()
        
        # Берём первое видео из очереди
        queue_dir = '/data/queue'
        video_file = next(iter(os.listdir(queue_dir)))
        
        with open(f'{queue_dir}/{video_file}') as f:
            video_metadata = json.load(f)
        
        result = publisher.publish_to_account(
            account_id='account_001',
            video_path=video_metadata['video_url'],
            caption=video_metadata['captions'][0]
        )
        
        assert result['status'] == 'published', f"Видео не опубликовано: {result}"
        assert 'post_url' in result, "post_url отсутствует в результате"
    
    def test_post_visible_in_instagram(self):
        """Тест: Пост видно в Instagram"""
        from ig_checker import InstagramChecker
        
        checker = InstagramChecker()
        
        # Проверяем, что пост появился на аккаунте
        posts = checker.get_account_posts('account_001')
        
        assert len(posts) > 0, "Посты не найдены на аккаунте"
        assert posts[0]['caption'], "Подпись отсутствует в посте"
    
    def test_caption_correct(self):
        """Тест: Подпись корректна"""
        from ig_checker import InstagramChecker
        
        checker = InstagramChecker()
        posts = checker.get_account_posts('account_001')
        
        caption = posts[0]['caption']
        
        assert '@' in caption, "Упоминание аккаунта отсутствует"
        assert '#' in caption, "Хештеги отсутствуют"
        assert len(caption) > 10, "Подпись слишком короткая"
    
    def test_post_saved_to_database(self):
        """Тест: Информация о посте сохранена в БД"""
        from postgres_client import PostgresClient
        
        client = PostgresClient(os.getenv('POSTGRES_URL'))
        
        posts = client.get_recent_posts(account_id='account_001', limit=1)
        
        assert len(posts) > 0, "Пост не найден в БД"
        assert posts[0]['post_url'], "post_url отсутствует в БД"
        assert posts[0]['caption'], "caption отсутствует в БД"

**Критерий завершения 3.1:**
- ✅ Видео опубликовано
- ✅ Пост видно в Instagram
- ✅ Подпись корректна
- ✅ Информация в БД
- ✅ Все тесты проходят
```

---

## 🏃 Как запустить тесты

```bash
# Установка pytest
pip install pytest pytest-cov

# Запуск всех тестов
pytest /home/roma/tests/ -v

# Запуск тестов конкретной фазы
pytest /home/roma/tests/test_1_1_api_keys.py -v

# Запуск с покрытием кода
pytest /home/roma/tests/ --cov=/home/roma/scripts --cov-report=html

# Запуск с выводом логов
pytest /home/roma/tests/ -v -s
```

---

## 📁 Структура папок для тестов

```
/home/roma/
├── tests/
│   ├── __init__.py
│   ├── conftest.py (общие фикстуры)
│   ├── test_1_1_api_keys.py
│   ├── test_1_2_single_video.py
│   ├── test_1_3_batch_videos.py
│   ├── test_2_1_phones_ready.py
│   ├── test_2_2_accounts_ready.py
│   ├── test_2_3_login.py
│   ├── test_2_4_warmup.py
│   ├── test_2_5_scale_25.py
│   ├── test_2_6_scale_100.py
│   ├── test_3_1_first_publication.py
│   ├── test_3_2_auto_publication.py
│   ├── test_3_3_analytics.py
│   ├── test_3_4_scale_300.py
│   └── test_3_5_ai_agent.py
└── scripts/
    ├── nano_banana_client.py
    ├── kling_client.py
    ├── ... (остальные скрипты)
```

---

## ✅ Критерии завершения каждой фазы

| Фаза | Критерий | Тест |
|------|----------|------|
| 1.1 | Все API ключи получены | test_1_1_api_keys.py |
| 1.2 | 1 видео создано | test_1_2_single_video.py |
| 1.3 | 10 видео в очереди | test_1_3_batch_videos.py |
| 1.4 | Подписи готовы | test_1_4_captions.py |
| 1.5 | 50+ видео в очереди | test_1_5_batch_50.py |
| 2.1 | 5 телефонов готово | test_2_1_phones_ready.py |
| 2.2 | 5 аккаунтов куплены | test_2_2_accounts_ready.py |
| 2.3 | 5 аккаунтов залогинены | test_2_3_login.py |
| 2.4 | 5 аккаунтов прогреты | test_2_4_warmup.py |
| 2.5 | 25 аккаунтов готово | test_2_5_scale_25.py |
| 2.6 | 100 аккаунтов готово | test_2_6_scale_100.py |
| 3.1 | Видео опубликовано | test_3_1_first_publication.py |
| 3.2 | Публикация автоматична | test_3_2_auto_publication.py |
| 3.3 | Метрики собираются | test_3_3_analytics.py |
| 3.4 | 300 видео/день | test_3_4_scale_300.py |
| 3.5 | AI управляет всем | test_3_5_ai_agent.py |

---

> **Версия:** 1.0  
> **Обновлено:** 25.02.2026  
> **Статус:** TDD стратегия готова ✅
