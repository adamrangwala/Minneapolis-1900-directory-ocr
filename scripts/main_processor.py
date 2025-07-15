"""
Main OCR Pipeline Processor

Entry point for processing individual pages or ranges with full pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.web_scraper import DirectoryScraper
from src.preprocessing import CityDirectoryExtractor, StructuralLineDetector
from src.ocr import TextExtractor
from src.parsing import CityDirectoryParser
from config.settings import ensure_directories

logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/main_processor.log')
        ]
    )


def process_single_page(page_number: int, download: bool = True) -> dict:
    """Process a single page through the complete pipeline."""
    logger.info(f"Processing page {page_number}")
    
    results = {
        'page_number': page_number,
        'downloaded': False,
        'extracted_columns': False,
        'ocr_completed': False,
        'json_parsed': False,
        'output_files': {}
    }
    
    try:
        # Step 1: Download image if needed
        if download:
            scraper = DirectoryScraper()
            downloaded_files = scraper.download_specific_pages([page_number])
            if page_number in downloaded_files:
                image_path = downloaded_files[page_number]
                results['downloaded'] = True
                results['output_files']['raw_image'] = image_path
                logger.info(f"Downloaded: {image_path}")
            else:
                logger.error(f"Failed to download page {page_number}")
                return results
        
        # Step 2: Extract columns
        detector = StructuralLineDetector()
        extractor = CityDirectoryExtractor(detector, output_dir="data/processed_images")
        
        # Process the downloaded image
        image_files = [results['output_files']['raw_image']]
        detector.process_images(image_files, directions=['both'])
        extracted_data = extractor.extract_columns(image_files)
        
        if extracted_data:
            results['extracted_columns'] = True
            logger.info("Column extraction completed")
        
        # Step 3: OCR processing
        text_extractor = TextExtractor()
        ocr_results = text_extractor.process_column_images(
            "data/processed_images",
            "data/ocr_text",
            raw_output_dir="data/raw_ocr"
        )
        
        if ocr_results:
            results['ocr_completed'] = True
            results['output_files']['ocr_text'] = list(ocr_results.values())[0]
            logger.info("OCR processing completed")
        
        # Step 4: JSON parsing
        parser = CityDirectoryParser()
        if results['output_files'].get('ocr_text'):
            entries = parser.parse_text_file(results['output_files']['ocr_text'])
            
            if entries:
                output_json = f"data/output_json/page_{page_number}.json"
                parser.save_to_json(output_json)
                results['json_parsed'] = True
                results['output_files']['json'] = output_json
                logger.info(f"JSON parsing completed: {len(entries)} entries")
        
        logger.info(f"Page {page_number} processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing page {page_number}: {e}")
    
    return results


def process_page_range(start_page: int, end_page: int) -> dict:
    """Process a range of pages."""
    logger.info(f"Processing pages {start_page} to {end_page}")
    
    all_results = {}
    
    for page_num in range(start_page, end_page + 1):
        page_results = process_single_page(page_num)
        all_results[page_num] = page_results
    
    return all_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='OCR Pipeline Processor')
    parser.add_argument('--page', type=int, help='Process single page')
    parser.add_argument('--start', type=int, help='Start page for range')
    parser.add_argument('--end', type=int, help='End page for range')
    parser.add_argument('--no-download', action='store_true', help='Skip download step')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Ensure directories exist
    ensure_directories()
    
    # Process based on arguments
    if args.page:
        results = process_single_page(args.page, download=not args.no_download)
        print(f"Page {args.page} results: {results}")
    
    elif args.start and args.end:
        results = process_page_range(args.start, args.end)
        print(f"Processed {len(results)} pages")
        
        # Summary
        successful = sum(1 for r in results.values() if r['json_parsed'])
        print(f"Successfully processed: {successful}/{len(results)} pages")
    
    else:
        print("Please specify either --page or --start/--end")
        parser.print_help()


if __name__ == "__main__":
    main()
