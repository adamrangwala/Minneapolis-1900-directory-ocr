#!/usr/bin/env python3
"""
Simple test script to verify raw OCR functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Direct imports to avoid dependency issues
from src.ocr.ocr_engine import TesseractEngine
from src.ocr.text_cleaner import TextCleaner
from PIL import Image

def test_raw_ocr_direct():
    """Test raw OCR saving functionality directly."""
    print("Testing raw OCR functionality (direct approach)...")
    
    # Check if we have processed images
    processed_dir = Path("data/processed_images")
    if not processed_dir.exists():
        print(f"Error: {processed_dir} does not exist")
        return
    
    # Find column images
    column_images = list(processed_dir.glob("*_col.jpg"))
    if not column_images:
        print("No column images found")
        return
    
    print(f"Found {len(column_images)} column images")
    
    # Initialize OCR components
    try:
        ocr_config = {'psm': 6, 'oem': 3, 'lang': 'eng'}
        cleaner_config = {'enable_text_cleaning': True}
        
        ocr_engine = TesseractEngine(ocr_config)
        text_cleaner = TextCleaner(cleaner_config)
        
        # Create raw OCR directory
        raw_dir = Path("data/raw_ocr")
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each image
        for image_file in column_images[:2]:  # Test with first 2 images
            print(f"\nProcessing: {image_file.name}")
            
            # Load image
            pil_img = Image.open(image_file)
            
            # Extract raw text
            raw_text = ocr_engine.extract_text(pil_img)
            print(f"Raw OCR text length: {len(raw_text)} characters")
            
            # Save raw text
            raw_filename = image_file.stem + ".txt"
            raw_file = raw_dir / raw_filename
            
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(raw_text)
            
            print(f"Saved raw OCR: {raw_filename}")
            
            # Clean text
            cleaned_text = text_cleaner.clean_text(raw_text)
            print(f"Cleaned text length: {len(cleaned_text)} characters")
            
            # Show first few lines of each
            print("Raw OCR (first 3 lines):")
            raw_lines = raw_text.split('\n')[:3]
            for i, line in enumerate(raw_lines, 1):
                print(f"  {i}: {line[:80]}...")
            
            print("Cleaned OCR (first 3 lines):")
            cleaned_lines = cleaned_text.split('\n')[:3]
            for i, line in enumerate(cleaned_lines, 1):
                print(f"  {i}: {line[:80]}...")
        
        # List all raw OCR files created
        raw_files = list(raw_dir.glob("*.txt"))
        print(f"\nTotal raw OCR files: {len(raw_files)}")
        for raw_file in raw_files:
            print(f"  {raw_file.name}")
            
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_ocr_direct()