"""
Image Processor for OCR Enhancement

Provides advanced image preprocessing capabilities to improve OCR accuracy
for city directory pages.

Based on the original OCR_Col_to_Text.py preprocessing but enhanced for the Final_Round pipeline.
"""

import cv2
import numpy as np
from PIL import Image
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import json

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import IMAGE_PREPROCESSING

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Advanced image processor for OCR enhancement."""
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict] = None):
        """
        Initialize image processor with configuration.
        
        Args:
            config_path: Path to JSON configuration file
            config_dict: Configuration dictionary (overrides config_path)
        """
        self.config = self._load_config(config_path, config_dict)
        self.preprocessing_config = self.config.get('preprocessing', {})
        
        logger.info(f"ImageProcessor initialized with config: {self.preprocessing_config}")
    
    def _load_config(self, config_path: Optional[str], config_dict: Optional[Dict]) -> Dict:
        """Load configuration from file or dictionary."""
        if config_dict:
            return config_dict
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Fallback to default configuration
        return {
            'preprocessing': IMAGE_PREPROCESSING,
            'tesseract': {
                'psm': 6,
                'oem': 3,
                'lang': 'eng'
            }
        }
    
    def preprocess_image(self, image_path: Union[str, Path], 
                        show_steps: bool = False) -> np.ndarray:
        """
        Comprehensive image preprocessing for OCR enhancement.
        
        Args:
            image_path: Path to input image
            show_steps: Whether to display preprocessing steps
            
        Returns:
            Preprocessed image as numpy array
        """
        # Load image in grayscale
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        original = img.copy()
        steps = [('Original', original)]
        
        # Step 1: Denoising
        if self.preprocessing_config.get('enable_denoising', True):
            img = self._apply_denoising(img)
            steps.append(('Denoised', img.copy()))
        
        # Step 2: Contrast enhancement
        if self.preprocessing_config.get('enable_contrast_enhancement', True):
            img = self._enhance_contrast(img)
            steps.append(('Enhanced Contrast', img.copy()))
        
        # Step 3: Binarization
        if self.preprocessing_config.get('enable_binarization', True):
            img = self._apply_binarization(img)
            steps.append(('Binarized', img.copy()))
        
        # Step 4: Morphological operations
        if self.preprocessing_config.get('enable_morphological_operations', True):
            img = self._apply_morphological_operations(img)
            steps.append(('Morphological Cleaned', img.copy()))
        
        if show_steps:
            self._display_preprocessing_steps(image_path, steps)
        
        return img
    
    def _apply_denoising(self, img: np.ndarray) -> np.ndarray:
        """Apply denoising filters to remove salt and pepper noise."""
        # Median filter to remove salt and pepper noise
        kernel_size = self.preprocessing_config.get('median_blur_kernel', 5)
        denoised = cv2.medianBlur(img, kernel_size)
        
        # Bilateral filter to smooth while preserving edges
        bilateral_config = self.preprocessing_config.get('bilateral_filter', {})
        d = bilateral_config.get('d', 9)
        sigma_color = bilateral_config.get('sigma_color', 75)
        sigma_space = bilateral_config.get('sigma_space', 75)
        
        denoised = cv2.bilateralFilter(denoised, d, sigma_color, sigma_space)
        
        logger.debug(f"Applied denoising: median_blur_kernel={kernel_size}, bilateral_filter=d:{d}")
        return denoised
    
    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE."""
        clahe_config = self.preprocessing_config.get('clahe', {})
        clip_limit = clahe_config.get('clip_limit', 2.0)
        tile_grid_size = tuple(clahe_config.get('tile_grid_size', [8, 8]))
        
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        enhanced = clahe.apply(img)
        
        logger.debug(f"Applied CLAHE: clip_limit={clip_limit}, tile_grid_size={tile_grid_size}")
        return enhanced
    
    def _apply_binarization(self, img: np.ndarray) -> np.ndarray:
        """Apply threshold to get clean black/white image."""
        threshold_config = self.preprocessing_config.get('threshold', {})
        method = threshold_config.get('method', 'otsu')
        
        if method == 'otsu':
            _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == 'adaptive':
            adaptive_method = threshold_config.get('adaptive_method', 'gaussian')
            block_size = threshold_config.get('adaptive_block_size', 11)
            c = threshold_config.get('adaptive_c', 2)
            
            if adaptive_method == 'gaussian':
                binary = cv2.adaptiveThreshold(
                    img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c
                )
            else:  # mean
                binary = cv2.adaptiveThreshold(
                    img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, c
                )
        else:
            # Simple threshold
            threshold_value = threshold_config.get('threshold_value', 127)
            _, binary = cv2.threshold(img, threshold_value, 255, cv2.THRESH_BINARY)
        
        logger.debug(f"Applied binarization: method={method}")
        return binary
    
    def _apply_morphological_operations(self, img: np.ndarray) -> np.ndarray:
        """Apply morphological operations to clean up the image."""
        morph_config = self.preprocessing_config.get('morphological', {})
        kernel_type = morph_config.get('kernel_type', 'ellipse')
        kernel_size = tuple(morph_config.get('kernel_size', [2, 2]))
        operation = morph_config.get('operation', 'opening')
        iterations = morph_config.get('iterations', 1)
        
        # Create kernel
        if kernel_type == 'ellipse':
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        elif kernel_type == 'rect':
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        else:  # cross
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, kernel_size)
        
        # Apply morphological operation
        if operation == 'opening':
            cleaned = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=iterations)
        elif operation == 'closing':
            cleaned = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        elif operation == 'erosion':
            cleaned = cv2.erode(img, kernel, iterations=iterations)
        elif operation == 'dilation':
            cleaned = cv2.dilate(img, kernel, iterations=iterations)
        else:
            cleaned = img  # No operation
        
        logger.debug(f"Applied morphological operation: {operation}, kernel={kernel_type}, size={kernel_size}")
        return cleaned
    
    def _display_preprocessing_steps(self, image_path: Union[str, Path], 
                                   steps: list) -> None:
        """Display preprocessing steps for debugging."""
        import matplotlib.pyplot as plt
        
        n_steps = len(steps)
        cols = min(3, n_steps)
        rows = (n_steps + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
        fig.suptitle(f'Preprocessing Steps: {Path(image_path).name}', fontsize=14)
        
        if n_steps == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes if isinstance(axes, (list, np.ndarray)) else [axes]
        else:
            axes = axes.flatten()
        
        for i, (title, img) in enumerate(steps):
            if i < len(axes):
                axes[i].imshow(img, cmap='gray')
                axes[i].set_title(title)
                axes[i].axis('off')
        
        # Hide unused subplots
        for i in range(len(steps), len(axes)):
            axes[i].axis('off')
        
        plt.tight_layout()
        plt.show()
        
        # Ask user if they want to continue
        input("\nPress Enter to continue to next image...")
        plt.close()
    
    def preprocess_for_tesseract(self, image_path: Union[str, Path]) -> Image.Image:
        """
        Preprocess image specifically for Tesseract OCR.
        
        Args:
            image_path: Path to input image
            
        Returns:
            PIL Image ready for Tesseract
        """
        processed_img = self.preprocess_image(image_path)
        
        # Convert to PIL Image
        pil_img = Image.fromarray(processed_img)
        
        return pil_img
    
    def batch_preprocess(self, image_paths: list, output_dir: Union[str, Path]) -> Dict[str, str]:
        """
        Preprocess multiple images and save to output directory.
        
        Args:
            image_paths: List of input image paths
            output_dir: Directory to save processed images
            
        Returns:
            Dictionary mapping original paths to processed paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_paths = {}
        
        for img_path in image_paths:
            try:
                # Preprocess image
                processed_img = self.preprocess_image(img_path)
                
                # Generate output path
                input_path = Path(img_path)
                output_path = output_dir / f"{input_path.stem}_processed{input_path.suffix}"
                
                # Save processed image
                cv2.imwrite(str(output_path), processed_img)
                
                processed_paths[str(img_path)] = str(output_path)
                logger.info(f"Processed and saved: {output_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to process {img_path}: {e}")
                processed_paths[str(img_path)] = None
        
        return processed_paths
    
    def get_image_quality_metrics(self, image_path: Union[str, Path]) -> Dict[str, float]:
        """
        Calculate image quality metrics.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Dictionary of quality metrics
        """
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {}
        
        # Calculate various quality metrics
        metrics = {}
        
        # Contrast (standard deviation)
        metrics['contrast'] = float(np.std(img))
        
        # Brightness (mean)
        metrics['brightness'] = float(np.mean(img))
        
        # Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        metrics['sharpness'] = float(laplacian.var())
        
        # Noise estimation (using median filter difference)
        median_filtered = cv2.medianBlur(img, 5)
        noise = np.mean(np.abs(img.astype(float) - median_filtered.astype(float)))
        metrics['noise_level'] = float(noise)
        
        # Dynamic range
        metrics['dynamic_range'] = float(np.max(img) - np.min(img))
        
        logger.debug(f"Image quality metrics for {image_path}: {metrics}")
        return metrics
    
    def auto_adjust_config(self, image_path: Union[str, Path]) -> Dict:
        """
        Automatically adjust preprocessing configuration based on image characteristics.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Adjusted configuration dictionary
        """
        metrics = self.get_image_quality_metrics(image_path)
        adjusted_config = self.config.copy()
        
        # Adjust based on image quality
        if metrics.get('noise_level', 0) > 10:
            # High noise - increase denoising
            adjusted_config['preprocessing']['median_blur_kernel'] = 7
            adjusted_config['preprocessing']['bilateral_filter']['d'] = 11
        
        if metrics.get('contrast', 0) < 30:
            # Low contrast - increase CLAHE
            adjusted_config['preprocessing']['clahe']['clip_limit'] = 3.0
        
        if metrics.get('sharpness', 0) < 100:
            # Low sharpness - reduce morphological operations
            adjusted_config['preprocessing']['morphological']['iterations'] = 1
        
        logger.debug(f"Auto-adjusted config based on image metrics: {adjusted_config}")
        return adjusted_config


def enhance_image_for_ocr(image_path: Union[str, Path], 
                         output_path: Optional[Union[str, Path]] = None,
                         config_path: Optional[str] = None) -> Union[str, np.ndarray]:
    """
    Convenience function to enhance a single image for OCR.
    
    Args:
        image_path: Path to input image
        output_path: Path to save enhanced image (optional)
        config_path: Path to configuration file (optional)
        
    Returns:
        Enhanced image array or path to saved image
    """
    processor = ImageProcessor(config_path=config_path)
    enhanced_img = processor.preprocess_image(image_path)
    
    if output_path:
        cv2.imwrite(str(output_path), enhanced_img)
        logger.info(f"Enhanced image saved to: {output_path}")
        return str(output_path)
    else:
        return enhanced_img


if __name__ == "__main__":
    # Example usage
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample image
    test_image = "test_images/sample.jpg"  # Replace with actual test image
    
    if Path(test_image).exists():
        processor = ImageProcessor()
        
        # Get quality metrics
        metrics = processor.get_image_quality_metrics(test_image)
        print(f"Image quality metrics: {metrics}")
        
        # Preprocess image
        enhanced = processor.preprocess_image(test_image, show_steps=True)
        
        # Save enhanced image
        output_path = "enhanced_sample.jpg"
        cv2.imwrite(output_path, enhanced)
        print(f"Enhanced image saved to: {output_path}")
    else:
        print(f"Test image not found: {test_image}")
        print("Please provide a valid test image path.")
