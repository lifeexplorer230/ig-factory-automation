"""
Caption Generator — генерация подписей к Instagram Reels через Claude API.

Фаза 1.4. Нужен CLAUDE_API_KEY от Сергея.

Формат подписи:
  [описание товара на английском, lifestyle-тон]
  [1-2 эмодзи]
  [упоминание бренд-аккаунта @...]
  [5-10 хештегов]
"""
import os
import json
import logging
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

# Модель по умолчанию — самая актуальная
DEFAULT_MODEL = 'claude-sonnet-4-6'

SYSTEM_PROMPT = """You are a professional Instagram copywriter for women's fashion.
Write engaging, lifestyle-focused captions in English.

Rules:
- Tone: aspirational, confident, modern — NOT salesy
- Always include the brand mention (provided)
- Always include relevant hashtags (5-10)
- No prices, no "buy now", no direct CTAs
- Keep it concise: 2-3 sentences max before hashtags
"""

CAPTION_TEMPLATE = """Write 5 different Instagram Reels captions for this product:

Product: {product_name}
Description: {product_description}
Brand mention: {brand_mention}

Return JSON array of 5 strings. Each string is a complete caption including
the brand mention and hashtags. Example format:
["caption 1 text @brand #tag1 #tag2", "caption 2 text @brand #tag1 #tag2", ...]

Only return the JSON array, no other text."""


class CaptionGenerator:
    """Генератор подписей для Instagram через Claude API."""

    def __init__(self, api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL):
        self.api_key       = api_key if api_key is not None else os.getenv('CLAUDE_API_KEY', '')
        self.model         = model
        self.brand_mention = os.getenv('BRAND_MENTION', '@brand')

    def generate_captions(self, product_name: str,
                          product_description: str,
                          count: int = 5) -> list:
        """
        Генерирует варианты подписей для товара.

        Args:
            product_name:        Название товара (например "Black Evening Dress")
            product_description: Краткое описание (материал, фасон, стиль)
            count:               Количество вариантов (по умолчанию 5)

        Returns:
            list[str]: Список подписей, каждая с @mention и #хештегами

        Raises:
            RuntimeError: Если CLAUDE_API_KEY не задан или API вернул ошибку
        """
        if not self.api_key:
            raise RuntimeError(
                'CLAUDE_API_KEY не задан в .env — нужен ключ от Сергея (Фаза 1.4)'
            )

        prompt = CAPTION_TEMPLATE.format(
            product_name=product_name,
            product_description=product_description,
            brand_mention=self.brand_mention,
        )

        body = json.dumps({
            'model': self.model,
            'max_tokens': 1024,
            'system': SYSTEM_PROMPT,
            'messages': [{'role': 'user', 'content': prompt}],
        }).encode()

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=body,
            headers={
                'Content-Type':      'application/json',
                'x-api-key':         self.api_key,
                'anthropic-version': '2023-06-01',
            },
            method='POST',
        )

        try:
            response = urllib.request.urlopen(req)
            data     = json.loads(response.read())
            text     = data['content'][0]['text'].strip()
            captions = json.loads(text)
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            raise RuntimeError(f'Claude API ошибка {e.code}: {err}')
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f'Не удалось распарсить ответ Claude: {e}')

        # Валидация
        if not isinstance(captions, list):
            raise RuntimeError(f'Claude вернул не список: {type(captions)}')

        captions = [str(c).strip() for c in captions if str(c).strip()]

        for i, caption in enumerate(captions):
            if '@' not in caption:
                logger.warning(f'Подпись {i+1} не содержит @mention')
            if '#' not in caption:
                logger.warning(f'Подпись {i+1} не содержит хештеги')

        logger.info(f'Сгенерировано {len(captions)} подписей для "{product_name}"')
        return captions[:count]

    def generate_with_fallback(self, product_name: str,
                               product_description: str) -> list:
        """
        Генерирует подписи с fallback на шаблон если API недоступен.
        Используется для разработки без ключа.
        """
        try:
            return self.generate_captions(product_name, product_description)
        except RuntimeError as e:
            logger.warning(f'Claude API недоступен ({e}), использую шаблон')
            return self._template_captions(product_name)

    def _template_captions(self, product_name: str) -> list:
        """Шаблонные подписи для разработки без API ключа."""
        mention = self.brand_mention
        return [
            f"Style that speaks for itself ✨ {mention} #fashion #womensfashion #ootd #style #outfit",
            f"Effortless elegance, every day 🖤 {mention} #fashionista #lookbook #styleinspo #womenswear #new",
            f"When comfort meets style 💫 {mention} #outfitoftheday #fashionblogger #stylegoals #clothing #chic",
            f"Dress the part, own the moment ✨ {mention} #instafashion #trendy #fashionlover #stylish #looks",
            f"Made for the woman who moves with intention 🌿 {mention} #sustainablefashion #slowfashion #style #fashion #ootd",
        ]
