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
            # Remove leading apostrophe from names like 'Smith
            if potential_first_name.startswith("'"):
                potential_first_name = potential_first_name[1:]
            
            if not self.looks_like_occupation(potential_first_name):
                return potential_first_name
        
        return ""
    
    def identify_widow_notation(self, text: str) -> str:
        """Identify widow notation in text."""
        import re
        
        # Look for various widow patterns
        widow_patterns = [
            # Pattern: (widow Name)
            r'\(widow\s+([^)]+)\)',
            # Pattern: wid Name
            r'\bwid\s+([^,)]+)',
            # Pattern: widow Name
            r'\bwidow\s+([^,)]+)'
        ]
        
        for pattern in widow_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                spouse_name = match.group(1).strip()
                # Add (deceased) if not already present
                if 'deceased' not in spouse_name.lower():
                    spouse_name += ' (deceased)'
                return spouse_name
        
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
        
        if not words:
            return "", text
        
        # Extract first name including middle names/initials
        first_name_parts = []
        remaining_words = []
        
        # Common occupation keywords to stop at
        occupation_keywords = [
            'porter', 'clerk', 'laborer', 'teamster', 'machinist', 'engineer',
            'salesman', 'bookkeeper', 'carpenter', 'conductor', 'waiter',
            'student', 'seamstress', 'nurse', 'cook', 'millwright', 'cutter',
            'clk', 'lab', 'tmstr', 'mach', 'eng', 'slsmn', 'bkpr', 'carp', 'cond',
            'photographer', 'domestic', 'superintendent', 'physician', 'driver',
            'letter', 'carrier', 'hostler', 'lawyer', 'traveling', 'agent',
            'manager', 'mnegr', 'mnfrs', 'peddler', 'apprentice', 'grocer',
            'confectioner', 'wireman', 'foreman', 'jeweler', 'seamstress',
            'house', 'mover', 'stenographer', 'salesman', 'operator', 'bartender',
            'car', 'repairer', 'with', 'died', 'moved', 'widow'
        ]
        
        # Address/location indicators that signal end of name
        location_indicators = [
            'residence', 'boards', 'rms', 'telephone', 'same', 'building',
            'bldg', 'avenue', 'street', 'av', 'st', 'north', 'south', 'east', 'west'
        ]
        
        for i, word in enumerate(words):
            word_clean = word.rstrip(',').lower()
            
            # Stop if we hit an occupation keyword
            if word_clean in occupation_keywords:
                remaining_words = words[i:]
                break
            
            # Stop if we hit a location indicator
            if word_clean in location_indicators:
                remaining_words = words[i:]
                break
            
            # Stop if we hit a parenthesis (like widow notation)
            if '(' in word:
                remaining_words = words[i:]
                break
                
            # Add to first name if it looks like a name part
            # Names typically are capitalized and don't contain numbers
            # Include single letters (initials) and names with apostrophes
            word_clean = word.rstrip(',')
            word_for_check = word_clean.lstrip("'")  # Remove leading apostrophe for checking
            
            if (word_for_check.isalpha() and
                (word_for_check[0].isupper() if word_for_check else False) and
                len(word_for_check) >= 1):  # Allow single letter initials
                # Clean the apostrophe from the beginning if it's there
                clean_name = word_clean.lstrip("'") if word_clean.startswith("'") else word_clean
                first_name_parts.append(clean_name)
            else:
                remaining_words = words[i:]
                break
        
        # If no remaining words were found, everything after first name part is remaining
        if not remaining_words and len(words) > len(first_name_parts):
            remaining_words = words[len(first_name_parts):]
        
        first_name = ' '.join(first_name_parts) if first_name_parts else ""
        remaining_text = ' '.join(remaining_words) if remaining_words else ""
        
        return first_name, remaining_text
