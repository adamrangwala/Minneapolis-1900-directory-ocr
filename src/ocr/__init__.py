"""
OCR module for text extraction from preprocessed images.
"""

from .text_extractor import TextExtractor
from .ocr_engine import TesseractEngine
from .text_cleaner import TextCleaner
from .batch_processor import BatchOCRProcessor

__all__ = ['TextExtractor', 'TesseractEngine', 'TextCleaner', 'BatchOCRProcessor']
