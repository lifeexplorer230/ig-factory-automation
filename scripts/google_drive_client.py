"""
Google Drive Client — хранилище видео и очередь.
Использует Google Drive API v3.
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GoogleDriveClient:
    """Клиент для Google Drive (загрузка/скачивание видео и метаданных)."""

    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_DRIVE_CREDENTIALS', '')
        self._service = None
        self._folder_ids: dict = {}

    @property
    def drive(self):
        """Lazy-инициализация Google Drive service."""
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def _build_service(self):
        """Создаёт Google Drive API service из credentials."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            scopes = ['https://www.googleapis.com/auth/drive']
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
            return build('drive', 'v3', credentials=creds)
        except ImportError:
            logger.warning("google-api-python-client не установлен. Используй: pip install google-api-python-client google-auth")
            return None
        except Exception as e:
            logger.error(f"Не удалось инициализировать Google Drive: {e}")
            return None

    def upload_file(self, local_path: str, folder_id: str, mime_type: str = 'video/mp4') -> dict:
        """
        Загружает файл в Google Drive.

        Args:
            local_path: Локальный путь к файлу
            folder_id: ID папки в Google Drive
            mime_type: MIME тип файла

        Returns:
            dict: {'id': '...', 'name': '...', 'webViewLink': '...'}
        """
        from googleapiclient.http import MediaFileUpload

        file_name = Path(local_path).name
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(local_path, mimetype=mime_type)

        file = self.drive.files().create(
            body=file_metadata, media_body=media, fields='id,name,webViewLink'
        ).execute()
        logger.info(f"Загружен файл: {file_name} → {file['webViewLink']}")
        return file

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Создаёт папку в Google Drive, возвращает её ID."""
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        if parent_id:
            metadata['parents'] = [parent_id]
        folder = self.drive.files().create(body=metadata, fields='id').execute()
        logger.info(f"Создана папка '{name}': {folder['id']}")
        return folder['id']

    def list_files(self, folder_id: str) -> list:
        """Возвращает список файлов в папке."""
        results = self.drive.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields='files(id,name,webViewLink,createdTime)',
        ).execute()
        return results.get('files', [])

    def setup_project_structure(self) -> dict:
        """
        Создаёт структуру папок проекта в Google Drive.

        Returns:
            dict: {'donors': '...', 'references': '...', 'models': '...', 'videos': '...', 'queue': '...'}
        """
        root_id = self.create_folder('ig-factory-automation')
        folders = {}
        for name in ['donors', 'references', 'models', 'videos', 'queue']:
            folders[name] = self.create_folder(name, parent_id=root_id)
        logger.info(f"Структура Google Drive создана: {folders}")
        return folders
