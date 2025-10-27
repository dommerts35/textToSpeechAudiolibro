# config.py
import os
from dataclasses import dataclass
from typing import List


@dataclass
class AudioConfig:
    format: str = "mp3"
    bitrate: str = "192k"
    sample_rate: int = 44100
    channels: int = 2


@dataclass
class TTSConfig:
    language: str = "es"
    slow: bool = False
    max_chunk_length: int = 4000


@dataclass
class ProcessingConfig:
    chapter_patterns: List[str] = None
    remove_footnotes: bool = True
    normalize_spaces: bool = True

    def __post_init__(self):
        if self.chapter_patterns is None:
            self.chapter_patterns = [
                r'^CAP[ÍI]TULO\s+\d+',
                r'^Capítulo\s+\d+',
                r'^CHAPTER\s+\d+',
                r'^\d+\.',
                r'^[IVXLCDM]+\.',
                r'^SECCI[ÓO]N\s+\d+',
                r'^Parte\s+\d+',
            ]


class Config:
    def __init__(self):
        self.audio = AudioConfig()
        self.tts = TTSConfig()
        self.processing = ProcessingConfig()
        self.output_dir = "outputs"

    def setup_directories(self):
        """Crea los directorios necesarios"""
        os.makedirs(self.output_dir, exist_ok=True)