"""
Directory Scraper for Web Archive

Scrapes directory images from the web archive with retry logic and error handling.
"""

import requests
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import TARGET_PAGES

logger = logging.getLogger(__name__)


class DirectoryScraper:
    """Scraper for downloading directory images from web archive."""
    
    def __init__(self, output_dir: str = "data/raw_images"):
        """Initialize directory scraper."""
        # Use the working URL pattern from the provided script
        self.base_url = "https://box2.nmtvault.com/Hennepin2/servlet/ImageTileRenderer"
        self.document_id = "7083e412-1de2-42fe-b070-7f82e5c869a4/mnmhcl00/20130429/00000008"
        self.scale = "1.0"  # Full resolution
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        
        # Set proper headers to mimic browser request (matching working script)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logger.info(f"DirectoryScraper initialized with output_dir: {output_dir}")
    
    def build_image_url(self, page_seq: int) -> str:
        """Build image URL for given page sequence using working format."""
        return f"{self.base_url}?doc_id={self.document_id}&pg_seq={page_seq}&scale={self.scale}"
    
    def _download_single_image(self, page_seq: int, filename: str) -> Optional[str]:
        """Download a single image with JPEG validation."""
        output_path = self.output_dir / filename
        
        # Skip if file already exists
        if output_path.exists():
            logger.info(f"File already exists: {filename}")
            return str(output_path)
        
        try:
            image_url = self.build_image_url(page_seq)
            logger.debug(f"Downloading {filename} from {image_url}")
            
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Validate image content (matching working script logic)
            if len(response.content) > 5000 and response.content.startswith(b'\xff\xd8'):  # JPEG signature
                # Save the image
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Successfully downloaded: {filename} ({len(response.content)//1024}KB)")
                return str(output_path)
            else:
                logger.warning(f"Invalid image content for {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading {filename}: {e}")
            return None

    def download_target_pages(self) -> Dict[int, str]:
        """Download target pages specified in configuration."""
        results = {}
        
        logger.info(f"Downloading {len(TARGET_PAGES)} target pages")
        
        for page_num, page_seq in TARGET_PAGES.items():
            try:
                filename = f"1900_{page_seq:04d}.jpg"
                
                file_path = self._download_single_image(page_seq, filename)
                if file_path:
                    results[page_num] = file_path
                    logger.info(f"Downloaded page {page_num} (seq {page_seq})")
                else:
                    logger.error(f"Failed to download page {page_num}")
                
                # Rate limiting with 1-second delay
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error downloading page {page_num}: {e}")
        
        logger.info(f"Successfully downloaded {len(results)} pages")
        return results
    
    def download_page_range(self, start_page: int, end_page: int) -> Dict[int, str]:
        """Download a range of pages."""
        results = {}
        
        logger.info(f"Downloading pages {start_page} to {end_page}")
        
        for page_seq in range(start_page, end_page + 1):
            try:
                filename = f"1900_{page_seq:04d}.jpg"
                
                file_path = self._download_single_image(page_seq, filename)
                if file_path:
                    results[page_seq] = file_path
                    logger.info(f"Downloaded page sequence {page_seq}")
                
                # Rate limiting with 1-second delay
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error downloading page sequence {page_seq}: {e}")
        
        logger.info(f"Successfully downloaded {len(results)} pages")
        return results
    
    def download_specific_pages(self, page_sequences: List[int]) -> Dict[int, str]:
        """Download specific page sequences."""
        results = {}
        
        logger.info(f"Downloading {len(page_sequences)} specific pages")
        
        for page_seq in page_sequences:
            try:
                filename = f"1900_{page_seq:04d}.jpg"
                
                file_path = self._download_single_image(page_seq, filename)
                if file_path:
                    results[page_seq] = file_path
                    logger.info(f"Downloaded page sequence {page_seq}")
                
                # Rate limiting with 1-second delay
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error downloading page sequence {page_seq}: {e}")
        
        logger.info(f"Successfully downloaded {len(results)} pages")
        return results
    
    def verify_downloads(self, downloaded_files: Dict[int, str]) -> Dict[int, bool]:
        """Verify that downloaded files exist and are valid."""
        verification_results = {}
        
        for page_id, file_path in downloaded_files.items():
            try:
                path = Path(file_path)
                if path.exists() and path.stat().st_size > 0:
                    verification_results[page_id] = True
                    logger.debug(f"Verified page {page_id}: {path.name}")
                else:
                    verification_results[page_id] = False
                    logger.warning(f"Failed verification for page {page_id}")
            except Exception as e:
                verification_results[page_id] = False
                logger.error(f"Error verifying page {page_id}: {e}")
        
        successful = sum(verification_results.values())
        logger.info(f"Verification complete: {successful}/{len(verification_results)} files valid")
        
        return verification_results
    
    def cleanup_session(self):
        """Clean up the requests session."""
        if self.session:
            self.session.close()
            logger.info("Cleaned up scraper session")


def download_target_pages(output_dir: str = "data/raw_images") -> Dict[int, str]:
    """Convenience function to download target pages."""
    scraper = DirectoryScraper(output_dir)
    try:
        return scraper.download_target_pages()
    finally:
        scraper.cleanup_session()
