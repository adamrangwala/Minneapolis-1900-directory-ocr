"""
Checkpoint Management

Handles saving and loading processing checkpoints for resumable operations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages checkpoints for resumable processing operations."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        """Initialize checkpoint manager."""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CheckpointManager initialized with dir: {checkpoint_dir}")
    
    def save_checkpoint(self, job_name: str, data: Dict) -> None:
        """Save checkpoint data for a job."""
        try:
            checkpoint_file = self.checkpoint_dir / f"{job_name}.json"
            
            # Add metadata
            checkpoint_data = {
                'job_name': job_name,
                'saved_at': time.time(),
                'data': data
            }
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            logger.debug(f"Checkpoint saved for job: {job_name}")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint for {job_name}: {e}")
    
    def load_checkpoint(self, job_name: str) -> Optional[Dict]:
        """Load checkpoint data for a job."""
        try:
            checkpoint_file = self.checkpoint_dir / f"{job_name}.json"
            
            if not checkpoint_file.exists():
                logger.debug(f"No checkpoint found for job: {job_name}")
                return None
            
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            logger.info(f"Checkpoint loaded for job: {job_name}")
            return checkpoint_data.get('data', {})
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint for {job_name}: {e}")
            return None
    
    def delete_checkpoint(self, job_name: str) -> bool:
        """Delete checkpoint for a job."""
        try:
            checkpoint_file = self.checkpoint_dir / f"{job_name}.json"
            
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                logger.info(f"Checkpoint deleted for job: {job_name}")
                return True
            else:
                logger.debug(f"No checkpoint to delete for job: {job_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete checkpoint for {job_name}: {e}")
            return False
    
    def list_checkpoints(self) -> list:
        """List all available checkpoints."""
        try:
            checkpoint_files = list(self.checkpoint_dir.glob("*.json"))
            job_names = [f.stem for f in checkpoint_files]
            logger.debug(f"Found {len(job_names)} checkpoints")
            return job_names
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    def get_checkpoint_info(self, job_name: str) -> Optional[Dict]:
        """Get metadata about a checkpoint."""
        try:
            checkpoint_file = self.checkpoint_dir / f"{job_name}.json"
            
            if not checkpoint_file.exists():
                return None
            
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            return {
                'job_name': checkpoint_data.get('job_name'),
                'saved_at': checkpoint_data.get('saved_at'),
                'file_size': checkpoint_file.stat().st_size,
                'has_data': 'data' in checkpoint_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint info for {job_name}: {e}")
            return None
    
    def cleanup_old_checkpoints(self, max_age_days: int = 7) -> int:
        """Clean up checkpoints older than specified days."""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            deleted_count = 0
            checkpoint_files = list(self.checkpoint_dir.glob("*.json"))
            
            for checkpoint_file in checkpoint_files:
                try:
                    with open(checkpoint_file, 'r', encoding='utf-8') as f:
                        checkpoint_data = json.load(f)
                    
                    saved_at = checkpoint_data.get('saved_at', 0)
                    age = current_time - saved_at
                    
                    if age > max_age_seconds:
                        checkpoint_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old checkpoint: {checkpoint_file.stem}")
                        
                except Exception as e:
                    logger.warning(f"Error processing checkpoint {checkpoint_file}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} old checkpoints")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old checkpoints: {e}")
            return 0
