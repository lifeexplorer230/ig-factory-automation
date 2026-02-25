"""
Фаза 2.2: Аккаунты куплены и credentials готовы.
TDD тест — написан до реальных аккаунтов.

Критерий завершения фазы:
  - Есть папка data/accounts/ с JSON-файлами
  - Каждый файл содержит username, password, totp_secret
  - Минимум 5 аккаунтов
  - Нет дубликатов username
"""
import json
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

ACCOUNTS_DIR = Path(__file__).parent.parent / 'data' / 'accounts'
MIN_ACCOUNTS  = 10  # 10 моделей на старте


# ── Блок 1: Файлы credentials ─────────────────────────────────────────────────

class TestAccountCredentials:
    """Credentials аккаунтов существуют и заполнены."""

    def test_accounts_dir_exists(self):
        """Папка data/accounts существует."""
        assert ACCOUNTS_DIR.exists(), (
            f"Папка {ACCOUNTS_DIR} не существует. "
            "Создай папку и добавь JSON-файлы с credentials каждого аккаунта."
        )

    def test_at_least_one_account(self):
        """Есть хотя бы один файл с credentials."""
        if not ACCOUNTS_DIR.exists():
            pytest.fail(f"Папка {ACCOUNTS_DIR} не существует")
        files = list(ACCOUNTS_DIR.glob('*.json'))
        assert len(files) >= 1, (
            f"В {ACCOUNTS_DIR} нет файлов. "
            "Добавь JSON с credentials: username, password, totp_secret."
        )

    def test_minimum_5_accounts(self):
        """Минимум 5 аккаунтов (критерий Фазы 2.2)."""
        if not ACCOUNTS_DIR.exists():
            pytest.fail(f"Папка {ACCOUNTS_DIR} не существует")
        files = list(ACCOUNTS_DIR.glob('*.json'))
        assert len(files) >= MIN_ACCOUNTS, (
            f"Найдено {len(files)} аккаунтов, нужно >= {MIN_ACCOUNTS}. "
            "Купи аккаунты и добавь их credentials."
        )

    @pytest.mark.skipif(
        not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.glob('*.json')),
        reason='Нет файлов credentials'
    )
    def test_accounts_have_required_fields(self):
        """Каждый файл содержит обязательные поля.

        Схема аккаунта:
          username        — логин Instagram
          password        — пароль
          totp_secret     — TOTP секрет для 2FA (может быть пустым если нет 2FA)
          model_photo_url — URL фото модели (лицо + тело, уникально для аккаунта)

        ВАЖНО: каждый аккаунт = отдельная AI-модель.
        model_photo_url — единственное что уникально между аккаунтами.
        Одежда, фон, исходное видео — общие для всех.
        """
        required = ['username', 'password', 'model_photo_url']
        for f in ACCOUNTS_DIR.glob('*.json'):
            data = json.loads(f.read_text())
            for field in required:
                assert field in data, (
                    f"Поле '{field}' отсутствует в {f.name}"
                )

    @pytest.mark.skipif(
        not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.glob('*.json')),
        reason='Нет файлов credentials'
    )
    def test_no_empty_credentials(self):
        """Credentials не пустые."""
        for f in ACCOUNTS_DIR.glob('*.json'):
            data = json.loads(f.read_text())
            assert data.get('username'), f"username пустой в {f.name}"
            assert data.get('password'), f"password пустой в {f.name}"
            # totp_secret опциональный — не у всех аккаунтов есть 2FA

    @pytest.mark.skipif(
        not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.glob('*.json')),
        reason='Нет файлов credentials'
    )
    def test_no_duplicate_usernames(self):
        """Нет дубликатов username."""
        usernames = []
        for f in ACCOUNTS_DIR.glob('*.json'):
            data = json.loads(f.read_text())
            u = data.get('username', '')
            if u:
                usernames.append(u)
        assert len(usernames) == len(set(usernames)), (
            f"Найдены дубликаты username: "
            f"{[u for u in usernames if usernames.count(u) > 1]}"
        )

    @pytest.mark.skipif(
        not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.glob('*.json')),
        reason='Нет файлов credentials'
    )
    def test_each_account_has_unique_model(self):
        """Каждый аккаунт использует уникальное фото модели.

        Архитектурное правило: 1 аккаунт = 1 модель (уникальное лицо + тело).
        Одна модель не может публиковаться в двух Instagram-аккаунтах одновременно.
        """
        model_photos = []
        for f in ACCOUNTS_DIR.glob('*.json'):
            data  = json.loads(f.read_text())
            photo = data.get('model_photo_url', '')
            if photo:
                model_photos.append((photo, f.name))

        urls    = [p for p, _ in model_photos]
        dupes   = [p for p in urls if urls.count(p) > 1]
        if dupes:
            files = [fname for p, fname in model_photos if p in dupes]
            pytest.fail(
                f"Одно фото модели используется в нескольких аккаунтах: {files}. "
                "Каждый аккаунт должен иметь уникальную модель."
            )


# ── Блок 2: Формат credentials ────────────────────────────────────────────────

class TestCredentialsFormat:
    """Credentials в правильном формате."""

    @pytest.mark.skipif(
        not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.glob('*.json')),
        reason='Нет файлов credentials'
    )
    def test_username_format(self):
        """Username в правильном формате (lowercase, без @)."""
        for f in ACCOUNTS_DIR.glob('*.json'):
            data = json.loads(f.read_text())
            u = data.get('username', '')
            if not u:
                continue
            assert '@' not in u, (
                f"username '{u}' содержит @. "
                "Используй только имя без @."
            )
            assert ' ' not in u, (
                f"username '{u}' содержит пробел."
            )

    @pytest.mark.skipif(
        not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.glob('*.json')),
        reason='Нет файлов credentials'
    )
    def test_totp_secret_format(self):
        """TOTP secret — base32-строка (если задан)."""
        import base64
        for f in ACCOUNTS_DIR.glob('*.json'):
            data  = json.loads(f.read_text())
            totp  = data.get('totp_secret', '')
            if not totp:
                continue
            # base32: буквы A-Z, цифры 2-7, без пробелов
            clean = totp.replace(' ', '').upper()
            try:
                base64.b32decode(clean + '=' * (-len(clean) % 8))
            except Exception:
                pytest.fail(
                    f"totp_secret в {f.name} не является валидным base32: '{totp}'"
                )


# ── Блок 3: Соответствие сессиям ─────────────────────────────────────────────

class TestAccountsMatchSessions:
    """Если сессии уже созданы — они соответствуют credentials."""

    SESSIONS_DIR = Path(__file__).parent.parent / 'data' / 'sessions'

    @pytest.mark.skipif(
        not ACCOUNTS_DIR.exists() or not any(ACCOUNTS_DIR.glob('*.json')),
        reason='Нет файлов credentials'
    )
    def test_session_usernames_match_credentials(self):
        """Каждая сессия ссылается на существующий credentials-файл."""
        if not self.SESSIONS_DIR.exists():
            pytest.skip("Сессий ещё нет — это нормально на Фазе 2.2")

        account_usernames = set()
        for f in ACCOUNTS_DIR.glob('*.json'):
            data = json.loads(f.read_text())
            u = data.get('username', '')
            if u:
                account_usernames.add(u)

        for sf in self.SESSIONS_DIR.glob('*.json'):
            data = json.loads(sf.read_text())
            u    = data.get('username', '')
            if not u:
                continue
            assert u in account_usernames, (
                f"Сессия {sf.name} содержит username '{u}', "
                f"но такого credentials-файла нет в {ACCOUNTS_DIR}."
            )
