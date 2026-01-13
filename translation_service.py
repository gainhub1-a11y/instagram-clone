"""
Translation service using DeepL with OpenAI formatting
"""
import logging
import deepl
from openai import AsyncOpenAI
from config import DEEPL_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)


class TranslationService:
    """Handles text translation from Italian to Spanish with HTML formatting"""
    
    def __init__(self):
        self.deepl_translator = deepl.Translator(DEEPL_API_KEY)
        self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    async def translate_caption(self, text: str) -> str:
        """
        Translate Instagram caption from Italian to Spanish
        
        Args:
            text: Caption text in Italian
        
        Returns:
            Translated and formatted caption in Spanish
        """
        try:
            # Step 1: Translate with DeepL
            logger.info(f"Translating caption with DeepL: {text[:100]}...")
            result = self.deepl_translator.translate_text(
                text,
                source_lang="IT",
                target_lang="ES"
            )
            translated_text = result.text
            logger.info(f"DeepL translation: {translated_text[:100]}...")
            
            # Step 2: Apply formatting with OpenAI (optional, keep simple for Instagram)
            # Instagram supports basic formatting in bio/comments, not in captions
            # So we keep the translation clean
            
            return translated_text
        
        except Exception as e:
            logger.error(f"Caption translation failed: {str(e)}")
            raise
    
    async def translate_caption_openai_fallback(self, text: str) -> str:
        """
        Fallback translation using OpenAI when DeepL fails
        
        Args:
            text: Caption text in Italian
        
        Returns:
            Translated caption in Spanish
        """
        try:
            logger.info(f"Using OpenAI fallback for translation: {text[:100]}...")
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a translator for Instagram captions. Translate the following Italian text to Spanish. Keep hashtags, mentions (@), emojis, and line breaks exactly as they are. Return ONLY the translation, nothing else."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=2048
            )
            
            translated_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI translation: {translated_text[:100]}...")
            
            return translated_text
        
        except Exception as e:
            logger.error(f"OpenAI fallback translation failed: {str(e)}")
            raise


def create_translation_service() -> TranslationService:
    """Factory function to create a TranslationService instance"""
    return TranslationService()
