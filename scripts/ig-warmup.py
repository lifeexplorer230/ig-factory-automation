#!/usr/bin/env python3
"""
Instagram Warmup & Post — MoreLogin Cloud Phone + ADB
======================================================

Что делает:
  1. Запускает облачный телефон (MoreLogin API)
  2. Включает ADB, открывает keeper-сессию
  3. Устанавливает Instagram если нет
  4. Логинится в аккаунт (включая 2FA и device-approval)
  5. Публикует фото
  6. Прогрев: 4:30–5:00 мин скролл Reels (рандомный, уникальный)
  7. Уведомление в Telegram с URL поста

Запуск:
  python3 ig-warmup.py /path/to/image.jpg

Зависимости:
  pip install pyotp
  apt install android-tools-adb

Открытые вопросы для продакшена:
  - TG_BOT_TOKEN / TG_CHAT_ID через env или secrets
  - Автоматический выбор прокси и телефона для 100 аккаунтов
"""

import subprocess, time, random, json, re, sys, os
import urllib.request
import xml.etree.ElementTree as ET
import pyotp

# ══════════════════════════════════════════════
#  КОНФИГ
# ══════════════════════════════════════════════

MORELOGIN = {
    'appId':     1689105551924663,   # integer, не строка!
    'appSecret': 'b4d061d5c7a24fac84d6f5f3c177e844',
    'api':       'https://api.morelogin.com',
}

TELEGRAM = {
    'bot_token': os.environ.get('TG_BOT_TOKEN', ''),
    'chat_id':   os.environ.get('TG_CHAT_ID', ''),
}

# ══════════════════════════════════════════════
#  MORELOGIN API
# ══════════════════════════════════════════════

_token_cache = {}

def ml_token():
    if _token_cache.get('token') and time.time() < _token_cache.get('exp', 0):
        return _token_cache['token']
    req = urllib.request.Request(
        f'{MORELOGIN["api"]}/oauth2/token',
        data=json.dumps({
            'client_id':     MORELOGIN['appId'],      # ВАЖНО: int, не str
            'client_secret': MORELOGIN['appSecret'],
            'grant_type':    'client_credentials',
        }).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    d = json.loads(urllib.request.urlopen(req).read())
    _token_cache['token'] = d['data']['access_token']
    _token_cache['exp'] = time.time() + 3500
    return _token_cache['token']

def ml(path, body):
    """POST к MoreLogin API"""
    token = ml_token()
    req = urllib.request.Request(
        f'{MORELOGIN["api"]}{path}',
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {token}'},
        method='POST')
    return json.loads(urllib.request.urlopen(req).read())


def phone_start(phone_name, proxy_id=None):
    """Запустить телефон, вернуть (phone_id, adb_info)"""
    phones = ml('/cloudphone/page', {'current': 1, 'size': 50})['data']['dataList']
    phone = next((p for p in phones if p['envName'] == phone_name), None)

    if not phone:
        if not proxy_id:
            raise RuntimeError(f'Телефон {phone_name!r} не найден и proxy_id не задан')
        print(f'  Создаём телефон {phone_name!r}...')
        ids = ml('/cloudphone/create', {
            'envName': phone_name, 'quantity': 1,
            'skuId': '10004', 'proxyId': proxy_id,
        })['data']
        phone_id = int(ids[0])
        ml('/cloudphone/updateAdb', {'ids': [phone_id], 'enableAdb': True})
        phone = {'id': str(phone_id), 'envStatus': 0}

    phone_id = int(phone['id'])

    if phone['envStatus'] == 4:
        # Уже запущен — берём adb info
        adb = phone.get('adbInfo') or {}
    else:
        ml('/cloudphone/powerOn', {'id': phone_id})
        print('  Ждём Running...')
        adb = {}
        for i in range(30):
            time.sleep(5)
            phones = ml('/cloudphone/page', {'current': 1, 'size': 50})['data']['dataList']
            phone = next((x for x in phones if int(x['id']) == phone_id), {})
            es = phone.get('envStatus', 0)
            adb = phone.get('adbInfo') or {}
            print(f'    [{i*5}с] envStatus={es}')
            if es == 4 and adb.get('adbIp'):
                break
            if es in [1, 2] and i > 2:
                raise RuntimeError('Телефон не запустился (status=failed/stop)')

    if not adb.get('adbIp'):
        raise RuntimeError('adbInfo пустой после запуска')

    print(f'  Телефон запущен: {adb["adbIp"]}:{adb["adbPort"]}')
    return phone_id, adb


def phone_stop(phone_id):
    ml('/cloudphone/powerOff', {'id': phone_id})
    print(f'  Телефон {phone_id} выключен')


# ══════════════════════════════════════════════
#  ADB
# ══════════════════════════════════════════════

_keeper = None
_adb_addr = None

def adb_start(ip, port, password):
    """
    Открыть keeper-сессию.

    Механизм MoreLogin:
      - adb shell <password>  →  открывает интерактивный shell (пароль = auth)
      - Обычный adb shell cmd  →  "error: closed" без открытой keeper-сессии
      - Пока keeper жив — параллельные adb shell команды работают нормально
    """
    global _keeper, _adb_addr
    _adb_addr = f'{ip}:{port}'

    subprocess.run(['adb', 'disconnect'], capture_output=True)
    time.sleep(0.5)
    subprocess.run(['adb', 'connect', _adb_addr], capture_output=True)
    time.sleep(1.5)

    _keeper = subprocess.Popen(
        ['adb', '-s', _adb_addr, 'shell', password],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    _keeper.stdin.write(b'sleep 600\n')
    _keeper.stdin.flush()
    time.sleep(1.5)

    r = subprocess.run(['adb', '-s', _adb_addr, 'shell', 'echo', 'ok'],
                       capture_output=True, text=True, timeout=5)
    if 'ok' not in r.stdout:
        raise RuntimeError(f'ADB keeper не работает: {r.stderr}')
    print(f'  ADB keeper OK ({_adb_addr})')


def adb_stop():
    global _keeper
    if _keeper:
        try:
            _keeper.kill()
        except Exception:
            pass
        _keeper = None


def sh(cmd, timeout=15):
    """Выполнить shell-команду через ADB"""
    r = subprocess.run(['adb', '-s', _adb_addr, 'shell', cmd],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def tap(x, y, jitter=12):
    """Тап с небольшим рандомом для уникальности"""
    rx = x + random.randint(-jitter, jitter)
    ry = y + random.randint(-jitter, jitter)
    sh(f'input tap {rx} {ry}')


def swipe(x1, y1, x2, y2, ms=None):
    if ms is None:
        ms = random.randint(280, 480)
    sh(f'input swipe {x1} {y1} {x2} {y2} {ms}')


def sleep_h(lo, hi):
    """Пауза с человеческим рандомом"""
    t = random.uniform(lo, hi)
    time.sleep(t)
    return t


def screenshot(path='/tmp/ig_screen.png'):
    sh('screencap -p /sdcard/_sc.png', timeout=15)
    subprocess.run(['adb', '-s', _adb_addr, 'pull', '/sdcard/_sc.png', path],
                   capture_output=True)


def ui_dump(path='/tmp/ig_ui.xml'):
    sh('uiautomator dump /sdcard/_ui.xml', timeout=15)
    subprocess.run(['adb', '-s', _adb_addr, 'pull', '/sdcard/_ui.xml', path],
                   capture_output=True)


def find_node(text=None, cls=None, res_id=None, desc=None):
    """Найти узел в последнем ui_dump, вернуть (cx, cy, bounds) или None"""
    try:
        tree = ET.parse('/tmp/ig_ui.xml')
        for node in tree.iter('node'):
            if text   and text   not in node.get('text', ''):           continue
            if cls    and cls    not in node.get('class', ''):          continue
            if res_id and res_id not in node.get('resource-id', ''):    continue
            if desc   and desc   not in node.get('content-desc', ''):   continue
            bounds = node.get('bounds', '')
            m = re.findall(r'\d+', bounds)
            if m and len(m) == 4:
                cx = (int(m[0]) + int(m[2])) // 2
                cy = (int(m[1]) + int(m[3])) // 2
                return cx, cy, bounds
    except Exception:
        pass
    return None


def xml_contains(text):
    """Есть ли текст где-то в ui dump"""
    try:
        tree = ET.parse('/tmp/ig_ui.xml')
        xml = ET.tostring(tree.getroot(), encoding='unicode')
        return text in xml
    except Exception:
        return False


# ══════════════════════════════════════════════
#  INSTAGRAM — УСТАНОВКА
# ══════════════════════════════════════════════

def ig_install(phone_id):
    """Установить Instagram если не установлен"""
    if 'instagram' in sh('pm list packages'):
        print('  Instagram уже установлен')
        return

    print('  Ищем Instagram в каталоге...')
    versions = ml('/cloudphone/app/page',
                  {'id': phone_id, 'appName': 'Instagram', 'current': 1, 'size': 1}
                  )['data']['dataList']
    ver_id = versions[0]['appVersionList'][0]['id']
    ml('/cloudphone/app/install', {'id': phone_id, 'appVersionId': str(ver_id)})

    print('  Ждём установки...')
    for _ in range(15):
        time.sleep(10)
        if 'instagram' in sh('pm list packages'):
            print('  Установлен!')
            return
    raise RuntimeError('Instagram не установился за 150с')


# ══════════════════════════════════════════════
#  INSTAGRAM — ЛОГИН
# ══════════════════════════════════════════════

def ig_login(username, password, totp_secret=None):
    """
    Полный логин в Instagram.

    Обрабатывает три сценария экрана 2FA/верификации:
      A) Стандартный TOTP (Enter the 6-digit code)
      B) Device approval (Check your notifications) → Try another way → Auth app
      C) Уже залогинен → пропускаем
    """
    print('  Открываем Instagram...')
    sh('monkey -p com.instagram.android 1', timeout=10)
    sleep_h(4, 6)
    ui_dump()

    # Уже залогинен?
    if xml_contains('com.instagram.android:id/tab_bar') or \
       xml_contains('com.instagram.android:id/bottom_tray'):
        print('  Уже залогинен — пропускаем')
        return

    # Экран приветствия "Join Instagram"
    have_account = find_node(text='I already have an account')
    if have_account:
        print('  Тапаем "I already have an account"...')
        tap(have_account[0], have_account[1])
        sleep_h(2, 3)
        ui_dump()

    # Поле username (несколько вариантов текста у разных версий IG)
    username_pos = (
        find_node(text='Phone number, username, or email') or
        find_node(text='Username, email or mobile number') or
        find_node(text='Username') or
        find_node(cls='EditText')
    )
    if not username_pos:
        screenshot('/tmp/ig_login_debug.png')
        raise RuntimeError('Поле username не найдено — см. /tmp/ig_login_debug.png')

    print('  Вводим логин...')
    tap(username_pos[0], username_pos[1])
    sleep_h(0.8, 1.4)
    sh(f'input text "{username}"')
    sleep_h(0.4, 0.8)

    # Переход к паролю (Tab)
    sh('input keyevent 61')
    sleep_h(0.5, 0.8)
    sh(f'input text "{password}"')
    sleep_h(0.4, 0.8)
    sh('input keyevent 4')   # убираем клавиатуру
    sleep_h(0.5, 1.0)

    # Кнопка Log in
    ui_dump()
    login_btn = find_node(text='Log in')
    if login_btn:
        tap(login_btn[0], login_btn[1])
    else:
        sh('input keyevent 66')  # Enter
    sleep_h(6, 10)

    # ── 2FA / верификация ──────────────────────
    for attempt in range(3):
        ui_dump()

        # A) Стандартный экран TOTP ("Enter the 6-digit code")
        if xml_contains('Enter the 6-digit code') or xml_contains('Authentication code'):
            if not totp_secret:
                raise RuntimeError('Требуется TOTP, но totp_secret не задан')
            _enter_totp(totp_secret)
            sleep_h(5, 8)
            ui_dump()

        # B) Device approval ("Check your notifications on another device")
        elif xml_contains('Check your notifications') or xml_contains('Waiting for approval'):
            print('  Device approval → Try another way...')
            try_another = find_node(text='Try another way')
            if try_another:
                tap(try_another[0], try_another[1])
                sleep_h(2, 3)
                ui_dump()

                # Выбираем "Authentication app"
                auth_app = find_node(text='Authentication app')
                if auth_app:
                    tap(auth_app[0], auth_app[1])
                    sleep_h(0.8, 1.2)
                    # Жмём Continue
                    continue_btn = find_node(text='Continue')
                    if continue_btn:
                        tap(continue_btn[0], continue_btn[1])
                        sleep_h(2, 3)
                    # Вводим TOTP
                    if totp_secret:
                        _enter_totp(totp_secret)
                        sleep_h(5, 8)
                        ui_dump()

        # Выходим если уже дома
        if _ig_on_home():
            break

        # "Save your login info?" → СОХРАНЯЕМ (user requested)
        if xml_contains('Save your login info'):
            save_btn = find_node(text='Save')
            if save_btn:
                print('  Сохраняем login info...')
                tap(save_btn[0], save_btn[1])
                sleep_h(3, 5)
                ui_dump()
            break

        # Синк контактов — Skip
        if xml_contains('Allow access to contacts'):
            skip = find_node(text='Skip')
            if skip:
                tap(skip[0], skip[1])
                sleep_h(1.5, 2.5)
            break

    print('  Логин завершён!')


def _enter_totp(totp_secret):
    """Ввести TOTP код на открытом экране 2FA"""
    # Ждём свежий код (минимум 5 сек до истечения)
    remaining = 30 - int(time.time()) % 30
    if remaining < 5:
        print(f'    Ждём {remaining+1}с для свежего TOTP...')
        time.sleep(remaining + 1)
    code = pyotp.TOTP(totp_secret).now()
    print(f'    TOTP: {code}')

    ui_dump()
    field = find_node(cls='EditText') or find_node(text='Code')
    if field:
        tap(field[0], field[1])
        sleep_h(0.5, 0.9)
    sh(f'input text "{code}"')
    sleep_h(0.4, 0.7)
    sh('input keyevent 4')  # убираем клавиатуру
    sleep_h(0.3, 0.6)

    ui_dump()
    btn = (find_node(text='Continue') or find_node(text='Confirm') or
           find_node(text='Submit') or find_node(text='Next'))
    if btn:
        tap(btn[0], btn[1])


def _ig_on_home():
    """Проверяем, находимся ли на главном экране IG"""
    return (xml_contains('com.instagram.android:id/tab_bar') or
            xml_contains('com.instagram.android:id/bottom_tray') or
            find_node(desc='Home') is not None)


# ══════════════════════════════════════════════
#  INSTAGRAM — ПУБЛИКАЦИЯ ФОТО
# ══════════════════════════════════════════════

def ig_post_image(image_path):
    """
    Опубликовать фото. Возвращает URL поста или None.

    Путь к файлу → на телефон → медиасканер →
    Create (540,1704) → Pictures альбом → Next → Next → Share
    """
    print('  Загружаем изображение на телефон...')
    remote = '/sdcard/Pictures/post_content.jpg'
    subprocess.run(['adb', '-s', _adb_addr, 'push', image_path, remote],
                   capture_output=True)
    sh(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE '
       f'-d file://{remote}')
    sleep_h(2, 3)

    # Открываем Create (кнопка + в нав-баре)
    # Реальные координаты нав-бара: Home=108,1704  Search=324,1704
    # Create=540,1704  Reels=756,1704  Profile=972,1704
    print('  Нажимаем Create (+)...')
    tap(540, 1704, jitter=8)
    sleep_h(2.5, 3.5)

    # Переключаемся на альбом Pictures (там лежит наш файл)
    ui_dump()
    if find_node(text='Recents') and not find_node(text='Pictures'):
        # Тапаем дропдаун "Recents"
        tap(165, 1325, jitter=10)
        sleep_h(1.5, 2.0)
        ui_dump()
    pictures = find_node(text='Pictures')
    if pictures:
        print('  Выбираем альбом Pictures...')
        tap(pictures[0], pictures[1])
        sleep_h(1.5, 2.0)
        ui_dump()

    # Первое фото уже выбрано → Next
    next_btn = find_node(text='Next')
    if next_btn:
        tap(next_btn[0], next_btn[1])
    else:
        tap(994, 84, jitter=15)   # правый верхний угол
    sleep_h(2, 3)

    # Экран фильтров → Next
    ui_dump()
    next_btn2 = find_node(text='Next')
    if next_btn2:
        tap(next_btn2[0], next_btn2[1])
    else:
        tap(949, 1853, jitter=15)  # кнопка Next на фильтрах
    sleep_h(2, 3)

    # Экран caption — закрываем popup если есть
    ui_dump()
    if xml_contains('Sharing posts'):
        ok_btn = find_node(text='OK')
        if ok_btn:
            tap(ok_btn[0], ok_btn[1])
            sleep_h(1, 1.5)

    # Share
    ui_dump()
    share_btn = find_node(text='Share') or find_node(text='Publish')
    if share_btn:
        print('  Публикуем...')
        tap(share_btn[0], share_btn[1])
    else:
        tap(540, 1854, jitter=15)
    sleep_h(6, 9)

    print('  Пост опубликован!')

    # Пробуем получить URL через Copy link
    post_url = _get_post_url()
    return post_url


def _get_post_url():
    """Перейти в профиль → тапнуть пост → ⋯ → Copy link → буфер обмена"""
    try:
        sleep_h(1, 2)
        # Dismiss celebration screen если есть
        ui_dump()
        dismiss = find_node(text='Dismiss')
        if dismiss:
            tap(dismiss[0], dismiss[1])
            sleep_h(1.5, 2)

        # Идём в Profile
        tap(972, 1704, jitter=8)
        sleep_h(2.5, 3.5)
        ui_dump()

        # Тапаем первый пост в грид
        post_thumb = find_node(desc='Photo by')
        if not post_thumb:
            # fallback — первая ячейка грида (примерно)
            post_thumb = (178, 1560, '')
        tap(post_thumb[0], post_thumb[1], jitter=5)
        sleep_h(2, 3)
        ui_dump()

        # Тапаем ⋯ "More actions"
        more = find_node(desc='More actions')
        if not more:
            more = find_node(desc='More options')
        if more:
            tap(more[0], more[1])
            sleep_h(1.5, 2)
            ui_dump()

            # Copy link
            copy_link = find_node(text='Copy link')
            if copy_link:
                tap(copy_link[0], copy_link[1])
                sleep_h(0.8, 1.2)
                # Читаем буфер
                clipboard = sh('content query --uri content://settings/secure '
                               '--where "name=\'clipboard\'" 2>/dev/null')
                # Или через input
                url_from_log = sh('logcat -d -t 100 | grep -o '
                                  '"instagram.com/p/[A-Za-z0-9_-]*"', timeout=8)
                if url_from_log:
                    return f'https://www.{url_from_log.strip().splitlines()[0]}'
    except Exception as e:
        print(f'  (URL не получен: {e})')
    return None


# ══════════════════════════════════════════════
#  INSTAGRAM — ПРОГРЕВ REELS
# ══════════════════════════════════════════════

def ig_warmup_reels(total_sec=None):
    """
    Имитация просмотра Reels.
    total_sec: 270–300 (4:30 – 5:00) рандомно если не задан.
    40% рилов смотрим полностью (8-25с), 60% пролистываем (2-7с).
    20% шанс лайка на полностью просмотренном риле (двойной тап).
    """
    if total_sec is None:
        total_sec = random.uniform(270, 300)

    print(f'  Прогрев Reels: {total_sec:.0f}с...')

    # Переходим в Reels (4-я иконка нав-бара)
    tap(756, 1704, jitter=8)
    sleep_h(2, 3)

    start = time.time()
    n = 0
    while time.time() - start < total_sec:
        remaining = total_sec - (time.time() - start)
        if remaining < 5:
            break

        watch_full = random.random() < 0.4
        watch_t = (random.uniform(8, 25) if watch_full
                   else random.uniform(2, 7))
        watch_t = min(watch_t, remaining - 3)
        if watch_t <= 0:
            break

        n += 1
        print(f'    Рил {n}: {"смотрим" if watch_full else "пропускаем"} '
              f'{watch_t:.1f}с')
        time.sleep(watch_t)

        # Лайк (двойной тап по центру экрана)
        if watch_full and random.random() < 0.2:
            tap(540, 960, jitter=60)
            sleep_h(0.3, 0.5)
            tap(540, 960, jitter=60)
            sleep_h(0.5, 1.0)
            print('    ❤️ лайк')

        # Свайп вверх → следующий рил
        swipe(540, 1400, 540, 400, random.randint(250, 450))
        sleep_h(0.8, 1.5)

    elapsed = time.time() - start
    print(f'  Прогрев: {elapsed:.0f}с, {n} рилов')


# ══════════════════════════════════════════════
#  TELEGRAM
# ══════════════════════════════════════════════

def tg_send(text):
    if not TELEGRAM['bot_token'] or not TELEGRAM['chat_id']:
        print(f'  [TG не настроен] {text}')
        return
    body = json.dumps({'chat_id': TELEGRAM['chat_id'], 'text': text}).encode()
    req = urllib.request.Request(
        f'https://api.telegram.org/bot{TELEGRAM["bot_token"]}/sendMessage',
        data=body, headers={'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(req)
    print(f'  TG: {text}')


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def run(account, image_path):
    """
    account = {
        'username':   'pulse.uw3489k2vip080332',
        'password':   'neon.8u8.040f5xxx098836',
        'totp':       '65UAPGF7HWR5DBECBP5A3GUIH6PDY4GY',
        'proxy_id':   '1689264898338740',   # ID прокси в MoreLogin (UI-добавленная)
        'phone_name': 'CP-6',
    }
    """
    print(f'\n{"="*55}')
    print(f'  Аккаунт: {account["username"]}')
    print(f'{"="*55}')

    phone_id = None
    try:
        # 1. Телефон
        print('\n[1] Запускаем телефон...')
        phone_id, adb = phone_start(account['phone_name'],
                                     account.get('proxy_id'))

        # 2. ADB keeper
        print('\n[2] ADB keeper...')
        adb_start(adb['adbIp'], adb['adbPort'], adb['adbPassword'])

        # 3. Instagram
        print('\n[3] Instagram...')
        ig_install(phone_id)

        # 4. Логин
        print('\n[4] Логин...')
        ig_login(account['username'], account['password'], account.get('totp'))

        # 5. Пост (сначала!)
        print('\n[5] Публикуем пост...')
        post_url = ig_post_image(image_path)
        print(f'  URL: {post_url}')

        # 6. Уведомление
        if post_url:
            tg_send(f'✅ Пост опубликован!\n'
                    f'@{account["username"]}\n{post_url}')
        else:
            tg_send(f'✅ Пост опубликован!\n'
                    f'@{account["username"]}\n(URL не определён)')

        # 7. Прогрев
        print('\n[7] Прогрев Reels...')
        ig_warmup_reels()

    finally:
        adb_stop()
        if phone_id:
            print('\n[8] Выключаем телефон...')
            phone_stop(phone_id)

    print('\n✅ Готово!')
    return post_url


# ══════════════════════════════════════════════

if __name__ == '__main__':
    account = {
        'username':   'pulse.uw3489k2vip080332',
        'password':   'neon.8u8.040f5xxx098836',
        'totp':       '65UAPGF7HWR5DBECBP5A3GUIH6PDY4GY',
        'proxy_id':   '1689264898338740',
        'phone_name': 'CP-6',
    }
    image_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/post_image.png'
    run(account, image_path)
