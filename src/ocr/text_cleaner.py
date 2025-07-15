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
                cleaned_line = self._clean_front_of_line(cleaned_line)
                cleaned_line = self._clean_end_of_line(cleaned_line)
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
        if not line:
            return line
            
        # Update this list of characters as needed in debugging
        noise_characters = self.config.get(
            'noise_characters',
            "~_"
        )
        for char in line:
            if char in noise_characters:
                line = line.replace(char, '')
        
        return line  # FIX: Added missing return statement

    def _clean_front_of_line(self, line: str) -> str:
        if not line:
            return line
            
        allowed_leading = set(self.config.get(
            'allowed_leading_chars',
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&'
        ))

        quote_artifacts = {''', ''', '‘', '’', '“', '”', '*', "'", '"', '"', '"', '´', '`','°', '‛', '❛', '❜', '❝', '❞'}
        
        has_leading_quote = False
        # Clean from the beginning - FIX: Added bounds checking
        if len(line) > 0 and line[0] in quote_artifacts:
            has_leading_quote = True
        elif len(line) > 1 and line[1] in quote_artifacts:
            has_leading_quote = True
            
        while line and line[0] not in allowed_leading:
            line = line[1:]
        if has_leading_quote == True and line and line[0] in allowed_leading:
            line = "'" + line
        
        return line
    
    def _clean_end_of_line(self, line: str) -> str:
    
        allowed_ending = set(self.config.get(
            'allowed_ending_chars',
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&)'
        ))
        # Clean from the end, but preserve periods that follow letters/numbers
        while line:
            last_char = line[-1]
            
            if last_char.isalnum() or last_char in '&':
                break
            elif last_char in ('.',',') and len(line) > 1 and line[-2] in allowed_ending:
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
            first_char = line.strip()[0]
            previous_line_first_char = combined_lines[-1].strip()[0] if combined_lines else ''
            previous_line_last_word = combined_lines[-1].strip().split()[-1] if combined_lines else ''
            continuation_ends = ['and', 'the', 'of', 'in', 'for', 'to', 'on', 'at', 'with', 'by', 'as', 'is', 'are', ',']
            print("Previous line last word:", previous_line_last_word)

            # if line starts with a quote, not a continuation
            if ord(first_char) in (8216, 8217, 8220, 8221, 39, 34) and combined_lines:
                combined_lines.append(line)
                logger.info(f"Line starts with quote, not continuation: '{line}'")
            # Handle hyphenated words split across lines
            elif combined_lines and combined_lines[-1].endswith('-'):
                combined_lines[-1] = combined_lines[-1][:-1] + line.strip()
                logger.info(f"Merging hyphenated line: '{combined_lines[-1]}'")
            # If line is a continuation of previous line, add to previous line
            elif combined_lines and self._is_continuation_line(line, continuation_indicators):
                combined_lines[-1] = combined_lines[-1] + ' ' + line.strip()
                logger.info(f"Merging continuation line: '{combined_lines[-1]}'")
            # If previous line ends with 'and' or 'the' or similar, treat as continuation
            elif previous_line_last_word.lower() in continuation_ends and combined_lines:
                combined_lines[-1] = combined_lines[-1] + ' ' + line.strip()
                logger.info(f"Merging line with previous 'and'/'the': '{combined_lines[-1]}'") # If previous line ends with 'and' or 'the' or similar, treat as continuation
            # If previous line ends with a number, treat as continuation (e.g. addresses)
            elif combined_lines and previous_line_last_word.isdigit():
                combined_lines[-1] = combined_lines[-1] + ' ' + line.strip()
                logger.info(f"Merging line after number: '{combined_lines[-1]}'")
            # Not a continuation
            else:
                combined_lines.append(line)
                logger.info(f"New line added: '{line}'")
                
        return combined_lines
    
    def _is_continuation_line(self, line: str, indicators: List[str]) -> bool:
        """Check if a line is a continuation of the previous entry."""
        if not line.strip():
            return False
        
        first_char = line.strip()[0]
        first_word = line.strip().split()[0] if line.strip() else ''
        
        # Simple indicators for continuation lines
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
