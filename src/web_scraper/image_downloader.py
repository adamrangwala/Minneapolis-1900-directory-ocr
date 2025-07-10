"""
Image Downloader with Retry Logic

Handles downloading images with retry logic and error handling.
"""

import requests
import logging
import time
from pathlib import Path
from typing import Optional

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import BATCH_PROCESSING

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Downloads images with retry logic and error handling."""
    
    def __init__(self, output_dir: Path):
        """Initialize image downloader."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get retry settings from config
        self.retry_attempts = BATCH_PROCESSING.get('retry_attempts', 3)
        self.retry_delay = BATCH_PROCESSING.get('retry_delay', 1.0)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logger.info(f"ImageDownloader initialized with {self.retry_attempts} retry attempts")
    
    def download_image(self, url: str, filename: str) -> Optional[str]:
        """Download image with retry logic."""
        output_path = self.output_dir / filename
        
        # Skip if file already exists
        if output_path.exists():
            logger.info(f"File already exists: {filename}")
            return str(output_path)
        
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Downloading {filename} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Check if response contains image data
                if len(response.content) < 1000:  # Minimum size check
                    raise ValueError("Response too small to be a valid image")
                
                # Save image
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Successfully downloaded: {filename}")
                return str(output_path)
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {filename}: {e}")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Failed to download {filename} after {self.retry_attempts} attempts")
        
        return None
    
    def verify_image(self, file_path: str) -> bool:
        """Verify that downloaded file is a valid image."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            # Basic size check
            if path.stat().st_size < 1000:
                return False
            
            # Try to read first few bytes to check for image headers
            with open(path, 'rb') as f:
                header = f.read(10)
                
            # Check for common image file signatures
            if header.startswith(b'\xff\xd8\xff'):  # JPEG
                return True
            elif header.startswith(b'\x89PNG'):  # PNG
                return True
            elif header.startswith(b'GIF8'):  # GIF
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying image {file_path}: {e}")
            return False
    
    def cleanup(self):
        """Clean up the session."""
        if self.session:
            self.session.close()
            logger.debug("Cleaned up downloader session")
