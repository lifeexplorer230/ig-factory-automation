"""
ADB Client — управление виртуальным Android-телефоном через ADB.

Извлечён из ig-warmup.py (24.02.2026).

ВАЖНО — keeper-сессия:
  MoreLogin требует открытой интерактивной ADB-сессии перед выполнением команд.
  Без keeper: обычный `adb shell cmd` → "error: closed".
  Механизм: `adb shell <password>` открывает интерактивный процесс,
  пока он жив — параллельные `adb shell` команды работают нормально.
"""
import re
import subprocess
import time
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


class AdbClient:
    """Управление Android-устройством через ADB."""

    def __init__(self, ip: str, port: int, password: str):
        self.ip       = ip
        self.port     = port
        self.password = password
        self.addr     = f"{ip}:{port}"
        self._keeper: Optional[subprocess.Popen] = None
        self._ui_xml_path = Path('/tmp/_ig_ui.xml')

    # ── Подключение ───────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Подключиться к устройству и открыть keeper-сессию."""
        subprocess.run(['adb', 'disconnect'], capture_output=True)
        time.sleep(0.5)
        subprocess.run(['adb', 'connect', self.addr], capture_output=True)
        time.sleep(1.5)
        self._start_keeper()

    def disconnect(self) -> None:
        """Закрыть keeper и отключиться."""
        self._stop_keeper()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    def _start_keeper(self) -> None:
        """Открыть интерактивную keeper-сессию."""
        self._keeper = subprocess.Popen(
            ['adb', '-s', self.addr, 'shell', self.password],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._keeper.stdin.write(b'sleep 600\n')
        self._keeper.stdin.flush()
        time.sleep(1.5)

        r = subprocess.run(
            ['adb', '-s', self.addr, 'shell', 'echo', 'ok'],
            capture_output=True, text=True, timeout=5,
        )
        if 'ok' not in r.stdout:
            raise RuntimeError(f'ADB keeper не работает: {r.stderr}')

    def _stop_keeper(self) -> None:
        if self._keeper:
            try:
                self._keeper.kill()
            except Exception:
                pass
            self._keeper = None

    # ── Shell-команды ─────────────────────────────────────────────────────────

    def sh(self, cmd: str, timeout: int = 15) -> str:
        """Выполнить shell-команду, вернуть stdout."""
        r = subprocess.run(
            ['adb', '-s', self.addr, 'shell', cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip()

    def push(self, local_path: str, remote_path: str) -> None:
        """Скопировать файл на устройство."""
        subprocess.run(
            ['adb', '-s', self.addr, 'push', local_path, remote_path],
            capture_output=True,
        )

    def pull(self, remote_path: str, local_path: str) -> None:
        """Скачать файл с устройства."""
        subprocess.run(
            ['adb', '-s', self.addr, 'pull', remote_path, local_path],
            capture_output=True,
        )

    # ── Жесты ─────────────────────────────────────────────────────────────────

    def tap(self, x: int, y: int, jitter: int = 12) -> None:
        """Тап с небольшим случайным смещением для уникальности."""
        rx = x + random.randint(-jitter, jitter)
        ry = y + random.randint(-jitter, jitter)
        self.sh(f'input tap {rx} {ry}')

    def swipe(self, x1: int, y1: int, x2: int, y2: int,
              duration_ms: Optional[int] = None) -> None:
        """Свайп между двумя точками."""
        ms = duration_ms or random.randint(280, 480)
        self.sh(f'input swipe {x1} {y1} {x2} {y2} {ms}')

    def key(self, keycode: int) -> None:
        """Нажать кнопку (keyevent)."""
        self.sh(f'input keyevent {keycode}')

    def type_text(self, text: str) -> None:
        """Ввести текст (без спецсимволов — используй key для Enter и т.д.)."""
        self.sh(f'input text "{text}"')

    @staticmethod
    def sleep(lo: float, hi: float) -> float:
        """Пауза с человеческим рандомом."""
        t = random.uniform(lo, hi)
        time.sleep(t)
        return t

    # ── UI Automator ──────────────────────────────────────────────────────────

    def ui_dump(self) -> str:
        """Сделать дамп UI и вернуть XML строку."""
        self.sh('uiautomator dump /sdcard/_ui.xml', timeout=15)
        self.pull('/sdcard/_ui.xml', str(self._ui_xml_path))
        return self._ui_xml_path.read_text(errors='ignore')

    def find_node(self, text: Optional[str] = None,
                  cls: Optional[str] = None,
                  res_id: Optional[str] = None,
                  desc: Optional[str] = None) -> Optional[tuple]:
        """
        Найти узел в последнем ui_dump.
        Возвращает (cx, cy, bounds) или None.
        """
        if not self._ui_xml_path.exists():
            return None
        try:
            tree = ET.parse(str(self._ui_xml_path))
            for node in tree.iter('node'):
                if text   and text   not in node.get('text', ''):        continue
                if cls    and cls    not in node.get('class', ''):       continue
                if res_id and res_id not in node.get('resource-id', ''): continue
                if desc   and desc   not in node.get('content-desc', ''): continue
                bounds = node.get('bounds', '')
                m = re.findall(r'\d+', bounds)
                if m and len(m) == 4:
                    cx = (int(m[0]) + int(m[2])) // 2
                    cy = (int(m[1]) + int(m[3])) // 2
                    return cx, cy, bounds
        except Exception:
            pass
        return None

    def xml_contains(self, text: str) -> bool:
        """Проверить, есть ли текст в последнем ui_dump."""
        if not self._ui_xml_path.exists():
            return False
        try:
            return text in self._ui_xml_path.read_text(errors='ignore')
        except Exception:
            return False

    def screenshot(self, local_path: str = '/tmp/_ig_screen.png') -> None:
        """Сделать скриншот и скачать на локальную машину."""
        self.sh('screencap -p /sdcard/_sc.png', timeout=15)
        self.pull('/sdcard/_sc.png', local_path)

    # ── Пакеты ───────────────────────────────────────────────────────────────

    def is_package_installed(self, package: str) -> bool:
        """Проверить, установлен ли пакет."""
        return package in self.sh(f'pm list packages | grep {package}')

    def start_app(self, package: str) -> None:
        """Запустить приложение через monkey."""
        self.sh(f'monkey -p {package} 1', timeout=10)
