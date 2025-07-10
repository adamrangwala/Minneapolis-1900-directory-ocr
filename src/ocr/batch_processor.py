"""
Batch OCR Processing

Handles batch processing of multiple images for OCR extraction.
"""

import logging
from pathlib import Path
from typing import Dict, List, Union

from .text_extractor import TextExtractor

logger = logging.getLogger(__name__)


class BatchOCRProcessor:
    """Batch processor for OCR text extraction."""
    
    def __init__(self, config_path: str = None):
        """Initialize batch processor."""
        self.extractor = TextExtractor(config_path=config_path)
        logger.info("BatchOCRProcessor initialized")
    
    def process_images(self, image_paths: List[Union[str, Path]], 
                      output_dir: Union[str, Path]) -> Dict[str, str]:
        """Process multiple images and save text files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for img_path in image_paths:
            try:
                text = self.extractor.extract_text(img_path)
                
                input_path = Path(img_path)
                output_path = output_dir / f"{input_path.stem}.txt"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                results[str(img_path)] = str(output_path)
                logger.info(f"Processed: {output_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to process {img_path}: {e}")
                results[str(img_path)] = None
        
        return results
    
    def process_column_images(self, input_dir: Union[str, Path], 
                             output_dir: Union[str, Path]) -> Dict[str, str]:
        """Process column images and combine by page."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find column images
        image_files = list(input_path.glob("*_col.jpg"))
        if not image_files:
            logger.warning(f"No column images found in {input_dir}")
            return {}
        
        # Group by page
        pages = self._group_by_page(image_files)
        
        results = {}
        for page_id, columns in sorted(pages.items()):
            logger.info(f"Processing page: {page_id}")
            
            combined_text = self._combine_page_text(columns)
            
            if combined_text:
                output_file = output_path / f"{page_id}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(combined_text)
                
                results[page_id] = str(output_file)
                logger.info(f"Saved: {output_file.name}")
        
        return results
    
    def _group_by_page(self, image_files: List[Path]) -> Dict[str, Dict[str, Path]]:
        """Group column images by page identifier."""
        pages = {}
        
        for image_file in image_files:
            name_parts = image_file.stem.split('_')
            if len(name_parts) >= 3:
                page_id = '_'.join(name_parts[:2])
                column_type = name_parts[2]
                
                if page_id not in pages:
                    pages[page_id] = {}
                pages[page_id][column_type] = image_file
        
        return pages
    
    def _combine_page_text(self, columns: Dict[str, Path]) -> str:
        """Extract and combine text from left and right columns."""
        combined_text = ""
        
        # Process left column
        if 'left' in columns:
            left_text = self.extractor.extract_text(columns['left'])
            if left_text:
                combined_text += left_text + "\n"
        
        # Process right column
        if 'right' in columns:
            right_text = self.extractor.extract_text(columns['right'])
            if right_text:
                combined_text += right_text
        
        return combined_text.strip()
