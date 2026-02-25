"""
Nano Banana API Client — генерация моделей для одежды.
Документация: https://nanobanana.ai/docs/api
"""
import os
import time
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class NanoBananaClient:
    """Клиент для Nano Banana API (генерация виртуальных моделей)."""

    BASE_URL = "https://api.nanobanana.ai/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('NANO_BANANA_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        })

    def generate_model(
        self,
        prompt: str,
        reference_image_url: str,
        clothing_image_url: str,
        num_angles: int = 5,
    ) -> dict:
        """
        Генерирует виртуальную модель в нескольких ракурсах.

        Args:
            prompt: Описание модели (например, "Красивая женщина, 25 лет")
            reference_image_url: URL референсного изображения лица/тела
            clothing_image_url: URL изображения одежды
            num_angles: Количество ракурсов (по умолчанию 5)

        Returns:
            dict: {'status': 'completed', 'model_id': '...', 'images': [...]}
        """
        payload = {
            'prompt': prompt,
            'reference_image_url': reference_image_url,
            'clothing_image_url': clothing_image_url,
            'num_angles': num_angles,
        }
        logger.info(f"Генерирую модель: {prompt[:50]}...")
        response = self.session.post(f"{self.BASE_URL}/generate", json=payload)
        response.raise_for_status()
        return response.json()

    def get_model_status(self, model_id: str) -> dict:
        """Проверяет статус генерации модели."""
        response = self.session.get(f"{self.BASE_URL}/models/{model_id}")
        response.raise_for_status()
        return response.json()

    def wait_for_model(self, model_id: str, timeout: int = 300, poll_interval: int = 10) -> dict:
        """
        Ожидает завершения генерации модели.

        Args:
            model_id: ID модели
            timeout: Максимальное время ожидания в секундах
            poll_interval: Интервал проверки в секундах

        Returns:
            dict: Финальный статус модели
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_model_status(model_id)
            if status['status'] == 'completed':
                logger.info(f"Модель {model_id} сгенерирована")
                return status
            elif status['status'] == 'failed':
                raise RuntimeError(f"Генерация модели провалилась: {status.get('error')}")
            logger.debug(f"Модель {model_id} ещё генерируется...")
            time.sleep(poll_interval)
        raise TimeoutError(f"Превышен таймаут ({timeout}s) ожидания модели {model_id}")
