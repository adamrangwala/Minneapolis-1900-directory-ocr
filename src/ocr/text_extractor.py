"""
Core Text Extractor for OCR Processing

Main interface for text extraction with preprocessing and post-processing.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Union
from PIL import Image

from .ocr_engine import TesseractEngine
from .text_cleaner import TextCleaner
from ..preprocessing.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class TextExtractor:
    """Main text extractor with OCR and post-processing capabilities."""
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict] = None):
        """Initialize text extractor with configuration."""
        self.config = self._load_config(config_path, config_dict)
        
        # Initialize components
        self.ocr_engine = TesseractEngine(self.config.get('tesseract', {}))
        self.text_cleaner = TextCleaner(self.config.get('postprocessing', {}))
        self.image_processor = ImageProcessor(config_dict=self.config)
        
        logger.info("TextExtractor initialized")
    
    def _load_config(self, config_path: Optional[str], config_dict: Optional[Dict]) -> Dict:
        """Load configuration from file or dictionary."""
        if config_dict:
            return config_dict
        
        if config_path and Path(config_path).exists():
            import json
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Fallback to default configuration
        return {
            'tesseract': {'psm': 6, 'oem': 3, 'lang': 'eng'},
            'postprocessing': {'enable_text_cleaning': True}
        }
    
    def extract_text(self, image_path: Union[str, Path], preprocess: bool = True,
                     save_raw: bool = False, raw_output_dir: Optional[Union[str, Path]] = None) -> str:
        """Extract text from image using OCR."""
        try:
            if preprocess:
                pil_img = self.image_processor.preprocess_for_tesseract(image_path)
            else:
                import cv2
                img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    raise ValueError(f"Could not load image: {image_path}")
                pil_img = Image.fromarray(img)
            
            # Extract raw text
            raw_text = self.ocr_engine.extract_text(pil_img)
            
            # Save raw OCR text if requested
            if save_raw and raw_output_dir:
                self._save_raw_ocr_text(image_path, raw_text, raw_output_dir)
            
            # Clean text
            cleaned_text = self.text_cleaner.clean_text(raw_text)
            
            logger.info(f"Extracted {len(cleaned_text)} characters from {Path(image_path).name}")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Failed to extract text from {image_path}: {e}")
            return ""
    
    def extract_with_confidence(self, image_path: Union[str, Path],
                               preprocess: bool = True, save_raw: bool = False,
                               raw_output_dir: Optional[Union[str, Path]] = None) -> tuple:
        """Extract text with confidence score."""
        try:
            if preprocess:
                pil_img = self.image_processor.preprocess_for_tesseract(image_path)
            else:
                import cv2
                img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                if img is None:
                    raise ValueError(f"Could not load image: {image_path}")
                pil_img = Image.fromarray(img)
            
            # Get text and confidence from OCR engine
            raw_text, confidence = self.ocr_engine.extract_with_confidence(pil_img)
            
            # Save raw OCR text if requested
            if save_raw and raw_output_dir:
                self._save_raw_ocr_text(image_path, raw_text, raw_output_dir)
            
            # Clean text
            cleaned_text = self.text_cleaner.clean_text(raw_text)
            
            return cleaned_text, confidence
            
        except Exception as e:
            logger.error(f"Failed to extract text with confidence from {image_path}: {e}")
            return "", 0.0


    def process_column_images(self, input_dir: Union[str, Path],
                             output_dir: Union[str, Path],
                             raw_output_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
        """Process all column images in a directory and save OCR text."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create raw output directory if specified
        if raw_output_dir:
            raw_path = Path(raw_output_dir)
            raw_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Find all column images (left_col.jpg and right_col.jpg)
        column_images = list(input_path.glob("*_col.jpg"))
        
        if not column_images:
            logger.warning(f"No column images found in {input_dir}")
            return results
        
        for image_file in column_images:
            try:
                # Extract text from column image (with raw OCR saving if specified)
                text = self.extract_text(
                    image_file,
                    preprocess=True,
                    save_raw=bool(raw_output_dir),
                    raw_output_dir=raw_output_dir
                )
                
                # Create output filename (replace .jpg with .txt)
                output_filename = image_file.stem + ".txt"
                output_file = output_path / output_filename
                
                # Save cleaned text to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                results[str(image_file)] = str(output_file)
                logger.info(f"Processed {image_file.name} -> {output_filename}")
                
            except Exception as e:
                logger.error(f"Failed to process {image_file}: {e}")
        
        return results
    
    def _save_raw_ocr_text(self, image_path: Union[str, Path], raw_text: str,
                          raw_output_dir: Union[str, Path]) -> None:
        """Save raw OCR text to file before cleaning."""
        try:
            image_path = Path(image_path)
            raw_output_path = Path(raw_output_dir)
            raw_output_path.mkdir(parents=True, exist_ok=True)
            
            # Create raw output filename (replace .jpg with .txt)
            raw_filename = image_path.stem + ".txt"
            raw_file = raw_output_path / raw_filename
            
            # Save raw text to file
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(raw_text)
            
            logger.info(f"Saved raw OCR text: {raw_filename}")
            
        except Exception as e:
            logger.error(f"Failed to save raw OCR text for {image_path}: {e}")


def extract_text_from_image(image_path: Union[str, Path], 
                           config_path: Optional[str] = None,
                           preprocess: bool = True) -> str:
    """Convenience function to extract text from a single image."""
    extractor = TextExtractor(config_path=config_path)
    return extractor.extract_text(image_path, preprocess=preprocess)
