# 🔧 Техническая спецификация фабрики контента

> Детальное описание каждого компонента, API, структур данных и интеграций

---

## 1️⃣ СЛОЙ ГЕНЕРАЦИИ КОНТЕНТА

### 1.1 Nano Banana API (Генерация моделей)

**Что это:** API для создания фотореалистичных моделей по текстовому описанию

**Документация:** https://nanobana.com/api/docs

**Основные параметры:**
```python
{
    "prompt": "Красивая женщина, 25 лет, европейская внешность, в чёрном платье",
    "reference_image": "https://drive.google.com/file/d/...",  # look & feel
    "style": "photorealistic",
    "angles": [
        "front",      # прямой взгляд
        "left_45",    # левый профиль 45°
        "right_45",   # правый профиль 45°
        "back",       # спина
        "3_4_view"    # 3/4 вид
    ],
    "resolution": "1080x1920",  # вертикальный формат для Reels
    "clothing": {
        "item": "black_dress",
        "image_url": "https://site-donor.com/product/image.jpg"
    }
}
```

**Ответ:**
```json
{
    "model_id": "model_12345",
    "status": "completed",
    "images": {
        "front": "gs://drive/Models/model_12345/front.jpg",
        "left_45": "gs://drive/Models/model_12345/left_45.jpg",
        "right_45": "gs://drive/Models/model_12345/right_45.jpg",
        "back": "gs://drive/Models/model_12345/back.jpg",
        "3_4_view": "gs://drive/Models/model_12345/3_4_view.jpg"
    },
    "created_at": "2026-02-25T10:30:00Z",
    "processing_time_sec": 120
}
```

**Скрипт `nano_banana_client.py`:**
```python
import requests
import json
from typing import Dict, List

class NanoBananaClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.nanobana.com/v1"
    
    def generate_model(
        self,
        prompt: str,
        reference_image_url: str,
        clothing_image_url: str,
        angles: List[str] = None
    ) -> Dict:
        """Генерирует модель в 5 ракурсах"""
        
        if angles is None:
            angles = ["front", "left_45", "right_45", "back", "3_4_view"]
        
        payload = {
            "prompt": prompt,
            "reference_image": reference_image_url,
            "style": "photorealistic",
            "angles": angles,
            "resolution": "1080x1920",
            "clothing": {
                "image_url": clothing_image_url
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/models/generate",
            json=payload,
            headers=headers,
            timeout=300
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_model_status(self, model_id: str) -> Dict:
        """Получает статус генерации модели"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.get(
            f"{self.base_url}/models/{model_id}",
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def download_model_images(self, model_id: str, output_dir: str) -> Dict:
        """Скачивает все изображения модели локально"""
        
        status = self.get_model_status(model_id)
        
        if status["status"] != "completed":
            raise ValueError(f"Model {model_id} is not ready yet")
        
        images = {}
        for angle, url in status["images"].items():
            # Скачиваем через Google Drive API
            local_path = f"{output_dir}/{model_id}_{angle}.jpg"
            # ... логика скачивания ...
            images[angle] = local_path
        
        return images
```

---

### 1.2 Kling AI API (Видео-анимация)

**Что это:** API для создания видео из статичных изображений

**Документация:** https://kling.ai/api/docs

**Основные параметры:**
```python
{
    "images": [
        "gs://drive/Models/model_12345/front.jpg",
        "gs://drive/Models/model_12345/left_45.jpg",
        "gs://drive/Models/model_12345/right_45.jpg"
    ],
    "reference_video": "gs://drive/References/video_ref_001.mp4",  # для стиля движения
    "duration": 20,  # секунды
    "fps": 30,
    "resolution": "1080x1920",
    "motion_intensity": "medium",  # low, medium, high
    "music": "upbeat_fashion"  # опционально
}
```

**Ответ:**
```json
{
    "video_id": "vid_12345",
    "status": "processing",
    "estimated_time_sec": 180,
    "progress": 0,
    "output_url": "gs://drive/Videos/vid_12345.mp4"
}
```

**Скрипт `kling_client.py`:**
```python
import requests
import time
from typing import Dict, List

class KlingAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.kling.ai/v1"
    
    def create_video(
        self,
        image_urls: List[str],
        reference_video_url: str,
        duration: int = 20,
        motion_intensity: str = "medium"
    ) -> Dict:
        """Создаёт видео из изображений"""
        
        payload = {
            "images": image_urls,
            "reference_video": reference_video_url,
            "duration": duration,
            "fps": 30,
            "resolution": "1080x1920",
            "motion_intensity": motion_intensity
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/videos/create",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def wait_for_video(self, video_id: str, max_wait_sec: int = 600) -> Dict:
        """Ждёт завершения создания видео"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_sec:
            response = requests.get(
                f"{self.base_url}/videos/{video_id}",
                headers=headers
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "completed":
                return data
            
            if data["status"] == "failed":
                raise ValueError(f"Video creation failed: {data.get('error')}")
            
            # Показываем прогресс
            print(f"Progress: {data.get('progress', 0)}%")
            time.sleep(10)
        
        raise TimeoutError(f"Video creation took too long")
    
    def download_video(self, video_id: str, output_path: str) -> str:
        """Скачивает готовое видео"""
        
        status = self.wait_for_video(video_id)
        
        # Скачиваем через Google Drive API
        # ... логика скачивания ...
        
        return output_path
```

---

### 1.3 Google Drive API (Облачное хранилище)

**Структура папок:**
```
Google Drive (ig-factory)
├── Donors/
│   ├── 2026-02-25/
│   │   ├── товар_1.json (ссылка, описание, изображение)
│   │   ├── товар_2.json
│   │   └── ...
├── References/
│   ├── angles/ (5 ракурсов)
│   ├── look_and_feel/ (исходные изображения для стиля)
│   └── video_refs/ (видео-референсы для Kling)
├── Models/
│   ├── model_12345/
│   │   ├── front.jpg
│   │   ├── left_45.jpg
│   │   ├── right_45.jpg
│   │   ├── back.jpg
│   │   ├── 3_4_view.jpg
│   │   └── metadata.json
│   └── ...
├── Videos/
│   ├── vid_12345.mp4 (готовое видео)
│   ├── vid_12346.mp4
│   └── ...
└── Queue/
    ├── ready/ (готовые к публикации)
    │   ├── vid_12345.json (метаданные + подпись)
    │   └── ...
    └── published/ (уже опубликованные)
```

**Скрипт `google_drive_client.py`:**
```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

class GoogleDriveClient:
    def __init__(self, credentials_json_path: str):
        self.credentials = Credentials.from_service_account_file(
            credentials_json_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.drive = build('drive', 'v3', credentials=self.credentials)
    
    def upload_file(self, file_path: str, folder_id: str, file_name: str = None) -> str:
        """Загружает файл в Google Drive"""
        
        if file_name is None:
            file_name = file_path.split('/')[-1]
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        file = self.drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')
    
    def download_file(self, file_id: str, output_path: str) -> str:
        """Скачивает файл из Google Drive"""
        
        request = self.drive.files().get_media(fileId=file_id)
        
        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        return output_path
    
    def list_files(self, folder_id: str, file_type: str = None) -> list:
        """Список файлов в папке"""
        
        query = f"'{folder_id}' in parents and trashed=false"
        
        if file_type:
            query += f" and mimeType='{file_type}'"
        
        results = self.drive.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, createdTime)',
            pageSize=100
        ).execute()
        
        return results.get('files', [])
```

---

### 1.4 Content Pipeline (Главный конвейер)

**Скрипт `content_pipeline.py`:**
```python
import json
import logging
from datetime import datetime
from typing import Dict, List

class ContentPipeline:
    def __init__(self, config_path: str):
        self.config = json.load(open(config_path))
        self.nano_banana = NanoBananaClient(self.config['nano_banana_key'])
        self.kling = KlingAIClient(self.config['kling_key'])
        self.drive = GoogleDriveClient(self.config['drive_credentials'])
        self.logger = logging.getLogger(__name__)
    
    def process_donor_item(self, donor_item: Dict) -> Dict:
        """
        Обрабатывает один товар от донора:
        товар → модель → видео → Google Drive
        """
        
        product_id = donor_item['id']
        self.logger.info(f"Processing product {product_id}")
        
        try:
            # Шаг 1: Генерируем модель
            self.logger.info(f"Generating model for {product_id}")
            model_result = self.nano_banana.generate_model(
                prompt=donor_item['prompt'],
                reference_image_url=donor_item['reference_image'],
                clothing_image_url=donor_item['product_image']
            )
            model_id = model_result['model_id']
            
            # Шаг 2: Скачиваем изображения модели
            self.logger.info(f"Downloading model images for {model_id}")
            model_images = self.nano_banana.download_model_images(
                model_id,
                output_dir="/data/models"
            )
            
            # Шаг 3: Загружаем в Google Drive
            self.logger.info(f"Uploading model to Drive")
            drive_image_urls = {}
            for angle, local_path in model_images.items():
                file_id = self.drive.upload_file(
                    local_path,
                    folder_id=self.config['drive_models_folder']
                )
                drive_image_urls[angle] = f"https://drive.google.com/uc?id={file_id}"
            
            # Шаг 4: Создаём видео в Kling
            self.logger.info(f"Creating video for {model_id}")
            video_result = self.kling.create_video(
                image_urls=list(drive_image_urls.values()),
                reference_video_url=donor_item['video_reference'],
                duration=20,
                motion_intensity="medium"
            )
            video_id = video_result['video_id']
            
            # Шаг 5: Ждём завершения видео
            self.logger.info(f"Waiting for video {video_id}")
            video_status = self.kling.wait_for_video(video_id)
            
            # Шаг 6: Скачиваем видео
            self.logger.info(f"Downloading video {video_id}")
            video_path = self.kling.download_video(
                video_id,
                output_path=f"/data/videos/{video_id}.mp4"
            )
            
            # Шаг 7: Загружаем видео в Google Drive
            self.logger.info(f"Uploading video to Drive")
            video_file_id = self.drive.upload_file(
                video_path,
                folder_id=self.config['drive_videos_folder']
            )
            
            # Шаг 8: Генерируем подпись
            caption = self.generate_caption(donor_item)
            
            # Шаг 9: Сохраняем метаданные в очередь
            queue_metadata = {
                "video_id": video_id,
                "product_id": product_id,
                "video_url": f"https://drive.google.com/uc?id={video_file_id}",
                "caption": caption,
                "hashtags": donor_item.get('hashtags', []),
                "mention": self.config['brand_mention'],
                "status": "ready_to_post",
                "created_at": datetime.now().isoformat()
            }
            
            # Загружаем метаданные в Drive
            metadata_path = f"/tmp/metadata_{video_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(queue_metadata, f)
            
            self.drive.upload_file(
                metadata_path,
                folder_id=self.config['drive_queue_folder']
            )
            
            self.logger.info(f"✅ Product {product_id} completed: {video_id}")
            return queue_metadata
        
        except Exception as e:
            self.logger.error(f"❌ Error processing {product_id}: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def generate_caption(self, donor_item: Dict) -> str:
        """Генерирует подпись к посту"""
        # Используем Claude API или ChatGPT
        # ... логика генерации ...
        pass
    
    def run_batch(self, count: int = 10):
        """Обрабатывает батч товаров"""
        
        # Читаем товары из Google Таблицы
        donors = self.get_donors_from_sheet(count)
        
        results = []
        for donor in donors:
            result = self.process_donor_item(donor)
            results.append(result)
        
        self.logger.info(f"Batch completed: {len(results)} items")
        return results
    
    def get_donors_from_sheet(self, count: int) -> List[Dict]:
        """Читает товары из Google Таблицы"""
        # ... логика чтения из Google Sheets ...
        pass
```

---

## 2️⃣ СЛОЙ ДИСТРИБУЦИИ (Instagram)

### 2.1 Multi-Account Login

**Скрипт `multi_account_login.py`:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

class MultiAccountLogin:
    def __init__(self, morelogin_api_key: str, max_concurrent: int = 10):
        self.morelogin = MoreLoginClient(morelogin_api_key)
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
    
    async def login_account(self, account_id: int, account_data: Dict) -> Dict:
        """Логинит один аккаунт"""
        
        try:
            # Шаг 1: Получаем виртуальный телефон
            phone_id = await self.morelogin.get_phone(account_id)
            
            # Шаг 2: Открываем ADB сессию
            adb_session = await self.morelogin.open_adb(phone_id)
            
            # Шаг 3: Запускаем Instagram
            await self.run_instagram_login(adb_session, account_data)
            
            # Шаг 4: Сохраняем session cookies
            cookies = await self.extract_cookies(adb_session)
            
            self.logger.info(f"✅ Account {account_id} logged in")
            return {
                "account_id": account_id,
                "phone_id": phone_id,
                "status": "logged_in",
                "cookies": cookies
            }
        
        except Exception as e:
            self.logger.error(f"❌ Login failed for {account_id}: {str(e)}")
            return {
                "account_id": account_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def login_batch(self, accounts: List[Dict]) -> List[Dict]:
        """Логинит батч аккаунтов параллельно"""
        
        results = []
        
        # Разбиваем на группы по max_concurrent
        for i in range(0, len(accounts), self.max_concurrent):
            batch = accounts[i:i + self.max_concurrent]
            
            tasks = [
                self.login_account(acc['id'], acc)
                for acc in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Интервал между батчами
            await asyncio.sleep(120)
        
        return results
    
    async def run_instagram_login(self, adb_session, account_data):
        """Логинит в Instagram через UIAutomator"""
        
        # Используем UIAutomator для автоматизации UI
        # ... логика логина (TOTP, device-approval) ...
        pass
```

---

### 2.2 Multi-Account Publisher

**Скрипт `multi_account_publisher.py`:**
```python
import asyncio
import random
from typing import Dict, List

class MultiAccountPublisher:
    def __init__(self, redis_client, postgres_client):
        self.redis = redis_client
        self.postgres = postgres_client
        self.logger = logging.getLogger(__name__)
    
    async def publish_to_account(
        self,
        account_id: int,
        video_path: str,
        caption: str,
        hashtags: List[str],
        mention: str
    ) -> Dict:
        """Публикует видео на один аккаунт"""
        
        try:
            # Шаг 1: Получаем ADB сессию
            adb = await self.get_adb_session(account_id)
            
            # Шаг 2: Открываем Instagram
            await self.open_instagram(adb)
            
            # Шаг 3: Нажимаем Create
            await self.tap_create(adb)
            
            # Шаг 4: Выбираем видео
            await self.select_video(adb, video_path)
            
            # Шаг 5: Добавляем подпись
            full_caption = f"{caption}\n\n{' '.join(hashtags)}\n{mention}"
            await self.add_caption(adb, full_caption)
            
            # Шаг 6: Публикуем
            post_url = await self.publish(adb)
            
            # Шаг 7: Сохраняем в БД
            await self.postgres.save_post(
                account_id=account_id,
                video_id=video_path.split('/')[-1],
                post_url=post_url,
                caption=full_caption
            )
            
            self.logger.info(f"✅ Published to account {account_id}: {post_url}")
            return {
                "account_id": account_id,
                "status": "published",
                "post_url": post_url
            }
        
        except Exception as e:
            self.logger.error(f"❌ Publish failed for {account_id}: {str(e)}")
            return {
                "account_id": account_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def publish_batch(
        self,
        account_ids: List[int],
        videos: List[Dict]
    ) -> List[Dict]:
        """Публикует видео на батч аккаунтов"""
        
        results = []
        
        for i, account_id in enumerate(account_ids):
            video = videos[i % len(videos)]
            
            result = await self.publish_to_account(
                account_id=account_id,
                video_path=video['path'],
                caption=video['caption'],
                hashtags=video['hashtags'],
                mention=video['mention']
            )
            
            results.append(result)
            
            # Случайный интервал между публикациями (3-7 мин)
            delay = random.randint(180, 420)
            await asyncio.sleep(delay)
        
        return results
```

---

### 2.3 Factory Orchestrator (Главный оркестратор)

**Скрипт `ig_factory_orchestrator.py`:**
```python
import schedule
import asyncio
from datetime import datetime

class IGFactoryOrchestrator:
    def __init__(self, config_path: str):
        self.config = json.load(open(config_path))
        self.redis = RedisClient(self.config['redis_url'])
        self.postgres = PostgresClient(self.config['postgres_url'])
        self.publisher = MultiAccountPublisher(self.redis, self.postgres)
        self.logger = logging.getLogger(__name__)
    
    async def daily_publish_cycle(self):
        """Ежедневный цикл публикации"""
        
        self.logger.info("Starting daily publish cycle")
        
        # Шаг 1: Получаем активные аккаунты
        accounts = await self.postgres.get_active_accounts()
        self.logger.info(f"Found {len(accounts)} active accounts")
        
        # Шаг 2: Получаем видео из очереди
        videos = await self.redis.get_queue_videos(count=len(accounts))
        self.logger.info(f"Got {len(videos)} videos from queue")
        
        if not videos:
            self.logger.warning("No videos in queue!")
            return
        
        # Шаг 3: Публикуем на все аккаунты
        results = await self.publisher.publish_batch(
            account_ids=[acc['id'] for acc in accounts],
            videos=videos
        )
        
        # Шаг 4: Логируем результаты
        success_count = sum(1 for r in results if r['status'] == 'published')
        self.logger.info(f"Published {success_count}/{len(results)} videos")
        
        # Шаг 5: Отправляем отчёт
        await self.send_report(results)
    
    def schedule_jobs(self):
        """Планирует ежедневные задачи"""
        
        # Публикация каждый день в 09:00
        schedule.every().day.at("09:00").do(
            asyncio.run,
            self.daily_publish_cycle()
        )
        
        # Прогрев каждый день в 10:00
        schedule.every().day.at("10:00").do(
            asyncio.run,
            self.warmup_accounts()
        )
        
        # Сбор аналитики каждый час
        schedule.every().hour.do(
            asyncio.run,
            self.collect_analytics()
        )
    
    def run(self):
        """Запускает оркестратор"""
        
        self.schedule_jobs()
        
        self.logger.info("Orchestrator started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
```

---

## 3️⃣ СЛОЙ УПРАВЛЕНИЯ (Redis + PostgreSQL)

### 3.1 Redis Queue Manager

**Структура очереди:**
```
Redis Keys:
├── queue:videos:ready (список видео готовых к публикации)
├── queue:videos:published (опубликованные видео)
├── queue:accounts:active (активные аккаунты)
└── queue:errors (ошибки)
```

**Скрипт `redis_queue_manager.py`:**
```python
import redis
import json
from typing import Dict, List

class RedisQueueManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def add_video_to_queue(self, video_metadata: Dict):
        """Добавляет видео в очередь"""
        
        video_id = video_metadata['video_id']
        
        self.redis.lpush(
            'queue:videos:ready',
            json.dumps(video_metadata)
        )
        
        # TTL: 7 дней
        self.redis.expire('queue:videos:ready', 604800)
    
    def get_next_video(self) -> Dict:
        """Получает следующее видео из очереди"""
        
        video_json = self.redis.rpop('queue:videos:ready')
        
        if video_json:
            return json.loads(video_json)
        
        return None
    
    def mark_published(self, video_id: str):
        """Отмечает видео как опубликованное"""
        
        self.redis.lpush(
            'queue:videos:published',
            video_id
        )
    
    def get_queue_stats(self) -> Dict:
        """Получает статистику очереди"""
        
        return {
            "ready": self.redis.llen('queue:videos:ready'),
            "published": self.redis.llen('queue:videos:published'),
            "errors": self.redis.llen('queue:errors')
        }
```

---

### 3.2 PostgreSQL Schema

**Схема БД:**
```sql
-- Таблица аккаунтов
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_encrypted VARCHAR(255),
    totp_secret VARCHAR(255),
    phone_id VARCHAR(255),
    proxy_id VARCHAR(255),
    status VARCHAR(50),  -- active, banned, warming_up
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица видео
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(255) UNIQUE NOT NULL,
    product_id VARCHAR(255),
    drive_url VARCHAR(500),
    caption TEXT,
    hashtags TEXT[],
    mention VARCHAR(255),
    status VARCHAR(50),  -- ready, published, failed
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица опубликованных постов
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    video_id INTEGER REFERENCES videos(id),
    post_url VARCHAR(500),
    caption TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    published_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица ошибок
CREATE TABLE errors (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    error_type VARCHAR(100),
    error_message TEXT,
    occurred_at TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_posts_account_id ON posts(account_id);
CREATE INDEX idx_posts_published_at ON posts(published_at);
```

---

## 4️⃣ СЛОЙ AI-АГЕНТА (OpenClaw + Claude)

**Скрипт `ai_agent_monitor.py`:**
```python
import anthropic
from datetime import datetime

class AIAgentMonitor:
    def __init__(self, config: Dict):
        self.client = anthropic.Anthropic(api_key=config['claude_api_key'])
        self.postgres = PostgresClient(config['postgres_url'])
        self.logger = logging.getLogger(__name__)
    
    async def generate_report(self) -> str:
        """Генерирует отчёт через Claude"""
        
        # Собираем метрики
        metrics = await self.collect_metrics()
        
        # Готовим промпт для Claude
        prompt = f"""
        Ты - AI-агент для управления Instagram-фабрикой.
        
        Текущие метрики:
        - Активные аккаунты: {metrics['active_accounts']}
        - Видео в очереди: {metrics['queue_videos']}
        - Опубликовано сегодня: {metrics['published_today']}
        - Средний охват: {metrics['avg_reach']}
        - Процент ошибок: {metrics['error_rate']}%
        
        Проблемы:
        {json.dumps(metrics['issues'], indent=2)}
        
        Дай рекомендации:
        1. Какие аккаунты нужно заменить?
        2. Нужно ли менять стратегию публикации?
        3. Какие видео работают лучше всего?
        4. Что нужно улучшить в следующие 24 часа?
        """
        
        # Вызываем Claude
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        report = message.content[0].text
        
        self.logger.info(f"Generated report:\n{report}")
        return report
    
    async def collect_metrics(self) -> Dict:
        """Собирает метрики из БД"""
        
        metrics = {
            "active_accounts": await self.postgres.count_active_accounts(),
            "queue_videos": await self.redis.llen('queue:videos:ready'),
            "published_today": await self.postgres.count_published_today(),
            "avg_reach": await self.postgres.get_avg_reach(),
            "error_rate": await self.postgres.get_error_rate(),
            "issues": await self.postgres.get_recent_errors(limit=5)
        }
        
        return metrics
    
    async def send_report_to_telegram(self, report: str):
        """Отправляет отчёт в Telegram"""
        
        # Используем Telegram Bot API
        # ... логика отправки ...
        pass
```

---

## 5️⃣ КОНФИГУРАЦИЯ И ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

**Файл `.env`:**
```bash
# Nano Banana
NANO_BANANA_API_KEY=sk_...

# Kling AI
KLING_API_KEY=sk_...

# Google Drive
GOOGLE_DRIVE_CREDENTIALS=/path/to/credentials.json

# MoreLogin
MORELOGIN_API_KEY=...
MORELOGIN_APP_ID=1689105551924663
MORELOGIN_APP_SECRET=b4d061d5c7a24fac84d6f5f3c177e844

# Redis
REDIS_URL=redis://localhost:6379

# PostgreSQL
POSTGRES_URL=postgresql://user:password@localhost:5432/ig_factory

# Claude API
CLAUDE_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Instagram
BRAND_MENTION=@main_brand_account
```

---

> **Последнее обновление:** 25.02.2026
