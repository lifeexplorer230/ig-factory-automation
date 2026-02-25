# ⚡ Быстрый старт (5 минут)

> Как развернуть проект на новом ПК и соединить с Claude

---

## 🎯 Что нужно сделать

### Шаг 1: Скопируй промпт для Cloud Code
```bash
cat /home/roma/CLOUD_CODE_PROMPT.md
```

### Шаг 2: Открой Cloud Code на своём ПК
- VS Code → Extensions → "Cloud Code" → Install
- Или: https://cloud.google.com/code

### Шаг 3: Вставь промпт в Cloud Code
1. Ctrl+Shift+P (Command Palette)
2. Напиши: "Cloud Code: Deploy Project"
3. Вставь текст из CLOUD_CODE_PROMPT.md
4. Нажми Enter

### Шаг 4: Cloud Code развернёт проект
- Создаст папку `~/ig-factory-automation`
- Скачает все файлы
- Настроит Python окружение
- Инициализирует Git

### Шаг 5: Отправь Claude промпт
```bash
cat ~/ig-factory-automation/CLAUDE_SYSTEM_PROMPT.md
```
Скопируй и отправь Claude в чате.

### Шаг 6: Claude начнёт работать
- Будет писать тесты
- Будет писать скрипты
- Будет документировать уроки
- Будет коммитить в GitHub

---

## 📋 Полный список файлов

Все файлы находятся в `/home/roma/`:

```
CLOUD_CODE_PROMPT.md           ← Промпт для Cloud Code
DEPLOYMENT_CHECKLIST.md        ← Чек-лист развертывания
CLAUDE_SYSTEM_PROMPT.md        ← Промпт для Claude
ROADMAP_BY_PROCESSES.md        ← Дорожная карта
TESTING_STRATEGY.md            ← TDD стратегия
PROJECT_JOURNAL.md             ← Журнал уроков
IMPLEMENTATION_GUIDE.md        ← Как работать
CHECKLIST_FOR_KLIM.md          ← Что запросить у Клима
FINAL_SUMMARY.md               ← Обзор версий
CLOUD_CODE_SETUP.md            ← Подробная инструкция
setup.sh                       ← Автоматизация
START_HERE.md                  ← Начни отсюда
```

---

## 🚀 Альтернативный способ (вручную)

Если Cloud Code не работает, делай вручную:

```bash
# 1. Создай папку
mkdir ~/ig-factory-automation
cd ~/ig-factory-automation

# 2. Скопируй файлы
cp /home/roma/*.md .
cp /home/roma/setup.sh .

# 3. Запусти автоматизацию
bash setup.sh

# 4. Активируй окружение
source venv/bin/activate

# 5. Инициализируй Git
git init
git remote add origin https://github.com/USERNAME/ig-factory-automation.git

# 6. Первый коммит
git add .
git commit -m "Initial commit: TDD project structure"
git push -u origin main

# 7. Открой в VS Code
code .
```

---

## ✅ Проверка

После развертывания проверь:

```bash
cd ~/ig-factory-automation

# Проверка Python
python3 --version

# Проверка виртуального окружения
source venv/bin/activate
pip list

# Проверка Git
git status
git log --oneline

# Проверка файлов
ls -la *.md
ls -la tests/
ls -la scripts/
```

---

## 📞 Если что-то не работает

| Проблема | Решение |
|----------|---------|
| Cloud Code не устанавливается | Скачай с https://cloud.google.com/code |
| Python не найден | Установи Python 3.9+: `brew install python@3.9` |
| setup.sh не работает | Дай права: `chmod +x setup.sh` |
| Git ошибка | Инициализируй: `git init` |
| Не можешь соединиться с Claude | Проверь Claude API ключ в .env |

---

## 🎯 Следующие шаги

1. **Заполни .env файл:**
   ```bash
   nano ~/ig-factory-automation/.env
   ```
   Добавь реальные API ключи

2. **Запроси ключи у Клима:**
   Используй `CHECKLIST_FOR_KLIM.md`

3. **Отправь Claude промпт:**
   Скопируй `CLAUDE_SYSTEM_PROMPT.md`

4. **Claude начнёт разработку:**
   - Фаза 1.1 (API ключи)
   - Фаза 1.2 (Первое видео)
   - И так далее...

---

> **Версия:** 1.0  
> **Обновлено:** 25.02.2026  
> **Статус:** Готово ✅
