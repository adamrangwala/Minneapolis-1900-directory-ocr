"""
OCR Engine Implementation

Handles the actual OCR processing using Tesseract.
"""

import pytesseract
from PIL import Image
import logging
from typing import Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TesseractEngine:
    """Tesseract OCR engine wrapper."""
    
    def __init__(self, config: Dict):
        """Initialize Tesseract engine with configuration."""
        self.config = config
        self._setup_tesseract()
        logger.info("TesseractEngine initialized")
    
    def _setup_tesseract(self) -> None:
        """Set up Tesseract configuration."""
        tesseract_cmd = self.config.get('cmd_path')
        if tesseract_cmd and Path(tesseract_cmd).exists():
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            logger.info(f"Using custom Tesseract path: {tesseract_cmd}")
    
    def extract_text(self, pil_img: Image.Image) -> str:
        """Extract text using Tesseract OCR."""
        config_string = self._build_config_string()
        lang = self.config.get('lang', 'eng')
        timeout = self.config.get('timeout', 30)
        
        try:
            text = pytesseract.image_to_string(
                pil_img, 
                lang=lang,
                config=config_string,
                timeout=timeout
            )
            return text
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""
    
    def extract_with_confidence(self, pil_img: Image.Image) -> Tuple[str, float]:
        """Extract text with confidence score."""
        try:
            # Get detailed data from Tesseract
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract text
            text = self.extract_text(pil_img)
            
            return text, avg_confidence / 100.0  # Convert to 0-1 scale
            
        except Exception as e:
            logger.error(f"Failed to extract text with confidence: {e}")
            return "", 0.0
    
    def _build_config_string(self) -> str:
        """Build Tesseract configuration string."""
        config_parts = []
        
        psm = self.config.get('psm', 6)
        oem = self.config.get('oem', 3)
        config_parts.append(f'--psm {psm}')
        config_parts.append(f'--oem {oem}')
        
        # Add whitelist/blacklist if specified
        whitelist = self.config.get('whitelist', '')
        if whitelist:
            config_parts.append(f'-c tessedit_char_whitelist={whitelist}')
        
        blacklist = self.config.get('blacklist', '')
        if blacklist:
            config_parts.append(f'-c tessedit_char_blacklist={blacklist}')
        
        return ' '.join(config_parts)
