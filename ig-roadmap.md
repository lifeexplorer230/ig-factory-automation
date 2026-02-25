# IG Content Factory — Roadmap & Lessons Learned

> Автоматическая публикация контента на 100 Instagram аккаунтов (300 постов/день)
> Стек: MoreLogin Cloud Phone + ADB + UIAutomator + Python

---

## Статус фаз

| Фаза | Описание | Статус |
|------|----------|--------|
| **Phase 0** | 1 телефон, 1 аккаунт, 1 пост вручную через скрипт | ✅ Готово |
| **Phase 1** | 5 аккаунтов, автоматический цикл | 🔲 Следующий |
| **Phase 2** | 20 аккаунтов, очередь задач, мониторинг | 🔲 |
| **Phase 3** | 100 аккаунтов, 300 постов/день, полный продакшен | 🔲 |

---

## Phase 0 — Итог

**Что сделано:**
- Поднят облачный телефон MoreLogin (CP-6, Android)
- Установлен Instagram через MoreLogin API
- Логин в аккаунт через ADB + UIAutomator (включая TOTP 2FA и device-approval)
- Опубликован первый пост (`https://files.catbox.moe/ex6qmf.png`)
- Прогрев: 295 секунд, 25 рилов, 1 лайк
- Смена аватарки профиля через Edit Profile → Choose from library
- Смена username: `pulse.uw3489k2vip080332` → `serhioklmani`
- Скрипт: `/home/roma/ig-warmup.py`

---

## Файлы проекта

```
/home/roma/
├── ig-warmup.py            # Основной скрипт (Phase 0–1)
├── ig-roadmap.md           # Этот файл
└── morelogin-cloud-api.js  # Node.js утилита для MoreLogin API (вспомогательная)
```

---

## MoreLogin API — Полный справочник

### Аутентификация

```python
POST https://api.morelogin.com/oauth2/token
{
  "client_id":     1689105551924663,  # INTEGER! не строка — иначе 401
  "client_secret": "b4d061d5c7a24fac84d6f5f3c177e844",
  "grant_type":    "client_credentials"
}
# → data.access_token  (живёт ~3600с)
# Заголовок: Authorization: Bearer <token>
```

**Критично:** `client_id` — число, не строка. Строка даёт 401 без объяснений.

### URL и пути

```
Base: https://api.morelogin.com
# Нет /api/ префикса! Правильно:
POST /cloudphone/page
POST /cloudphone/create
POST /cloudphone/powerOn
# Неправильно: /api/cloudphone/page  → 404
```

### Телефоны — CRUD

```python
# Список
POST /cloudphone/page  {"current": 1, "size": 50}
# → data.dataList[].{id, envName, envStatus, adbInfo, proxyId}

# Создать
POST /cloudphone/create
{
  "envName": "CP-6",
  "quantity": 1,
  "skuId": "10004",      # тариф
  "proxyId": "1689264898338740"
}
# → data: [phone_id_str, ...]

# Включить
POST /cloudphone/powerOn  {"id": 1689270659160562}

# Выключить
POST /cloudphone/powerOff  {"id": 1689270659160562}

# Удалить
POST /cloudphone/delete  {"ids": [1689270659160562]}
```

### envStatus коды

| Код | Значение |
|-----|----------|
| 0 | New (только создан) |
| 1 | Failed |
| 2 | Stop |
| 3 | Starting |
| 4 | **Running** ✅ |
| 5 | Resetting |

### ADB

```python
# Включить ADB на телефоне (нужно один раз после создания)
POST /cloudphone/updateAdb
{"ids": [1689270659160562], "enableAdb": true}

# После powerOn adbInfo появляется в /cloudphone/page:
# adbInfo: {adbIp, adbPort, adbPassword}
```

### Прокси

```python
# КРИТИЧНО: proxyProvider: 0 обязателен — иначе ошибка 14023
POST /proxyInfo/add
{
  "proxyType": 2,           # 2 = SOCKS5
  "host": "...",
  "port": 53412,
  "proxyProvider": 0,       # ОБЯЗАТЕЛЬНО
  "username": "...",
  "password": "..."
}

# Удаление — тело должно быть RAW JSON массив int, не объект!
POST /proxyInfo/delete
[1689264898338740, 1689264898338741]   # НЕ {"ids": [...]}

# ПРОБЛЕМА: credentials (username/password) через API не сохраняются
# username: null, password: null в ответе
# РЕШЕНИЕ: добавлять прокси через UI MoreLogin вручную
```

### Приложения

```python
# Поиск по названию (не packageName!)
POST /cloudphone/app/page
{"id": phone_id, "appName": "Instagram", "current": 1, "size": 1}
# → data.dataList[0].appVersionList[0].id  = appVersionId

# Установка (appVersionId, не packageName!)
POST /cloudphone/app/install
{"id": phone_id, "appVersionId": "1682134957917431"}
# Instagram v412.0.0.35.87 → appVersionId = 1682134957917431
```

---

## ADB — Механизм MoreLogin Cloud Phone

### Как работает

Стандартный ADB к облачному телефону MoreLogin — **нестандартный**:

```bash
adb shell ls          # → "error: closed"  ❌
adb shell PASSWORD    # → открывает интерактивный shell ✅
```

Пароль (`adbPassword` из API) — это не auth токен системы, а **команда**, которую
нужно передать как аргумент `adb shell`. Она открывает авторизованный shell.

### Keeper-паттерн (единственный рабочий способ)

```python
import subprocess, time

keeper = subprocess.Popen(
    ['adb', '-s', f'{ip}:{port}', 'shell', password],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
keeper.stdin.write(b'sleep 600\n')  # держим stdin открытым
keeper.stdin.flush()
time.sleep(1.5)

# Пока keeper жив → параллельные команды работают нормально:
subprocess.run(['adb', '-s', addr, 'shell', 'echo', 'test'])  # ✅
subprocess.run(['adb', '-s', addr, 'shell', 'pm list packages'])  # ✅
```

**Важно:** Keeper нужно открывать сразу после `powerOn`, пока соединение свежее.
После перезагрузки телефона — открывать новый keeper.

### Типовые команды

```bash
# UI dump для поиска элементов
adb shell uiautomator dump /sdcard/_ui.xml
adb pull /sdcard/_ui.xml /tmp/ig_ui.xml

# Скриншот
adb shell screencap -p /sdcard/_sc.png
adb pull /sdcard/_sc.png /tmp/screen.png

# Тап
adb shell input tap 540 1704

# Свайп (x1 y1 x2 y2 duration_ms)
adb shell input swipe 540 1400 540 400 350

# Ввод текста
adb shell input text "hello_world"

# Клавиши: Enter=66, Tab=61, Back=4
adb shell input keyevent 66

# Запуск приложения
adb shell monkey -p com.instagram.android 1

# Медиасканер
adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE \
  -d file:///sdcard/Pictures/post_content.jpg

# Пуш файла
adb push /tmp/image.jpg /sdcard/Pictures/post_content.jpg
```

---

## Instagram — Логин (3 сценария)

### Сценарий 1: Уже залогинен
```python
# Проверяем наличие tab_bar / bottom_tray в UI dump
if 'com.instagram.android:id/tab_bar' in xml: skip_login()
```

### Сценарий 2: Стандартный логин + TOTP
```
Welcome screen → "I already have an account"
→ Форма: "Phone number, username, or email"  (текст поля)
→ Tab → Password
→ Log in
→ "Enter the 6-digit code" → TOTP код → Continue
→ "Save your login info?" → СОХРАНЯЕМ (Save, не Not now)
→ "Allow access to contacts" → Skip
```

**Текст поля username** (меняется от версии к версии, пробуем по очереди):
- `Phone number, username, or email`
- `Username, email or mobile number`
- `Username`
- fallback: любой `EditText`

### Сценарий 3: Device Approval (новый вход с незнакомого устройства)
```
"Check your notifications on another device"
"Waiting for approval"
→ Tap "Try another way"
→ Выбрать "Authentication app" (radio button)
→ Tap "Continue"
→ Ввести TOTP код
→ Включить "Trust this device" (чекбокс)
→ Continue
→ "Save your login info?" → Save
```

### TOTP — нюансы
```python
import pyotp
# Ждать минимум 5 секунд до истечения текущего кода
remaining = 30 - int(time.time()) % 30
if remaining < 5:
    time.sleep(remaining + 1)
code = pyotp.TOTP(secret).now()
```

---

## Instagram — Навигация

### Нав-бар (координаты для нашего телефона)

Instagram обновил навигацию — **два разных лейаута** в зависимости от версии/обновления:

**Старый лейаут (5 кнопок, был при первом запуске):**

| Кнопка | X | Y |
|--------|---|---|
| Home | 108 | 1704 |
| Search | 324 | 1704 |
| **Create (+)** | **540** | **1704** |
| Reels | 756 | 1704 |
| Profile | 972 | 1704 |

**Новый лейаут (после popup "Swipe to easily access Reels"):**

| Кнопка | X | Y |
|--------|---|---|
| Home | 108 | 1704 |
| Reels | 324 | 1704 |
| Message | 540 | 1704 |
| Search | 756 | 1704 |
| Profile | 972 | 1704 |

> Create (+) в новом лейауте — через долгое нажатие на кнопку сверху или другой путь (TODO).
> При появлении popup "Swipe to easily access Reels" — нажать "Got it" перед навигацией.
> Разрешение экрана: 1080×1776 (с учётом нав-бара снизу)

### Публикация фото — правильный порядок

```
1. push image → /sdcard/Pictures/post_content.jpg
2. am broadcast MEDIA_SCANNER_SCAN_FILE
3. Tap Create (540, 1704)
4. Dropdown "Recents" → выбрать альбом "Pictures"
   (в Recents будут скриншоты, в Pictures — наш файл)
5. Первое фото уже выбрано → Next (994, 84)
6. Экран фильтров → Next (949, 1853)
7. Экран caption:
   - Закрыть popup "Sharing posts" → OK
   - Tap Share (540, 1854)
8. Celebration screen "Your first post" → Dismiss
```

### Получение URL поста
```
Profile → тапнуть пост → ⋯ (More actions) → Copy link
→ буфер обмена или logcat grep instagram.com/p/
```
> logcat часто не содержит URL — нужен более надёжный метод (TODO)

### Редактирование профиля

```
Profile → "Edit profile"
→ Tap "Edit profile picture" → выбрать источник
→ "Choose from library" → галерея открывается в Recents
→ Первый файл (самый новый) уже выбран → Done
→ Автоматически возвращает на Edit profile с новой аватаркой

Смена username:
→ Tap поле Username → открывается отдельный экран
→ Очистить: MOVE_END + 50x DEL (Ctrl+A ненадёжен)
→ input text "новый_ник"  (Instagram → lowercase автоматически)
→ Done (галочка, верхний правый угол) → возврат на Edit profile
→ Back (или keyevent 4) → изменения сохраняются автоматически
```

**Нюансы Edit profile:**
- Нет отдельной кнопки "Save" на главном экране Edit profile — всё сохраняется при Back
- Username всегда lowercase — Instagram не принимает заглавные буквы
- При смене username IG предупреждает: "можно вернуть старый ник в течение 14 дней"
- `Ctrl+A` для select-all ненадёжен в Instagram полях → лучше `MOVE_END + N*DEL`

### Скачивание файлов на телефон

catbox.moe недоступен с сервера напрямую (SSL ошибка). Два рабочих способа:

```bash
# Способ 1: скачать через сам телефон (у него есть интернет через прокси)
adb shell curl -L -o /sdcard/Pictures/avatar.jpg "https://files.catbox.moe/xxx.png"

# Способ 2: через внешний HTTP-прокси (если доступен)
curl -L --proxy http://user:pass@host:port -o /tmp/file.png "https://..."
```

---

## Прогрев — Алгоритм

```
Длительность: random(270, 300) секунд  = 4:30–5:00 мин

На каждый рил:
  40% → смотрим полностью: random(8, 25) секунд
  60% → пролистываем:      random(2, 7) секунд

  Если смотрели полностью:
    20% шанс лайка (двойной тап по центру с jitter ±60px)

  Свайп вверх: random(250, 450) мс

Координаты свайпа: (540, 1400) → (540, 400)
```

**Уникальность на 100 аккаунтов:**
- Разное total_sec (random каждый раз)
- Разный watch/skip выбор (random.random())
- Jitter ±12px на все тапы
- Разная длительность свайпа

---

## Текущий аккаунт (Phase 0)

```
username:   serhioklmani  (было: pulse.uw3489k2vip080332)
password:   neon.8u8.040f5xxx098836
totp:       65UAPGF7HWR5DBECBP5A3GUIH6PDY4GY
proxy_id:   1689264898338740   (SOCKS5, добавлена через UI MoreLogin)
phone_name: CP-6
phone_id:   1689270659160562
```

> Прокси добавлена через UI (не API) — только так сохраняются credentials.
> Instagram приводит username к lowercase — "SerhioKlmani" становится "serhioklmani".

---

## Известные проблемы и TODO

### Критичные для Phase 1

- [ ] **URL поста** — logcat не всегда содержит URL. Нужен надёжный способ:
  копировать ссылку через UI (More actions → Copy link) + читать clipboard
- [ ] **Telegram уведомления** — настроить `TG_BOT_TOKEN` + `TG_CHAT_ID`
- [ ] **Phone timeout** — MoreLogin останавливает телефон через ~30–40 мин.
  Нужен watchdog или укладываться в сессию
- [ ] **Прокси через API** — credentials не сохраняются. Для 100 аккаунтов
  нужно либо добавлять через UI, либо найти правильный API-формат

### Для Phase 2+

- [ ] Очередь задач (Redis/RabbitMQ или простой JSON список)
- [ ] Параллельный запуск N телефонов (MoreLogin поддерживает concurrent)
- [ ] База аккаунтов: username / password / totp / proxy_id / phone_name / status
- [ ] Ротация контента: откуда брать картинки/видео для каждого поста
- [ ] Мониторинг: забанен ли аккаунт, прошёл ли пост
- [ ] Retry логика при ошибках ADB / API
- [ ] Логирование в файл с timestamp

### Технический долг

- [ ] `ig_post_image()` — не умеет публиковать видео (только фото)
- [ ] Нет обработки "Account suspended" / "Action blocked" экранов IG
- [ ] Координаты нав-бара хардкодены — могут отличаться при другом разрешении
- [ ] Нав-бар меняется после popup "Swipe to easily access Reels" — нужна детекция лейаута
- [ ] Автоматизация смены аватарки и username не добавлена в ig-warmup.py (пока делалось вручную)

---

## Инфраструктура

### MoreLogin

- **Dashboard:** https://app.morelogin.com
- **API docs:** https://www.morelogin.com/docs (Open Platform)
- **AppId:** 1689105551924663
- **Proxy (UI-добавленная):** ID 1689264898338740, SOCKS5, port 53412

### Запуск скрипта

```bash
# Установить зависимости (один раз)
pip install pyotp
apt install android-tools-adb

# Запуск
python3 /home/roma/ig-warmup.py /path/to/image.jpg

# С Telegram
TG_BOT_TOKEN=xxx TG_CHAT_ID=yyy python3 ig-warmup.py image.jpg
```

### Полезные команды отладки

```bash
# Проверить ADB подключение
adb devices

# Открыть keeper вручную
echo 'sleep 600' | adb -s IP:PORT shell PASSWORD &
sleep 2
adb -s IP:PORT shell echo test   # должно вернуть "test"

# Скриншот вручную
adb -s IP:PORT shell screencap -p /sdcard/_sc.png
adb pull /sdcard/_sc.png /tmp/screen.png

# UI dump вручную
adb -s IP:PORT shell uiautomator dump /sdcard/_ui.xml
adb pull /sdcard/_ui.xml /tmp/ui.xml
```

---

*Обновлено: 2026-02-24 (сессия 2 — редактирование профиля)*
