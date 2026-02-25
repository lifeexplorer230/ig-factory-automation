# 📋 Чек-лист развертывания проекта на новом ПК

> Пошаговая инструкция для быстрого развертывания

---

## ✅ Шаг 1: Установка инструментов

### macOS
```bash
brew install git python@3.9 visual-studio-code
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y git python3.9 python3.9-venv build-essential
```

### Windows
- Скачай Git: https://git-scm.com/download/win
- Скачай Python: https://www.python.org/downloads/
- Скачай VS Code: https://code.visualstudio.com

### Проверка
```bash
git --version
python3 --version
```

---

## ✅ Шаг 2: Клонирование проекта

```bash
# Замени USERNAME на свой GitHub username
git clone https://github.com/USERNAME/ig-factory-automation.git
cd ig-factory-automation

# Создай структуру папок
mkdir -p tests scripts data/{models,videos,queue,sessions,logs,backups} docs .vscode
```

---

## ✅ Шаг 3: Копирование файлов документации

```bash
# Скопируй из исходного проекта (замени /home/roma на путь)
cp /home/roma/TESTING_STRATEGY.md .
cp /home/roma/PROJECT_JOURNAL.md .
cp /home/roma/IMPLEMENTATION_GUIDE.md .
cp /home/roma/ROADMAP_BY_PROCESSES.md .
cp /home/roma/CHECKLIST_FOR_KLIM.md .
cp /home/roma/FINAL_SUMMARY.md .
cp /home/roma/CLOUD_CODE_SETUP.md .
cp /home/roma/setup.sh .

# Копирование папок (если есть готовые тесты)
cp -r /home/roma/tests/* ./tests/ 2>/dev/null || true
cp -r /home/roma/scripts/* ./scripts/ 2>/dev/null || true
```

---

## ✅ Шаг 4: Настройка Python окружения

```bash
# Создай виртуальное окружение
python3 -m venv venv

# Активируй (macOS/Linux)
source venv/bin/activate

# Активируй (Windows)
venv\Scripts\activate

# Обнови pip
pip install --upgrade pip

# Установи зависимости
pip install -r requirements.txt
```

---

## ✅ Шаг 5: Конфигурация проекта

### Создай .env файл
```bash
cat > .env << 'EOF'
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
EOF
```

### Создай .gitignore
```bash
cat > .gitignore << 'EOF'
.env
.env.local
__pycache__/
*.py[cod]
*.so
venv/
env/
.vscode/
.idea/
*.swp
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
EOF
```

---

## ✅ Шаг 6: VS Code конфигурация

```bash
# Создай .vscode/settings.json
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
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
EOF

# Создай .vscode/launch.json
cat > .vscode/launch.json << 'EOF'
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
EOF
```

---

## ✅ Шаг 7: GitHub инициализация

```bash
# Инициализируй Git (если нужно)
git init

# Добавь удалённый репозиторий (замени URL)
git remote add origin https://github.com/USERNAME/ig-factory-automation.git

# Добавь файлы
git add .

# Проверь, что .env не в списке
git status

# Первый коммит
git commit -m "Initial commit: TDD project structure with documentation"

# Загрузи в GitHub
git push -u origin main
```

---

## ✅ Шаг 8: Проверка всего работает

```bash
# Проверка Python
python3 --version
pip list

# Проверка тестов
pytest tests/ --collect-only -q

# Проверка Git
git status
git log --oneline
```

---

## ✅ Шаг 9: Открытие в VS Code

```bash
# Открой проект в VS Code
code .

# Установи расширения:
# - Python (Microsoft)
# - Pylance
# - Cloud Code (Google)
```

---

## ✅ Шаг 10: Заполнение API ключей

1. Открой .env файл
2. Заполни реальные API ключи:
   - NANO_BANANA_API_KEY
   - KLING_API_KEY
   - CLAUDE_API_KEY
   - MORELOGIN_API_KEY
   - GOOGLE_DRIVE_CREDENTIALS
   - POSTGRES_URL
   - REDIS_URL

---

## ✅ Шаг 11: Запрос ключей у Клима

1. Открой CHECKLIST_FOR_KLIM.md
2. Отправь Климу список необходимых ключей
3. Дождись ответа с ключами
4. Заполни .env файл

---

## ✅ Шаг 12: Первый запуск

```bash
# Активируй окружение
source venv/bin/activate

# Запусти тесты
pytest tests/test_1_1_api_keys.py -v

# Если всё работает, начни с Фазы 1.1
```

---

## 📚 Следующие шаги

1. Прочитай ROADMAP_BY_PROCESSES.md
2. Прочитай TESTING_STRATEGY.md
3. Прочитай IMPLEMENTATION_GUIDE.md
4. Начни с Фазы 1.1
5. Документируй уроки в PROJECT_JOURNAL.md

---

## 📞 Важные команды

```bash
# Активировать окружение
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Запустить тесты
pytest tests/ -v
pytest tests/test_1_1_api_keys.py -v
pytest tests/ --cov=scripts

# Коммитить изменения
git add .
git commit -m "Фаза X.X: [описание]"
git push origin main

# Открыть проект в VS Code
code .
```

---

## 🚀 Быстрый старт (одна команда)

Если у тебя есть setup.sh:
```bash
bash setup.sh
```

---

> **Версия:** 1.0  
> **Обновлено:** 25.02.2026  
> **Статус:** Готово к развертыванию ✅
