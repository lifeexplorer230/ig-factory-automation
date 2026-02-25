"""
Фаза 2.1: Проверяем инфраструктуру MoreLogin Cloud.
TDD: тест написан на основе реальной отладки 24.02.2026.

Критерий завершения фазы:
  - MoreLogin API доступен (токен получен)
  - Минимум 1 телефон существует
  - Минимум 1 прокси существует
  - На активном телефоне Instagram установлен
"""
import os
import sys
import json
import subprocess
import time
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


@pytest.fixture(scope='module')
def client():
    from morelogin_client import MoreLoginClient
    return MoreLoginClient()


@pytest.fixture(scope='module')
def phones(client):
    return client.list_phones()


@pytest.fixture(scope='module')
def proxies(client):
    return client.list_proxies()


# ── Блок 1: Авторизация ───────────────────────────────────────────────────────

class TestMoreLoginAuth:
    """MoreLogin API доступен и авторизация работает."""

    def test_credentials_in_env(self):
        """APP_ID и APP_SECRET заполнены в .env (не заглушки)."""
        app_id     = os.getenv('MORELOGIN_APP_ID', '')
        app_secret = os.getenv('MORELOGIN_APP_SECRET', '')
        assert app_id,                      "MORELOGIN_APP_ID не задан в .env"
        assert app_secret,                  "MORELOGIN_APP_SECRET не задан в .env"
        assert app_secret != '...',         "MORELOGIN_APP_SECRET содержит заглушку"
        assert app_id.isdigit(),            "MORELOGIN_APP_ID должен быть числом (integer!)"

    def test_token_obtained(self, client):
        """OAuth2 токен успешно получен."""
        token = client._get_token()
        assert token,              "Токен пустой"
        assert len(token) > 20,   "Токен слишком короткий — возможно невалидный"

    def test_token_is_cached(self, client):
        """Повторный вызов возвращает тот же токен (кеш работает)."""
        t1 = client._get_token()
        t2 = client._get_token()
        assert t1 == t2, "Токен не кешируется — каждый раз новый запрос к API"


# ── Блок 2: Телефоны ──────────────────────────────────────────────────────────

class TestPhonesExist:
    """Виртуальные телефоны созданы в аккаунте."""

    def test_at_least_one_phone(self, phones):
        """В аккаунте есть минимум 1 телефон."""
        assert len(phones) >= 1, (
            f"Телефонов нет. Создай хотя бы один через morelogin_client.create_phone()"
        )

    def test_phones_have_required_fields(self, phones):
        """У каждого телефона есть обязательные поля."""
        required = ['id', 'envName', 'envStatus']
        for p in phones:
            for field in required:
                assert field in p, f"Поле '{field}' отсутствует у телефона {p.get('id')}"

    def test_known_phones_present(self, phones):
        """CP-6 существует (создан 24.02.2026)."""
        names = [p['envName'] for p in phones]
        assert 'CP-6' in names, (
            f"CP-6 не найден. Есть: {names}"
        )

    def test_env_status_values_are_valid(self, phones):
        """envStatus у всех телефонов — известное значение (0-5)."""
        valid = {0, 1, 2, 3, 4, 5}
        for p in phones:
            st = p.get('envStatus')
            assert st in valid, (
                f"Телефон {p['envName']}: неизвестный envStatus={st}. "
                f"Ожидаемые: 0=New 1=Failed 2=Stop 3=Starting 4=Running 5=Resetting"
            )


# ── Блок 3: Прокси ────────────────────────────────────────────────────────────

class TestProxiesExist:
    """Прокси настроены в аккаунте."""

    def test_at_least_one_proxy(self, proxies):
        """В аккаунте есть минимум 1 прокси."""
        assert len(proxies) >= 1, (
            "Прокси нет. Добавь через morelogin_client.add_proxy() "
            "или через UI MoreLogin (с proxyProvider=0!)"
        )

    def test_proxies_have_required_fields(self, proxies):
        """У каждой прокси есть обязательные поля."""
        for pr in proxies:
            assert 'id'        in pr, f"Поле 'id' отсутствует у прокси {pr}"
            assert 'proxyName' in pr, f"Поле 'proxyName' отсутствует у прокси {pr}"


# ── Блок 4: Instagram на телефонах ───────────────────────────────────────────

class TestInstagramInstalled:
    """
    Проверяем Instagram через ADB на ЗАПУЩЕННОМ телефоне.

    ВАЖНО: тест пропускается если ни один телефон не запущен (Running).
    Запустить телефон: client.power_on(phone_id) + client.wait_running(phone_id)
    """

    @pytest.fixture(scope='class')
    def running_phone(self, phones):
        """Возвращает первый Running телефон или пропускает тест."""
        running = [p for p in phones if p.get('envStatus') == 4]
        if not running:
            pytest.skip(
                "Нет запущенных телефонов (envStatus=4). "
                "Запусти телефон перед тестом: client.power_on(phone_id)"
            )
        p   = running[0]
        adb = p.get('adbInfo') or {}
        if not adb.get('adbIp'):
            pytest.skip(f"Телефон {p['envName']} Running но adbInfo пустой")
        return p

    def test_adb_connects(self, running_phone):
        """ADB успешно подключается к телефону."""
        adb  = running_phone['adbInfo']
        addr = f"{adb['adbIp']}:{adb['adbPort']}"
        subprocess.run(['adb', 'disconnect'], capture_output=True)
        time.sleep(0.3)
        r = subprocess.run(['adb', 'connect', addr], capture_output=True, text=True)
        assert 'connected' in r.stdout.lower(), (
            f"ADB не подключился к {addr}: {r.stdout} {r.stderr}"
        )

    def test_adb_keeper_works(self, running_phone):
        """ADB keeper-сессия работает — команды выполняются."""
        adb  = running_phone['adbInfo']
        addr = f"{adb['adbIp']}:{adb['adbPort']}"

        keeper = subprocess.Popen(
            ['adb', '-s', addr, 'shell', adb['adbPassword']],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        keeper.stdin.write(b'sleep 30\n')
        keeper.stdin.flush()
        time.sleep(1.5)

        r = subprocess.run(
            ['adb', '-s', addr, 'shell', 'echo', 'keeper_ok'],
            capture_output=True, text=True, timeout=5,
        )
        keeper.kill()
        assert 'keeper_ok' in r.stdout, (
            f"ADB keeper не работает: {r.stderr}. "
            "Проверь adbPassword и что ADB включён (updateAdb enableAdb=true)"
        )

    def test_instagram_installed(self, running_phone):
        """Instagram установлен на телефоне."""
        adb  = running_phone['adbInfo']
        addr = f"{adb['adbIp']}:{adb['adbPort']}"
        r    = subprocess.run(
            ['adb', '-s', addr, 'shell', 'pm list packages | grep instagram'],
            capture_output=True, text=True, timeout=10,
        )
        assert 'com.instagram.android' in r.stdout, (
            f"Instagram не установлен на {running_phone['envName']}. "
            "Установи через morelogin_client.install_app() с appVersionId=1682134957917431"
        )

    def test_instagram_account_logged_in(self, running_phone):
        """Аккаунт залогинен в Instagram (виден tab_bar / bottom_tray)."""
        adb  = running_phone['adbInfo']
        addr = f"{adb['adbIp']}:{adb['adbPort']}"

        subprocess.run(
            ['adb', '-s', addr, 'shell', 'monkey -p com.instagram.android 1'],
            capture_output=True, timeout=10,
        )
        time.sleep(5)
        subprocess.run(
            ['adb', '-s', addr, 'shell', 'uiautomator dump /sdcard/_ui.xml'],
            capture_output=True, timeout=15,
        )
        subprocess.run(
            ['adb', '-s', addr, 'pull', '/sdcard/_ui.xml', '/tmp/_ig_test_ui.xml'],
            capture_output=True,
        )
        xml = Path('/tmp/_ig_test_ui.xml').read_text(errors='ignore')

        assert 'tab_bar' in xml or 'bottom_tray' in xml, (
            "Аккаунт не залогинен — нет tab_bar/bottom_tray на экране. "
            "Запусти ig-warmup.py для логина."
        )
