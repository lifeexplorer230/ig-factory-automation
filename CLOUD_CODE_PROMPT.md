# 🚀 Промпт для Cloud Code (Развертывание проекта)

> Используй этот промпт в своём Cloud Code на компьютере

---

## Инструкция для Cloud Code

Скопируй весь текст ниже (между линиями) и вставь в Cloud Code:

```
═══════════════════════════════════════════════════════════════════════════════

Ты — Cloud Code Assistant для развертывания проекта Instagram Content Factory.

ТВОЯ ЗАДАЧА:
1. Соединиться с Claude API
2. Получить файлы проекта с сервера (https://github.com/USERNAME/ig-factory-automation или локально)
3. Развернуть проект в отдельной папке на компьютере
4. Настроить окружение (Python venv, зависимости)
5. Инициализировать Git репозиторий
6. Подготовить проект к работе с Claude

ЭТАПЫ РАЗВЕРТЫВАНИЯ:

1️⃣ ПОЛУЧЕНИЕ ФАЙЛОВ

Источники (в порядке приоритета):
a) GitHub репозиторий: https://github.com/USERNAME/ig-factory-automation
   - git clone https://github.com/USERNAME/ig-factory-automation.git
   - или скачать ZIP

b) Локальный сервер: /home/roma/
   - Скопировать файлы через SCP или локально

c) Встроенные файлы:
   - Если файлы встроены в Cloud Code, использовать их

НЕОБХОДИМЫЕ ФАЙЛЫ:
✅ ROADMAP_BY_PROCESSES.md
✅ TESTING_STRATEGY.md
✅ PROJECT_JOURNAL.md
✅ IMPLEMENTATION_GUIDE.md
✅ CHECKLIST_FOR_KLIM.md
✅ FINAL_SUMMARY.md
✅ CLOUD_CODE_SETUP.md
✅ DEPLOYMENT_CHECKLIST.md
✅ CLAUDE_SYSTEM_PROMPT.md
✅ setup.sh
✅ requirements.txt (если есть)

2️⃣ СОЗДАНИЕ СТРУКТУРЫ ПРОЕКТА

На компьютере пользователя:
1. Создать папку: ~/ig-factory-automation
2. Создать подпапки:
   - tests/
   - scripts/
   - data/{models,videos,queue,sessions,logs,backups}
   - docs/
   - .vscode/

3. Скопировать все файлы документации в корень

3️⃣ НАСТРОЙКА PYTHON ОКРУЖЕНИЯ

1. Проверить Python версию: python3 --version (должна быть 3.9+)
2. Создать виртуальное окружение:
   python3 -m venv venv
3. Активировать:
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
4. Обновить pip:
   pip install --upgrade pip
5. Установить зависимости:
   pip install pytest pytest-cov requests aiohttp redis psycopg2-binary anthropic google-auth google-api-python-client python-dotenv

4️⃣ СОЗДАНИЕ КОНФИГУРАЦИОННЫХ ФАЙЛОВ

Создать .env файл:
```
# API Keys
NANO_BANANA_API_KEY=sk_...
KLING_API_KEY=sk_...
GOOGLE_DRIVE_CREDENTIALS=/path/to/credentials.json
MORELOGIN_API_KEY=...
MORELOGIN_APP_ID=1689105551924663
MORELOGIN_APP_SECRET=...

# Database
POSTGRES_URL=postgresql://user:password@localhost:5432/ig_factory
REDIS_URL=redis://localhost:6379

# AI
CLAUDE_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Instagram
BRAND_MENTION=@main_brand_account
```

Создать .gitignore:
```
.env
.env.local
__pycache__/
*.py[cod]
venv/
env/
.vscode/
.idea/
data/models/*
data/videos/*
data/queue/*
data/sessions/*
data/logs/*
data/backups/*
.DS_Store
Thumbs.db
.coverage
.pytest_cache/
htmlcov/
*credentials.json
*secrets*
```

5️⃣ ИНИЦИАЛИЗАЦИЯ GIT

1. Инициализировать репозиторий:
   git init
2. Добавить удалённый репозиторий (опционально):
   git remote add origin https://github.com/USERNAME/ig-factory-automation.git
3. Первый коммит:
   git add .
   git commit -m "Initial commit: TDD project structure"
4. Загрузить в GitHub (если репозиторий создан):
   git push -u origin main

6️⃣ VS CODE КОНФИГУРАЦИЯ

Создать .vscode/settings.json:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "[python]": {
        "editor.formatOnSave": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true
    }
}
```

Создать .vscode/launch.json:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

7️⃣ ПРОВЕРКА УСТАНОВКИ

Выполнить проверки:
1. python3 --version
2. pip list (должны быть все зависимости)
3. pytest tests/ --collect-only -q (если есть тесты)
4. git status
5. git log --oneline

8️⃣ ПОДГОТОВКА К РАБОТЕ С CLAUDE

1. Открыть проект в VS Code:
   code .

2. Установить расширения:
   - Python (Microsoft)
   - Pylance
   - Cloud Code (Google)

3. Прочитать документы:
   - START_HERE.md (5 мин)
   - ROADMAP_BY_PROCESSES.md (30 мин)
   - TESTING_STRATEGY.md (30 мин)

4. Заполнить .env файл с реальными API ключами

5. Создать GitHub репозиторий (если нужно):
   https://github.com/new

6. Загрузить проект в GitHub:
   git add .
   git commit -m "Initial commit"
   git push -u origin main

9️⃣ СОЕДИНЕНИЕ С CLAUDE

1. Скопировать CLAUDE_SYSTEM_PROMPT.md

2. Отправить Claude:
   - Весь текст из CLAUDE_SYSTEM_PROMPT.md
   - Ссылку на GitHub репозиторий
   - Сообщение: "Ты готов начать разработку?"

3. Claude начнёт работать:
   - Писать тесты (TDD)
   - Писать скрипты
   - Документировать уроки
   - Коммитить в GitHub

КОМАНДЫ ДЛЯ БЫСТРОГО СТАРТА:

# Активировать окружение
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Запустить тесты
pytest tests/ -v
pytest tests/test_1_1_api_keys.py -v

# Коммитить изменения
git add .
git commit -m "Фаза X.X: [описание]"
git push origin main

# Открыть в VS Code
code .

ВАЖНЫЕ ПРАВИЛА:

1. Никогда не коммитьте .env файл
2. Всегда проверяйте git status перед коммитом
3. Используйте понятные сообщения коммитов
4. Создавайте отдельный репозиторий для каждого проекта
5. Синхронизируйте с GitHub регулярно

СТАТУС ПРОЕКТА:

Завершённые фазы:
✅ 1.1 — Подготовка (API ключи)
✅ 1.2 — Тест на 1 товаре
✅ 2.1 — Подготовка (телефоны)
✅ 2.4 — Прогрев
✅ 3.1 — Первая публикация

В процессе:
⏳ 1.3 — Масштаб на 10 товаров
⏳ Остальные фазы

ПОДДЕРЖКА:

Если что-то не работает:
1. Проверь логи: tail -f venv/bin/activate.log
2. Проверь Python версию: python3 --version
3. Переустанови зависимости: pip install -r requirements.txt
4. Проверь Git: git status
5. Спроси Claude: "Как решить эту проблему?"

═══════════════════════════════════════════════════════════════════════════════
```

---

## Как использовать этот промпт

### Вариант 1: Cloud Code на VS Code (рекомендуется)

1. **Установи расширение Cloud Code:**
   - Открой VS Code
   - Extensions → поищи "Cloud Code"
   - Установи от Google

2. **Скопируй промпт:**
   - Выдели весь текст выше (между линиями)
   - Ctrl+C (копировать)

3. **Отправь Cloud Code:**
   - Нажми Ctrl+Shift+P
   - Напиши "Cloud Code: Open Command Palette"
   - Вставь промпт (Ctrl+V)
   - Нажми Enter

4. **Cloud Code начнёт развертывание:**
   - Создаст папку `ig-factory-automation`
   - Скачает файлы
   - Настроит окружение
   - Инициализирует Git

### Вариант 2: Через терминал Cloud Code

1. **Открой терминал в Cloud Code**
2. **Запусти команды вручную:**
   ```bash
   mkdir ig-factory-automation
   cd ig-factory-automation
   git clone https://github.com/USERNAME/ig-factory-automation.git .
   bash setup.sh
   ```

### Вариант 3: Через Cloud Code API

Если у тебя есть доступ к Cloud Code API:

```python
import cloud_code

# Инициализировать проект
project = cloud_code.Project(
    name="ig-factory-automation",
    path="~/ig-factory-automation",
    git_url="https://github.com/USERNAME/ig-factory-automation.git"
)

# Развернуть
project.deploy()

# Подключить Claude
project.connect_claude(
    api_key="sk-...",
    system_prompt=open("CLAUDE_SYSTEM_PROMPT.md").read()
)
```

---

## Что произойдёт после развертывания

1. **Проект готов:**
   - Папка `~/ig-factory-automation` с полной структурой
   - Python окружение настроено
   - Git инициализирован
   - Все файлы на месте

2. **Cloud Code подключится к Claude:**
   - Отправит CLAUDE_SYSTEM_PROMPT.md
   - Claude получит инструкции
   - Claude начнёт работать по TDD

3. **Ежедневный цикл:**
   - Claude пишет тесты
   - Claude пишет скрипты
   - Claude документирует уроки
   - Cloud Code коммитит в GitHub
   - Ты получаешь отчёты

---

## Если что-то не работает

**Проблема:** Cloud Code не может скачать файлы
**Решение:** Используй локальный путь `/home/roma/` вместо GitHub

**Проблема:** Python не установлен
**Решение:** Установи Python 3.9+: `brew install python@3.9`

**Проблема:** Git не инициализирован
**Решение:** Запусти `git init` вручную

**Проблема:** Не можешь соединиться с Claude
**Решение:** Проверь Claude API ключ в .env

---

> **Версия:** 1.0  
> **Обновлено:** 25.02.2026  
> **Статус:** Готово к использованию ✅
