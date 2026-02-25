"""
MoreLogin Cloud API Client.

ВАЖНЫЕ ОТКРЫТИЯ (добыты через отладку 24.02.2026):

1. client_id в /oauth2/token — ОБЯЗАТЕЛЬНО INTEGER, не строка!
   Иначе: {"code": 1001, "msg": "invalid client_id"}

2. Пути БЕЗ /api/ префикса:
   ✅ /cloudphone/page
   ❌ /api/cloudphone/page

3. proxyInfo/delete принимает RAW JSON array integers: [id1, id2]
   Не объект {"ids": [...]}, а именно голый массив!

4. app/install требует appVersionId (не packageName!)
   appVersionId ищется через /cloudphone/app/page с appName в теле.
   Без appName в теле возвращает только 10 дефолтных приложений.

5. Прокси ОБЯЗАТЕЛЬНО с proxyProvider:0
   Для SOCKS5: proxyType:2 — credentials (user/pass) сохраняются.

6. envStatus значения:
   0=New, 1=Failed, 2=Stop, 3=Starting, 4=Running, 5=Resetting

7. ADB keeper-сессия:
   adb shell <password> — открывает интерактивный shell (пароль = auth).
   Обычный adb shell cmd → "error: closed" без открытой keeper-сессии.
   Пока keeper жив — параллельные adb shell команды работают нормально.

8. Instagram v412.0.0.35.87:
   appVersionId = '1682134957917431'
   package     = 'com.instagram.android'
   skuId для телефона = '10004'
"""
import os
import time
import json
import logging
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)


class MoreLoginClient:
    """Клиент для MoreLogin Cloud API (виртуальные Android-телефоны)."""

    BASE_URL = 'https://api.morelogin.com'

    # Версия Instagram, проверенная в работе
    INSTAGRAM_VERSION_ID = '1682134957917431'
    INSTAGRAM_PACKAGE    = 'com.instagram.android'
    PHONE_SKU_ID         = '10004'

    def __init__(self, api_key: Optional[str] = None):
        # api_key здесь не используется для аутентификации —
        # MoreLogin использует OAuth2 client_credentials (appId + appSecret).
        # Поле оставлено для совместимости с интерфейсом других клиентов.
        self.api_key    = api_key or os.getenv('MORELOGIN_API_KEY', '')
        self.app_id     = int(os.getenv('MORELOGIN_APP_ID', '0'))   # ОБЯЗАТЕЛЬНО int!
        self.app_secret = os.getenv('MORELOGIN_APP_SECRET', '')
        self._token: Optional[str] = None
        self._token_exp: float = 0.0

    # ── Auth ─────────────────────────────────────────────────────────────────

    def _get_token(self) -> str:
        """OAuth2 client_credentials. Кешируется на 3500 секунд."""
        if self._token and time.time() < self._token_exp:
            return self._token

        body = json.dumps({
            'grant_type':    'client_credentials',
            'client_id':     self.app_id,      # ← ВАЖНО: int, не строка!
            'client_secret': self.app_secret,
        }).encode()
        req = urllib.request.Request(
            f'{self.BASE_URL}/oauth2/token', data=body,
            headers={'Content-Type': 'application/json'}, method='POST',
        )
        data = json.loads(urllib.request.urlopen(req).read())
        if data.get('code') != 0:
            raise RuntimeError(f"MoreLogin auth failed: code={data.get('code')} msg={data.get('msg')}")
        self._token     = data['data']['access_token']
        self._token_exp = time.time() + 3500
        return self._token

    def _post(self, path: str, body) -> dict:
        """POST к MoreLogin API. path — без /api/ префикса!"""
        token = self._get_token()
        raw   = json.dumps(body).encode()
        req   = urllib.request.Request(
            f'{self.BASE_URL}{path}', data=raw,
            headers={
                'Content-Type':  'application/json',
                'Authorization': f'Bearer {token}',
            },
            method='POST',
        )
        return json.loads(urllib.request.urlopen(req).read())

    # ── Proxies ───────────────────────────────────────────────────────────────

    def list_proxies(self) -> list:
        """Список всех прокси в аккаунте."""
        r = self._post('/proxyInfo/page', {'current': 1, 'size': 100})
        return r.get('data', {}).get('dataList', [])

    def add_proxy(self, name: str, ip: str, port: int,
                  username: str, password: str) -> int:
        """
        Добавить SOCKS5 прокси. Возвращает ID созданной прокси.
        proxyProvider:0 ОБЯЗАТЕЛЕН — иначе credentials не сохраняются.
        """
        r = self._post('/proxyInfo/add', {
            'proxyName':         name,
            'proxyCategoryType': 2,
            'proxyProvider':     0,    # ← ОБЯЗАТЕЛЬНО!
            'proxyType':         2,    # 2 = SOCKS5
            'proxyIp':           ip,
            'proxyPort':         port,
            'username':          username,
            'password':          password,
        })
        if r.get('code') != 0:
            raise RuntimeError(f"add_proxy failed: {r.get('msg')}")
        logger.info(f"Прокси добавлена: {ip}:{port} → ID {r['data']}")
        return r['data']

    def delete_proxies(self, ids: list) -> bool:
        """
        Удалить прокси по ID.
        ВАЖНО: тело запроса — голый JSON array integers, не объект!
        ✅ [123, 456]
        ❌ {"ids": [123, 456]}
        """
        r = self._post('/proxyInfo/delete', [int(i) for i in ids])
        return r.get('code') == 0

    # ── Cloud Phones ──────────────────────────────────────────────────────────

    def list_phones(self) -> list:
        """Список всех виртуальных телефонов."""
        r = self._post('/cloudphone/page', {'current': 1, 'size': 100})
        return r.get('data', {}).get('dataList', [])

    def create_phone(self, name: str, proxy_id: int) -> int:
        """
        Создать виртуальный телефон и сразу включить ADB.
        Возвращает phone_id (int).
        """
        r = self._post('/cloudphone/create', {
            'envName':  name,
            'quantity': 1,
            'skuId':    self.PHONE_SKU_ID,
            'proxyId':  str(proxy_id),
        })
        if r.get('code') != 0:
            raise RuntimeError(f"create_phone failed: {r.get('msg')}")
        phone_id = int(r['data'][0])

        # Сразу включаем ADB — без этого keeper не заработает
        self._post('/cloudphone/updateAdb', {
            'ids':       [phone_id],
            'enableAdb': True,
        })
        logger.info(f"Телефон создан: {name} → ID {phone_id}")
        return phone_id

    def power_on(self, phone_id: int) -> None:
        r = self._post('/cloudphone/powerOn', {'id': phone_id})
        if r.get('code') != 0:
            raise RuntimeError(f"powerOn failed: {r.get('msg')}")

    def power_off(self, phone_id: int) -> None:
        self._post('/cloudphone/powerOff', {'id': phone_id})

    def wait_running(self, phone_id: int, timeout: int = 120) -> dict:
        """
        Ждёт пока телефон перейдёт в envStatus=4 (Running).
        Возвращает adbInfo = {'adbIp': ..., 'adbPort': ..., 'adbPassword': ...}

        envStatus: 0=New 1=Failed 2=Stop 3=Starting 4=Running 5=Resetting
        """
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(5)
            phones = self.list_phones()
            phone  = next((p for p in phones if int(p['id']) == phone_id), None)
            if not phone:
                raise RuntimeError(f"Телефон {phone_id} исчез из списка")
            status = phone.get('envStatus', 0)
            adb    = phone.get('adbInfo') or {}
            logger.debug(f"phone {phone_id} envStatus={status}")
            if status == 4 and adb.get('adbIp'):
                return adb
            if status in (1, 2) and time.time() - start > 15:
                raise RuntimeError(f"Телефон упал (envStatus={status})")
        raise TimeoutError(f"Телефон {phone_id} не запустился за {timeout}с")

    def delete_phones(self, ids: list) -> bool:
        r = self._post('/cloudphone/delete/batch', {'ids': [str(i) for i in ids]})
        return r.get('code') == 0

    # ── Apps ──────────────────────────────────────────────────────────────────

    def find_app_version_id(self, phone_id: int, app_name: str) -> dict:
        """
        Найти appVersionId для установки.
        ВАЖНО: appName ОБЯЗАТЕЛЕН в теле — без него вернёт только 10 дефолтных.
        Возвращает {'appVersionId': ..., 'packageName': ...}
        """
        r = self._post('/cloudphone/app/page', {
            'id':      phone_id,
            'appName': app_name,    # ← ОБЯЗАТЕЛЕН!
            'current': 1,
            'size':    5,
        })
        apps = r.get('data', {}).get('dataList', [])
        if not apps:
            raise RuntimeError(f"Приложение '{app_name}' не найдено в каталоге")
        app     = apps[0]
        version = app['appVersionList'][0]
        return {'appVersionId': version['id'], 'packageName': app['packageName']}

    def install_app(self, phone_id: int, app_version_id: str) -> None:
        """
        Установить приложение.
        ВАЖНО: передаём appVersionId (не packageName!).
        """
        r = self._post('/cloudphone/app/install', {
            'id':           phone_id,
            'appVersionId': str(app_version_id),   # ← appVersionId, не packageName!
        })
        if r.get('code') != 0:
            raise RuntimeError(f"install_app failed: {r.get('msg')}")

    def list_installed_apps(self, phone_id: int) -> list:
        r = self._post('/cloudphone/app/installedList', {'id': phone_id})
        return r.get('data', [])

    def start_app(self, phone_id: int, package_name: str) -> None:
        r = self._post('/cloudphone/app/start', {
            'id':          phone_id,
            'packageName': package_name,
        })
        if r.get('code') != 0:
            raise RuntimeError(f"start_app failed: {r.get('msg')}")

    # ── Convenience ───────────────────────────────────────────────────────────

    def get_or_start_phone(self, phone_name: str,
                           proxy_id: Optional[int] = None) -> tuple:
        """
        Найти телефон по имени, запустить если не запущен.
        Возвращает (phone_id, adb_info).
        Создаёт новый если не найден (нужен proxy_id).
        """
        phones = self.list_phones()
        phone  = next((p for p in phones if p['envName'] == phone_name), None)

        if not phone:
            if not proxy_id:
                raise RuntimeError(f"Телефон '{phone_name}' не найден и proxy_id не задан")
            phone_id = self.create_phone(phone_name, proxy_id)
            self.power_on(phone_id)
            adb = self.wait_running(phone_id)
            return phone_id, adb

        phone_id = int(phone['id'])
        if phone['envStatus'] == 4:
            adb = phone.get('adbInfo') or {}
            if adb.get('adbIp'):
                return phone_id, adb
        self.power_on(phone_id)
        adb = self.wait_running(phone_id)
        return phone_id, adb
