"""
Unit-тесты multi_account_publisher.py — без реального телефона и Instagram.

TDD: тест написан до покрытия внутренней логики publisher.
Проверяем: build_caption, _pick_session, mark_as_published, save_published_post, run(dry_run).
"""
import json
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# ── Блок 1: build_caption ────────────────────────────────────────────────────

class TestBuildCaption:
    """build_caption() собирает подпись из метаданных видео."""

    def test_caption_contains_mention(self, monkeypatch):
        """Подпись содержит @mention из video_data."""
        import multi_account_publisher as pub
        monkeypatch.setenv('BRAND_MENTION', '@testbrand')
        video = {
            'captions': [],
            'mention':  '@anna_style',
            'hashtags': ['#fashion'],
        }
        caption = pub.build_caption(video)
        assert '@anna_style' in caption

    def test_caption_uses_random_from_captions(self):
        """Если captions есть — выбирается один из них."""
        import multi_account_publisher as pub
        video = {
            'captions': ['Caption A @brand #tag', 'Caption B @brand #tag'],
            'mention':  '@brand',
            'hashtags': ['#tag'],
        }
        caption = pub.build_caption(video)
        assert caption in video['captions']

    def test_caption_adds_mention_if_missing(self, monkeypatch):
        """Если в выбранном caption нет @mention — добавляется."""
        import multi_account_publisher as pub
        monkeypatch.setenv('BRAND_MENTION', '@fallback')
        video = {
            'captions': ['Caption without mention #tag'],
            'mention':  '@mymodel',
            'hashtags': ['#tag'],
        }
        caption = pub.build_caption(video)
        assert '@mymodel' in caption

    def test_caption_adds_hashtags_if_missing(self):
        """Если в выбранном caption нет хештегов — добавляются."""
        import multi_account_publisher as pub
        video = {
            'captions': ['Caption without hashtags @brand'],
            'mention':  '@brand',
            'hashtags': ['#fashion', '#style'],
        }
        caption = pub.build_caption(video)
        assert '#' in caption

    def test_caption_fallback_when_no_captions(self, monkeypatch):
        """Если captions пустой — генерируется минимальная подпись."""
        import multi_account_publisher as pub
        monkeypatch.setenv('BRAND_MENTION', '@fallback')
        video = {
            'captions': [],
            'mention':  '@mymodel',
            'hashtags': ['#fashion'],
        }
        caption = pub.build_caption(video)
        assert '@mymodel' in caption
        assert '#' in caption


# ── Блок 2: _pick_session ────────────────────────────────────────────────────

class TestPickSession:
    """_pick_session() выбирает подходящий аккаунт для видео."""

    def _make_session(self, username: str, posts: list = None) -> dict:
        return {
            'username':        username,
            'logged_in':       True,
            '_session_file':   f'/tmp/{username}.json',
            'published_posts': posts or [],
        }

    def test_picks_from_available_sessions(self):
        """Возвращает один из доступных сессий."""
        import multi_account_publisher as pub
        sessions = [self._make_session('anna'), self._make_session('sofia')]
        video    = {'video_id': 'vid001'}
        result   = pub._pick_session(sessions, video)
        assert result['username'] in ('anna', 'sofia')

    def test_avoids_account_that_already_published(self):
        """Не выбирает аккаунт, который уже публиковал это видео."""
        import multi_account_publisher as pub
        sessions = [
            self._make_session('anna', posts=[{'video_id': 'vid001'}]),
            self._make_session('sofia'),
        ]
        video  = {'video_id': 'vid001'}
        result = pub._pick_session(sessions, video)
        assert result['username'] == 'sofia'

    def test_falls_back_if_all_published(self):
        """Если все аккаунты уже публиковали — берёт любой."""
        import multi_account_publisher as pub
        sessions = [
            self._make_session('anna',  posts=[{'video_id': 'vid001'}]),
            self._make_session('sofia', posts=[{'video_id': 'vid001'}]),
        ]
        video  = {'video_id': 'vid001'}
        result = pub._pick_session(sessions, video)
        assert result['username'] in ('anna', 'sofia')


# ── Блок 3: mark_as_published ────────────────────────────────────────────────

class TestMarkAsPublished:
    """mark_as_published() обновляет статус видео в очереди."""

    def test_marks_status_published(self, tmp_path):
        """Статус меняется с ready_to_post на published."""
        import multi_account_publisher as pub
        queue_file = tmp_path / 'video001.json'
        queue_file.write_text(json.dumps({
            'video_id': 'vid001',
            'status':   'ready_to_post',
        }))
        pub.mark_as_published(str(queue_file), 'https://instagram.com/p/ABC/')
        data = json.loads(queue_file.read_text())
        assert data['status'] == 'published'

    def test_saves_post_url(self, tmp_path):
        """post_url сохраняется в файл."""
        import multi_account_publisher as pub
        queue_file = tmp_path / 'video001.json'
        queue_file.write_text(json.dumps({'video_id': 'vid001', 'status': 'ready_to_post'}))
        pub.mark_as_published(str(queue_file), 'https://instagram.com/p/XYZ/')
        data = json.loads(queue_file.read_text())
        assert data['post_url'] == 'https://instagram.com/p/XYZ/'

    def test_saves_published_at_timestamp(self, tmp_path):
        """published_at сохраняется в ISO формате."""
        import multi_account_publisher as pub
        queue_file = tmp_path / 'video001.json'
        queue_file.write_text(json.dumps({'video_id': 'vid001', 'status': 'ready_to_post'}))
        pub.mark_as_published(str(queue_file), 'https://instagram.com/p/XYZ/')
        data = json.loads(queue_file.read_text())
        assert 'published_at' in data
        assert 'T' in data['published_at']  # ISO формат


# ── Блок 4: save_published_post ──────────────────────────────────────────────

class TestSavePublishedPost:
    """save_published_post() добавляет запись в session-файл."""

    def test_adds_post_to_session(self, tmp_path):
        """published_posts пополняется новой записью."""
        import multi_account_publisher as pub
        session_file = tmp_path / 'anna.json'
        session_file.write_text(json.dumps({
            'username':        'anna',
            'logged_in':       True,
            'published_posts': [],
        }))
        session = {
            'username':       'anna',
            '_session_file':  str(session_file),
            'published_posts': [],
        }
        pub.save_published_post(session, {
            'video_id':     'vid001',
            'post_url':     'https://instagram.com/p/ABC/',
            'caption':      'Test @brand #fashion',
            'published_at': '2026-02-25T12:00:00+00:00',
            'account':      'anna',
        })
        data = json.loads(session_file.read_text())
        assert len(data['published_posts']) == 1
        assert data['published_posts'][0]['video_id'] == 'vid001'

    def test_multiple_posts_accumulate(self, tmp_path):
        """Несколько вызовов накапливают посты в массиве."""
        import multi_account_publisher as pub
        session_file = tmp_path / 'anna.json'
        session_file.write_text(json.dumps({'username': 'anna', 'published_posts': []}))
        session = {'username': 'anna', '_session_file': str(session_file), 'published_posts': []}

        for i in range(3):
            pub.save_published_post(session, {'video_id': f'vid{i:03d}', 'post_url': f'https://ig.com/p/{i}'})
            session = {'username': 'anna', '_session_file': str(session_file),
                       'published_posts': json.loads(session_file.read_text()).get('published_posts', [])}

        data = json.loads(session_file.read_text())
        assert len(data['published_posts']) == 3


# ── Блок 5: run(dry_run=True) ────────────────────────────────────────────────

class TestRunDryRun:
    """run(dry_run=True) — полный цикл без реального ADB."""

    def _setup(self, tmp_path, monkeypatch):
        """Создать минимальное окружение: одно видео + один аккаунт."""
        import multi_account_publisher as pub

        # Папки
        queue_dir   = tmp_path / 'queue'
        session_dir = tmp_path / 'sessions'
        queue_dir.mkdir()
        session_dir.mkdir()

        # Видео в очереди
        video = {
            'video_id':        'vid001',
            'video_url':       'https://example.com/vid001.mp4',
            'account':         'brand_anna',
            'captions':        ['Test caption @anna #fashion'],
            'hashtags':        ['#fashion'],
            'mention':         '@anna',
            'status':          'ready_to_post',
            '_queue_file':     str(queue_dir / 'vid001.json'),
        }
        (queue_dir / 'vid001.json').write_text(json.dumps(video))

        # Сессия
        session = {
            'username':        'brand_anna',
            'logged_in':       True,
            'phone_name':      'CP-6',
            'published_posts': [],
            '_session_file':   str(session_dir / 'brand_anna.json'),
        }
        (session_dir / 'brand_anna.json').write_text(json.dumps(session))

        monkeypatch.setattr(pub, 'QUEUE_DIR',    queue_dir)
        monkeypatch.setattr(pub, 'SESSIONS_DIR', session_dir)

        return video, session

    def test_dry_run_returns_1(self, tmp_path, monkeypatch):
        """run(dry_run=True) возвращает 1 (одна успешная публикация)."""
        import multi_account_publisher as pub
        self._setup(tmp_path, monkeypatch)
        count = pub.run(dry_run=True)
        assert count == 1

    def test_dry_run_updates_session(self, tmp_path, monkeypatch):
        """После dry-run в session-файле появляется запись о посте."""
        import multi_account_publisher as pub
        _, session = self._setup(tmp_path, monkeypatch)
        pub.run(dry_run=True)
        data = json.loads(Path(session['_session_file']).read_text())
        assert len(data.get('published_posts', [])) == 1

    def test_dry_run_does_not_mark_queue(self, tmp_path, monkeypatch):
        """dry-run НЕ меняет статус в очереди (только реальный run меняет)."""
        import multi_account_publisher as pub
        video, _ = self._setup(tmp_path, monkeypatch)
        pub.run(dry_run=True)
        data = json.loads(Path(video['_queue_file']).read_text())
        assert data['status'] == 'ready_to_post'  # не изменился

    def test_empty_queue_returns_0(self, tmp_path, monkeypatch):
        """Пустая очередь → run возвращает 0."""
        import multi_account_publisher as pub
        queue_dir   = tmp_path / 'queue'
        session_dir = tmp_path / 'sessions'
        queue_dir.mkdir()
        session_dir.mkdir()
        monkeypatch.setattr(pub, 'QUEUE_DIR',    queue_dir)
        monkeypatch.setattr(pub, 'SESSIONS_DIR', session_dir)
        assert pub.run(dry_run=True) == 0

    def test_no_sessions_returns_0(self, tmp_path, monkeypatch):
        """Нет сессий → run возвращает 0."""
        import multi_account_publisher as pub
        queue_dir   = tmp_path / 'queue'
        session_dir = tmp_path / 'sessions'
        queue_dir.mkdir()
        session_dir.mkdir()
        (queue_dir / 'vid001.json').write_text(json.dumps({
            'video_id': 'v1', 'status': 'ready_to_post',
            'captions': [], 'mention': '@x', 'hashtags': [],
        }))
        monkeypatch.setattr(pub, 'QUEUE_DIR',    queue_dir)
        monkeypatch.setattr(pub, 'SESSIONS_DIR', session_dir)
        assert pub.run(dry_run=True) == 0
