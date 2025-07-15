#!/usr/bin/env python3
"""
Test script to verify raw OCR functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ocr.text_extractor import TextExtractor

def test_raw_ocr():
    """Test raw OCR saving functionality."""
    print("Testing raw OCR functionality...")
    
    # Initialize text extractor
    extractor = TextExtractor()
    
    # Process existing column images with raw OCR saving
    input_dir = "data/processed_images"
    output_dir = "data/ocr_text"
    raw_output_dir = "data/raw_ocr"
    
    print(f"Processing images from: {input_dir}")
    print(f"Cleaned OCR output to: {output_dir}")
    print(f"Raw OCR output to: {raw_output_dir}")
    
    # Process column images
    results = extractor.process_column_images(
        input_dir=input_dir,
        output_dir=output_dir,
        raw_output_dir=raw_output_dir
    )
    
    print(f"\nProcessed {len(results)} files:")
    for image_path, text_path in results.items():
        print(f"  {Path(image_path).name} -> {Path(text_path).name}")
    
    # Check if raw OCR files were created
    raw_path = Path(raw_output_dir)
    if raw_path.exists():
        raw_files = list(raw_path.glob("*.txt"))
        print(f"\nRaw OCR files created: {len(raw_files)}")
        for raw_file in raw_files:
            print(f"  {raw_file.name}")
    else:
        print(f"\nWarning: Raw OCR directory not found: {raw_output_dir}")

if __name__ == "__main__":
    test_raw_ocr()