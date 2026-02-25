"""
Unit-тесты ig_warmup_runner.py — без реального телефона и Instagram.

TDD: покрываем внутреннюю логику runner'а.
Проверяем: load_sessions, is_warmed_up, update_session, warmup_account(dry_run), run(dry_run).
"""
import json
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# ── Блок 1: load_sessions ────────────────────────────────────────────────────

class TestLoadSessions:
    """load_sessions() читает session-файлы, пропуская забаненных."""

    def _make_session(self, tmp_path: Path, username: str, **kwargs) -> Path:
        data = {'username': username, 'logged_in': True, **kwargs}
        f = tmp_path / f'{username}.json'
        f.write_text(json.dumps(data))
        return f

    def test_returns_empty_if_dir_missing(self, tmp_path, monkeypatch):
        """Папка не существует → пустой список."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path / 'missing')
        assert runner.load_sessions() == []

    def test_skips_not_logged_in(self, tmp_path, monkeypatch):
        """Аккаунты с logged_in=False пропускаются."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        self._make_session(tmp_path, 'anna', logged_in=True)
        self._make_session(tmp_path, 'sofia', logged_in=False)
        sessions = runner.load_sessions()
        assert len(sessions) == 1
        assert sessions[0]['username'] == 'anna'

    def test_skips_banned(self, tmp_path, monkeypatch):
        """Аккаунты со статусом banned пропускаются."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        self._make_session(tmp_path, 'anna')
        self._make_session(tmp_path, 'banned_user', status='banned')
        sessions = runner.load_sessions()
        assert len(sessions) == 1
        assert sessions[0]['username'] == 'anna'

    def test_skips_action_block(self, tmp_path, monkeypatch):
        """Аккаунты со статусом action_block пропускаются."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        self._make_session(tmp_path, 'blocked', status='action_block')
        assert runner.load_sessions() == []

    def test_filters_by_only(self, tmp_path, monkeypatch):
        """Параметр only фильтрует по username."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        for name in ('anna', 'sofia', 'mia'):
            self._make_session(tmp_path, name)
        result = runner.load_sessions(only='sofia')
        assert len(result) == 1
        assert result[0]['username'] == 'sofia'

    def test_adds_session_file_path(self, tmp_path, monkeypatch):
        """К каждой сессии добавляется _session_file."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        self._make_session(tmp_path, 'anna')
        sessions = runner.load_sessions()
        assert '_session_file' in sessions[0]
        assert 'anna.json' in sessions[0]['_session_file']


# ── Блок 2: is_warmed_up ─────────────────────────────────────────────────────

class TestIsWarmedUp:
    """is_warmed_up() проверяет достаточность прогрева."""

    def test_not_warmed_if_no_warmup(self):
        """Нет поля warmup → не прогрет."""
        import ig_warmup_runner as runner
        assert runner.is_warmed_up({}) is False

    def test_not_warmed_if_below_min(self):
        """Меньше MIN_REELS рилов → не прогрет."""
        import ig_warmup_runner as runner
        session = {'warmup': {'reels_watched': runner.MIN_REELS - 1}}
        assert runner.is_warmed_up(session) is False

    def test_warmed_at_exactly_min(self):
        """Ровно MIN_REELS → прогрет."""
        import ig_warmup_runner as runner
        session = {'warmup': {'reels_watched': runner.MIN_REELS}}
        assert runner.is_warmed_up(session) is True

    def test_warmed_above_min(self):
        """Больше MIN_REELS → прогрет."""
        import ig_warmup_runner as runner
        session = {'warmup': {'reels_watched': runner.MIN_REELS + 10}}
        assert runner.is_warmed_up(session) is True


# ── Блок 3: update_session ───────────────────────────────────────────────────

class TestUpdateSession:
    """update_session() накапливает статистику прогрева."""

    def test_updates_reels_count(self, tmp_path):
        """reels_watched накапливается."""
        import ig_warmup_runner as runner
        session_file = tmp_path / 'anna.json'
        session_file.write_text(json.dumps({
            'username': 'anna',
            'warmup':   {'reels_watched': 10, 'likes': 2, 'elapsed_sec': 120, 'runs_count': 1},
        }))
        session = {'username': 'anna', '_session_file': str(session_file)}
        runner.update_session(session, {'reels_watched': 15, 'likes': 3, 'elapsed': 180.0})
        data = json.loads(session_file.read_text())
        assert data['warmup']['reels_watched'] == 25  # 10 + 15

    def test_accumulates_likes(self, tmp_path):
        """likes накапливаются между запусками."""
        import ig_warmup_runner as runner
        session_file = tmp_path / 'anna.json'
        session_file.write_text(json.dumps({'warmup': {'likes': 5}}))
        session = {'_session_file': str(session_file)}
        runner.update_session(session, {'reels_watched': 10, 'likes': 3, 'elapsed': 100.0})
        data = json.loads(session_file.read_text())
        assert data['warmup']['likes'] == 8  # 5 + 3

    def test_increments_runs_count(self, tmp_path):
        """runs_count увеличивается на 1 с каждым запуском."""
        import ig_warmup_runner as runner
        session_file = tmp_path / 'anna.json'
        session_file.write_text(json.dumps({'warmup': {'runs_count': 2}}))
        session = {'_session_file': str(session_file)}
        runner.update_session(session, {'reels_watched': 5, 'likes': 1, 'elapsed': 60.0})
        data = json.loads(session_file.read_text())
        assert data['warmup']['runs_count'] == 3

    def test_saves_last_run_at(self, tmp_path):
        """last_run_at содержит ISO-метку времени."""
        import ig_warmup_runner as runner
        session_file = tmp_path / 'anna.json'
        session_file.write_text(json.dumps({'warmup': {}}))
        session = {'_session_file': str(session_file)}
        runner.update_session(session, {'reels_watched': 5, 'likes': 1, 'elapsed': 60.0})
        data = json.loads(session_file.read_text())
        assert 'last_run_at' in data['warmup']
        assert 'T' in data['warmup']['last_run_at']

    def test_first_run_starts_at_zero(self, tmp_path):
        """Первый запуск корректно стартует с нуля (нет поля warmup)."""
        import ig_warmup_runner as runner
        session_file = tmp_path / 'anna.json'
        session_file.write_text(json.dumps({'username': 'anna'}))
        session = {'_session_file': str(session_file)}
        runner.update_session(session, {'reels_watched': 20, 'likes': 4, 'elapsed': 250.0})
        data = json.loads(session_file.read_text())
        assert data['warmup']['reels_watched'] == 20
        assert data['warmup']['runs_count'] == 1


# ── Блок 4: warmup_account(dry_run=True) ─────────────────────────────────────

class TestWarmupAccountDryRun:
    """warmup_account(dry_run=True) симулирует прогрев без ADB."""

    def _make_session(self, tmp_path: Path) -> dict:
        session_file = tmp_path / 'brand_anna.json'
        session_file.write_text(json.dumps({
            'username':  'brand_anna',
            'logged_in': True,
            'warmup':    {},
        }))
        return {
            'username':       'brand_anna',
            'phone_name':     'CP-1',
            '_session_file':  str(session_file),
        }

    def test_dry_run_returns_true(self, tmp_path):
        """dry_run возвращает True (успех)."""
        import ig_warmup_runner as runner
        session = self._make_session(tmp_path)
        assert runner.warmup_account(session, dry_run=True) is True

    def test_dry_run_updates_session(self, tmp_path):
        """dry_run записывает статистику в session-файл."""
        import ig_warmup_runner as runner
        session = self._make_session(tmp_path)
        runner.warmup_account(session, dry_run=True)
        data = json.loads(Path(session['_session_file']).read_text())
        assert data['warmup']['reels_watched'] >= runner.MIN_REELS

    def test_dry_run_marks_warmed(self, tmp_path):
        """После dry_run аккаунт считается прогретым."""
        import ig_warmup_runner as runner
        session = self._make_session(tmp_path)
        runner.warmup_account(session, dry_run=True)
        # Загружаем обновлённые данные
        updated = json.loads(Path(session['_session_file']).read_text())
        updated['_session_file'] = session['_session_file']
        assert runner.is_warmed_up(updated) is True


# ── Блок 5: run(dry_run=True) ─────────────────────────────────────────────────

class TestRunDryRun:
    """run(dry_run=True) — полный цикл без ADB."""

    def _setup(self, tmp_path: Path, monkeypatch, n: int = 3):
        """Создать n session-файлов."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        sessions = []
        for i in range(n):
            data = {
                'username':  f'user{i}',
                'logged_in': True,
                'warmup':    {},
            }
            (tmp_path / f'user{i}.json').write_text(json.dumps(data))
            sessions.append(data)
        return sessions

    def test_dry_run_warms_all(self, tmp_path, monkeypatch):
        """dry_run прогревает все аккаунты."""
        import ig_warmup_runner as runner
        self._setup(tmp_path, monkeypatch, n=3)
        result = runner.run(dry_run=True, pause_sec=0)
        assert result['success'] == 3
        assert result['failed'] == 0

    def test_skip_already_warmed(self, tmp_path, monkeypatch):
        """skip_warmed=True пропускает уже прогретые аккаунты."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        # Прогретый аккаунт
        (tmp_path / 'warmed.json').write_text(json.dumps({
            'username':  'warmed',
            'logged_in': True,
            'warmup':    {'reels_watched': runner.MIN_REELS},
        }))
        # Не прогретый
        (tmp_path / 'cold.json').write_text(json.dumps({
            'username':  'cold',
            'logged_in': True,
            'warmup':    {'reels_watched': 0},
        }))
        result = runner.run(skip_warmed=True, dry_run=True, pause_sec=0)
        assert result['skipped'] == 1
        assert result['success'] == 1

    def test_all_flag_warms_even_warmed(self, tmp_path, monkeypatch):
        """skip_warmed=False прогревает даже уже прогретые."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        (tmp_path / 'warmed.json').write_text(json.dumps({
            'username':  'warmed',
            'logged_in': True,
            'warmup':    {'reels_watched': runner.MIN_REELS},
        }))
        result = runner.run(skip_warmed=False, dry_run=True, pause_sec=0)
        assert result['success'] == 1
        assert result['skipped'] == 0

    def test_only_filter(self, tmp_path, monkeypatch):
        """Параметр only прогревает только указанный аккаунт."""
        import ig_warmup_runner as runner
        self._setup(tmp_path, monkeypatch, n=3)
        result = runner.run(only='user1', dry_run=True, pause_sec=0)
        assert result['success'] == 1

    def test_empty_sessions_returns_zeros(self, tmp_path, monkeypatch):
        """Нет сессий → нулевой результат."""
        import ig_warmup_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path / 'empty')
        result = runner.run(dry_run=True, pause_sec=0)
        assert result == {'success': 0, 'skipped': 0, 'failed': 0}
