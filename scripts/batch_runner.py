"""
Batch Runner for OCR Pipeline

Processes entire directory in batches with automatic checkpoint management.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils import BatchProcessor
from src.web_scraper import DirectoryScraper
from config.settings import TARGET_PAGES, ensure_directories

logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/batch_runner.log')
        ]
    )


def process_page_batch(page_number: int) -> dict:
    """Process a single page (used by batch processor)."""
    from main_processor import process_single_page
    return process_single_page(page_number, download=True)


def run_target_pages_batch() -> dict:
    """Run batch processing for target pages."""
    logger.info("Starting batch processing for target pages")
    
    # Get target page numbers
    target_page_numbers = list(TARGET_PAGES.keys())
    logger.info(f"Target pages: {target_page_numbers}")
    
    # Initialize batch processor
    batch_processor = BatchProcessor()
    
    # Process pages in batches
    results = batch_processor.process_items(
        items=target_page_numbers,
        process_func=process_page_batch,
        job_name="target_pages_processing"
    )
    
    return results


def run_custom_batch(page_list: list) -> dict:
    """Run batch processing for custom page list."""
    logger.info(f"Starting batch processing for pages: {page_list}")
    
    # Initialize batch processor
    batch_processor = BatchProcessor()
    
    # Process pages in batches
    results = batch_processor.process_items(
        items=page_list,
        process_func=process_page_batch,
        job_name="custom_batch_processing"
    )
    
    return results


def download_target_pages() -> dict:
    """Download all target pages."""
    logger.info("Downloading target pages")
    
    scraper = DirectoryScraper()
    try:
        downloaded_files = scraper.download_target_pages()
        logger.info(f"Downloaded {len(downloaded_files)} pages")
        return downloaded_files
    finally:
        scraper.cleanup_session()


def check_batch_progress(job_name: str) -> None:
    """Check progress of a batch job."""
    batch_processor = BatchProcessor()
    progress = batch_processor.get_progress(job_name)
    
    if progress:
        print(f"Job: {job_name}")
        print(f"Progress: {progress['processed_items']}/{progress['total_items']} "
              f"({progress['progress_percent']:.1f}%)")
        print(f"Completed: {progress['completed']}")
        
        if progress['timestamp']:
            import time
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', 
                                    time.localtime(progress['timestamp']))
            print(f"Last updated: {timestamp}")
    else:
        print(f"No progress found for job: {job_name}")


def create_combined_output():
    """Create combined JSON output file from all individual page JSONs."""
    from src.parsing.json_parser import combine_json_outputs
    
    logger.info("Creating combined output file")
    
    # Use the existing combine function but with custom filename
    combine_json_outputs(
        output_dir="data/output_json",
        final_output_file="focused_sample_output.json"
    )
    
    print("Created combined output file: data/output_json/focused_sample_output.json")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Batch OCR Pipeline Runner')
    parser.add_argument('--target-pages', action='store_true', 
                       help='Process target pages (104-108)')
    parser.add_argument('--pages', nargs='+', type=int, 
                       help='Process specific pages')
    parser.add_argument('--download-only', action='store_true', 
                       help='Only download target pages')
    parser.add_argument('--progress', type=str, 
                       help='Check progress of job')
    parser.add_argument('--verbose', action='store_true', 
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Ensure directories exist
    ensure_directories()
    
    # Handle different operations
    if args.progress:
        check_batch_progress(args.progress)
        return
    
    if args.download_only:
        results = download_target_pages()
        print(f"Downloaded {len(results)} pages")
        return
    
    if args.target_pages:
        results = run_target_pages_batch()
        
        # Print summary
        successful = sum(1 for r in results.values()
                        if isinstance(r, dict) and r.get('json_parsed', False))
        print(f"Target pages batch complete: {successful}/{len(results)} successful")
        
        # Print detailed results
        for page_num, result in results.items():
            if isinstance(result, dict):
                status = "✓" if result.get('json_parsed', False) else "✗"
                print(f"  Page {page_num}: {status}")
        
        # Create combined output file
        if successful > 0:
            create_combined_output()
    
    elif args.pages:
        results = run_custom_batch(args.pages)
        
        # Print summary
        successful = sum(1 for r in results.values() 
                        if isinstance(r, dict) and r.get('json_parsed', False))
        print(f"Custom batch complete: {successful}/{len(results)} successful")
    
    else:
        print("Please specify an operation:")
        print("  --target-pages: Process target pages (104-108)")
        print("  --pages 104 105 106: Process specific pages")
        print("  --download-only: Download target pages only")
        print("  --progress job_name: Check job progress")
        parser.print_help()


if __name__ == "__main__":
    main()
