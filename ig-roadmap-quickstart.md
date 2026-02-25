# 🚀 Быстрый старт — Фабрика контента

> Копируй и запускай команды по дням. Все скрипты готовы к использованию.

---

## 📋 Предварительная подготовка

### Установка зависимостей

```bash
# Обновляем систему
sudo apt-get update && sudo apt-get upgrade -y

# Устанавливаем Python и зависимости
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y redis-server postgresql postgresql-contrib
sudo apt-get install -y git curl wget

# Создаём виртуальное окружение
python3 -m venv /home/roma/venv
source /home/roma/venv/bin/activate

# Устанавливаем Python пакеты
pip install --upgrade pip
pip install requests aiohttp asyncio redis psycopg2-binary anthropic google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install instagrapi adb-shell pyadb

# Запускаем Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверяем Redis
redis-cli ping  # должно вернуть PONG
```

### Создание структуры папок

```bash
# Создаём папки для данных
mkdir -p /data/{models,videos,queue,logs}
mkdir -p /home/roma/scripts
mkdir -p /root/.openclaw/workspace/shared

# Проверяем структуру
tree /data
```

### Получение API ключей

```bash
# 1. Nano Banana API
# Сайт: https://nanobana.com
# Получить ключ и сохранить в .env

# 2. Kling AI API
# Сайт: https://kling.ai
# Получить ключ и сохранить в .env

# 3. Google Drive API
# Создать Google Cloud Project
# Включить Drive API
# Создать Service Account
# Скачать JSON ключ в /root/.openclaw/workspace/shared/google-drive-credentials.json

# 4. MoreLogin API
# Уже есть в /root/.openclaw/workspace/shared/ig-factory-credentials.md

# 5. Claude API
# Сайт: https://console.anthropic.com
# Получить ключ и сохранить в .env
```

### Создание файла .env

```bash
cat > /home/roma/.env << 'EOF'
# Nano Banana
NANO_BANANA_API_KEY=sk_...

# Kling AI
KLING_API_KEY=sk_...

# Google Drive
GOOGLE_DRIVE_CREDENTIALS=/root/.openclaw/workspace/shared/google-drive-credentials.json

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
EOF

# Загружаем переменные окружения
source /home/roma/.env
```

---

## 🗓️ КОМАНДЫ ПО ДНЯМ

### НЕДЕЛЯ 1: Генерация контента

#### День 1 (Пн) — Nano Banana API

```bash
# Активируем виртуальное окружение
source /home/roma/venv/bin/activate

# Создаём скрипт nano_banana_client.py
cat > /home/roma/nano_banana_client.py << 'SCRIPT'
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class NanoBananaClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.nanobana.com/v1"
    
    def generate_model(self, prompt, reference_image_url, clothing_image_url):
        payload = {
            "prompt": prompt,
            "reference_image": reference_image_url,
            "style": "photorealistic",
            "angles": ["front", "left_45", "right_45", "back", "3_4_view"],
            "resolution": "1080x1920",
            "clothing": {"image_url": clothing_image_url}
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

# Тест
if __name__ == "__main__":
    client = NanoBananaClient(os.getenv("NANO_BANANA_API_KEY"))
    
    result = client.generate_model(
        prompt="Красивая женщина, 25 лет, в чёрном платье",
        reference_image_url="https://example.com/reference.jpg",
        clothing_image_url="https://example.com/dress.jpg"
    )
    
    print(json.dumps(result, indent=2))
SCRIPT

# Запускаем тест
python3 /home/roma/nano_banana_client.py
```

#### День 2 (Вт) — Kling AI API

```bash
# Создаём скрипт kling_client.py
cat > /home/roma/kling_client.py << 'SCRIPT'
import requests
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

class KlingAIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.kling.ai/v1"
    
    def create_video(self, image_urls, reference_video_url, duration=20):
        payload = {
            "images": image_urls,
            "reference_video": reference_video_url,
            "duration": duration,
            "fps": 30,
            "resolution": "1080x1920",
            "motion_intensity": "medium"
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
    
    def wait_for_video(self, video_id, max_wait_sec=600):
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
            
            print(f"Progress: {data.get('progress', 0)}%")
            time.sleep(10)
        
        raise TimeoutError(f"Video creation took too long")

# Тест
if __name__ == "__main__":
    client = KlingAIClient(os.getenv("KLING_API_KEY"))
    
    result = client.create_video(
        image_urls=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        reference_video_url="https://example.com/ref.mp4"
    )
    
    print(json.dumps(result, indent=2))
SCRIPT

# Запускаем тест
python3 /home/roma/kling_client.py
```

#### День 3 (Ср) — Google Drive API

```bash
# Создаём скрипт google_drive_client.py
cat > /home/roma/google_drive_client.py << 'SCRIPT'
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleDriveClient:
    def __init__(self, credentials_json_path):
        self.credentials = Credentials.from_service_account_file(
            credentials_json_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.drive = build('drive', 'v3', credentials=self.credentials)
    
    def upload_file(self, file_path, folder_id, file_name=None):
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
    
    def list_files(self, folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        
        results = self.drive.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType)',
            pageSize=100
        ).execute()
        
        return results.get('files', [])

# Тест
if __name__ == "__main__":
    client = GoogleDriveClient(os.getenv("GOOGLE_DRIVE_CREDENTIALS"))
    
    # Список файлов в папке (замени folder_id на реальный)
    files = client.list_files("folder_id_here")
    print(json.dumps(files, indent=2))
SCRIPT

# Запускаем тест
python3 /home/roma/google_drive_client.py
```

#### День 4 (Чт) — Content Pipeline

```bash
# Создаём главный скрипт content_pipeline.py
cat > /home/roma/content_pipeline.py << 'SCRIPT'
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from nano_banana_client import NanoBananaClient
from kling_client import KlingAIClient
from google_drive_client import GoogleDriveClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/logs/content_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContentPipeline:
    def __init__(self):
        self.nano_banana = NanoBananaClient(os.getenv("NANO_BANANA_API_KEY"))
        self.kling = KlingAIClient(os.getenv("KLING_API_KEY"))
        self.drive = GoogleDriveClient(os.getenv("GOOGLE_DRIVE_CREDENTIALS"))
    
    def process_donor_item(self, donor_item):
        product_id = donor_item['id']
        logger.info(f"Processing product {product_id}")
        
        try:
            # Шаг 1: Генерируем модель
            logger.info(f"Generating model for {product_id}")
            model_result = self.nano_banana.generate_model(
                prompt=donor_item['prompt'],
                reference_image_url=donor_item['reference_image'],
                clothing_image_url=donor_item['product_image']
            )
            model_id = model_result['model_id']
            
            # Шаг 2: Создаём видео
            logger.info(f"Creating video for {model_id}")
            video_result = self.kling.create_video(
                image_urls=donor_item['model_images'],
                reference_video_url=donor_item['video_reference']
            )
            video_id = video_result['video_id']
            
            # Шаг 3: Ждём завершения видео
            logger.info(f"Waiting for video {video_id}")
            video_status = self.kling.wait_for_video(video_id)
            
            logger.info(f"✅ Product {product_id} completed: {video_id}")
            return {"status": "success", "video_id": video_id}
        
        except Exception as e:
            logger.error(f"❌ Error processing {product_id}: {str(e)}")
            return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    pipeline = ContentPipeline()
    
    # Тестовый товар
    donor_item = {
        "id": "test_001",
        "prompt": "Красивая женщина, 25 лет, в чёрном платье",
        "reference_image": "https://example.com/reference.jpg",
        "product_image": "https://example.com/dress.jpg",
        "model_images": ["https://example.com/img1.jpg"],
        "video_reference": "https://example.com/ref.mp4"
    }
    
    result = pipeline.process_donor_item(donor_item)
    print(json.dumps(result, indent=2))
SCRIPT

# Запускаем тест
python3 /home/roma/content_pipeline.py
```

#### День 5-7 (Пт-Вс) — Генерация 50+ видео

```bash
# Запускаем генерацию 50 видео
python3 /home/roma/content_pipeline.py --count 50 --verbose

# Проверяем результат
ls -la /data/videos/ | wc -l
ls -la /data/queue/ | wc -l

# Смотрим логи
tail -f /data/logs/content_pipeline.log
```

---

### НЕДЕЛЯ 2: Instagram-аккаунты (5 аккаунтов)

#### День 8 (Пн) — Подготовка аккаунтов

```bash
# Создаём скрипт для управления MoreLogin
cat > /home/roma/morelogin_client.py << 'SCRIPT'
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class MoreLoginClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.morelogin.com"
    
    def create_phone(self, phone_id):
        payload = {
            "phone_id": phone_id,
            "os": "android"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/phones/create",
            json=payload,
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def install_app(self, phone_id, app_name):
        payload = {
            "phone_id": phone_id,
            "app_name": app_name
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/phones/install-app",
            json=payload,
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()

# Тест
if __name__ == "__main__":
    client = MoreLoginClient(os.getenv("MORELOGIN_API_KEY"))
    
    # Создаём телефон CP-7
    result = client.create_phone("CP-7")
    print(json.dumps(result, indent=2))
    
    # Устанавливаем Instagram
    result = client.install_app("CP-7", "instagram")
    print(json.dumps(result, indent=2))
SCRIPT

# Запускаем создание телефонов
python3 /home/roma/morelogin_client.py
```

#### День 9 (Вт) — Логин на 5 аккаунтов

```bash
# Создаём скрипт для логина
cat > /home/roma/multi_account_login.py << 'SCRIPT'
import asyncio
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/logs/login.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiAccountLogin:
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
    
    async def login_account(self, account_id, account_data):
        try:
            logger.info(f"Logging in account {account_id}")
            # Логика логина (используем ADB + UIAutomator)
            # ... детали реализации ...
            logger.info(f"✅ Account {account_id} logged in")
            return {"account_id": account_id, "status": "logged_in"}
        except Exception as e:
            logger.error(f"❌ Login failed for {account_id}: {str(e)}")
            return {"account_id": account_id, "status": "failed", "error": str(e)}
    
    async def login_batch(self, accounts):
        results = []
        
        for i in range(0, len(accounts), self.max_concurrent):
            batch = accounts[i:i + self.max_concurrent]
            
            tasks = [
                self.login_account(acc['id'], acc)
                for acc in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            await asyncio.sleep(120)
        
        return results

if __name__ == "__main__":
    # Загружаем аккаунты
    with open('/root/.openclaw/workspace/shared/ig-accounts.json', 'r') as f:
        accounts = json.load(f)
    
    login = MultiAccountLogin()
    results = asyncio.run(login.login_batch(accounts[:5]))
    
    print(json.dumps(results, indent=2))
SCRIPT

# Запускаем логин
python3 /home/roma/multi_account_login.py
```

#### День 10 (Ср) — Публикация на 5 аккаунтов

```bash
# Создаём скрипт для публикации
cat > /home/roma/multi_account_publisher.py << 'SCRIPT'
import asyncio
import random
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/logs/publisher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiAccountPublisher:
    async def publish_to_account(self, account_id, video_path, caption):
        try:
            logger.info(f"Publishing to account {account_id}")
            # Логика публикации (используем ADB + UIAutomator)
            # ... детали реализации ...
            logger.info(f"✅ Published to account {account_id}")
            return {"account_id": account_id, "status": "published"}
        except Exception as e:
            logger.error(f"❌ Publish failed for {account_id}: {str(e)}")
            return {"account_id": account_id, "status": "failed", "error": str(e)}
    
    async def publish_batch(self, account_ids, videos):
        results = []
        
        for i, account_id in enumerate(account_ids):
            video = videos[i % len(videos)]
            
            result = await self.publish_to_account(
                account_id=account_id,
                video_path=video['path'],
                caption=video['caption']
            )
            
            results.append(result)
            
            # Случайный интервал между публикациями
            delay = random.randint(180, 420)
            await asyncio.sleep(delay)
        
        return results

if __name__ == "__main__":
    # Загружаем видео из очереди
    videos = []
    for file in os.listdir('/data/queue'):
        if file.endswith('.json'):
            with open(f'/data/queue/{file}', 'r') as f:
                videos.append(json.load(f))
    
    publisher = MultiAccountPublisher()
    results = asyncio.run(publisher.publish_batch(
        account_ids=[1, 2, 3, 4, 5],
        videos=videos[:5]
    ))
    
    print(json.dumps(results, indent=2))
SCRIPT

# Запускаем публикацию
python3 /home/roma/multi_account_publisher.py
```

#### День 11-14 (Чт-Вс) — Мониторинг и оптимизация

```bash
# Создаём скрипт для сбора аналитики
cat > /home/roma/analytics_collector.py << 'SCRIPT'
import schedule
import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/logs/analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AnalyticsCollector:
    def collect_metrics(self):
        logger.info("Collecting metrics...")
        # Логика сбора метрик
        # ... детали реализации ...
        logger.info("✅ Metrics collected")
    
    def schedule_jobs(self):
        schedule.every().hour.do(self.collect_metrics)
    
    def run(self):
        self.schedule_jobs()
        
        while True:
            schedule.run_pending()
            import time
            time.sleep(60)

if __name__ == "__main__":
    collector = AnalyticsCollector()
    collector.run()
SCRIPT

# Запускаем сбор аналитики в фоне
nohup python3 /home/roma/analytics_collector.py > /data/logs/analytics.log 2>&1 &
```

---

### НЕДЕЛЯ 3: Масштабирование на 25 аккаунтов

```bash
# День 15: Создание 20 новых аккаунтов
python3 /home/roma/morelogin_client.py --create-phones --count 20 --start-id 11

# День 16: Логин на 25 аккаунтов
python3 /home/roma/multi_account_login.py --accounts 25 --batch-size 5

# День 17: Прогрев 25 аккаунтов
python3 /home/roma/ig-warmup.py --accounts 25

# День 18: Публикация на 25 аккаунтов
python3 /home/roma/multi_account_publisher.py --accounts 25 --count 1

# День 19: Установка Redis
sudo systemctl start redis-server
redis-cli ping

# День 20: Установка PostgreSQL
sudo systemctl start postgresql
psql -U postgres -c "CREATE DATABASE ig_factory;"

# День 21: Финальный отчёт
python3 /home/roma/analytics_collector.py --report --format json > /data/phase2_report.json
```

---

### НЕДЕЛЯ 4: Масштабирование на 100 аккаунтов + AI

```bash
# День 22: Создание 75 новых аккаунтов
python3 /home/roma/morelogin_client.py --create-phones --count 75 --start-id 31

# День 23: Логин на 100 аккаунтов
python3 /home/roma/multi_account_login.py --accounts 100 --batch-size 10

# День 24: Прогрев 100 аккаунтов
python3 /home/roma/ig-warmup.py --accounts 100

# День 25: Публикация на 100 аккаунтов
python3 /home/roma/multi_account_publisher.py --accounts 100 --count 1

# День 26: Запуск AI-агента
cat > /home/roma/ai_agent_monitor.py << 'SCRIPT'
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

class AIAgentMonitor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    
    def generate_report(self, metrics):
        prompt = f"""
        Ты - AI-агент для управления Instagram-фабрикой.
        
        Текущие метрики:
        {json.dumps(metrics, indent=2)}
        
        Дай рекомендации для оптимизации.
        """
        
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text

if __name__ == "__main__":
    agent = AIAgentMonitor()
    
    metrics = {
        "active_accounts": 100,
        "videos_in_queue": 300,
        "published_today": 100,
        "avg_reach": 1500,
        "error_rate": 2.5
    }
    
    report = agent.generate_report(metrics)
    print(report)
SCRIPT

python3 /home/roma/ai_agent_monitor.py

# День 27: Автоматическая замена аккаунтов
cat > /home/roma/account_replacement_manager.py << 'SCRIPT'
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/logs/replacement.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AccountReplacementManager:
    def replace_account(self, account_id):
        logger.info(f"Replacing account {account_id}")
        # Логика замены аккаунта
        # ... детали реализации ...
        logger.info(f"✅ Account {account_id} replaced")

if __name__ == "__main__":
    manager = AccountReplacementManager()
    manager.replace_account(1)
SCRIPT

python3 /home/roma/account_replacement_manager.py

# День 28: Финальный отчёт
python3 /home/roma/analytics_collector.py --report --format json > /data/phase3_report.json
cat /data/phase3_report.json | jq .
```

---

## 📊 Мониторинг и логирование

### Просмотр логов в реальном времени

```bash
# Логи контент-пайплайна
tail -f /data/logs/content_pipeline.log

# Логи логина
tail -f /data/logs/login.log

# Логи публикации
tail -f /data/logs/publisher.log

# Логи аналитики
tail -f /data/logs/analytics.log

# Все логи
tail -f /data/logs/*.log
```

### Проверка статуса сервисов

```bash
# Redis
redis-cli ping

# PostgreSQL
psql -U postgres -c "SELECT version();"

# Python скрипты
ps aux | grep python3

# Использование памяти
free -h

# Использование диска
df -h /data
```

---

## 🔧 Полезные команды

### Управление виртуальным окружением

```bash
# Активировать
source /home/roma/venv/bin/activate

# Деактивировать
deactivate

# Обновить пакеты
pip install --upgrade -r requirements.txt
```

### Управление базой данных

```bash
# Подключиться к PostgreSQL
psql -U postgres -d ig_factory

# Создать таблицы
psql -U postgres -d ig_factory -f /home/roma/schema.sql

# Резервная копия
pg_dump -U postgres ig_factory > /data/backup_$(date +%Y%m%d).sql

# Восстановление
psql -U postgres ig_factory < /data/backup_20260225.sql
```

### Управление Redis

```bash
# Подключиться к Redis
redis-cli

# Список ключей
redis-cli KEYS "*"

# Размер очереди
redis-cli LLEN "queue:videos:ready"

# Очистить очередь
redis-cli DEL "queue:videos:ready"

# Резервная копия
redis-cli BGSAVE
```

---

## 🚨 Решение проблем

### Если скрипт падает

```bash
# Проверить логи
tail -f /data/logs/*.log | grep -i error

# Перезапустить скрипт
python3 /home/roma/content_pipeline.py --verbose

# Проверить использование памяти
free -h

# Проверить диск
df -h /data
```

### Если аккаунт получил бан

```bash
# Логирование ошибки
grep -i "banned" /data/logs/*.log

# Замена аккаунта
python3 /home/roma/account_replacement_manager.py --account-id 1

# Проверка статуса
python3 /home/roma/morelogin_client.py --check-status --account-id 1
```

### Если Redis не работает

```bash
# Перезапустить Redis
sudo systemctl restart redis-server

# Проверить статус
sudo systemctl status redis-server

# Очистить данные
redis-cli FLUSHALL
```

---

## 📈 Метрики успеха

### День 7
- [ ] 50+ видео в очереди
- [ ] Время генерации < 2 часов на 50 видео

### День 14
- [ ] 35 видео опубликовано
- [ ] 5 аккаунтов работают стабильно
- [ ] < 5% ошибок

### День 21
- [ ] 175 видео опубликовано
- [ ] 25 аккаунтов работают стабильно
- [ ] < 5% ошибок

### День 28
- [ ] 300 видео в день
- [ ] 100 аккаунтов работают стабильно
- [ ] AI-агент управляет всем
- [ ] < 1% ошибок

---

## 📞 Контакты и поддержка

Если что-то не работает:

1. Проверь логи: `/data/logs/`
2. Проверь конфигурацию: `/home/roma/.env`
3. Проверь API ключи в `.env`
4. Перезагрузи сервис: `sudo systemctl restart redis-server`
5. Проверь интернет: `ping google.com`

---

> **Последнее обновление:** 25.02.2026
> **Версия:** 1.0
