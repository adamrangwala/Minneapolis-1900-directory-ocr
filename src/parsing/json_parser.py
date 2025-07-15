"""
Main JSON Parser for City Directory Entries

Converts OCR text output into structured JSON format.
Based on the original JSON_Parser.py but enhanced for the Final_Round pipeline.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .text_analyzer import TextAnalyzer
from .entry_extractor import EntryExtractor

# Import configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import JSON_OUTPUT_FORMAT

logger = logging.getLogger(__name__)


class CityDirectoryParser:
    """Main parser for converting OCR text to structured JSON entries."""
    
    def __init__(self, year: str = "1900"):
        """Initialize parser with directory year."""
        self.year = year
        self.current_surname = ""
        self.current_address = ""
        self.entries = []
        
        # Initialize helper components
        self.text_analyzer = TextAnalyzer()
        self.entry_extractor = EntryExtractor(year)
        
        logger.info(f"CityDirectoryParser initialized for year {year}")
    
    def parse_text_file(self, file_path: str) -> List[Dict]:
        """Parse a single OCR text file into structured JSON entries."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            self.entries = []
            self.current_surname = ""
            self.current_address = ""
            
            # Extract page number from filename
            page_number = self._extract_page_number_from_filename(file_path)
            
            for line_num, line in enumerate(lines, 1):
                entry = self.parse_line(line, line_num)
                if entry:
                    # Set page number for each entry
                    if page_number:
                        entry["PageNumber"] = page_number
                    self.entries.append(entry)
            
            logger.info(f"Parsed {len(self.entries)} entries from {file_path}")
            return self.entries
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return []
    
    def parse_line(self, line: str, line_num: int) -> Optional[Dict]:
        """Parse a single line into a structured entry."""
        if not line or len(line) < 3:
            return None
        
        # Filter out non-resident lines (advertisements, etc.)
        if not self._is_resident_line(line):
            return None
        
        # Initialize entry with template
        entry = self._create_entry_template(line_num, line)
        
        # Check if this line starts with a new surname
        if self.text_analyzer.starts_with_surname(line):
            self._parse_surname_line(entry, line)
        else:
            self._parse_continuation_line(entry, line)
        
        # Extract address information
        self.entry_extractor.extract_address_info(entry, self.current_address)
        
        return entry
    
    def _create_entry_template(self, line_num: int, line: str) -> Dict:
        """Create entry template with basic information."""
        import copy
        entry = copy.deepcopy(JSON_OUTPUT_FORMAT)
        entry["DirectoryName"] = f"Minneapolis {self.year}"
        # Store internal fields for processing but don't include in final output
        entry["_line_number"] = line_num
        entry["_raw_text"] = line
        entry["_parsing_notes"] = []
        return entry
    
    def _parse_surname_line(self, entry: Dict, line: str) -> None:
        """Parse line that starts with a new surname."""
        parts = line.split(' ', 2)
        if len(parts) >= 2:
            self.current_surname = parts[0].rstrip(',')
            entry["LastName"] = self.current_surname
            
            remainder = ' '.join(parts[1:]) if len(parts) > 1 else ""
            self.entry_extractor.parse_name_and_details(entry, remainder)
        else:
            entry["_parsing_notes"].append("Could not parse surname properly")
    
    def _parse_continuation_line(self, entry: Dict, line: str) -> None:
        """Parse line that continues from previous surname."""
        entry["LastName"] = self.current_surname
        entry["_parsing_notes"].append("Inherited surname from previous entry")
        self.entry_extractor.parse_name_and_details(entry, line)
    
    def _is_resident_line(self, line: str) -> bool:
        """Check if line represents a resident entry vs advertisement/non-resident content."""
        line_lower = line.lower()
        
        # Filter out obvious advertisement patterns
        ad_patterns = [
            'furnished promptly',
            'delivered for',
            'telephone',
            'cents',
            'promptly',
            'trunks delivered',
            'messengers furnished'
        ]
        
        # Check for advertisement patterns
        for pattern in ad_patterns:
            if pattern in line_lower:
                return False
        
        # Filter out lines that don't have typical resident structure
        # Valid resident lines should have:
        # 1. A name pattern (First Last, or 'First Last,)
        # 2. Followed by occupation/address information
        # 3. Or contain residence indicators
        
        # Check for residence indicators that suggest this is a resident entry
        residence_indicators = ['r', 'boards', 'rms', 'student', 'wid']
        has_residence_indicator = any(indicator in line_lower for indicator in residence_indicators)
        
        # Check for occupation keywords
        occupation_keywords = [
            'porter', 'clerk', 'laborer', 'teamster', 'machinist', 'engineer',
            'salesman', 'bookkeeper', 'carpenter', 'conductor', 'waiter',
            'student', 'seamstress', 'nurse', 'cook', 'millwright', 'cutter'
        ]
        has_occupation = any(occupation in line_lower for occupation in occupation_keywords)
        
        # Check for typical name structure (Last First, or 'First)
        has_name_structure = (
            (',' in line and not line.startswith('AQ!')) or  # Has comma separator
            line.startswith("'") or  # Continuation with apostrophe
            any(char.isupper() for char in line[:10])  # Has uppercase letters in first 10 chars
        )
        
        # Check for address patterns (numbers followed by street names)
        import re
        has_address = bool(re.search(r'\b\d{3,4}\b.*\b(avenue|street|av|st|place|blvd)\b', line_lower))
        
        # A line is considered a resident entry if it has:
        # - Name structure AND (residence indicator OR occupation OR address)
        # - OR if it's a "see also" reference line
        if 'see also' in line_lower:
            return True
            
        return has_name_structure and (has_residence_indicator or has_occupation or has_address)
    
    def _clean_entry(self, entry: Dict) -> Dict:
        """Clean entry by removing internal fields and ensuring proper format."""
        cleaned_entry = {}
        for key, value in entry.items():
            if not key.startswith('_'):  # Skip internal fields
                cleaned_entry[key] = value
        return cleaned_entry
    
    def _extract_page_number_from_filename(self, filename: str) -> int:
        """Extract page number from filename."""
        import re
        # Look for patterns like 1900_0112 where 0112 corresponds to page 112
        match = re.search(r'1900_0(\d+)', filename)
        if match:
            return int(match.group(1))
        return None
    
    def set_page_number(self, page_number: int) -> None:
        """Set page number for all entries."""
        for entry in self.entries:
            entry["PageNumber"] = page_number
    
    def save_to_json(self, output_file: str, page_number: int = None) -> None:
        """Save parsed entries to JSON file."""
        try:
            output_dir = Path("data/output_json")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / Path(output_file).name
            
            # Set page number if provided
            if page_number:
                self.set_page_number(page_number)
            
            # Clean entries before saving
            cleaned_entries = [self._clean_entry(entry) for entry in self.entries]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_entries, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(cleaned_entries)} entries to {output_path}")
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
    
    def get_summary(self) -> Dict:
        """Get summary statistics of parsed entries."""
        if not self.entries:
            return {}
        
        last_names = set(entry["LastName"] for entry in self.entries if entry["LastName"])
        with_addresses = sum(1 for entry in self.entries 
                           if entry["HomeAddress"]["StreetName"])
        with_occupations = sum(1 for entry in self.entries if entry["Occupation"])
        
        return {
            "total_entries": len(self.entries),
            "unique_last_names": len(last_names),
            "entries_with_addresses": with_addresses,
            "entries_with_occupations": with_occupations
        }


def parse_directory_file(file_path: str, year: str = "1900") -> List[Dict]:
    """Convenience function to parse a single directory file."""
    parser = CityDirectoryParser(year=year)
    return parser.parse_text_file(file_path)


def combine_json_outputs(output_dir: str = "data/output_json",
                        final_output_file: str = "final_json_output.json") -> None:
    """Combine all individual JSON files into a single final output file."""
    import glob
    
    output_path = Path(output_dir)
    final_output_path = output_path / final_output_file
    
    all_entries = []
    
    # Find all page JSON files
    json_files = glob.glob(str(output_path / "page_*.json"))
    json_files.sort()  # Sort to maintain order
    
    logger.info(f"Found {len(json_files)} JSON files to combine")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                entries = json.load(f)
                if isinstance(entries, list):
                    all_entries.extend(entries)
                    logger.info(f"Added {len(entries)} entries from {Path(json_file).name}")
                else:
                    logger.warning(f"Unexpected format in {json_file}")
        except Exception as e:
            logger.error(f"Error reading {json_file}: {e}")
    
    # Save combined output
    try:
        with open(final_output_path, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Combined {len(all_entries)} total entries into {final_output_path}")
        print(f"Successfully created {final_output_path} with {len(all_entries)} entries")
        
    except Exception as e:
        logger.error(f"Error saving combined output: {e}")
