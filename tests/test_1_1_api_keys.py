"""
Фаза 1.1: Проверяем, что все API ключи получены и клиенты инициализируются.
TDD: Сначала тест → потом скрипты.
"""
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env
load_dotenv(Path(__file__).parent.parent / '.env')

# Добавляем scripts/ в PATH для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestPhase11APIKeys:
    """Фаза 1.1: Проверяем наличие API ключей в .env"""

    def test_nano_banana_key_exists(self):
        """API ключ Nano Banana установлен и не является заглушкой"""
        key = os.getenv('NANO_BANANA_API_KEY', '')
        assert key, "NANO_BANANA_API_KEY не установлен в .env"
        assert not key.startswith('sk_...'), "NANO_BANANA_API_KEY содержит заглушку — замени реальным ключом"

    def test_kling_ai_key_exists(self):
        """API ключ Kling AI установлен и не является заглушкой"""
        key = os.getenv('KLING_API_KEY', '')
        assert key, "KLING_API_KEY не установлен в .env"
        assert not key.startswith('sk_...'), "KLING_API_KEY содержит заглушку — замени реальным ключом"

    def test_google_drive_credentials_configured(self):
        """Google Drive credentials path установлен"""
        creds_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS', '')
        assert creds_path, "GOOGLE_DRIVE_CREDENTIALS не установлен в .env"
        assert not creds_path.startswith('/path/to/'), \
            "GOOGLE_DRIVE_CREDENTIALS содержит заглушку — укажи реальный путь"

    def test_google_sheets_id_configured(self):
        """Google Sheets ID таблицы заданий установлен.

        Таблица заданий — основной интерфейс между оператором и пайплайном.
        Оператор добавляет строки: аккаунт + одежда (Drive ID) + видео (Drive ID).
        content_pipeline.py читает pending-строки и генерирует видео.
        """
        sheets_id = os.getenv('GOOGLE_SHEETS_ID', '')
        assert sheets_id, "GOOGLE_SHEETS_ID не установлен в .env"
        assert sheets_id != '...', (
            "GOOGLE_SHEETS_ID содержит заглушку — "
            "укажи реальный ID из URL таблицы: /spreadsheets/d/<ID>/"
        )

    def test_morelogin_credentials_exist(self):
        """MoreLogin credentials установлены"""
        assert os.getenv('MORELOGIN_API_KEY', ''), "MORELOGIN_API_KEY не установлен"
        assert os.getenv('MORELOGIN_APP_ID', ''), "MORELOGIN_APP_ID не установлен"
        assert os.getenv('MORELOGIN_APP_SECRET', ''), "MORELOGIN_APP_SECRET не установлен"

    def test_telegram_configured(self):
        """Telegram bot token и chat_id установлены"""
        assert os.getenv('TELEGRAM_BOT_TOKEN', ''), "TELEGRAM_BOT_TOKEN не установлен"
        assert os.getenv('TELEGRAM_CHAT_ID', ''), "TELEGRAM_CHAT_ID не установлен"


class TestPhase11ClientInit:
    """Фаза 1.1: Проверяем, что клиенты инициализируются из ключей"""

    def test_nano_banana_client_init(self):
        """Nano Banana клиент инициализируется с API ключом"""
        from nano_banana_client import NanoBananaClient
        key = os.getenv('NANO_BANANA_API_KEY', 'test_key_placeholder')
        client = NanoBananaClient(api_key=key)
        assert client.api_key == key, "NanoBananaClient не сохранил api_key"

    def test_kling_client_init(self):
        """Kling AI клиент инициализируется с API ключом"""
        from kling_client import KlingAIClient
        key = os.getenv('KLING_API_KEY', 'test_key_placeholder')
        client = KlingAIClient(api_key=key)
        assert client.api_key == key, "KlingAIClient не сохранил api_key"

    def test_google_drive_client_init(self):
        """Google Drive клиент инициализируется"""
        from google_drive_client import GoogleDriveClient
        creds = os.getenv('GOOGLE_DRIVE_CREDENTIALS', '/tmp/fake_credentials.json')
        client = GoogleDriveClient(credentials_path=creds)
        assert client.credentials_path == creds, "GoogleDriveClient не сохранил credentials_path"

    def test_google_sheets_client_init(self):
        """Google Sheets клиент инициализируется"""
        from google_sheets_client import GoogleSheetsClient
        creds    = os.getenv('GOOGLE_DRIVE_CREDENTIALS', '/tmp/fake_creds.json')
        sheet_id = os.getenv('GOOGLE_SHEETS_ID', 'test_sheet_id')
        client   = GoogleSheetsClient(credentials_path=creds, spreadsheet_id=sheet_id)
        assert client.credentials_path == creds,    "GoogleSheetsClient не сохранил credentials_path"
        assert client.spreadsheet_id   == sheet_id, "GoogleSheetsClient не сохранил spreadsheet_id"

    def test_morelogin_client_init(self):
        """MoreLogin клиент инициализируется"""
        from morelogin_client import MoreLoginClient
        key = os.getenv('MORELOGIN_API_KEY', 'test_key_placeholder')
        client = MoreLoginClient(api_key=key)
        assert client.api_key == key, "MoreLoginClient не сохранил api_key"


class TestPhase11ProjectStructure:
    """Фаза 1.1: Проверяем, что структура проекта создана"""

    def test_scripts_dir_exists(self):
        """Папка scripts существует"""
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        assert scripts_dir.exists(), "Папка scripts не существует"

    def test_tests_dir_exists(self):
        """Папка tests существует"""
        tests_dir = Path(__file__).parent
        assert tests_dir.exists(), "Папка tests не существует"

    def test_data_dirs_exist(self):
        """Папки data/ существуют"""
        base = Path(__file__).parent.parent / 'data'
        for subdir in ['queue', 'sessions', 'logs', 'videos']:
            assert (base / subdir).exists(), f"Папка data/{subdir} не существует"

    def test_env_file_exists(self):
        """.env файл существует"""
        env_path = Path(__file__).parent.parent / '.env'
        assert env_path.exists(), ".env файл не существует — запусти setup.sh"

    def test_gitignore_excludes_env(self):
        """.gitignore содержит .env"""
        gitignore = Path(__file__).parent.parent / '.gitignore'
        assert gitignore.exists(), ".gitignore не существует"
        content = gitignore.read_text()
        assert '.env' in content, ".gitignore не исключает .env — это опасно!"
