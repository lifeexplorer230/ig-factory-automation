# 🚀 Руководство по реализации проекта (TDD + Документирование)

> Как работать с проектом: пишем тесты → скрипты → документируем уроки

---

## 📋 Процесс работы (для каждой фазы)

### Шаг 1️⃣: Напиши тест

```bash
# Создай файл теста
touch /home/roma/tests/test_X_X_phase_name.py

# Напиши тест (используй шаблон из TESTING_STRATEGY.md)
# Тест должен проверять критерий завершения фазы
```

**Пример:**
```python
def test_5_phones_created(self):
    """Тест: 5 телефонов созданы в MoreLogin"""
    from morelogin_client import MoreLoginClient
    
    client = MoreLoginClient(os.getenv('MORELOGIN_API_KEY'))
    phones = client.list_phones()
    
    assert len(phones) >= 5, f"Создано {len(phones)} телефонов, ожидалось >= 5"
```

### Шаг 2️⃣: Запусти тест (он падает)

```bash
# Запусти тест
pytest /home/roma/tests/test_X_X_phase_name.py -v

# Результат: FAILED (тест падает, потому что скрипта ещё нет)
```

### Шаг 3️⃣: Напиши скрипт

```bash
# Создай скрипт
touch /home/roma/scripts/script_name.py

# Напиши скрипт, который пройдёт тест
```

**Пример:**
```python
class MoreLoginClient:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def list_phones(self):
        """Возвращает список телефонов"""
        # Реализация
        return phones
```

### Шаг 4️⃣: Запусти тест (он проходит)

```bash
# Запусти тест
pytest /home/roma/tests/test_X_X_phase_name.py -v

# Результат: PASSED ✅
```

### Шаг 5️⃣: Документируй результат

```bash
# Открой PROJECT_JOURNAL.md
nano /home/roma/PROJECT_JOURNAL.md

# Добавь запись о фазе (используй шаблон)
```

**Пример записи:**
```markdown
### Запись 2.1.1 — Создание телефонов

**Дата:** 26.02.2026 15:00  
**Фаза:** 2.1  
**Статус:** ✅ УСПЕХ

**Что делали:**
- Создали 5 виртуальных телефонов в MoreLogin

**Результат:**
- ✅ 5 телефонов созданы

**Гипотеза:**
- Создание телефонов займёт 30 мин

**Реальность:**
- Создание заняло 15 мин

**Урок:**
- MoreLogin API работает быстро

**Действие:**
- ✅ Переходим к следующей фазе
```

### Шаг 6️⃣: Переходи к следующей фазе

```bash
# Повтори шаги 1-5 для следующей фазы
```

---

## 📁 Структура проекта

```
/home/roma/
├── TESTING_STRATEGY.md          ← Стратегия тестирования (TDD)
├── PROJECT_JOURNAL.md           ← Журнал всех уроков и ошибок
├── IMPLEMENTATION_GUIDE.md      ← Этот файл
│
├── tests/                       ← Все тесты
│   ├── __init__.py
│   ├── conftest.py              ← Общие фикстуры
│   ├── test_1_1_api_keys.py
│   ├── test_1_2_single_video.py
│   ├── test_1_3_batch_videos.py
│   ├── test_2_1_phones_ready.py
│   ├── test_2_4_warmup.py
│   └── test_3_1_first_publication.py
│
├── scripts/                     ← Все скрипты
│   ├── nano_banana_client.py
│   ├── kling_client.py
│   ├── google_drive_client.py
│   ├── content_pipeline.py
│   ├── morelogin_client.py
│   ├── multi_account_login.py
│   ├── ig_warmup.py
│   ├── multi_account_publisher.py
│   └── ...
│
├── data/                        ← Данные
│   ├── models/                  ← Сгенерированные модели
│   ├── videos/                  ← Готовые видео
│   ├── queue/                   ← Очередь на публикацию
│   ├── sessions/                ← Session cookies
│   ├── logs/                    ← Локальные логи
│   └── backups/                 ← Резервные копии
│
└── config.json                  ← Конфигурация проекта
```

---

## 🧪 Команды для тестирования

### Запустить все тесты
```bash
pytest /home/roma/tests/ -v
```

### Запустить тесты конкретной фазы
```bash
pytest /home/roma/tests/test_1_2_single_video.py -v
```

### Запустить тесты с покрытием кода
```bash
pytest /home/roma/tests/ --cov=/home/roma/scripts --cov-report=html
```

### Запустить тесты с выводом логов
```bash
pytest /home/roma/tests/ -v -s
```

### Запустить только падающие тесты
```bash
pytest /home/roma/tests/ -v --lf
```

---

## 📊 Критерии завершения каждой фазы

| Фаза | Критерий | Тест |
|------|----------|------|
| 1.1 | Все API ключи получены | test_1_1_api_keys.py ✅ |
| 1.2 | 1 видео создано | test_1_2_single_video.py ✅ |
| 1.3 | 10 видео в очереди | test_1_3_batch_videos.py ⏳ |
| 1.4 | Подписи готовы | test_1_4_captions.py ⏳ |
| 1.5 | 50+ видео в очереди | test_1_5_batch_50.py ⏳ |
| 2.1 | 5 телефонов готово | test_2_1_phones_ready.py ✅ |
| 2.2 | 5 аккаунтов куплены | test_2_2_accounts_ready.py ⏳ |
| 2.3 | 5 аккаунтов залогинены | test_2_3_login.py ⏳ |
| 2.4 | 5 аккаунтов прогреты | test_2_4_warmup.py ✅ |
| 2.5 | 25 аккаунтов готово | test_2_5_scale_25.py ⏳ |
| 2.6 | 100 аккаунтов готово | test_2_6_scale_100.py ⏳ |
| 3.1 | Видео опубликовано | test_3_1_first_publication.py ✅ |
| 3.2 | Публикация автоматична | test_3_2_auto_publication.py ⏳ |
| 3.3 | Метрики собираются | test_3_3_analytics.py ⏳ |
| 3.4 | 300 видео/день | test_3_4_scale_300.py ⏳ |
| 3.5 | AI управляет всем | test_3_5_ai_agent.py ⏳ |

---

## 📝 Как документировать уроки

### 1. После каждой успешной фазы
```bash
# Открой PROJECT_JOURNAL.md
nano /home/roma/PROJECT_JOURNAL.md

# Добавь запись:
# - Что делали
# - Результат
# - Гипотеза vs Реальность
# - Урок
# - Действие
```

### 2. После каждой ошибки
```bash
# Открой PROJECT_JOURNAL.md
nano /home/roma/PROJECT_JOURNAL.md

# Добавь запись:
# - Ошибка (что произошло)
# - Причина (почему)
# - Решение (как исправили)
# - Урок (что извлекли)
```

### 3. Коммитни в git
```bash
cd /home/roma
git add PROJECT_JOURNAL.md
git commit -m "Фаза X.X: [краткое описание]"
git push
```

---

## 🎯 Текущий статус

### Завершённые фазы ✅
- [x] 1.1 — Подготовка (API ключи)
- [x] 1.2 — Тест на 1 товаре
- [x] 2.1 — Подготовка (телефоны)
- [x] 2.4 — Прогрев
- [x] 3.1 — Первая публикация

### В процессе ⏳
- [ ] 1.3 — Масштаб на 10 товаров
- [ ] 1.4 — Копирайтинг
- [ ] 1.5 — Масштаб на 50+ видео
- [ ] 2.2 — Закупка аккаунтов
- [ ] 2.3 — Логин
- [ ] 2.5 — Масштаб на 25 аккаунтов
- [ ] 2.6 — Масштаб на 100 аккаунтов
- [ ] 3.2 — Автоматическая публикация
- [ ] 3.3 — Аналитика
- [ ] 3.4 — Масштабирование (300 видео/день)
- [ ] 3.5 — AI-агент

---

## 🚀 Быстрый старт

### День 1
```bash
# 1. Прочитай TESTING_STRATEGY.md
cat /home/roma/TESTING_STRATEGY.md

# 2. Запусти тесты для фазы 1.1
pytest /home/roma/tests/test_1_1_api_keys.py -v

# 3. Если тесты падают, напиши скрипты
# 4. Если тесты проходят, документируй результат
nano /home/roma/PROJECT_JOURNAL.md
```

### День 2+
```bash
# Повтори для каждой фазы:
# 1. Напиши тест
# 2. Запусти тест (он падает)
# 3. Напиши скрипт
# 4. Запусти тест (он проходит)
# 5. Документируй результат
```

---

## 📞 Контакты

| Что | Где |
|-----|-----|
| Тесты | `/home/roma/tests/` |
| Скрипты | `/home/roma/scripts/` |
| Журнал | `/home/roma/PROJECT_JOURNAL.md` |
| Стратегия | `/home/roma/TESTING_STRATEGY.md` |
| Конфиг | `/home/roma/config.json` |

---

> **Версия:** 1.0  
> **Обновлено:** 25.02.2026  
> **Статус:** Готово к использованию ✅
