# 🚀 Развертывание проекта через Cloud Code + GitHub + Claude

> Пошаговая инструкция для нового компьютера

---

## 📋 Что нужно перед началом

### На новом компьютере установить:
- [ ] Git
- [ ] Python 3.9+
- [ ] VS Code
- [ ] Google Cloud Code extension (для VS Code)
- [ ] GitHub Desktop (опционально)

### Аккаунты:
- [ ] GitHub аккаунт
- [ ] Google Cloud аккаунт
- [ ] Claude API ключ (от Anthropic)

---

## 🔧 Шаг 1: Подготовка на новом компьютере

### 1.1 Установка Git
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# Windows
# Скачай с https://git-scm.com/download/win
```

### 1.2 Установка Python
```bash
# macOS
brew install python@3.9

# Ubuntu/Debian
sudo apt-get install python3.9 python3.9-venv

# Проверка
python3 --version
```

### 1.3 Установка VS Code
```bash
# Скачай с https://code.visualstudio.com
# Или через brew (macOS)
brew install visual-studio-code
```

### 1.4 Установка Google Cloud Code
```bash
# В VS Code:
# 1. Открой Extensions (Ctrl+Shift+X)
# 2. Поищи "Cloud Code"
# 3. Установи расширение от Google
```

### 1.5 Конфигурация Git
```bash
git config --global user.name "Твоё имя"
git config --global user.email "твой@email.com"
git config --global core.editor "nano"
```

---

## 📦 Шаг 2: Клонирование проекта с GitHub

### 2.1 Создание репозитория на GitHub
```bash
# На GitHub.com:
# 1. Нажми "New repository"
# 2. Название: ig-factory-automation
# 3. Описание: Instagram Content Factory Automation with TDD
# 4. Выбери Public или Private
# 5. Инициализируй с README
# 6. Нажми "Create repository"
```

### 2.2 Клонирование на локальный компьютер
```bash
# Замени USERNAME на свой GitHub username
git clone https://github.com/USERNAME/ig-factory-automation.git
cd ig-factory-automation
```

### 2.3 Структура проекта (создай папки)
```bash
mkdir -p tests scripts data/{models,videos,queue,sessions,logs,backups}
mkdir -p docs
```

---

## 📄 Шаг 3: Загрузка файлов проекта

### 3.1 Копирование файлов документации
```bash
# Скопируй эти файлы в корень проекта:
cp /home/roma/TESTING_STRATEGY.md .
cp /home/roma/PROJECT_JOURNAL.md .
cp /home/roma/IMPLEMENTATION_GUIDE.md .
cp /home/roma/ROADMAP_BY_PROCESSES.md .
cp /home/roma/CHECKLIST_FOR_KLIM.md .
cp /home/roma/FINAL_SUMMARY.md .
```

### 3.2 Копирование папок
```bash
# Скопируй папку tests (если есть готовые тесты)
cp -r /home/roma/tests/* ./tests/ 2>/dev/null || true

# Скопируй папку scripts (если есть готовые скрипты)
cp -r /home/roma/scripts/* ./scripts/ 2>/dev/null || true
```

### 3.3 Создание конфигурационных файлов
```bash
# Создай .env файл (не коммитить в GitHub!)
cat > .env << 'ENVFILE'
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
ENVFILE
```

### 3.4 Создание .gitignore
```bash
cat > .gitignore << 'GITIGNORE'
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Data
data/models/*
data/videos/*
data/queue/*
data/sessions/*
data/logs/*
data/backups/*

# OS
.DS_Store
Thumbs.db

# Test coverage
htmlcov/
.coverage
.pytest_cache/

# Credentials
*credentials.json
*secrets*
GITIGNORE
```

---

## 🐍 Шаг 4: Настройка Python окружения

### 4.1 Создание виртуального окружения
```bash
# Создай venv
python3 -m venv venv

# Активируй (macOS/Linux)
source venv/bin/activate

# Активируй (Windows)
venv\Scripts\activate
```

### 4.2 Установка зависимостей
```bash
# Создай requirements.txt
cat > requirements.txt << 'REQUIREMENTS'
pytest==7.4.0
pytest-cov==4.1.0
requests==2.31.0
aiohttp==3.8.5
asyncio==3.4.3
redis==5.0.0
psycopg2-binary==2.9.7
anthropic==0.7.0
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.2.0
google-api-python-client==2.100.0
instagrapi==2.0.0
adb-shell==0.3.3
python-dotenv==1.0.0
REQUIREMENTS

# Установи зависимости
pip install -r requirements.txt
```

---

## 🔐 Шаг 5: Конфигурация GitHub

### 5.1 Добавление файлов в Git
```bash
git add .
git status  # Проверь, что .env не в списке
git commit -m "Initial commit: TDD project structure"
git push origin main
```

### 5.2 Создание GitHub Secrets (для CI/CD)
```bash
# На GitHub.com:
# 1. Перейди в Settings → Secrets and variables → Actions
# 2. Нажми "New repository secret"
# 3. Добавь секреты:
#    - NANO_BANANA_API_KEY
#    - KLING_API_KEY
#    - CLAUDE_API_KEY
#    - MORELOGIN_API_KEY
#    - POSTGRES_URL
#    - REDIS_URL
```

---

## 🤖 Шаг 6: Инструкции для Claude

### 6.1 Создание файла инструкций для Claude
```bash
cat > CLAUDE_INSTRUCTIONS.md << 'CLAUDE'
# 📋 Инструкции для Claude по управлению проектом

## 🎯 Твоя роль
Ты — главный разработчик проекта "Instagram Content Factory Automation".
Твоя задача — реализовать проект согласно дорожной карте, используя TDD подход.

## 📚 Основные документы
1. **ROADMAP_BY_PROCESSES.md** — дорожная карта (3 параллельных потока)
2. **TESTING_STRATEGY.md** — TDD стратегия (как писать тесты)
3. **PROJECT_JOURNAL.md** — журнал всех уроков и ошибок
4. **IMPLEMENTATION_GUIDE.md** — как работать с проектом
5. **CHECKLIST_FOR_KLIM.md** — что запросить у Клима

## 🎯 Процесс работы (TDD)

Для каждой фазы:

1️⃣ **Напиши тест** (файл: tests/test_X_X_name.py)
   - Тест должен проверять критерий завершения фазы
   - Используй pytest
   - Пример: assert len(phones) >= 5

2️⃣ **Запусти тест** (он падает)
   - pytest tests/test_X_X_name.py -v
   - Результат: FAILED ❌

3️⃣ **Напиши скрипт** (файл: scripts/script_name.py)
   - Скрипт должен пройти тест
   - Используй примеры из TESTING_STRATEGY.md
   - Добавь обработку ошибок

4️⃣ **Запусти тест** (он проходит)
   - pytest tests/test_X_X_name.py -v
   - Результат: PASSED ✅

5️⃣ **Документируй результат**
   - Открой PROJECT_JOURNAL.md
   - Добавь запись о фазе
   - Структура: Дата → Что делали → Результат → Гипотеза → Реальность → Урок → Действие

6️⃣ **Коммитни в Git**
   - git add .
   - git commit -m "Фаза X.X: [описание]"
   - git push origin main

7️⃣ **Переходи к следующей фазе**
   - Повтори шаги 1-6

## 📊 Критерии завершения фаз

Фаза считается завершённой, когда:
- ✅ Тест PASSED
- ✅ Результат задокументирован в PROJECT_JOURNAL.md
- ✅ Код закоммичен в GitHub
- ✅ Нет критических ошибок

## 🔄 Параллельные потоки

Работай над потоками параллельно:
- **Поток 1** (Контент): Nano Banana + Kling AI + Google Drive
- **Поток 2** (Аккаунты): MoreLogin + Instagram прогрев
- **Поток 3** (Публикация): Начинается когда оба потока готовы

## 📝 Документирование уроков

Для каждой ошибки или нового урока добавляй запись в PROJECT_JOURNAL.md:

```markdown
### Запись X.X.X — [Название]

**Дата:** ДД.ММ.ГГГГ ЧЧ:ММ  
**Фаза:** X.X  
**Статус:** ✅ УСПЕХ / ⚠️ ОШИБКА

**Что делали:**
- ...

**Результат:**
- ...

**Гипотеза:**
- Что мы предполагали?

**Реальность:**
- Что произошло на самом деле?

**Урок:**
- Что мы извлекли?

**Действие:**
- Что делаем дальше?
```

## 🚀 Начало работы

1. Прочитай все основные документы
2. Запроси у Клима все необходимые ключи (CHECKLIST_FOR_KLIM.md)
3. Начни с Фазы 1.1 (Подготовка API ключей)
4. Следуй процессу TDD для каждой фазы
5. Документируй все уроки

## 📞 Команды для работы

```bash
# Запустить все тесты
pytest tests/ -v

# Запустить тесты конкретной фазы
pytest tests/test_1_1_api_keys.py -v

# Запустить с покрытием кода
pytest tests/ --cov=scripts --cov-report=html

# Активировать виртуальное окружение
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Коммитить изменения
git add .
git commit -m "Фаза X.X: [описание]"
git push origin main
```

## 🎯 Текущий статус

Завершённые фазы:
- ✅ 1.1 — Подготовка (API ключи)
- ✅ 1.2 — Тест на 1 товаре
- ✅ 2.1 — Подготовка (телефоны)
- ✅ 2.4 — Прогрев
- ✅ 3.1 — Первая публикация

В процессе:
- ⏳ 1.3 — Масштаб на 10 товаров
- ⏳ Остальные фазы

## ⚠️ Важные правила

1. **Всегда пиши тест перед скриптом** (TDD)
2. **Всегда документируй уроки** (даже ошибки)
3. **Всегда коммитни в GitHub** (после каждой фазы)
4. **Никогда не коммитьте .env файл** (только примеры)
5. **Всегда проверяй гипотезы vs реальность** (учись на ошибках)

## 🔮 Будущие улучшения

- [ ] CI/CD интеграция (GitHub Actions)
- [ ] Автоматические отчёты
- [ ] Дашборд для мониторинга
- [ ] Интеграция с Telegram

---

**Начни с ROADMAP_BY_PROCESSES.md и TESTING_STRATEGY.md!**
CLAUDE

# Скопируй файл в проект
cp CLAUDE_INSTRUCTIONS.md ./docs/
```

---

## 📱 Шаг 7: VS Code + Cloud Code

### 7.1 Открытие проекта в VS Code
```bash
# Открой папку проекта
code .
```

### 7.2 Конфигурация VS Code
```bash
# Создай .vscode/settings.json
mkdir -p .vscode

cat > .vscode/settings.json << 'VSCODE'
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "ms-python.python"
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true
    }
}
VSCODE

# Создай .vscode/launch.json для отладки
cat > .vscode/launch.json << 'LAUNCH'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/",
                "-v"
            ],
            "console": "integratedTerminal"
        }
    ]
}
LAUNCH
```

---

## ✅ Шаг 8: Проверка всего работает

### 8.1 Проверка Git
```bash
git status
git log --oneline
```

### 8.2 Проверка Python
```bash
python3 --version
pip list
```

### 8.3 Проверка тестов
```bash
pytest tests/ -v --collect-only
```

### 8.4 Первый коммит
```bash
git add .
git commit -m "Setup: Initial project structure with TDD"
git push origin main
```

---

## 🚀 Шаг 9: Передача проекта Claude

### 9.1 Создание README для Claude
```bash
cat > README.md << 'README'
# 🎬 Instagram Content Factory Automation

Автоматизированная система публикации контента в Instagram с TDD подходом.

## 🚀 Быстрый старт

1. Клонируй проект
2. Создай виртуальное окружение: `python3 -m venv venv`
3. Активируй: `source venv/bin/activate`
4. Установи зависимости: `pip install -r requirements.txt`
5. Прочитай `ROADMAP_BY_PROCESSES.md`
6. Начни с Фазы 1.1

## 📚 Документация

- **ROADMAP_BY_PROCESSES.md** — дорожная карта (3 потока)
- **TESTING_STRATEGY.md** — TDD стратегия
- **PROJECT_JOURNAL.md** — журнал уроков
- **IMPLEMENTATION_GUIDE.md** — как работать
- **docs/CLAUDE_INSTRUCTIONS.md** — инструкции для Claude

## 🧪 Тестирование

```bash
# Все тесты
pytest tests/ -v

# Конкретная фаза
pytest tests/test_1_1_api_keys.py -v

# С покрытием
pytest tests/ --cov=scripts
```

## 📊 Текущий статус

✅ Завершено: 5 фаз  
⏳ В процессе: 11 фаз  
📈 Прогресс: 31%

## 🎯 Следующие шаги

1. Запроси ключи у Клима (CHECKLIST_FOR_KLIM.md)
2. Начни с Фазы 1.3 (Масштаб на 10 товаров)
3. Документируй все уроки в PROJECT_JOURNAL.md
4. Коммитьте каждую фазу в GitHub

README

git add README.md
git commit -m "docs: Add README"
git push origin main
```

### 9.2 Отправка ссылки Claude
```
Вот ссылка на проект: https://github.com/USERNAME/ig-factory-automation

Инструкции для работы находятся в:
- docs/CLAUDE_INSTRUCTIONS.md
- ROADMAP_BY_PROCESSES.md
- TESTING_STRATEGY.md

Начни с прочтения этих файлов и запроса ключей у Клима.
```

---

## 📋 Чек-лист развертывания

### На новом компьютере:
- [ ] Установлен Git
- [ ] Установлен Python 3.9+
- [ ] Установлен VS Code
- [ ] Установлено Google Cloud Code расширение
- [ ] Склонирован проект с GitHub
- [ ] Создано виртуальное окружение (venv)
- [ ] Установлены зависимости (requirements.txt)
- [ ] Создан .env файл (не коммичен)
- [ ] Запущены тесты (pytest)
- [ ] Все файлы в GitHub

### Готово к работе:
- [ ] Claude получил инструкции
- [ ] Claude получил ссылку на GitHub
- [ ] Claude запросил ключи у Клима
- [ ] Claude начал Фазу 1.3

---

> **Версия:** 1.0  
> **Обновлено:** 25.02.2026  
> **Статус:** Готово к развертыванию ✅
