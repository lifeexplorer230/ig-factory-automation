"""
Instagram Client — логин, публикация, прогрев через ADB.

Извлечён из ig-warmup.py (24.02.2026).
Работает поверх AdbClient.

Проверенные знания:
  - Навигационный бар (1080×1920): Home=108 Search=324 Create=540 Reels=756 Profile=972, Y=1704
  - Логин: 3 сценария верификации (TOTP / device approval / уже залогинен)
  - TOTP: ждать свежий код если до истечения < 5 сек
  - Публикация: фото через Pictures альбом, координата Create = (540, 1704)
  - Прогрев: 270–300с, 40% полный просмотр, 60% пролистывание, 20% лайк
"""
import random
import time
import subprocess
from pathlib import Path
from typing import Optional

import pyotp

from adb_client import AdbClient

# Координаты навигационного бара Instagram (1080×1920)
NAV_Y    = 1704
NAV_HOME    = (108,  NAV_Y)
NAV_SEARCH  = (324,  NAV_Y)
NAV_CREATE  = (540,  NAV_Y)
NAV_REELS   = (756,  NAV_Y)
NAV_PROFILE = (972,  NAV_Y)

IG_PACKAGE = 'com.instagram.android'


class InstagramClient:
    """
    Управляет Instagram на виртуальном телефоне через AdbClient.

    Использование:
        with AdbClient(ip, port, password) as adb:
            ig = InstagramClient(adb)
            ig.install(phone_id, morelogin_client)
            ig.login(username, password, totp_secret)
            ig.post_image('/path/to/image.jpg')
            ig.warmup_reels()
    """

    def __init__(self, adb: AdbClient):
        self.adb = adb

    # ── Установка ─────────────────────────────────────────────────────────────

    def install(self, phone_id: int, morelogin_client) -> None:
        """
        Установить Instagram если ещё не установлен.
        Использует MoreLoginClient для поиска appVersionId.
        """
        if self.adb.is_package_installed(IG_PACKAGE):
            return

        info    = morelogin_client.find_app_version_id(phone_id, 'Instagram')
        ver_id  = info['appVersionId']
        morelogin_client.install_app(phone_id, ver_id)

        for _ in range(15):
            time.sleep(10)
            if self.adb.is_package_installed(IG_PACKAGE):
                return
        raise RuntimeError('Instagram не установился за 150с')

    # ── Логин ─────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str,
              totp_secret: Optional[str] = None) -> None:
        """
        Полный логин в Instagram.

        Три сценария верификации:
          A) Стандартный TOTP — "Enter the 6-digit code"
          B) Device approval — "Check your notifications" → Try another way → Auth app → TOTP
          C) Уже залогинен — пропускаем
        """
        self.adb.start_app(IG_PACKAGE)
        self.adb.sleep(4, 6)
        self.adb.ui_dump()

        # C) Уже залогинен
        if self._on_home():
            return

        # Экран приветствия
        node = self.adb.find_node(text='I already have an account')
        if node:
            self.adb.tap(node[0], node[1])
            self.adb.sleep(2, 3)
            self.adb.ui_dump()

        # Поле username
        username_node = (
            self.adb.find_node(text='Phone number, username, or email') or
            self.adb.find_node(text='Username, email or mobile number') or
            self.adb.find_node(text='Username') or
            self.adb.find_node(cls='EditText')
        )
        if not username_node:
            self.adb.screenshot('/tmp/_ig_login_debug.png')
            raise RuntimeError('Поле username не найдено — см. /tmp/_ig_login_debug.png')

        self.adb.tap(username_node[0], username_node[1])
        self.adb.sleep(0.8, 1.4)
        self.adb.type_text(username)
        self.adb.sleep(0.4, 0.8)
        self.adb.key(61)   # Tab → поле пароля
        self.adb.sleep(0.5, 0.8)
        self.adb.type_text(password)
        self.adb.sleep(0.4, 0.8)
        self.adb.key(4)    # убрать клавиатуру

        self.adb.ui_dump()
        login_btn = self.adb.find_node(text='Log in')
        if login_btn:
            self.adb.tap(login_btn[0], login_btn[1])
        else:
            self.adb.key(66)   # Enter
        self.adb.sleep(6, 10)

        # Верификация (до 3 попыток)
        for _ in range(3):
            self.adb.ui_dump()

            # A) TOTP
            if self.adb.xml_contains('Enter the 6-digit code') or \
               self.adb.xml_contains('Authentication code'):
                if not totp_secret:
                    raise RuntimeError('Требуется TOTP, но totp_secret не задан')
                self._enter_totp(totp_secret)
                self.adb.sleep(5, 8)

            # B) Device approval
            elif self.adb.xml_contains('Check your notifications') or \
                 self.adb.xml_contains('Waiting for approval'):
                try_another = self.adb.find_node(text='Try another way')
                if try_another:
                    self.adb.tap(try_another[0], try_another[1])
                    self.adb.sleep(2, 3)
                    self.adb.ui_dump()
                    auth_app = self.adb.find_node(text='Authentication app')
                    if auth_app:
                        self.adb.tap(auth_app[0], auth_app[1])
                        self.adb.sleep(0.8, 1.2)
                        cont = self.adb.find_node(text='Continue')
                        if cont:
                            self.adb.tap(cont[0], cont[1])
                            self.adb.sleep(2, 3)
                        if totp_secret:
                            self._enter_totp(totp_secret)
                            self.adb.sleep(5, 8)

            if self._on_home():
                break

            # "Save your login info?"
            if self.adb.xml_contains('Save your login info'):
                save = self.adb.find_node(text='Save')
                if save:
                    self.adb.tap(save[0], save[1])
                    self.adb.sleep(3, 5)
                break

            # Синк контактов
            if self.adb.xml_contains('Allow access to contacts'):
                skip = self.adb.find_node(text='Skip')
                if skip:
                    self.adb.tap(skip[0], skip[1])
                    self.adb.sleep(1.5, 2.5)
                break

    def _enter_totp(self, totp_secret: str) -> None:
        """Ввести TOTP код. Ждёт свежий если до истечения < 5 сек."""
        remaining = 30 - int(time.time()) % 30
        if remaining < 5:
            time.sleep(remaining + 1)
        code = pyotp.TOTP(totp_secret).now()

        self.adb.ui_dump()
        field = self.adb.find_node(cls='EditText') or self.adb.find_node(text='Code')
        if field:
            self.adb.tap(field[0], field[1])
            self.adb.sleep(0.5, 0.9)
        self.adb.type_text(code)
        self.adb.sleep(0.4, 0.7)
        self.adb.key(4)
        self.adb.sleep(0.3, 0.6)

        self.adb.ui_dump()
        btn = (self.adb.find_node(text='Continue') or
               self.adb.find_node(text='Confirm')  or
               self.adb.find_node(text='Submit')   or
               self.adb.find_node(text='Next'))
        if btn:
            self.adb.tap(btn[0], btn[1])

    def _on_home(self) -> bool:
        """Проверить, находимся ли на главном экране Instagram."""
        return (
            self.adb.xml_contains('com.instagram.android:id/tab_bar') or
            self.adb.xml_contains('com.instagram.android:id/bottom_tray') or
            self.adb.find_node(desc='Home') is not None
        )

    # ── Публикация ────────────────────────────────────────────────────────────

    def post_image(self, image_path: str) -> Optional[str]:
        """
        Опубликовать фото. Возвращает URL поста или None.

        Флоу: загрузка на телефон → медиасканер →
        Create (540,1704) → альбом Pictures → Next → Next → Share
        """
        remote = '/sdcard/Pictures/post_content.jpg'
        self.adb.push(image_path, remote)
        self.adb.sh(
            f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE '
            f'-d file://{remote}'
        )
        self.adb.sleep(2, 3)

        # Create (+)
        self.adb.tap(*NAV_CREATE, jitter=8)
        self.adb.sleep(2.5, 3.5)

        # Переключиться на Pictures
        self.adb.ui_dump()
        if self.adb.find_node(text='Recents') and not self.adb.find_node(text='Pictures'):
            self.adb.tap(165, 1325, jitter=10)
            self.adb.sleep(1.5, 2.0)
            self.adb.ui_dump()
        pictures = self.adb.find_node(text='Pictures')
        if pictures:
            self.adb.tap(pictures[0], pictures[1])
            self.adb.sleep(1.5, 2.0)
            self.adb.ui_dump()

        # Next (выбор фото)
        nxt = self.adb.find_node(text='Next')
        self.adb.tap(nxt[0], nxt[1]) if nxt else self.adb.tap(994, 84, jitter=15)
        self.adb.sleep(2, 3)

        # Next (фильтры)
        self.adb.ui_dump()
        nxt2 = self.adb.find_node(text='Next')
        self.adb.tap(nxt2[0], nxt2[1]) if nxt2 else self.adb.tap(949, 1853, jitter=15)
        self.adb.sleep(2, 3)

        # Закрыть popup если есть
        self.adb.ui_dump()
        if self.adb.xml_contains('Sharing posts'):
            ok = self.adb.find_node(text='OK')
            if ok:
                self.adb.tap(ok[0], ok[1])
                self.adb.sleep(1, 1.5)

        # Share
        self.adb.ui_dump()
        share = self.adb.find_node(text='Share') or self.adb.find_node(text='Publish')
        self.adb.tap(share[0], share[1]) if share else self.adb.tap(540, 1854, jitter=15)
        self.adb.sleep(6, 9)

        return self._get_post_url()

    def _get_post_url(self) -> Optional[str]:
        """Получить URL опубликованного поста через logcat."""
        try:
            self.adb.sleep(1, 2)
            self.adb.ui_dump()
            dismiss = self.adb.find_node(text='Dismiss')
            if dismiss:
                self.adb.tap(dismiss[0], dismiss[1])
                self.adb.sleep(1.5, 2)

            # Профиль
            self.adb.tap(*NAV_PROFILE, jitter=8)
            self.adb.sleep(2.5, 3.5)
            self.adb.ui_dump()

            # Первый пост
            post = self.adb.find_node(desc='Photo by') or (178, 1560, '')
            self.adb.tap(post[0], post[1], jitter=5)
            self.adb.sleep(2, 3)
            self.adb.ui_dump()

            # ⋯ More actions → Copy link
            more = (self.adb.find_node(desc='More actions') or
                    self.adb.find_node(desc='More options'))
            if more:
                self.adb.tap(more[0], more[1])
                self.adb.sleep(1.5, 2)
                self.adb.ui_dump()
                copy_link = self.adb.find_node(text='Copy link')
                if copy_link:
                    self.adb.tap(copy_link[0], copy_link[1])
                    self.adb.sleep(0.8, 1.2)
                    url = self.adb.sh(
                        'logcat -d -t 100 | grep -o "instagram.com/p/[A-Za-z0-9_-]*"',
                        timeout=8,
                    )
                    if url:
                        return f'https://www.{url.strip().splitlines()[0]}'
        except Exception:
            pass
        return None

    # ── Прогрев ───────────────────────────────────────────────────────────────

    def warmup_reels(self, total_sec: Optional[float] = None) -> dict:
        """
        Имитация просмотра Reels.

        Параметры (проверены на практике 24.02.2026):
          - Длительность: 270–300с (4:30–5:00)
          - 40% рилов: смотрим полностью (8–25с)
          - 60% рилов: пролистываем (2–7с)
          - 20% шанс лайка на полностью просмотренном (двойной тап)

        Возвращает: {'elapsed': сек, 'reels_watched': n, 'likes': n}
        """
        if total_sec is None:
            total_sec = random.uniform(270, 300)

        # Переходим в Reels
        self.adb.tap(*NAV_REELS, jitter=8)
        self.adb.sleep(2, 3)

        start  = time.time()
        reels  = 0
        likes  = 0

        while True:
            remaining = total_sec - (time.time() - start)
            if remaining < 5:
                break

            watch_full = random.random() < 0.4
            watch_t    = (random.uniform(8, 25) if watch_full
                          else random.uniform(2, 7))
            watch_t    = min(watch_t, remaining - 3)
            if watch_t <= 0:
                break

            time.sleep(watch_t)
            reels += 1

            # Лайк — двойной тап по центру
            if watch_full and random.random() < 0.2:
                self.adb.tap(540, 960, jitter=60)
                self.adb.sleep(0.3, 0.5)
                self.adb.tap(540, 960, jitter=60)
                self.adb.sleep(0.5, 1.0)
                likes += 1

            # Свайп вверх → следующий рил
            self.adb.swipe(540, 1400, 540, 400, random.randint(250, 450))
            self.adb.sleep(0.8, 1.5)

        elapsed = time.time() - start
        return {'elapsed': elapsed, 'reels_watched': reels, 'likes': likes}
