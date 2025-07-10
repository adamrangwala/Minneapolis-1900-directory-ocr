"""
Batch Processing Utilities

Handles batch processing of multiple pages with progress tracking.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .checkpoint_manager import CheckpointManager

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import BATCH_PROCESSING

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Handles batch processing with progress tracking and checkpointing."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        """Initialize batch processor."""
        self.checkpoint_manager = CheckpointManager(checkpoint_dir)
        
        # Get batch settings from config
        self.batch_size = BATCH_PROCESSING.get('batch_size', 5)
        self.max_workers = BATCH_PROCESSING.get('max_workers', 4)
        self.checkpoint_interval = BATCH_PROCESSING.get('checkpoint_interval', 10)
        
        logger.info(f"BatchProcessor initialized with batch_size={self.batch_size}")
    
    def process_items(self, items: List, process_func: Callable, 
                     job_name: str = "batch_job") -> Dict:
        """Process items in batches with checkpointing."""
        # Load existing checkpoint if available
        checkpoint = self.checkpoint_manager.load_checkpoint(job_name)
        
        if checkpoint:
            processed_items = checkpoint.get('processed_items', {})
            start_index = checkpoint.get('last_index', 0)
            logger.info(f"Resuming from checkpoint: {start_index}/{len(items)} items")
        else:
            processed_items = {}
            start_index = 0
            logger.info(f"Starting new batch job: {len(items)} items")
        
        # Process remaining items
        for i in range(start_index, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = self._process_batch(batch, process_func)
            
            # Update processed items
            for item_id, result in batch_results.items():
                processed_items[item_id] = result
            
            # Save checkpoint periodically
            if (i + self.batch_size) % self.checkpoint_interval == 0:
                checkpoint_data = {
                    'processed_items': processed_items,
                    'last_index': i + self.batch_size,
                    'total_items': len(items),
                    'timestamp': time.time()
                }
                self.checkpoint_manager.save_checkpoint(job_name, checkpoint_data)
                logger.info(f"Checkpoint saved at item {i + self.batch_size}")
        
        # Final checkpoint
        final_checkpoint = {
            'processed_items': processed_items,
            'last_index': len(items),
            'total_items': len(items),
            'timestamp': time.time(),
            'completed': True
        }
        self.checkpoint_manager.save_checkpoint(job_name, final_checkpoint)
        
        logger.info(f"Batch processing complete: {len(processed_items)} items processed")
        return processed_items
    
    def _process_batch(self, batch: List, process_func: Callable) -> Dict:
        """Process a single batch of items."""
        results = {}
        
        if self.max_workers > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_item = {executor.submit(process_func, item): item for item in batch}
                
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        result = future.result()
                        results[str(item)] = result
                    except Exception as e:
                        logger.error(f"Error processing {item}: {e}")
                        results[str(item)] = None
        else:
            # Sequential processing
            for item in batch:
                try:
                    result = process_func(item)
                    results[str(item)] = result
                except Exception as e:
                    logger.error(f"Error processing {item}: {e}")
                    results[str(item)] = None
        
        return results
    
    def get_progress(self, job_name: str) -> Optional[Dict]:
        """Get progress information for a job."""
        checkpoint = self.checkpoint_manager.load_checkpoint(job_name)
        
        if not checkpoint:
            return None
        
        total_items = checkpoint.get('total_items', 0)
        last_index = checkpoint.get('last_index', 0)
        
        if total_items > 0:
            progress_percent = (last_index / total_items) * 100
        else:
            progress_percent = 0
        
        return {
            'total_items': total_items,
            'processed_items': last_index,
            'progress_percent': progress_percent,
            'completed': checkpoint.get('completed', False),
            'timestamp': checkpoint.get('timestamp')
        }
    
    def cleanup_job(self, job_name: str) -> None:
        """Clean up checkpoint for completed job."""
        self.checkpoint_manager.delete_checkpoint(job_name)
        logger.info(f"Cleaned up job: {job_name}")


def process_in_batches(items: List, process_func: Callable, 
                      job_name: str = "batch_job") -> Dict:
    """Convenience function for batch processing."""
    processor = BatchProcessor()
    return processor.process_items(items, process_func, job_name)
