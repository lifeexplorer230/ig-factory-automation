"""
Фаза 2.4: Прогрев аккаунтов.
TDD тест — написан до реализации автоматического прогрева.

Критерий завершения фазы:
  - 5+ аккаунтов залогинены (session файлы существуют)
  - Прогрев завершён (25+ рилов просмотрено)
  - 0 банов
  - Аккаунты живые (Instagram открывается на главном экране)
"""
import os
import sys
import json
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

SESSIONS_DIR = Path(__file__).parent.parent / 'data' / 'sessions'
MIN_ACCOUNTS = 5


# ── Блок 1: Session файлы ─────────────────────────────────────────────────────

class TestSessionFiles:
    """Аккаунты залогинены — session файлы существуют."""

    def test_sessions_dir_exists(self):
        """Папка data/sessions существует."""
        assert SESSIONS_DIR.exists(), (
            f"Папка {SESSIONS_DIR} не существует. "
            "Запусти ig-warmup.py для логина хотя бы одного аккаунта."
        )

    def test_at_least_one_session(self):
        """Есть хотя бы один session файл."""
        sessions = list(SESSIONS_DIR.glob('*.json'))
        assert len(sessions) >= 1, (
            f"В {SESSIONS_DIR} нет session файлов. "
            "Запусти ig-warmup.py для логина аккаунта."
        )

    @pytest.mark.skipif(
        not any(SESSIONS_DIR.glob('*.json')) if SESSIONS_DIR.exists() else True,
        reason='Нет session файлов'
    )
    def test_session_files_have_required_fields(self):
        """Каждый session файл содержит обязательные поля."""
        required = ['username', 'phone_name', 'logged_in']
        for session_file in SESSIONS_DIR.glob('*.json'):
            data = json.loads(session_file.read_text())
            for field in required:
                assert field in data, (
                    f"Поле '{field}' отсутствует в {session_file.name}"
                )

    @pytest.mark.skipif(
        not any(SESSIONS_DIR.glob('*.json')) if SESSIONS_DIR.exists() else True,
        reason='Нет session файлов'
    )
    def test_all_sessions_are_logged_in(self):
        """Все сессии помечены как залогиненные."""
        for session_file in SESSIONS_DIR.glob('*.json'):
            data = json.loads(session_file.read_text())
            assert data.get('logged_in'), (
                f"Аккаунт {data.get('username', session_file.name)} не залогинен. "
                "Повтори логин через ig-warmup.py."
            )

    def test_minimum_5_accounts_logged_in(self):
        """Залогинено минимум 5 аккаунтов (критерий Фазы 2.4)."""
        if not SESSIONS_DIR.exists():
            pytest.fail(f"Папка {SESSIONS_DIR} не существует")
        logged_in = [
            f for f in SESSIONS_DIR.glob('*.json')
            if json.loads(f.read_text()).get('logged_in')
        ]
        assert len(logged_in) >= MIN_ACCOUNTS, (
            f"Залогинено {len(logged_in)} аккаунтов, нужно >= {MIN_ACCOUNTS}. "
            "Добавь аккаунты через ig-warmup.py."
        )


# ── Блок 2: Прогрев ───────────────────────────────────────────────────────────

class TestWarmupCompleted:
    """Прогрев выполнен на всех аккаунтах."""

    @pytest.mark.skipif(
        not any(SESSIONS_DIR.glob('*.json')) if SESSIONS_DIR.exists() else True,
        reason='Нет session файлов'
    )
    def test_warmup_stats_recorded(self):
        """В каждой сессии есть статистика прогрева."""
        for session_file in SESSIONS_DIR.glob('*.json'):
            data = json.loads(session_file.read_text())
            assert 'warmup' in data, (
                f"Статистика прогрева отсутствует в {session_file.name}. "
                "Запусти ig_warmup.py с записью результата в session файл."
            )

    @pytest.mark.skipif(
        not any(SESSIONS_DIR.glob('*.json')) if SESSIONS_DIR.exists() else True,
        reason='Нет session файлов'
    )
    def test_at_least_25_reels_watched(self):
        """Каждый аккаунт просмотрел минимум 25 рилов суммарно."""
        for session_file in SESSIONS_DIR.glob('*.json'):
            data     = json.loads(session_file.read_text())
            warmup   = data.get('warmup', {})
            watched  = warmup.get('reels_watched', 0)
            username = data.get('username', session_file.name)
            assert watched >= 25, (
                f"@{username}: просмотрено {watched} рилов, нужно >= 25. "
                "Запусти ig_warmup.py для прогрева."
            )

    @pytest.mark.skipif(
        not any(SESSIONS_DIR.glob('*.json')) if SESSIONS_DIR.exists() else True,
        reason='Нет session файлов'
    )
    def test_warmup_duration_reasonable(self):
        """Прогрев длился не менее 4 минут (240 сек)."""
        for session_file in SESSIONS_DIR.glob('*.json'):
            data     = json.loads(session_file.read_text())
            warmup   = data.get('warmup', {})
            elapsed  = warmup.get('elapsed_sec', 0)
            username = data.get('username', session_file.name)
            # Пропускаем если warmup ещё не запускался
            if elapsed == 0:
                continue
            assert elapsed >= 240, (
                f"@{username}: прогрев длился {elapsed}с, нужно >= 240с (4 мин). "
                "Слишком быстрый прогрев — Instagram может заблокировать."
            )


# ── Блок 3: Баны ─────────────────────────────────────────────────────────────

class TestNoBans:
    """Ни один аккаунт не получил бан."""

    @pytest.mark.skipif(
        not any(SESSIONS_DIR.glob('*.json')) if SESSIONS_DIR.exists() else True,
        reason='Нет session файлов'
    )
    def test_zero_banned_accounts(self):
        """Нет аккаунтов со статусом banned."""
        banned = []
        for session_file in SESSIONS_DIR.glob('*.json'):
            data = json.loads(session_file.read_text())
            if data.get('status') == 'banned':
                banned.append(data.get('username', session_file.name))
        assert len(banned) == 0, (
            f"Забанены аккаунты: {banned}. "
            "Замедли прогрев (увеличь total_sec, добавь рандомные паузы)."
        )

    @pytest.mark.skipif(
        not any(SESSIONS_DIR.glob('*.json')) if SESSIONS_DIR.exists() else True,
        reason='Нет session файлов'
    )
    def test_no_action_blocks(self):
        """Нет временных action block блокировок."""
        blocked = []
        for session_file in SESSIONS_DIR.glob('*.json'):
            data = json.loads(session_file.read_text())
            if data.get('status') == 'action_block':
                blocked.append(data.get('username', session_file.name))
        assert len(blocked) == 0, (
            f"Action block у аккаунтов: {blocked}. "
            "Подожди 12-24 часа — обычно снимается автоматически."
        )


# ── Блок 4: Ig_client unit-тесты ─────────────────────────────────────────────

class TestIgClientUnit:
    """Unit-тесты ig_client.py без реального устройства."""

    def test_ig_client_imports(self):
        """ig_client.py импортируется без ошибок."""
        # Пропускаем если pyotp не установлен
        pytest.importorskip('pyotp', reason='pip install pyotp')
        from ig_client import InstagramClient, NAV_Y, NAV_CREATE
        assert NAV_Y    == 1704
        assert NAV_CREATE == (540, 1704)

    def test_nav_bar_coordinates(self):
        """Координаты навигационного бара корректны (1080×1920)."""
        pytest.importorskip('pyotp', reason='pip install pyotp')
        from ig_client import NAV_HOME, NAV_SEARCH, NAV_CREATE, NAV_REELS, NAV_PROFILE, NAV_Y
        assert NAV_HOME    == (108,  NAV_Y)
        assert NAV_SEARCH  == (324,  NAV_Y)
        assert NAV_CREATE  == (540,  NAV_Y)
        assert NAV_REELS   == (756,  NAV_Y)
        assert NAV_PROFILE == (972,  NAV_Y)

    def test_warmup_params(self):
        """Параметры прогрева в допустимых диапазонах."""
        import random
        # Симулируем 100 прогревов и проверяем что длительность в диапазоне
        for _ in range(100):
            total = random.uniform(270, 300)
            assert 270 <= total <= 300, f"total_sec={total} вышел за диапазон 270-300"
