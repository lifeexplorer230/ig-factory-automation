"""
Фаза 1.2: Генерация одного видео (первый прогон контент-пайплайна).
TDD тест — написан до реальной интеграции с API.

Критерий завершения фазы:
  - content_pipeline.py обрабатывает один товар без ошибок
  - Видео появляется в data/queue/ со статусом ready_to_post
  - Метаданные полные: video_id, video_url, captions, hashtags, mention, status
  - dry-run режим работает без API ключей

Блоки:
  1. Unit-тесты content_pipeline.py (без API — работают всегда)
  2. Тест dry-run (без API, создаёт реальный JSON в очереди)
  3. Интеграционные тесты (нужны API ключи от Сергея)
"""
import json
import os
import sys
import uuid
import tempfile
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

QUEUE_DIR = Path(__file__).parent.parent / 'data' / 'queue'


# ── Блок 1: Unit-тесты content_pipeline (без API) ────────────────────────────

class TestContentPipelineUnit:
    """Unit-тесты content_pipeline.py — работают без API ключей."""

    def test_content_pipeline_imports(self):
        """content_pipeline.py импортируется без ошибок."""
        import content_pipeline
        assert content_pipeline is not None

    def test_queue_status_empty(self, tmp_path, monkeypatch):
        """queue_status() возвращает нули если папка пуста."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR', tmp_path)
        stat = content_pipeline.queue_status()
        assert stat['total'] == 0
        assert stat['ready_to_post'] == 0

    def test_save_to_queue_creates_file(self, tmp_path, monkeypatch):
        """save_to_queue() создаёт JSON-файл в папке очереди."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        video_data = {
            'video_id':  'test001',
            'video_url': 'https://example.com/test001.mp4',
            'product':   'Black Dress',
            'captions':  ['Caption 1 @brand #fashion'],
            'hashtags':  ['#fashion'],
            'mention':   '@brand',
            'status':    'ready_to_post',
        }
        path = content_pipeline.save_to_queue(video_data)
        assert path.exists(), "JSON-файл не создан"
        saved = json.loads(path.read_text())
        assert saved['video_id'] == 'test001'
        assert saved['status'] == 'ready_to_post'
        assert 'created_at' in saved

    def test_save_to_queue_generates_id(self, tmp_path, monkeypatch):
        """save_to_queue() генерирует video_id если не передан."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        path = content_pipeline.save_to_queue({
            'video_url': 'https://example.com/x.mp4',
            'captions':  [],
        })
        saved = json.loads(path.read_text())
        assert saved.get('video_id'), "video_id не сгенерирован"

    def test_queue_status_counts_statuses(self, tmp_path, monkeypatch):
        """queue_status() правильно считает статусы."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        # Создаём 2 ready_to_post и 1 published
        for i in range(2):
            (tmp_path / f'r{i}.json').write_text(
                json.dumps({'status': 'ready_to_post', 'video_id': f'r{i}'})
            )
        (tmp_path / 'p0.json').write_text(
            json.dumps({'status': 'published', 'video_id': 'p0'})
        )

        stat = content_pipeline.queue_status()
        assert stat['total'] == 3
        assert stat['ready_to_post'] == 2
        assert stat['published'] == 1

    def test_dry_run_product_returns_valid_data(self):
        """_dry_run_product() возвращает полные метаданные без API."""
        import content_pipeline
        data = content_pipeline._dry_run_product('Black Dress')

        required = ['video_id', 'video_url', 'product', 'captions',
                    'hashtags', 'mention', 'status']
        for field in required:
            assert field in data, f"Поле '{field}' отсутствует"

        assert data['status'] == 'ready_to_post'
        assert data['dry_run'] is True
        assert len(data['captions']) >= 1


# ── Блок 2: Dry-run публикация (без API) ─────────────────────────────────────

class TestDryRunPipeline:
    """Полный dry-run пайплайн без API ключей."""

    def test_dry_run_single_product(self, tmp_path, monkeypatch):
        """process_product с dry_run=True завершается без ошибок."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        data = content_pipeline.process_product(
            product_name='Test Dress',
            product_description='Cotton dress',
            dry_run=True,
        )
        assert data['status'] == 'ready_to_post'
        assert '@' in data['mention']

    def test_dry_run_saves_to_queue(self, tmp_path, monkeypatch):
        """dry-run сохраняет метаданные в очередь."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        data = content_pipeline.process_product('Test Dress', '', dry_run=True)
        path = content_pipeline.save_to_queue(data)

        assert path.exists()
        saved = json.loads(path.read_text())
        assert saved['status'] == 'ready_to_post'

    def test_dry_run_batch(self, tmp_path, tmp_path_factory, monkeypatch):
        """process_batch с dry_run=True обрабатывает несколько товаров."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        # Создаём тестовый products.json
        products = [
            {'name': f'Dress {i}', 'description': f'Desc {i}'}
            for i in range(3)
        ]
        products_file = tmp_path / 'products.json'
        products_file.write_text(json.dumps(products))

        count = content_pipeline.process_batch(str(products_file), dry_run=True)
        assert count == 3

        # Проверяем что все попали в очередь
        stat = content_pipeline.queue_status()
        assert stat['ready_to_post'] == 3

    def test_dry_run_captions_have_mention(self, monkeypatch):
        """dry-run подписи содержат @mention."""
        import content_pipeline
        monkeypatch.setenv('BRAND_MENTION', '@testbrand')
        data = content_pipeline._dry_run_product('Test Dress')
        for caption in data['captions']:
            assert '@' in caption, f"Нет @mention в: {caption}"

    def test_dry_run_captions_have_hashtags(self):
        """dry-run подписи содержат хештеги."""
        import content_pipeline
        data = content_pipeline._dry_run_product('Test Dress')
        for caption in data['captions']:
            assert '#' in caption, f"Нет хештегов в: {caption}"


# ── Блок 3: Интеграция с реальным API (нужны ключи от Сергея) ────────────────

@pytest.mark.skipif(
    not os.getenv('NANO_BANANA_API_KEY') or
    os.getenv('NANO_BANANA_API_KEY', '').startswith('sk_...'),
    reason='NANO_BANANA_API_KEY не задан — ждём ключи от Сергея'
)
class TestSingleVideoIntegration:
    """
    Интеграционные тесты — нужны реальные API ключи.
    Запускать только после Фазы 1.1 (все ключи получены).
    """

    def test_nano_banana_generates_model(self):
        """Nano Banana генерирует модель в одежде."""
        from nano_banana_client import NanoBananaClient
        client = NanoBananaClient()
        result = client.generate_model(
            product_name='Black Evening Dress',
            model_image_url='',
            clothing_image_url='',
            background_image_url='',
        )
        assert result.get('model_id'), "model_id не получен"

    def test_kling_creates_video(self):
        """Kling AI создаёт видео из изображения."""
        from kling_client import KlingAIClient
        client = KlingAIClient()
        result = client.create_video(
            image_url='https://example.com/model.jpg',
            prompt='Fashion Reels 9:16 vertical',
        )
        assert result.get('video_id'), "video_id не получен"

    def test_full_pipeline_single_product(self):
        """Полный пайплайн: товар → видео в очереди."""
        import content_pipeline
        data = content_pipeline.process_product(
            product_name='Black Evening Dress',
            product_description='Elegant cotton dress, A-line silhouette',
        )
        assert data['status'] == 'ready_to_post'
        assert data.get('video_url')
        assert len(data.get('captions', [])) >= 1

        path = content_pipeline.save_to_queue(data)
        assert path.exists()
