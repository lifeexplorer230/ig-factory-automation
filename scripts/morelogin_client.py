"""
MoreLogin API Client — управление виртуальными Android-телефонами.
Документация: https://www.morelogin.com/docs/api
"""
import os
import hashlib
import hmac
import time
import logging
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)


class MoreLoginClient:
    """Клиент для MoreLogin API (виртуальные телефоны для Instagram)."""

    BASE_URL = "https://api.morelogin.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('MORELOGIN_API_KEY', '')
        self.app_id = os.getenv('MORELOGIN_APP_ID', '')
        self.app_secret = os.getenv('MORELOGIN_APP_SECRET', '')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def _get_headers(self) -> dict:
        """Генерирует авторизационные заголовки с подписью."""
        timestamp = str(int(time.time() * 1000))
        nonce = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        sign_str = f"{self.app_id}{timestamp}{nonce}{self.app_secret}"
        signature = hashlib.sha256(sign_str.encode()).hexdigest()
        return {
            'appId': self.app_id,
            'timestamp': timestamp,
            'nonce': nonce,
            'sign': signature,
        }

    def list_phones(self) -> List[dict]:
        """Возвращает список всех виртуальных телефонов."""
        headers = self._get_headers()
        response = self.session.post(
            f"{self.BASE_URL}/api/v1/device/list",
            headers=headers,
            json={'page': 1, 'pageSize': 100}
        )
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('list', [])

    def create_phone(self, name: str, proxy_id: Optional[str] = None) -> dict:
        """
        Создаёт новый виртуальный телефон.

        Args:
            name: Имя телефона (например, 'CP-1')
            proxy_id: ID прокси для привязки

        Returns:
            dict: Информация о созданном телефоне
        """
        headers = self._get_headers()
        payload = {
            'name': name,
            'osType': 2,  # Android
            'androidVersion': '13',
        }
        if proxy_id:
            payload['proxyId'] = proxy_id
        response = self.session.post(
            f"{self.BASE_URL}/api/v1/device/create",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Создан телефон '{name}': {result.get('data', {}).get('deviceId')}")
        return result.get('data', {})

    def list_proxies(self) -> List[dict]:
        """Возвращает список всех прокси."""
        headers = self._get_headers()
        response = self.session.post(
            f"{self.BASE_URL}/api/v1/proxy/list",
            headers=headers,
            json={'page': 1, 'pageSize': 100}
        )
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('list', [])

    def add_proxy(self, host: str, port: int, username: str, password: str,
                  proxy_type: str = 'socks5') -> dict:
        """Добавляет прокси в MoreLogin."""
        headers = self._get_headers()
        payload = {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'proxyType': proxy_type,
        }
        response = self.session.post(
            f"{self.BASE_URL}/api/v1/proxy/add",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json().get('data', {})

    def list_apps(self, device_id: str) -> List[dict]:
        """Возвращает список установленных приложений на телефоне."""
        headers = self._get_headers()
        response = self.session.post(
            f"{self.BASE_URL}/api/v1/device/apps",
            headers=headers,
            json={'deviceId': device_id}
        )
        response.raise_for_status()
        return response.json().get('data', {}).get('apps', [])

    def check_adb(self, device_id: str) -> dict:
        """Проверяет доступность ADB на телефоне."""
        headers = self._get_headers()
        response = self.session.post(
            f"{self.BASE_URL}/api/v1/device/adb/status",
            headers=headers,
            json={'deviceId': device_id}
        )
        response.raise_for_status()
        return response.json().get('data', {})
