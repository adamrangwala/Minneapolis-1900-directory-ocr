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
            
            for line_num, line in enumerate(lines, 1):
                entry = self.parse_line(line, line_num)
                if entry:
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
        entry = JSON_OUTPUT_FORMAT.copy()
        entry.update({
            "line_number": line_num,
            "raw_text": line,
            "DirectoryName": f"Minneapolis {self.year}",
            "year": self.year,
            "parsing_notes": []
        })
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
            entry["parsing_notes"].append("Could not parse surname properly")
    
    def _parse_continuation_line(self, entry: Dict, line: str) -> None:
        """Parse line that continues from previous surname."""
        entry["LastName"] = self.current_surname
        entry["parsing_notes"].append("Inherited surname from previous entry")
        self.entry_extractor.parse_name_and_details(entry, line)
    
    def save_to_json(self, output_file: str) -> None:
        """Save parsed entries to JSON file."""
        try:
            output_dir = Path("data/output_json")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / Path(output_file).name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.entries, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.entries)} entries to {output_path}")
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
