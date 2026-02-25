"""
Google Sheets Client — чтение заданий для контент-пайплайна.

Фаза 1.1. Нужны GOOGLE_DRIVE_CREDENTIALS (сервисный аккаунт) и GOOGLE_SHEETS_ID.

Структура таблицы заданий (Google Sheets):
  Колонки:
    account            — username Instagram-аккаунта (например brand_anna)
    clothing_drive_id  — ID файла одежды в Google Drive
    source_video_drive_id — ID исходного видео в Google Drive (движение + аудио)
    status             — pending / processing / done / error
    video_id           — заполняется после генерации
    error              — текст ошибки если status=error

  Пример строки:
    brand_anna | 1abc2XYZ... | 3def4UVW... | pending | |

Оператор добавляет строки в таблицу.
content_pipeline.py читает pending-строки и обрабатывает их.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Ожидаемые колонки таблицы заданий
TASK_COLUMNS = [
    'account',
    'clothing_drive_id',
    'source_video_drive_id',
    'status',
    'video_id',
    'error',
]


class GoogleSheetsClient:
    """Клиент для чтения заданий из Google Sheets."""

    def __init__(self,
                 credentials_path: Optional[str] = None,
                 spreadsheet_id: Optional[str] = None):
        self.credentials_path = (
            credentials_path or
            os.getenv('GOOGLE_DRIVE_CREDENTIALS', '')
        )
        self.spreadsheet_id = (
            spreadsheet_id or
            os.getenv('GOOGLE_SHEETS_ID', '')
        )
        self._service = None

    def _get_service(self):
        """Получить или создать Google Sheets API service."""
        if self._service:
            return self._service

        if not self.credentials_path:
            raise RuntimeError(
                'GOOGLE_DRIVE_CREDENTIALS не задан в .env — '
                'нужен путь к credentials.json сервисного аккаунта'
            )
        if not self.spreadsheet_id:
            raise RuntimeError(
                'GOOGLE_SHEETS_ID не задан в .env — '
                'нужен ID таблицы заданий от Сергея'
            )

        # TODO: реализовать после получения credentials от Сергея
        # from google.oauth2.service_account import Credentials
        # from googleapiclient.discovery import build
        # creds = Credentials.from_service_account_file(
        #     self.credentials_path,
        #     scopes=['https://www.googleapis.com/auth/spreadsheets']
        # )
        # self._service = build('sheets', 'v4', credentials=creds)
        raise NotImplementedError(
            'GoogleSheetsClient не реализован — ждём credentials от Сергея'
        )

    def get_pending_tasks(self) -> list[dict]:
        """
        Вернуть список заданий со статусом 'pending'.

        Returns:
            list[dict]: Каждый элемент содержит:
                account              — username аккаунта
                clothing_drive_id    — ID файла одежды в Drive
                source_video_drive_id — ID исходного видео в Drive
                row_index            — номер строки (для обновления статуса)
        """
        service = self._get_service()
        # TODO: реализовать после получения credentials
        raise NotImplementedError

    def update_task_status(self, row_index: int, status: str,
                           video_id: str = '', error: str = '') -> None:
        """
        Обновить статус задания в таблице.

        Args:
            row_index: Номер строки (от 2, т.к. 1 = заголовок)
            status:    'processing' / 'done' / 'error'
            video_id:  ID сгенерированного видео (для статуса 'done')
            error:     Текст ошибки (для статуса 'error')
        """
        service = self._get_service()
        # TODO: реализовать после получения credentials
        raise NotImplementedError

    def validate_sheet_structure(self) -> bool:
        """
        Проверить что таблица имеет правильные колонки.

        Returns:
            True если структура корректная.

        Raises:
            RuntimeError если колонки не совпадают.
        """
        service = self._get_service()
        # TODO: реализовать после получения credentials
        raise NotImplementedError
