"""
Фаза 1.3: Пакетная генерация 10 видео.
TDD тест — написан до реальной пакетной обработки.

Критерий завершения фазы:
  - 10+ видео в data/queue/ со статусом ready_to_post
  - Нет дубликатов video_id
  - Все метаданные полные
  - Нет ошибок обработки

Блоки:
  1. Unit-тесты пакетной логики (без API)
  2. Тест 10 видео в очереди (результат реального запуска)
  3. Интеграционные тесты (нужны API ключи от Сергея)
"""
import json
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

QUEUE_DIR = Path(__file__).parent.parent / 'data' / 'queue'


# ── Блок 1: Unit-тесты пакетной логики ───────────────────────────────────────

class TestBatchPipelineUnit:
    """Unit-тесты пакетной обработки без API."""

    def test_batch_file_not_found_returns_zero(self, tmp_path, monkeypatch):
        """process_batch возвращает 0 если файл не найден."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')
        count = content_pipeline.process_batch('/nonexistent.json', dry_run=True)
        assert count == 0

    def test_empty_batch_returns_zero(self, tmp_path, monkeypatch):
        """process_batch с пустым массивом возвращает 0."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        products_file = tmp_path / 'empty.json'
        products_file.write_text('[]')
        count = content_pipeline.process_batch(str(products_file), dry_run=True)
        assert count == 0

    def test_batch_10_dry_run(self, tmp_path, monkeypatch):
        """process_batch(10 товаров, dry_run=True) возвращает 10."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        products = [{'name': f'Product {i}', 'description': f'Desc {i}'}
                    for i in range(10)]
        pf = tmp_path / 'products.json'
        pf.write_text(json.dumps(products))

        count = content_pipeline.process_batch(str(pf), dry_run=True)
        assert count == 10

    def test_batch_creates_no_duplicates(self, tmp_path, monkeypatch):
        """Пакетная обработка не создаёт дубликаты video_id."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        products = [{'name': f'P{i}', 'description': ''} for i in range(5)]
        pf = tmp_path / 'products.json'
        pf.write_text(json.dumps(products))
        content_pipeline.process_batch(str(pf), dry_run=True)

        video_ids = []
        for f in tmp_path.glob('*.json'):
            d = json.loads(f.read_text())
            if not isinstance(d, dict) or 'video_id' not in d:
                continue  # пропускаем входные файлы (списки)
            video_ids.append(d.get('video_id'))

        assert len(video_ids) == len(set(video_ids)), (
            f"Найдены дубликаты video_id: "
            f"{[x for x in video_ids if video_ids.count(x) > 1]}"
        )

    def test_batch_all_metadata_complete(self, tmp_path, monkeypatch):
        """Каждый элемент пакета имеет полные метаданные."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        products = [{'name': f'P{i}', 'description': ''} for i in range(3)]
        pf = tmp_path / 'p.json'
        pf.write_text(json.dumps(products))
        content_pipeline.process_batch(str(pf), dry_run=True)

        required = ['video_id', 'video_url', 'captions', 'hashtags', 'mention', 'status']
        for f in tmp_path.glob('*.json'):
            d = json.loads(f.read_text())
            if not isinstance(d, dict) or 'video_id' not in d:
                continue  # пропускаем входные файлы (списки)
            for field in required:
                assert field in d, f"Поле '{field}' отсутствует в {f.name}"

    def test_batch_error_does_not_stop_processing(self, tmp_path, monkeypatch):
        """Ошибка одного товара не останавливает обработку остальных."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        # Один товар без имени — может вызвать ошибку
        products = [
            {'name': 'Good Product', 'description': 'OK'},
            {},  # плохой товар — нет name
            {'name': 'Another Good', 'description': 'OK'},
        ]
        pf = tmp_path / 'mixed.json'
        pf.write_text(json.dumps(products))

        # Должно обработать хотя бы 2 из 3
        count = content_pipeline.process_batch(str(pf), dry_run=True)
        assert count >= 2, f"Обработано только {count} товаров из 3"


# ── Блок 2: Реальные данные в очереди (после запуска пайплайна) ──────────────

class TestQueueHas10Videos:
    """Проверяет очередь после реального запуска content_pipeline.py."""

    def test_queue_dir_exists(self):
        """data/queue/ существует."""
        assert QUEUE_DIR.exists(), (
            "Папка data/queue не существует. "
            "Запусти: python content_pipeline.py --batch products.json"
        )

    def test_at_least_10_ready_videos(self):
        """В очереди >= 10 видео со статусом ready_to_post."""
        if not QUEUE_DIR.exists():
            pytest.fail("Папка data/queue не существует")

        ready = [
            f for f in QUEUE_DIR.glob('*.json')
            if json.loads(f.read_text()).get('status') == 'ready_to_post'
        ]
        assert len(ready) >= 10, (
            f"В очереди {len(ready)} видео, нужно >= 10. "
            "Запусти: python content_pipeline.py --batch products.json"
        )

    def test_no_duplicate_video_ids(self):
        """Нет дубликатов video_id в очереди."""
        if not QUEUE_DIR.exists():
            pytest.skip("Очередь пуста")
        video_ids = []
        for f in QUEUE_DIR.glob('*.json'):
            d = json.loads(f.read_text())
            video_ids.append(d.get('video_id'))
        dupes = [x for x in video_ids if video_ids.count(x) > 1]
        assert not dupes, f"Дубликаты video_id: {dupes}"

    def test_all_queue_items_have_metadata(self):
        """Все элементы очереди имеют полные метаданные."""
        if not QUEUE_DIR.exists():
            pytest.skip("Очередь пуста")
        required = ['video_id', 'video_url', 'captions', 'hashtags', 'mention', 'status']
        for f in QUEUE_DIR.glob('*.json'):
            d = json.loads(f.read_text())
            for field in required:
                assert field in d, f"Поле '{field}' отсутствует в {f.name}"


# ── Блок 3: Интеграция с реальным API (нужны ключи Сергея) ───────────────────

@pytest.mark.skipif(
    not os.getenv('NANO_BANANA_API_KEY') or
    os.getenv('NANO_BANANA_API_KEY', '').startswith('sk_...'),
    reason='NANO_BANANA_API_KEY не задан — ждём ключи от Сергея'
)
class TestBatchIntegration:
    """Интеграционные тесты — нужны реальные API ключи."""

    def test_batch_10_real_api(self, tmp_path, monkeypatch):
        """Пакет из 10 товаров через реальные API."""
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        products = [
            {
                'name': f'Test Dress {i}',
                'description': f'Elegant dress model {i}',
            }
            for i in range(10)
        ]
        pf = tmp_path / 'products.json'
        pf.write_text(json.dumps(products))

        count = content_pipeline.process_batch(str(pf))
        assert count == 10, f"Обработано {count} из 10 товаров"

    def test_processing_time_under_2_hours(self, tmp_path, monkeypatch):
        """10 товаров обрабатываются менее чем за 2 часа."""
        import time
        import content_pipeline
        monkeypatch.setattr(content_pipeline, 'QUEUE_DIR',  tmp_path)
        monkeypatch.setattr(content_pipeline, 'VIDEOS_DIR', tmp_path / 'videos')

        products = [{'name': f'P{i}', 'description': ''} for i in range(10)]
        pf = tmp_path / 'p.json'
        pf.write_text(json.dumps(products))

        start = time.time()
        content_pipeline.process_batch(str(pf))
        elapsed = time.time() - start

        assert elapsed < 7200, (
            f"Обработка заняла {elapsed:.0f}с (> 2 часов). "
            "Оптимизируй параллелизм в content_pipeline.py."
        )
