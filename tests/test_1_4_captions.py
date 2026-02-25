"""
Фаза 1.4: Генерация подписей через Claude API.
TDD: Сначала тест → потом caption_generator.py
"""
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestPhase14CaptionAPIKey:
    """Фаза 1.4: Проверяем наличие Claude API ключа"""

    def test_claude_api_key_exists(self):
        """Claude API ключ установлен и не является заглушкой"""
        key = os.getenv('CLAUDE_API_KEY', '')
        assert key, "CLAUDE_API_KEY не установлен в .env"
        assert not key.startswith('sk-...'), "CLAUDE_API_KEY содержит заглушку — замени реальным ключом"


class TestPhase14CaptionGenerator:
    """Фаза 1.4: Проверяем генерацию подписей через Claude"""

    def test_caption_generator_init(self):
        """CaptionGenerator инициализируется с API ключом"""
        from caption_generator import CaptionGenerator
        key = os.getenv('CLAUDE_API_KEY', 'test_key_placeholder')
        gen = CaptionGenerator(api_key=key)
        assert gen.api_key == key

    def test_generates_5_captions(self):
        """Генерирует минимум 5 вариантов подписи"""
        from caption_generator import CaptionGenerator
        gen = CaptionGenerator(api_key=os.getenv('CLAUDE_API_KEY'))
        captions = gen.generate_captions(
            product_name="Чёрное платье",
            product_description="Элегантное платье из хлопка",
        )
        assert len(captions) >= 5, f"Получено {len(captions)} подписей, нужно >= 5"

    def test_captions_not_empty(self):
        """Все подписи не пустые"""
        from caption_generator import CaptionGenerator
        gen = CaptionGenerator(api_key=os.getenv('CLAUDE_API_KEY'))
        captions = gen.generate_captions(
            product_name="Чёрное платье",
            product_description="Элегантное платье из хлопка",
        )
        assert all(len(c) > 10 for c in captions), "Некоторые подписи слишком короткие"

    def test_captions_contain_mention(self):
        """Каждая подпись содержит упоминание аккаунта (@)"""
        from caption_generator import CaptionGenerator
        gen = CaptionGenerator(api_key=os.getenv('CLAUDE_API_KEY'))
        captions = gen.generate_captions(
            product_name="Чёрное платье",
            product_description="Элегантное платье из хлопка",
        )
        assert all('@' in c for c in captions), "Не все подписи содержат упоминание аккаунта"

    def test_captions_contain_hashtags(self):
        """Каждая подпись содержит хештеги (#)"""
        from caption_generator import CaptionGenerator
        gen = CaptionGenerator(api_key=os.getenv('CLAUDE_API_KEY'))
        captions = gen.generate_captions(
            product_name="Чёрное платье",
            product_description="Элегантное платье из хлопка",
        )
        assert all('#' in c for c in captions), "Не все подписи содержат хештеги"
