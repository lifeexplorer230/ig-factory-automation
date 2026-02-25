"""
Unit-тесты ig_login_runner.py — без реального телефона и Instagram.

TDD: покрываем внутреннюю логику runner'а.
Проверяем: load_accounts, is_logged_in, save_session, login_account(dry_run), run(dry_run).
"""
import json
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# ── Блок 1: load_accounts ────────────────────────────────────────────────────

class TestLoadAccounts:
    """load_accounts() читает файлы из data/accounts/, пропуская шаблоны."""

    def test_returns_empty_if_dir_missing(self, tmp_path, monkeypatch):
        """Если папки нет — возвращает пустой список."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'ACCOUNTS_DIR', tmp_path / 'missing')
        assert runner.load_accounts() == []

    def test_skips_template_files(self, tmp_path, monkeypatch):
        """Файлы начинающиеся с _ (шаблоны) пропускаются."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'ACCOUNTS_DIR', tmp_path)
        (tmp_path / '_template.json').write_text(json.dumps({'username': 'tmpl'}))
        (tmp_path / 'anna.json').write_text(json.dumps({'username': 'anna'}))
        accounts = runner.load_accounts()
        assert len(accounts) == 1
        assert accounts[0]['username'] == 'anna'

    def test_filters_by_only(self, tmp_path, monkeypatch):
        """Параметр only фильтрует по username."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'ACCOUNTS_DIR', tmp_path)
        for name in ('anna', 'sofia', 'mia'):
            (tmp_path / f'{name}.json').write_text(json.dumps({'username': name}))
        result = runner.load_accounts(only='sofia')
        assert len(result) == 1
        assert result[0]['username'] == 'sofia'

    def test_adds_file_path(self, tmp_path, monkeypatch):
        """К каждому аккаунту добавляется _file для обратной записи."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'ACCOUNTS_DIR', tmp_path)
        (tmp_path / 'anna.json').write_text(json.dumps({'username': 'anna'}))
        accounts = runner.load_accounts()
        assert '_file' in accounts[0]
        assert 'anna.json' in accounts[0]['_file']

    def test_returns_all_accounts(self, tmp_path, monkeypatch):
        """Возвращает все аккаунты без фильтрации."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'ACCOUNTS_DIR', tmp_path)
        for i in range(5):
            (tmp_path / f'acc{i}.json').write_text(json.dumps({'username': f'user{i}'}))
        assert len(runner.load_accounts()) == 5


# ── Блок 2: is_logged_in ─────────────────────────────────────────────────────

class TestIsLoggedIn:
    """is_logged_in() проверяет session-файл."""

    def test_false_if_no_session(self, tmp_path, monkeypatch):
        """Нет session-файла → не залогинен."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        assert runner.is_logged_in('new_user') is False

    def test_false_if_logged_in_false(self, tmp_path, monkeypatch):
        """logged_in=False → не залогинен."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        (tmp_path / 'anna.json').write_text(json.dumps({'logged_in': False}))
        assert runner.is_logged_in('anna') is False

    def test_true_if_logged_in_true(self, tmp_path, monkeypatch):
        """logged_in=True → залогинен."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        (tmp_path / 'anna.json').write_text(json.dumps({'logged_in': True}))
        assert runner.is_logged_in('anna') is True


# ── Блок 3: save_session ─────────────────────────────────────────────────────

class TestSaveSession:
    """save_session() сохраняет session-файл."""

    def test_creates_session_file(self, tmp_path, monkeypatch):
        """Создаёт файл username.json в SESSIONS_DIR."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        runner.save_session('anna', {'username': 'anna', 'logged_in': True})
        assert (tmp_path / 'anna.json').exists()

    def test_creates_dir_if_missing(self, tmp_path, monkeypatch):
        """Создаёт SESSIONS_DIR если его нет."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path / 'sessions')
        runner.save_session('anna', {'logged_in': True})
        assert (tmp_path / 'sessions' / 'anna.json').exists()

    def test_session_content_correct(self, tmp_path, monkeypatch):
        """Содержимое файла соответствует переданным данным."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        runner.save_session('anna', {'username': 'anna', 'logged_in': True, 'phone_name': 'CP-1'})
        data = json.loads((tmp_path / 'anna.json').read_text())
        assert data['logged_in'] is True
        assert data['phone_name'] == 'CP-1'


# ── Блок 4: login_account(dry_run=True) ──────────────────────────────────────

class TestLoginAccountDryRun:
    """login_account(dry_run=True) симулирует логин без ADB."""

    def _make_account(self) -> dict:
        return {
            'username':       'brand_anna',
            'password':       'secret123',
            'totp_secret':    None,
            'model_photo_url': 'https://drive.google.com/file/d/abc',
        }

    def test_dry_run_returns_true(self, tmp_path, monkeypatch):
        """dry_run возвращает True (успех)."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        result = runner.login_account(self._make_account(), dry_run=True)
        assert result is True

    def test_dry_run_saves_session(self, tmp_path, monkeypatch):
        """dry_run создаёт session-файл с logged_in=True."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        runner.login_account(self._make_account(), dry_run=True)
        session_file = tmp_path / 'brand_anna.json'
        assert session_file.exists()
        data = json.loads(session_file.read_text())
        assert data['logged_in'] is True

    def test_dry_run_session_has_model_photo(self, tmp_path, monkeypatch):
        """dry_run сохраняет model_photo_url в сессию."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        runner.login_account(self._make_account(), dry_run=True)
        data = json.loads((tmp_path / 'brand_anna.json').read_text())
        assert data.get('model_photo_url') == 'https://drive.google.com/file/d/abc'

    def test_dry_run_session_has_logged_in_at(self, tmp_path, monkeypatch):
        """dry_run записывает временную метку logged_in_at."""
        import ig_login_runner as runner
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path)
        runner.login_account(self._make_account(), dry_run=True)
        data = json.loads((tmp_path / 'brand_anna.json').read_text())
        assert 'logged_in_at' in data
        assert 'T' in data['logged_in_at']  # ISO формат


# ── Блок 5: run(dry_run=True) ─────────────────────────────────────────────────

class TestRunDryRun:
    """run(dry_run=True) — полный цикл без ADB."""

    def _setup(self, tmp_path, monkeypatch, n: int = 3):
        """Создать n аккаунтов в tmp_path."""
        import ig_login_runner as runner
        accounts_dir = tmp_path / 'accounts'
        sessions_dir = tmp_path / 'sessions'
        accounts_dir.mkdir()
        sessions_dir.mkdir()

        for i in range(n):
            (accounts_dir / f'user{i}.json').write_text(json.dumps({
                'username':       f'user{i}',
                'password':       'pass',
                'model_photo_url': f'https://drive.google.com/file/d/{i}',
            }))

        monkeypatch.setattr(runner, 'ACCOUNTS_DIR', accounts_dir)
        monkeypatch.setattr(runner, 'SESSIONS_DIR', sessions_dir)
        return accounts_dir, sessions_dir

    def test_dry_run_logs_in_all(self, tmp_path, monkeypatch):
        """dry_run логинит все аккаунты."""
        import ig_login_runner as runner
        _, sessions_dir = self._setup(tmp_path, monkeypatch, n=3)
        result = runner.run(dry_run=True)
        assert result['success'] == 3
        assert result['failed'] == 0

    def test_dry_run_creates_session_files(self, tmp_path, monkeypatch):
        """После dry_run появляются session-файлы."""
        import ig_login_runner as runner
        _, sessions_dir = self._setup(tmp_path, monkeypatch, n=3)
        runner.run(dry_run=True)
        sessions = list(sessions_dir.glob('*.json'))
        assert len(sessions) == 3

    def test_skip_already_logged_in(self, tmp_path, monkeypatch):
        """skip_existing=True пропускает уже залогиненных."""
        import ig_login_runner as runner
        accounts_dir, sessions_dir = self._setup(tmp_path, monkeypatch, n=3)
        # Создаём существующую сессию для user0
        (sessions_dir / 'user0.json').write_text(json.dumps({'logged_in': True}))
        result = runner.run(skip_existing=True, dry_run=True)
        assert result['skipped'] == 1
        assert result['success'] == 2

    def test_all_flag_ignores_existing(self, tmp_path, monkeypatch):
        """skip_existing=False логинит даже уже залогиненных."""
        import ig_login_runner as runner
        accounts_dir, sessions_dir = self._setup(tmp_path, monkeypatch, n=2)
        (sessions_dir / 'user0.json').write_text(json.dumps({'logged_in': True}))
        result = runner.run(skip_existing=False, dry_run=True)
        assert result['skipped'] == 0
        assert result['success'] == 2

    def test_only_filter(self, tmp_path, monkeypatch):
        """Параметр only логинит только указанный аккаунт."""
        import ig_login_runner as runner
        self._setup(tmp_path, monkeypatch, n=3)
        result = runner.run(only='user1', dry_run=True)
        assert result['success'] == 1

    def test_empty_accounts_returns_zeros(self, tmp_path, monkeypatch):
        """Нет аккаунтов → нулевой результат."""
        import ig_login_runner as runner
        accounts_dir = tmp_path / 'accounts'
        accounts_dir.mkdir()
        monkeypatch.setattr(runner, 'ACCOUNTS_DIR', accounts_dir)
        monkeypatch.setattr(runner, 'SESSIONS_DIR', tmp_path / 'sessions')
        result = runner.run(dry_run=True)
        assert result == {'success': 0, 'skipped': 0, 'failed': 0}
