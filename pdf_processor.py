import PyPDF2
import re
import logging
from typing import Dict, List, Tuple
from config import Config

logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.logger = logger

    def extract_text_with_metadata(self, pdf_path: str) -> Dict:
        """Extrae texto y metadatos del PDF de forma robusta"""
        try:
            self.logger.info(f"Procesando PDF: {pdf_path}")

            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                text = ""
                total_pages = len(pdf_reader.pages)

                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    if page_text:
                        cleaned_text = self._clean_page_text(page_text)
                        text += cleaned_text + "\n"

                    # Log cada 10 páginas para no saturar
                    if (page_num + 1) % 10 == 0 or (page_num + 1) == total_pages:
                        self.logger.info(f"Página {page_num + 1}/{total_pages} procesada")

                # Limpieza final del texto
                final_text = self._clean_complete_text(text)

                metadata = {
                    'title': self._get_metadata_value(pdf_reader.metadata, 'title', 'Sin título'),
                    'author': self._get_metadata_value(pdf_reader.metadata, 'author', 'Desconocido'),
                    'pages': total_pages,
                    'text': final_text,
                    'characters': len(final_text),
                    'words': len(final_text.split())
                }

                return metadata

        except Exception as e:
            self.logger.error(f"Error procesando PDF {pdf_path}: {e}")
            raise

    def _get_metadata_value(self, metadata, key, default):
        """Obtiene valores de metadata de forma segura"""
        try:
            return getattr(metadata, key, default) or default
        except:
            return default

    def _clean_page_text(self, text: str) -> str:
        """Limpia el texto de una página individual"""
        if not text:
            return ""

        # Eliminar caracteres problemáticos
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # Unir palabras divididas con guión al final de línea
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

        # Normalizar saltos de línea múltiples
        text = re.sub(r'\n+', '\n', text)

        return text.strip()

    def _clean_complete_text(self, text: str) -> str:
        """Limpieza final de todo el texto"""
        if not text:
            return ""

        # Normalizar espacios
        text = re.sub(r' +', ' ', text)

        # Corregir puntuación
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

        # Eliminar números de página solos
        text = re.sub(r'\n\d+\n', '\n', text)

        # Unir párrafos rotos
        lines = text.split('\n')
        cleaned_lines = []

        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # Si la línea anterior termina con letra y esta empieza con minúscula, unir
                if (cleaned_lines and
                        cleaned_lines[-1] and
                        cleaned_lines[-1][-1].isalpha() and
                        line and line[0].islower()):
                    cleaned_lines[-1] += " " + line
                else:
                    cleaned_lines.append(line)

        return '\n\n'.join(cleaned_lines)

    def split_into_chapters(self, text: str) -> List[Dict]:
        """Divide el texto en capítulos usando patrones configurables"""
        chapters = []
        lines = text.split('\n')

        current_chapter = {"title": "Introducción", "content": "", "words": 0}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if self._is_chapter_start(line):
                # Guardar capítulo anterior si tiene contenido
                if current_chapter["content"].strip():
                    current_chapter["words"] = len(current_chapter["content"].split())
                    chapters.append(current_chapter)

                # Nuevo capítulo
                current_chapter = {
                    "title": line,
                    "content": "",
                    "words": 0
                }
            else:
                current_chapter["content"] += line + "\n"

        # Añadir último capítulo
        if current_chapter["content"].strip():
            current_chapter["words"] = len(current_chapter["content"].split())
            chapters.append(current_chapter)

        # Si no se detectaron capítulos, crear uno con todo el contenido
        if not chapters:
            chapters.append({
                "title": "Contenido Completo",
                "content": text,
                "words": len(text.split())
            })

        return chapters

    def _is_chapter_start(self, line: str) -> bool:
        """Determina si una línea indica inicio de capítulo"""
        for pattern in self.config.processing.chapter_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        return False

    def split_text_into_chunks(self, text: str, max_length: int = None) -> List[str]:
        """Divide texto en chunks para TTS de forma inteligente"""
        if max_length is None:
            max_length = self.config.tts.max_chunk_length

        if len(text) <= max_length:
            return [text]

        chunks = []
        sentences = self._split_into_sentences(text)
        current_chunk = ""

        for sentence in sentences:
            # Si añadir esta oración excede el límite, guardar chunk actual
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Añadir el último chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Divide texto en oraciones de forma simple"""
        # División básica por puntos, signos de exclamación e interrogación
        sentences = re.split(r'([.!?]+\s+)', text)

        # Recombinar cada oración con su puntuación
        result = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and re.match(r'^[.!?]+\s+$', sentences[i + 1]):
                result.append(sentences[i] + sentences[i + 1])
                i += 2
            else:
                if sentences[i].strip():
                    result.append(sentences[i])
                i += 1

        return [s.strip() for s in result if s.strip()]