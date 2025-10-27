from abc import ABC, abstractmethod
import pyttsx3
from gtts import gTTS
import os
from typing import Optional
import logging
import tempfile


class TTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> bool:
        pass


class PyTTSX3Engine(TTSEngine):
    def __init__(self, rate: int = 150, volume: float = 0.9, voice: str = None):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)

        if voice:
            voices = self.engine.getProperty('voices')
            for v in voices:
                if voice in v.id:
                    self.engine.setProperty('voice', v.id)
                    break

    def synthesize(self, text: str, output_path: str) -> bool:
        try:
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logging.error(f"Error en síntesis de voz: {e}")
            return False


class GoogleTTSEngine(TTSEngine):
    def __init__(self, language: str = 'es', slow: bool = False):
        self.language = language
        self.slow = slow

    def synthesize(self, text: str, output_path: str) -> bool:
        try:
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(output_path)
            return True
        except Exception as e:
            logging.error(f"Error con Google TTS: {e}")
            return False


class TTSFactory:
    @staticmethod
    def create_engine(engine_type: str, **kwargs) -> TTSEngine:
        engines = {
            'pyttsx3': PyTTSX3Engine,
            'google': GoogleTTSEngine,
        }

        if engine_type not in engines:
            raise ValueError(f"Motor TTS no soportado: {engine_type}")

        return engines[engine_type](**kwargs)