#!/bin/bash

# 🚀 Скрипт для автоматического развертывания проекта
# Использование: bash setup.sh

set -e  # Выход при ошибке

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Развертывание проекта Instagram Content Factory            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Проверка Python
echo "📦 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен!"
    echo "Установи Python3 и попробуй снова"
    exit 1
fi
python3 --version

# Проверка Git
echo ""
echo "📦 Проверка Git..."
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен!"
    echo "Установи Git и попробуй снова"
    exit 1
fi
git --version

# Создание виртуального окружения
echo ""
echo "🐍 Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Активация виртуального окружения
echo ""
echo "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo ""
echo "📦 Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo ""
echo "📦 Установка зависимостей..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Зависимости установлены"
else
    echo "⚠️  requirements.txt не найден"
fi

# Создание структуры папок
echo ""
echo "📁 Создание структуры папок..."
mkdir -p tests scripts data/{models,videos,queue,sessions,logs,backups} docs .vscode

# Создание .env файла (если не существует)
echo ""
echo "⚙️  Создание .env файла..."
if [ ! -f ".env" ]; then
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
    echo "✅ .env файл создан (заполни API ключи!)"
else
    echo "✅ .env файл уже существует"
fi

# Создание .gitignore
echo ""
echo "⚙️  Создание .gitignore..."
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'GITIGNORE'
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp

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

# Tests
.coverage
.pytest_cache/
htmlcov/

# Credentials
*credentials.json
*secrets*
GITIGNORE
    echo "✅ .gitignore создан"
else
    echo "✅ .gitignore уже существует"
fi

# Создание VS Code конфигурации
echo ""
echo "⚙️  Создание VS Code конфигурации..."
mkdir -p .vscode

cat > .vscode/settings.json << 'VSCODE'
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
VSCODE

cat > .vscode/launch.json << 'LAUNCH'
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
LAUNCH

echo "✅ VS Code конфигурация создана"

# Проверка тестов
echo ""
echo "🧪 Проверка тестов..."
if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
    pytest tests/ --collect-only -q
    echo "✅ Тесты найдены"
else
    echo "⚠️  Папка tests пуста"
fi

# Git инициализация (если нужна)
echo ""
echo "📦 Проверка Git..."
if [ ! -d ".git" ]; then
    echo "⚠️  Git репозиторий не инициализирован"
    echo "Инициализируй: git init && git remote add origin <URL>"
else
    echo "✅ Git репозиторий инициализирован"
fi

# Финальная информация
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ Развертывание завершено!                                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📚 Следующие шаги:"
echo "1. Заполни API ключи в .env файле"
echo "2. Прочитай ROADMAP_BY_PROCESSES.md"
echo "3. Прочитай TESTING_STRATEGY.md"
echo "4. Запроси ключи у Клима (CHECKLIST_FOR_KLIM.md)"
echo "5. Начни с Фазы 1.1"
echo ""
echo "📞 Команды:"
echo "  source venv/bin/activate    # Активировать окружение"
echo "  pytest tests/ -v             # Запустить тесты"
echo "  git add . && git commit ...  # Коммитить изменения"
echo ""
