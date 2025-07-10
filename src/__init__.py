"""
Minneapolis 1900 City Directory OCR Pipeline

A comprehensive system for extracting structured resident data from 
the 1900 Minneapolis city directory using OCR and intelligent parsing.
"""

__version__ = "1.0.0"
__author__ = "City Directory OCR Team"
__description__ = "OCR Pipeline for Minneapolis 1900 City Directory"

from .preprocessing import column_extractor, image_processor
from .ocr import text_extractor
from .parsing import json_parser
from .web_scraper import directory_scraper
from .utils import batch_processor, checkpoint_manager

__all__ = [
    'column_extractor',
    'image_processor', 
    'text_extractor',
    'json_parser',
    'directory_scraper',
    'batch_processor',
    'checkpoint_manager'
]
