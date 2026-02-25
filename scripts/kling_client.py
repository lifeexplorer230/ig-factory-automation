"""
Kling AI API Client — генерация видео из изображений модели.
Документация: https://klingai.com/docs/api
"""
import os
import time
import logging
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)


class KlingAIClient:
    """Клиент для Kling AI API (генерация видео из изображений)."""

    BASE_URL = "https://api.klingai.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('KLING_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        })

    def create_video(
        self,
        image_urls: List[str],
        reference_video_url: str,
        duration: int = 20,
        fps: int = 24,
    ) -> dict:
        """
        Создаёт видео из изображений модели.

        Args:
            image_urls: Список URL изображений (ракурсы модели)
            reference_video_url: URL референсного видео для стиля движения
            duration: Длительность видео в секундах (15-30)
            fps: FPS видео

        Returns:
            dict: {'status': 'processing', 'video_id': '...'}
        """
        payload = {
            'image_urls': image_urls,
            'reference_video_url': reference_video_url,
            'duration': duration,
            'fps': fps,
        }
        logger.info(f"Создаю видео из {len(image_urls)} изображений, {duration}s...")
        response = self.session.post(f"{self.BASE_URL}/videos", json=payload)
        response.raise_for_status()
        return response.json()

    def get_video_status(self, video_id: str) -> dict:
        """Проверяет статус генерации видео."""
        response = self.session.get(f"{self.BASE_URL}/videos/{video_id}")
        response.raise_for_status()
        return response.json()

    def wait_for_video(self, video_id: str, timeout: int = 600, poll_interval: int = 15) -> dict:
        """
        Ожидает завершения генерации видео.

        Args:
            video_id: ID видео
            timeout: Максимальное время ожидания (по умолчанию 10 минут)
            poll_interval: Интервал проверки в секундах

        Returns:
            dict: Финальный статус с URL видео
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_video_status(video_id)
            if status['status'] == 'completed':
                logger.info(f"Видео {video_id} готово: {status.get('video_url')}")
                return status
            elif status['status'] == 'failed':
                raise RuntimeError(f"Генерация видео провалилась: {status.get('error')}")
            logger.debug(f"Видео {video_id} ещё генерируется...")
            time.sleep(poll_interval)
        raise TimeoutError(f"Превышен таймаут ({timeout}s) ожидания видео {video_id}")
