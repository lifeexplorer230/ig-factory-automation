"""
Фаза 3.1: Первая публикация видео на Instagram аккаунт.
TDD тест — написан до реализации multi_account_publisher.py.

Предусловия (проверяются в тесте):
  - Поток 1 готов: есть видео в data/queue/
  - Поток 2 готов: есть залогиненный аккаунт в data/sessions/

Критерий завершения фазы:
  - Видео взято из очереди
  - Опубликовано на аккаунт
  - Пост сохранён в data/sessions/<account>.json
  - Нет ошибок публикации
"""
import os
import sys
import json
import pytest
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

QUEUE_DIR    = Path(__file__).parent.parent / 'data' / 'queue'
SESSIONS_DIR = Path(__file__).parent.parent / 'data' / 'sessions'
VIDEOS_DIR   = Path(__file__).parent.parent / 'data' / 'videos'


# ── Блок 1: Предусловия ───────────────────────────────────────────────────────

class TestPreconditions:
    """Потоки 1 и 2 готовы к публикации."""

    def test_queue_dir_exists(self):
        """Папка data/queue существует."""
        assert QUEUE_DIR.exists(), (
            "Папка data/queue не существует. "
            "Сначала запусти content_pipeline.py (Поток 1)."
        )

    def test_queue_has_videos(self):
        """В очереди есть хотя бы одно видео готовое к публикации."""
        ready = [
            f for f in QUEUE_DIR.glob('*.json')
            if json.loads(f.read_text()).get('status') == 'ready_to_post'
        ]
        assert len(ready) >= 1, (
            f"В {QUEUE_DIR} нет видео со статусом 'ready_to_post'. "
            "Сначала сгенерируй контент через content_pipeline.py (Поток 1)."
        )

    def test_queue_metadata_complete(self):
        """Метаданные видео в очереди полные."""
        required = ['video_id', 'video_url', 'captions', 'hashtags',
                    'mention', 'status']
        for f in QUEUE_DIR.glob('*.json'):
            data = json.loads(f.read_text())
            if data.get('status') != 'ready_to_post':
                continue
            for field in required:
                assert field in data, (
                    f"Поле '{field}' отсутствует в {f.name}"
                )

    def test_sessions_dir_has_logged_in_account(self):
        """Есть хотя бы один залогиненный аккаунт."""
        if not SESSIONS_DIR.exists():
            pytest.fail(
                "Папка data/sessions не существует. "
                "Сначала залогинься через ig-warmup.py (Поток 2)."
            )
        logged_in = [
            f for f in SESSIONS_DIR.glob('*.json')
            if json.loads(f.read_text()).get('logged_in')
        ]
        assert len(logged_in) >= 1, (
            "Нет залогиненных аккаунтов. "
            "Сначала залогинься через ig-warmup.py (Поток 2)."
        )


# ── Блок 2: Публикация ────────────────────────────────────────────────────────

class TestPublicationResult:
    """
    Видео опубликовано и результат сохранён.
    Тесты проверяют данные ПОСЛЕ запуска публикации.
    """

    @pytest.fixture
    def published_posts(self):
        """Возвращает список записей об опубликованных постах."""
        posts = []
        if not SESSIONS_DIR.exists():
            return posts
        for f in SESSIONS_DIR.glob('*.json'):
            data = json.loads(f.read_text())
            posts.extend(data.get('published_posts', []))
        return posts

    def test_at_least_one_post_published(self, published_posts):
        """Хотя бы один пост опубликован."""
        assert len(published_posts) >= 1, (
            "Нет опубликованных постов. "
            "Запусти публикацию через ig-warmup.py или multi_account_publisher.py."
        )

    def test_post_has_url(self, published_posts):
        """Каждый пост содержит URL или пометку что URL не определён."""
        if not published_posts:
            pytest.skip("Нет опубликованных постов")
        for post in published_posts:
            assert 'post_url' in post, (
                f"Поле 'post_url' отсутствует в посте {post}"
            )

    def test_post_has_caption(self, published_posts):
        """Каждый пост содержит подпись."""
        if not published_posts:
            pytest.skip("Нет опубликованных постов")
        for post in published_posts:
            caption = post.get('caption', '')
            assert caption, "Подпись поста пустая"
            assert '@' in caption, "Подпись не содержит @mention"
            assert '#' in caption, "Подпись не содержит хештеги"

    def test_post_has_timestamp(self, published_posts):
        """Каждый пост содержит время публикации."""
        if not published_posts:
            pytest.skip("Нет опубликованных постов")
        for post in published_posts:
            assert 'published_at' in post, (
                f"Поле 'published_at' отсутствует в посте {post}"
            )

    def test_video_marked_as_published_in_queue(self, published_posts):
        """Опубликованные видео помечены в очереди (не дублируются)."""
        if not published_posts or not QUEUE_DIR.exists():
            pytest.skip("Нет данных для проверки")
        published_ids = {p.get('video_id') for p in published_posts}
        for queue_file in QUEUE_DIR.glob('*.json'):
            data = json.loads(queue_file.read_text())
            if data.get('video_id') in published_ids:
                assert data.get('status') == 'published', (
                    f"Видео {data['video_id']} опубликовано, "
                    f"но в очереди статус '{data.get('status')}' вместо 'published'. "
                    "Обнови статус в очереди после публикации."
                )


# ── Блок 3: Caption Generator unit-тесты ─────────────────────────────────────

class TestCaptionGeneratorUnit:
    """Unit-тесты caption_generator.py без реального API ключа."""

    def test_caption_generator_imports(self):
        """caption_generator.py импортируется без ошибок."""
        from caption_generator import CaptionGenerator
        assert CaptionGenerator is not None

    def test_caption_generator_init(self):
        """CaptionGenerator инициализируется с тестовым ключом."""
        from caption_generator import CaptionGenerator
        gen = CaptionGenerator(api_key='test_key')
        assert gen.api_key == 'test_key'

    def test_fallback_returns_5_captions(self):
        """Fallback шаблон возвращает 5 подписей без API ключа."""
        from caption_generator import CaptionGenerator
        gen      = CaptionGenerator(api_key='')
        captions = gen._template_captions('Black Dress')
        assert len(captions) == 5

    def test_fallback_captions_have_mention(self):
        """Шаблонные подписи содержат @mention."""
        from caption_generator import CaptionGenerator
        gen      = CaptionGenerator(api_key='')
        captions = gen._template_captions('Black Dress')
        for c in captions:
            assert '@' in c, f"Подпись без @mention: {c}"

    def test_fallback_captions_have_hashtags(self):
        """Шаблонные подписи содержат хештеги."""
        from caption_generator import CaptionGenerator
        gen      = CaptionGenerator(api_key='')
        captions = gen._template_captions('Black Dress')
        for c in captions:
            assert '#' in c, f"Подпись без хештегов: {c}"

    def test_no_api_key_raises_runtime_error(self):
        """generate_captions без ключа выбрасывает RuntimeError."""
        from caption_generator import CaptionGenerator
        gen = CaptionGenerator(api_key='')
        with pytest.raises(RuntimeError, match='CLAUDE_API_KEY'):
            gen.generate_captions('Black Dress', 'Elegant cotton dress')
