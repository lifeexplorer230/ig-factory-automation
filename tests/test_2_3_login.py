"""
Фаза 2.3: Аккаунты залогинены в Instagram.
TDD тест — написан до реального логина.

Предусловия (из Фазы 2.2):
  - data/accounts/ содержит credentials
  - data/sessions/ ещё не заполнен (заполнится после логина)

Критерий завершения фазы:
  - Каждый аккаунт из data/accounts/ имеет соответствующий session-файл
  - Session-файл содержит logged_in=True
  - Не более 1 бана
"""
import json
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

ACCOUNTS_DIR = Path(__file__).parent.parent / 'data' / 'accounts'
SESSIONS_DIR = Path(__file__).parent.parent / 'data' / 'sessions'


def _load_accounts() -> list[dict]:
    """Загрузить все credentials-файлы."""
    if not ACCOUNTS_DIR.exists():
        return []
    result = []
    for f in ACCOUNTS_DIR.glob('*.json'):
        d = json.loads(f.read_text())
        d['_file'] = f.name
        result.append(d)
    return result


def _load_sessions() -> list[dict]:
    """Загрузить все session-файлы."""
    if not SESSIONS_DIR.exists():
        return []
    result = []
    for f in SESSIONS_DIR.glob('*.json'):
        d = json.loads(f.read_text())
        d['_file'] = f.name
        result.append(d)
    return result


# ── Блок 1: Предусловия ───────────────────────────────────────────────────────

class TestLoginPreconditions:
    """Credentials готовы для логина."""

    def test_accounts_dir_has_credentials(self):
        """data/accounts/ содержит минимум 1 credentials-файл."""
        accounts = _load_accounts()
        assert len(accounts) >= 1, (
            "Нет credentials-файлов. Сначала пройди Фазу 2.2."
        )

    @pytest.mark.skipif(not _load_accounts(), reason='Нет credentials')
    def test_credentials_have_username_and_password(self):
        """Каждый credentials-файл содержит username и password."""
        for acc in _load_accounts():
            assert acc.get('username'), f"username пустой в {acc['_file']}"
            assert acc.get('password'), f"password пустой в {acc['_file']}"


# ── Блок 2: Сессии после логина ───────────────────────────────────────────────

class TestSessionsAfterLogin:
    """После логина каждый аккаунт имеет session-файл."""

    def test_sessions_dir_exists(self):
        """data/sessions/ существует."""
        assert SESSIONS_DIR.exists(), (
            "Папка data/sessions не существует. "
            "Запусти ig-warmup.py или multi_account_publisher.py для логина."
        )

    def test_each_account_has_session(self):
        """Каждому credentials-файлу соответствует session-файл."""
        accounts  = _load_accounts()
        if not accounts:
            pytest.skip("Нет credentials-файлов")

        sessions   = _load_sessions()
        sess_users = {s.get('username') for s in sessions}

        missing = [
            acc['username']
            for acc in accounts
            if acc.get('username') and acc['username'] not in sess_users
        ]
        assert not missing, (
            f"Нет session-файлов для аккаунтов: {missing}. "
            "Запусти логин через ig-warmup.py."
        )

    def test_all_sessions_logged_in(self):
        """Все session-файлы содержат logged_in=True."""
        sessions = _load_sessions()
        if not sessions:
            pytest.fail(
                "Нет session-файлов. "
                "Запусти логин через ig-warmup.py."
            )
        for s in sessions:
            assert s.get('logged_in'), (
                f"Аккаунт {s.get('username', s['_file'])} не залогинен. "
                "Повтори логин через ig-warmup.py."
            )

    def test_session_has_phone_name(self):
        """Каждая сессия содержит название телефона (phone_name)."""
        sessions = _load_sessions()
        if not sessions:
            pytest.skip("Нет session-файлов")
        for s in sessions:
            assert s.get('phone_name'), (
                f"phone_name пустой в {s['_file']}. "
                "Добавь поле при создании сессии."
            )


# ── Блок 3: Безопасность ─────────────────────────────────────────────────────

class TestNoLoginBans:
    """Логин не привёл к банам."""

    def test_no_banned_accounts(self):
        """Ни один аккаунт не получил бан при логине."""
        sessions = _load_sessions()
        if not sessions:
            pytest.skip("Нет session-файлов")

        banned = [
            s.get('username', s['_file'])
            for s in sessions
            if s.get('status') == 'banned'
        ]
        assert not banned, (
            f"Забанены при логине: {banned}. "
            "Проверь прокси и не логинься в два аккаунта с одного IP."
        )

    def test_no_checkpoint_accounts(self):
        """Ни один аккаунт не попал на checkpoint (подтверждение личности)."""
        sessions = _load_sessions()
        if not sessions:
            pytest.skip("Нет session-файлов")

        checkpoints = [
            s.get('username', s['_file'])
            for s in sessions
            if s.get('status') == 'checkpoint'
        ]
        assert not checkpoints, (
            f"Checkpoint у аккаунтов: {checkpoints}. "
            "Пройди проверку вручную или замени аккаунт."
        )


# ── Блок 4: IgClient unit-тест логина (без реального устройства) ──────────────

class TestLoginLogic:
    """Unit-тесты логики логина в ig_client.py."""

    def test_ig_client_has_login_method(self):
        """InstagramClient содержит метод login."""
        pytest.importorskip('pyotp', reason='pip install pyotp')
        from ig_client import InstagramClient
        assert hasattr(InstagramClient, 'login'), (
            "Метод login отсутствует в InstagramClient"
        )

    def test_ig_client_has_on_home_method(self):
        """InstagramClient содержит _on_home для проверки главного экрана."""
        pytest.importorskip('pyotp', reason='pip install pyotp')
        from ig_client import InstagramClient
        assert hasattr(InstagramClient, '_on_home'), (
            "Метод _on_home отсутствует в InstagramClient"
        )

    def test_ig_client_has_enter_totp_method(self):
        """InstagramClient содержит _enter_totp для 2FA."""
        pytest.importorskip('pyotp', reason='pip install pyotp')
        from ig_client import InstagramClient
        assert hasattr(InstagramClient, '_enter_totp'), (
            "Метод _enter_totp отсутствует в InstagramClient"
        )
