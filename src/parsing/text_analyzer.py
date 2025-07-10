"""
Text Analysis for Directory Parsing

Analyzes OCR text to identify patterns and structure.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """Analyzes text patterns for directory entry parsing."""
    
    def __init__(self):
        """Initialize text analyzer."""
        self.occupation_indicators = ['clk', 'lab', 'tmstr', 'mach', 'eng', 'student', 'moved', 'died']
        logger.info("TextAnalyzer initialized")
    
    def starts_with_surname(self, line: str) -> bool:
        """Check if line starts with a new surname."""
        words = line.split(', ')
        full_name = words[0] if words else ""
        
        name_split = full_name.split()
        if len(name_split) > 1:
            potential_surname = name_split[0]
            
            if (potential_surname and 
                potential_surname[0].isupper() and 
                not self.looks_like_occupation(potential_surname) and
                len(potential_surname) > 1):
                return True
        
        elif len(name_split) == 1 and 'see also' in line:
            potential_surname = name_split[0]
            if (potential_surname and 
                potential_surname[0].isupper() and 
                not self.looks_like_occupation(potential_surname) and
                len(potential_surname) > 1):
                return True
        
        return False
    
    def looks_like_occupation(self, word: str) -> bool:
        """Check if a word looks like an occupation rather than a first name."""
        return word.lower() in self.occupation_indicators
    
    def extract_first_name(self, text: str) -> str:
        """Extract first name from text."""
        text = text.lstrip(', ')
        words = text.split()
        
        if words:
            potential_first_name = words[0].rstrip(',')
            if not self.looks_like_occupation(potential_first_name):
                return potential_first_name
        
        return ""
    
    def identify_widow_notation(self, text: str) -> str:
        """Identify widow notation in text."""
        import re
        if 'wid ' in text.lower():
            match = re.search(r'wid ([^,)]+)', text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
    
    def extract_residence_indicators(self, text: str) -> tuple:
        """Extract residence indicators from text."""
        import re
        text_lower = text.lower()
        
        residence_patterns = [
            (r'\br\s+([^,]+)', 'resides'),
            (r'\bb\s+([^,]+)', 'boards'),
            (r'\brms\s+([^,]+)', 'rooms'),
            (r'\bh\s+([^,]+)', 'house')
        ]
        
        for pattern, indicator in residence_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return indicator, match.group(1).strip()
        
        return "", ""
    
    def find_address_patterns(self, text: str) -> str:
        """Find address patterns in text."""
        import re
        text_lower = text.lower()
        
        # Look for number + street patterns
        addr_match = re.search(r'\b(\d+[^,]*(?:av|st|blvd|rd)[^,]*)', text_lower)
        if addr_match:
            return addr_match.group(1).strip()
        
        return ""
    
    def split_name_and_details(self, text: str) -> tuple:
        """Split text into name and remaining details."""
        text = text.lstrip(', ')
        words = text.split()
        
        if words:
            potential_first_name = words[0].rstrip(',')
            
            if not self.looks_like_occupation(potential_first_name):
                remaining_text = ' '.join(words[1:])
                return potential_first_name, remaining_text
        
        return "", text
