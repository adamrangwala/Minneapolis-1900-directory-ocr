"""
Text Cleaning and Post-processing

Handles cleaning of OCR text output to remove noise and improve quality.
"""

import re
import logging
from typing import Dict, List

# Import configuration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import ABBREVIATIONS

logger = logging.getLogger(__name__)


class TextCleaner:
    """Text cleaning and post-processing for OCR output."""
    
    def __init__(self, config: Dict):
        """Initialize text cleaner with configuration."""
        self.config = config
        logger.info("TextCleaner initialized")
    
    def clean_text(self, text: str) -> str:
        """Clean OCR text by removing noise and applying post-processing."""
        if not text:
            return text
        
        lines = text.split('\n')
        cleaned_lines = []
        
        min_line_length = self.config.get('min_line_length', 3)
        
        for line in lines:
            if not line.strip() or len(line.strip()) < min_line_length:
                continue
            
            cleaned_line = line
            
            # Remove noise characters if enabled
            if self.config.get('remove_noise_characters', True):
                cleaned_line = self._remove_noise_characters(cleaned_line)
            
            if cleaned_line.strip():
                cleaned_lines.append(cleaned_line.strip())
        
        # Merge continuation lines if enabled
        if self.config.get('merge_continuation_lines', True):
            cleaned_lines = self._merge_continuation_lines(cleaned_lines)
        
        # Expand abbreviations if enabled
        if self.config.get('expand_abbreviations', True):
            cleaned_lines = self._expand_abbreviations(cleaned_lines)
        
        return '\n'.join(cleaned_lines)
    
    def _remove_noise_characters(self, line: str) -> str:
        """Remove noise characters from line while preserving valid content."""
        noise_chars = self.config.get(
            'noise_characters', 
            "~`!@#$%^&*()_+=[]{}|\\:;\"'<>?,./"
        )
        
        allowed_leading = set(self.config.get(
            'allowed_leading_chars',
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&'
        ))
        
        # Clean from the beginning
        while line and line[0] not in allowed_leading:
            line = line[1:]
        
        # Clean from the end, but preserve periods that follow letters/numbers
        while line:
            last_char = line[-1]
            
            if last_char.isalnum() or last_char in '&':
                break
            elif last_char == '.' and len(line) > 1 and line[-2] in allowed_leading:
                break
            else:
                line = line[:-1]
        
        return line
    
    def _merge_continuation_lines(self, lines: List[str]) -> List[str]:
        """Merge continuation lines with previous entries."""
        if not lines:
            return lines
        
        combined_lines = []
        continuation_indicators = self.config.get(
            'continuation_indicators',
            ['starts_with_digit', 'starts_with_lowercase', 'very_short_line', 'common_continuation_words']
        )
        
        for line in lines:
            if combined_lines and self._is_continuation_line(line, continuation_indicators):
                combined_lines[-1] = combined_lines[-1] + ' ' + line.strip()
            else:
                combined_lines.append(line)
        
        return combined_lines
    
    def _is_continuation_line(self, line: str, indicators: List[str]) -> bool:
        """Check if a line is a continuation of the previous entry."""
        if not line.strip():
            return False
        
        first_char = line.strip()[0]
        first_word = line.strip().split()[0] if line.strip() else ''
        
        for indicator in indicators:
            if indicator == 'starts_with_digit' and first_char.isdigit():
                return True
            elif indicator == 'starts_with_lowercase' and first_char.islower():
                return True
            elif indicator == 'very_short_line' and len(line.strip()) < 16:
                return True
            elif indicator == 'common_continuation_words':
                common_words = self.config.get(
                    'common_continuation_words',
                    ['Co', 'same', 'Co,', 'Inc', 'Ltd', 'Corp']
                )
                if first_word in common_words:
                    return True
        
        return False
    
    def _expand_abbreviations(self, lines: List[str]) -> List[str]:
        """Expand common abbreviations in the text."""
        expanded_lines = []
        
        for line in lines:
            expanded_line = line
            
            for abbrev, full_form in ABBREVIATIONS.items():
                pattern = r'\b' + re.escape(abbrev) + r'\b'
                expanded_line = re.sub(pattern, full_form, expanded_line, flags=re.IGNORECASE)
            
            expanded_lines.append(expanded_line)
        
        return expanded_lines
