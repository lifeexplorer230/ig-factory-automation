# 🎬 Дорожная карта по процессам

> Вместо "День 1, День 2..." — делаем по процессам и критериям.
> Когда задача готова (тест зелёный) → переходим к следующей.
>
> **Легенда:** ✅ = сделано | 🔄 = в процессе | ⏳ = ждём Сергея | ❌ = не начато

---

## 🏗️ АРХИТЕКТУРА ПРОЕКТА

### Ключевой принцип: 1 аккаунт = 1 модель

```
Каждый Instagram-аккаунт — это ОТДЕЛЬНАЯ AI-модель (уникальное лицо + тело).
Одна модель публикуется ТОЛЬКО в своём аккаунте.
Ротации аккаунтов нет.
На старте: 10 моделей = 10 аккаунтов.

В будущем (YouTube, TikTok) одна модель может иметь аккаунты на разных
платформах — но в Instagram всегда строго 1:1.
```

### Что уникально для каждого аккаунта:
```
  model_photo.jpg  — AI-сгенерированный персонаж (лицо + тело)
                     Генерируется один раз, используется во всех видео аккаунта.
                     Источник: Midjourney / Stable Diffusion / другой AI-генератор.
```

### Что задаётся на каждое задание (task):
```
  clothing_photo.jpg  — фото одежды (зависит от задания от Сергея)
  source_video.mp4    — исходное видео от оператора (движение + аудио)
```

### Общий пул (потенциально переиспользуется):
```
  data/shared/source_videos/   — видео от оператора (движение + аудио)
  data/shared/clothing/        — фото одежды
  data/shared/backgrounds/     — фото фонов (если нужны)
```

### Поток генерации одного видео:
```
  Входные данные:
  model_photo.jpg  (из аккаунта) ──┐
  clothing_photo.jpg (из задания) ─┤── Nano Banana → модель в одежде
  source_video.mp4 (от оператора) ─┘
        ↓
  Nano Banana: model_photo + clothing_photo
        →  сгенерированное фото: модель Анна в данной одежде
        ↓
  Kling AI: сгенерированное фото + движение из source_video
        →  видео: Анна в одежде, двигается как в source_video, аудио то же
        ↓
  Claude: подпись к видео (@brand_anna, хештеги)
        ↓
  Queue: data/queue/brand_anna/video_001.json
        ↓
  Publisher: → публикует на @brand_anna
```

### Схема данных:
```
data/
  accounts/
    brand_anna.json    → { username, password, totp_secret, model_photo_url }
    brand_sofia.json   → { username, password, totp_secret, model_photo_url }
    ... (10 аккаунтов)

  queue/
    brand_anna/
      video_001.json   → { account, clothing_photo_url, source_video_url,
                            video_url, captions, hashtags, status }
    brand_sofia/
      video_001.json   → { account, clothing_photo_url, source_video_url,
                            video_url, captions, hashtags, status }

  shared/
    source_videos/     — видео от оператора (движение + аудио)
    clothing/          — фото одежды (для заданий)
    backgrounds/       — фото фонов (опционально)

  sessions/
    brand_anna.json    → { username, logged_in, phone_name, warmup, published_posts }
    brand_sofia.json   → { ... }

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ПОТОК 1: КОНТЕНТ-ФАБРИКА          ПОТОК 2: INSTAGRAM-ФАБРИКА │
│  (Генерация видео)                  (Аккаунты и прогрев)        │
│                                                                 │
│  ├─ Nano Banana API ⏳              ├─ MoreLogin Cloud API ✅   │
│  ├─ Kling AI API ⏳                 ├─ ADB + UIAutomator ✅     │
│  ├─ Google Drive ⏳                 ├─ Instagram логин ✅       │
│  ├─ Content Pipeline 🔄            ├─ Прогрев Reels ✅         │
│  └─ Очередь (JSON, per-account) ✅ └─ Session файлы ✅         │
│                                                                 │
│  Результат: 10+ видео на аккаунт    Результат: 5+ аккаунтов   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ПОТОК 3: ПУБЛИКАЦИЯ
                    (Когда оба потока готовы)

                    ├─ multi_account_publisher.py ✅ (написан)
                    ├─ Каждый аккаунт публикует СВОИ видео
                    ├─ Нет ротации — нет общей очереди
                    ├─ Собираем метрики ❌
                    └─ Масштабируем ❌
```

---

## 📊 ПОТОК 1: КОНТЕНТ-ФАБРИКА

### Этап 1.1: Подготовка (Критерий: все ключи получены)

**Скрипты:**
- ✅ `nano_banana_client.py` — заглушка (ждём API ключ)
- ✅ `kling_client.py` — заглушка (ждём API ключ)
- ✅ `google_drive_client.py` — заглушка (ждём credentials)
- ✅ `google_sheets_client.py` — заглушка (ждём credentials + Sheet ID)
- ✅ `morelogin_client.py` — реальная реализация (24.02.2026)

**Тесты:**
- ✅ `test_1_1_api_keys.py` — 12/16 pass | 4 fail (ключи-заглушки)

**Что нужно от Сергея:**
- ⏳ `NANO_BANANA_API_KEY` — реальный ключ
- ⏳ `KLING_API_KEY` — реальный ключ
- ⏳ `GOOGLE_DRIVE_CREDENTIALS` — credentials.json сервисного аккаунта
- ⏳ `GOOGLE_SHEETS_ID` — ID таблицы заданий (из URL таблицы)
- ⏳ `CLAUDE_API_KEY` — реальный ключ (перенесён в Фазу 1.4)
- ⏳ `BRAND_MENTION` — название аккаунта для подписи

**Критерий завершения:**
- [ ] test_1_1_api_keys.py: все 16 тестов зелёные

---

### Этап 1.2: Первое видео (Критерий: 1 видео создано)

**Поток генерации одного видео:**
```
Google Sheets (задание от оператора):
  account=brand_anna, clothing_drive_id=X, source_video_drive_id=Y
        ↓
google_drive_client: скачать clothing.jpg и source_video.mp4
        ↓
nano_banana_client: model_photo (из аккаунта) + clothing.jpg → сгенерированное фото
        ↓
kling_client: сгенерированное фото + source_video.mp4 → итоговое видео
        ↓
caption_generator: подпись с @mention и хештегами
        ↓
data/queue/brand_anna/video_001.json → ready_to_post
```

**Скрипты:**
- ✅ `content_pipeline.py` — написан (dry-run работает, реальный API заглушка)
- ✅ `caption_generator.py` — написан (fallback шаблоны работают, API ждёт ключ)

**Тесты:**
- ✅ `test_1_2_single_video.py` — unit-тесты pass, интеграция skip (ждём ключи)
- ✅ `test_1_4_captions.py` — unit-тесты pass, API-тесты fail (ждём Claude ключ)

**Вопросы (открытые):**
- ❓ Nano Banana API: виртуальная примерка (nakładanie одежды на модель) или генерация с нуля?
- ❓ Kling AI: принимает image + reference_video (движение)? Или только image-to-video?
- ❓ Длина видео: 15 или 30 сек?

**Критерий завершения:**
- [ ] Одно видео создано через реальный API
- [ ] Видео в data/queue/ со статусом ready_to_post
- [ ] test_1_2_single_video.py: все тесты зелёные

---

### Этап 1.3: Масштаб 10 видео (Критерий: 10 видео в очереди)

**Скрипты:**
- ✅ `content_pipeline.py` — поддерживает `--batch products.json`

**Тесты:**
- ✅ `test_1_3_batch_videos.py` — unit-тесты pass, интеграция skip (ждём ключи)

**Вопросы (открытые):**
- ❓ Rate limits Nano Banana API — сколько параллельных запросов?
- ❓ Rate limits Kling AI — сколько параллельных видео?
- ❓ Стоимость генерации 10 видео — нужен бюджет?

**Критерий завершения:**
- [ ] 10 видео в data/queue/ со статусом ready_to_post
- [ ] test_1_3_batch_videos.py: TestQueueHas10Videos зелёный

---

### Этап 1.4: Подписи Claude (Критерий: подписи генерируются)

**Скрипты:**
- ✅ `caption_generator.py` — реальная реализация через Claude API

**Тесты:**
- ✅ `test_1_4_captions.py` — unit/fallback pass, API-тест ждёт ключ

**Что нужно от Сергея:**
- ⏳ `CLAUDE_API_KEY` — реальный ключ

**Критерий завершения:**
- [ ] test_1_4_captions.py: все тесты зелёные

---

## 📊 ПОТОК 2: INSTAGRAM-ФАБРИКА

### Этап 2.1: Телефоны готовы (Критерий: MoreLogin работает)

**Скрипты:**
- ✅ `morelogin_client.py` — реальная реализация (11 открытий из 24.02.2026)
- ✅ `ig-warmup.py` — рабочий скрипт (скопирован с сервера 24.02.2026)

**Тесты:**
- ✅ `test_2_1_phones_ready.py` — 9/13 pass, 4 skip (ADB тесты без запущенного телефона)

**Реальное состояние (25.02.2026):**
- ✅ CP-5 (Stop), CP-6 (Stop) — телефоны существуют
- ✅ 1 мобильный прокси (IP ротируется каждые 30 мин)
- ✅ CP-6 проверен: Instagram установлен, аккаунт pulse.uw3489k2vip080332 залогинен

**Ограничения:**
- ⚠️ Один прокси → нельзя заходить с одного IP в два аккаунта одновременно
- ⚠️ Биллинг по-минутно → минимизировать время работы телефонов
- ⚠️ IP меняется каждые 30 мин → минимум 30 мин между разными аккаунтами

**Критерий завершения:**
- [ ] test_2_1_phones_ready.py: все 13 тестов зелёные (нужен запущенный телефон)

---

### Этап 2.2: Аккаунты куплены (Критерий: 10 credentials готовы)

**Скрипты:**
- нет (покупка/создание аккаунтов — ручная операция)

**Тесты:**
- ✅ `test_2_2_accounts_ready.py` — 0/12 pass (нет data/accounts/ папки)
  Проверяет: username, password, model_photo_url, уникальность модели

**Вопросы (открытые):**
- ❓ Откуда берём аккаунты — покупаем готовые или создаём с нуля?
- ❓ У аккаунтов есть TOTP (2FA) или нет?
- ❓ Нужен ли email/SMS доступ для прохождения device approval?
- ❓ Нужно ли 10 разных прокси под 10 аккаунтов или хватит 1 с ротацией?

**Критерий завершения:**
- [ ] 10 JSON-файлов в data/accounts/ с username, password, model_photo_url
- [ ] test_2_2_accounts_ready.py: все тесты зелёные

---

### Этап 2.3: Логин (Критерий: 5 аккаунтов залогинены)

**Скрипты:**
- ✅ `ig_client.py` — login() с 3 сценариями (TOTP / device approval / уже залогинен)
- ✅ `adb_client.py` — ADB wrapper (keeper session, tap/swipe/ui_dump)

**Тесты:**
- ✅ `test_2_3_login.py` — unit-тесты pass, данные ждут (нет data/accounts/)

**Урок из 24.02.2026:**
- Сценарий B (device approval) требует: "Try another way" → "Authentication app" → TOTP
- TOTP: ждать свежий код если до истечения < 5 сек

**Критерий завершения:**
- [ ] 5 JSON-файлов в data/sessions/ с logged_in=True
- [ ] test_2_3_login.py: все тесты зелёные

---

### Этап 2.4: Прогрев (Критерий: 5 аккаунтов прогреты)

**Скрипты:**
- ✅ `ig_client.py` — warmup_reels() (270–300с, 40% полный просмотр, 20% лайк)

**Тесты:**
- ✅ `test_2_4_warmup.py` — unit-тесты pass, данные ждут (нет sessions)

**Параметры прогрева (проверены 24.02.2026):**
- Длительность: 270–300с (4:30–5:00)
- 40% рилов: смотрим полностью (8–25с)
- 60% рилов: пролистываем (2–7с)
- 20% шанс лайка (двойной тап)

**Критерий завершения:**
- [ ] 5 session-файлов с warmup.reels_watched >= 25
- [ ] test_2_4_warmup.py: все тесты зелёные

---

## 📊 ПОТОК 3: ПУБЛИКАЦИЯ

### Этап 3.1: Первая публикация (Критерий: 1 видео опубликовано)

**Скрипты:**
- ✅ `multi_account_publisher.py` — оркестратор (очередь → телефон → публикация)
  - Поддерживает `--dry-run` для симуляции
  - Поддерживает `--all` для публикации всей очереди

**Тесты:**
- ✅ `test_3_1_first_publication.py` — unit-тесты pass, интеграция ждёт данные

**Вопросы (открытые):**
- ❓ Ждём ли 24 часа после прогрева перед первой публикацией?
- ❓ Сколько постов в день на один аккаунт в начале?
- ❓ Публикуем видео или только фото на старте?
- ❓ Нужна ли подпись с хештегами на первых постах или безопасней без?

**Критерий завершения:**
- [ ] Пост опубликован в Instagram (виден на аккаунте)
- [ ] data/sessions/<account>.json содержит published_posts
- [ ] data/queue/<video>.json имеет status=published
- [ ] test_3_1_first_publication.py: TestPublicationResult зелёный

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ (25.02.2026)

### Тест-сьют

```
Всего тестов: 81
Passing:      37  ✅  (все unit/structure тесты)
Failing:      18  ❌  (ожидаемо — нет данных/ключей)
Skipped:      26  ⏭️  (ADB тесты без запущенного телефона)
```

### Детализация failures (все ожидаемые):

| Тест | Причина | Разблокирует |
|------|---------|-------------|
| test_1_1: nano/kling/gdrive | Заглушки в .env | Сергей: API ключи |
| test_1_4: claude key + captions | Заглушка в .env | Сергей: Claude ключ |
| test_2_2: accounts | Нет data/accounts/ | Купить/создать 5 аккаунтов |
| test_2_3: login | Нет data/accounts/ | После 2.2 |
| test_2_4: sessions | Нет data/sessions/ | После 2.3 + логин |
| test_3_1: queue + sessions + posts | Нет данных | После 1.3 + 2.4 |

### Файлы проекта

```
scripts/
  adb_client.py          ✅ реальный (ADB управление)
  ig_client.py           ✅ реальный (Instagram: логин, пост, прогрев)
  ig-warmup.py           ✅ реальный (полный цикл, 24.02.2026)
  morelogin_client.py    ✅ реальный (MoreLogin Cloud API)
  caption_generator.py   ✅ реальный (Claude API + fallback шаблоны)
  content_pipeline.py    🔄 stub (dry-run работает, API заглушки)
  multi_account_publisher.py  ✅ реальный (готов к использованию)
  nano_banana_client.py  ⏳ stub (ждём API ключ)
  kling_client.py        ⏳ stub (ждём API ключ)
  google_drive_client.py ⏳ stub (ждём credentials)

tests/
  test_1_1_api_keys.py       ✅
  test_1_2_single_video.py   ✅
  test_1_3_batch_videos.py   ✅
  test_1_4_captions.py       ✅
  test_2_1_phones_ready.py   ✅
  test_2_2_accounts_ready.py ✅
  test_2_3_login.py          ✅
  test_2_4_warmup.py         ✅
  test_3_1_first_publication.py ✅

data/
  sessions/  ✅ папка существует (пустая)
  queue/     ✅ папка существует (пустая)
  videos/    ✅ папка существует (пустая)
  accounts/  ❌ не существует (нужно создать)
```

---

## ❓ ОТКРЫТЫЕ ВОПРОСЫ ДЛЯ СЕРГЕЯ

### API ключи
1. `NANO_BANANA_API_KEY` — реальный ключ
2. `KLING_API_KEY` — реальный ключ
3. `CLAUDE_API_KEY` — реальный ключ
4. `GOOGLE_DRIVE_CREDENTIALS` — путь к credentials.json

### Контент
5. Название бренд-аккаунта (`BRAND_MENTION`, например `@brand_name`)
6. Список первых 10 товаров (название + описание + фото)
7. Откуда фото модели — загружает Сергей или выбираем автоматически?
8. Nano Banana — это виртуальная примерка или генерация модели с нуля?
9. Kling AI — принимает image + reference_video или только image-to-video?
10. Длина видео: 15 сек или 30 сек?

### Модели и аккаунты
11. Откуда аккаунты — покупаем готовые или создаём с нуля?
12. У аккаунтов есть TOTP (2FA) или нет?
13. Нужно ли 10 разных прокси под 10 аккаунтов или хватит 1 с ротацией?
14. ✅ Количество аккаунтов на старте: **10**
15. ✅ Фото модели: **AI-сгенерированный персонаж** (не реальный человек)
    - ❓ Через какой генератор — Midjourney, Stable Diffusion, другой?
    - ❓ Один ракурс или несколько (фронт, полный рост)?
    - ❓ Кто генерирует — Сергей или мы?
16. Название каждого аккаунта (@...) — Сергей придумывает или мы?

### Контент-пул
17. ✅ Исходные видео (движение + аудио): **загружаются на Google Drive оператором**
    - ❓ Оператор — это Сергей сам снимает или отдельный человек?
    - ❓ Формат и разрешение: 9:16, 1080×1920?
18. ✅ Одежда: **зависит от задания, загружается на Google Drive**
19. ✅ Задания: **таблица Google Sheets**
    - Строка = задание: account + clothing_drive_id + source_video_drive_id + status
    - ❓ Кто заполняет таблицу — Сергей вручную или автоматически из каталога?
20. Фон — нейтральный студийный или тематический?

### Публикация
20. Сколько дней прогревать аккаунт перед первой публикацией?
21. Сколько постов в день на один аккаунт в начале?
22. Сначала фото или сразу Reels?

---

## 🎓 УРОКИ

### MoreLogin Cloud API (24.02.2026)
- `client_id` должен быть INTEGER, не строка
- Пути БЕЗ `/api/` префикса (например `/cloudphone/page`, не `/api/cloudphone/page`)
- `proxyInfo/delete` принимает голый JSON array `[id1, id2]`, не объект
- `app/install` требует `appVersionId`, не `packageName`
- `proxyProvider:0` обязателен для SOCKS5 с паролем
- `envStatus`: 0=New, 1=Failed, 2=Stop, 3=Starting, 4=Running, 5=Resetting

### ADB + MoreLogin (24.02.2026)
- ADB требует keeper-сессию: открыть `adb shell <password>` как интерактивный процесс
- Без keeper → "error: closed" на каждой команде
- После создания телефона сразу вызвать `/cloudphone/updateAdb` с `enableAdb:true`

### Instagram автоматизация (24.02.2026)
- Навигационный бар (1080×1920): Home=108 Search=324 Create=540 Reels=756 Profile=972, Y=1704
- Три сценария верификации при логине (см. ig_client.py)
- TOTP: ждать свежий код если до истечения < 5 сек
- Прогрев 4:30–5:00 мин (270–300с) — проверенные параметры

### TDD
- Писать тест ДО скрипта — тест = критерий завершения фазы
- Нарушение: content_pipeline.py написан до test_1_2/test_1_3 → исправлено
- Unit-тесты с monkeypatch позволяют тестировать логику без реальных данных

---

> **Обновлено:** 25.02.2026
> **Статус:** Активно разрабатывается
