import re
import nltk
from typing import List
import logging


class TextCleaner:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

    def clean_text(self, text: str) -> str:
        text = self._remove_header_footer(text)
        text = self._fix_punctuation(text)
        text = self._normalize_paragraphs(text)
        text = self._remove_excessive_spaces(text)

        return text

    def _remove_header_footer(self, text: str) -> str:
        """Elimina encabezados y pies de página comunes"""
        patterns = [
            r'\n\d+\s*\n',  
            r'Página\s*\d+', 
            r'©.*\n', 
            r'www\..*\.com',  
        ]

        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text

    def _fix_punctuation(self, text: str) -> str:

        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

        text = re.sub(r'\s+([,.!?;:])', r'\1', text)

        return text

    def _normalize_paragraphs(self, text: str) -> str:

        text = re.sub(r'(\w)\n(\w)', r'\1 \2', text)

        text = re.sub(r'([.!?])\s*', r'\1\n\n', text)

        return text

    def _remove_excessive_spaces(self, text: str) -> str:
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def split_into_sentences(self, text: str) -> List[str]:
        from nltk.tokenize import sent_tokenize

        return sent_tokenize(text)
