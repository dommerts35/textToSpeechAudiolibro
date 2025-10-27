from gtts import gTTS
import os
import tempfile
import logging
from typing import List, Dict
from config import Config

logger = logging.getLogger(__name__)


class AudioManager:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.temp_dir = tempfile.mkdtemp()
        self.logger = logger

    def convert_chapters_to_audio(self, chapters: List[Dict], base_output_path: str) -> Dict:
        try:
            results = {
                'successful': [],
                'failed': [],
                'total_chapters': len(chapters)
            }

            for i, chapter in enumerate(chapters):
                chapter_title = chapter["title"]
                chapter_filename = f"capitulo_{i + 1:02d}_{self._sanitize_filename(chapter_title)}.mp3"
                chapter_path = os.path.join(os.path.dirname(base_output_path), chapter_filename)

                self.logger.info(f"Convirtiendo capítulo {i + 1}: {chapter_title}")

                success = self.text_to_speech(
                    chapter["content"],
                    chapter_path,
                    self.config.tts.language
                )

                if success:
                    chapter_info = {
                        'title': chapter_title,
                        'file_path': chapter_path,
                        'words': chapter.get('words', 0),
                        'duration_estimate': self._estimate_duration(chapter['content'])
                    }
                    results['successful'].append(chapter_info)
                    self.logger.info(f"✅ Capítulo {i + 1} convertido: {chapter_filename}")
                else:
                    results['failed'].append({
                        'title': chapter_title,
                        'index': i + 1
                    })
                    self.logger.error(f"❌ Error en capítulo {i + 1}: {chapter_title}")

            return results

        except Exception as e:
            self.logger.error(f"Error convirtiendo capítulos: {e}")
            return {'successful': [], 'failed': [], 'total_chapters': len(chapters)}

    def text_to_speech(self, text: str, output_path: str, language: str = "es") -> bool:
        try:
            if not text.strip():
                self.logger.warning("Texto vacío, no se puede convertir")
                return False

            if len(text) > self.config.tts.max_chunk_length:
                from pdf_processor import PDFProcessor
                processor = PDFProcessor(self.config)
                chunks = processor.split_text_into_chunks(text)
                return self._convert_long_text(chunks, output_path, language)
            else:
                return self._convert_chunk(text, output_path, language)

        except Exception as e:
            self.logger.error(f"Error en text_to_speech: {e}")
            return False

    def _convert_chunk(self, text: str, output_path: str, language: str) -> bool:
        try:

            safe_text = text[:self.config.tts.max_chunk_length]

            tts = gTTS(text=safe_text, lang=language, slow=self.config.tts.slow)
            tts.save(output_path)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size_kb = os.path.getsize(output_path) / 1024
                self.logger.info(f"Audio creado: {output_path} ({file_size_kb:.1f} KB)")
                return True
            else:
                self.logger.error("El archivo de audio no se creó correctamente")
                return False

        except Exception as e:
            self.logger.error(f"Error convirtiendo chunk: {e}")
            return False

    def _convert_long_text(self, chunks: List[str], output_path: str, language: str) -> bool:
        try:
            audio_files = []

            for i, chunk in enumerate(chunks):
                chunk_path = os.path.join(self.temp_dir, f"chunk_{i:03d}.mp3")

                self.logger.info(f"Procesando chunk {i + 1}/{len(chunks)}...")

                if self._convert_chunk(chunk, chunk_path, language):
                    audio_files.append(chunk_path)
                else:
                    self.logger.error(f"Error convirtiendo chunk {i + 1}")
                    continue

            if not audio_files:
                self.logger.error("No se pudo convertir ningún chunk")
                return False

            if audio_files:
                os.rename(audio_files[0], output_path)
                self.logger.info(f"Texto largo convertido (usando primer chunk): {output_path}")


                for temp_file in audio_files[1:]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)

                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error en conversión de texto largo: {e}")
            return False

    def _sanitize_filename(self, filename: str) -> str:
        import re
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        cleaned = cleaned[:50]
        return cleaned.strip()

    def _estimate_duration(self, text: str) -> float:
        """Estima la duración del audio en minutos"""
        words = len(text.split())

        return words / 150.0

