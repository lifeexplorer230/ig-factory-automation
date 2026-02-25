# 🎬 Instagram Content Factory Automation

Автоматизированная система публикации контента в Instagram с TDD подходом.

## 🚀 Быстрый старт

1. Клонируй проект: `git clone <URL>`
2. Создай окружение: `python3 -m venv venv`
3. Активируй: `source venv/bin/activate`
4. Установи зависимости: `pip install -r requirements.txt`
5. Заполни .env файл
6. Прочитай ROADMAP_BY_PROCESSES.md

## 📚 Документация

- **ROADMAP_BY_PROCESSES.md** — дорожная карта (3 потока)
- **TESTING_STRATEGY.md** — TDD стратегия
- **PROJECT_JOURNAL.md** — журнал уроков
- **IMPLEMENTATION_GUIDE.md** — как работать
- **docs/CLAUDE_INSTRUCTIONS.md** — инструкции для Claude

## 🧪 Тестирование

```bash
pytest tests/ -v                    # Все тесты
pytest tests/test_1_1_api_keys.py -v  # Конкретная фаза
pytest tests/ --cov=scripts         # С покрытием
```

## 📊 Текущий статус

✅ Завершено: 5 фаз  
⏳ В процессе: 11 фаз  
📈 Прогресс: 31%

## 🎯 Следующие шаги

1. Запроси ключи у Клима (CHECKLIST_FOR_KLIM.md)
2. Начни с Фазы 1.3
3. Документируй уроки в PROJECT_JOURNAL.md
4. Коммитьте в GitHub

