"""
Entry Extraction for Directory Parsing

Extracts specific information from directory entries.
"""

import logging
from typing import Dict

from .text_analyzer import TextAnalyzer

# Import configuration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import ABBREVIATIONS

logger = logging.getLogger(__name__)


class EntryExtractor:
    """Extracts specific information from directory entries."""
    
    def __init__(self, year: str = "1900"):
        """Initialize entry extractor."""
        self.year = year
        self.text_analyzer = TextAnalyzer()
        logger.info(f"EntryExtractor initialized for year {year}")
    
    def parse_name_and_details(self, entry: Dict, text: str) -> None:
        """Parse first name and other details from text."""
        if not text:
            return
        
        # Extract first name
        first_name, remaining_text = self.text_analyzer.split_name_and_details(text)
        if first_name:
            entry["FirstName"] = first_name
        
        # Parse remaining details
        if remaining_text:
            self.parse_occupation_and_employer(entry, remaining_text)
    
    def parse_occupation_and_employer(self, entry: Dict, text: str) -> None:
        """Extract occupation and employer information."""
        if not text:
            return
        
        # Check for widow notation
        widow_spouse = self.text_analyzer.identify_widow_notation(text)
        if widow_spouse:
            entry["Spouse"] = widow_spouse
            entry["parsing_notes"].append("Identified as widow")
        
        # Look for common occupation patterns
        self._extract_occupation(entry, text)
        
        # Store remaining text for further analysis
        entry["parsing_notes"].append(f"Remaining text: {text}")
    
    def _extract_occupation(self, entry: Dict, text: str) -> None:
        """Extract occupation from text using abbreviations."""
        for abbrev, full_form in ABBREVIATIONS.items():
            if abbrev in text and not entry["Occupation"]:
                if abbrev in ['clk', 'lab', 'tmstr', 'mach', 'eng']:
                    entry["Occupation"] = full_form
                    break
    
    def extract_address_info(self, entry: Dict, current_address: str) -> None:
        """Extract address and residence indicators."""
        text = entry["raw_text"].lower()
        
        # Look for residence indicators
        indicator, address = self.text_analyzer.extract_residence_indicators(text)
        if indicator and address:
            entry["HomeAddress"]["ResidenceIndicator"] = indicator
            entry["HomeAddress"]["StreetName"] = address
            return
        
        # Look for address patterns
        address = self.text_analyzer.find_address_patterns(text)
        if address:
            entry["HomeAddress"]["StreetName"] = address
        elif current_address:
            entry["HomeAddress"]["StreetName"] = current_address
            entry["parsing_notes"].append("Inherited address from previous entry")
    
    def extract_work_address(self, entry: Dict, text: str) -> None:
        """Extract work address from text."""
        # Simple pattern matching for work addresses
        if "office" in text.lower() or "bldg" in text.lower():
            # Extract potential work address
            parts = text.split(',')
            for part in parts:
                if any(keyword in part.lower() for keyword in ["office", "bldg", "room"]):
                    entry["WorkAddress"] = part.strip()
                    break
    
    def extract_telephone(self, entry: Dict, text: str) -> None:
        """Extract telephone information from text."""
        import re
        # Look for telephone patterns
        tel_match = re.search(r'tel[:\s]+([^,\s]+)', text.lower())
        if tel_match:
            entry["Telephone"] = tel_match.group(1)
    
    def extract_company_name(self, entry: Dict, text: str) -> None:
        """Extract company name from text."""
        # Look for company indicators
        company_indicators = ["Co", "Inc", "Ltd", "Corp", "Company"]
        
        words = text.split()
        for i, word in enumerate(words):
            if word in company_indicators:
                # Try to extract company name around this indicator
                start = max(0, i - 2)
                end = min(len(words), i + 2)
                potential_company = ' '.join(words[start:end])
                entry["CompanyName"] = potential_company.strip()
                break
    
    def parse_address_components(self, address: str) -> Dict[str, str]:
        """Parse address into components."""
        import re
        components = {
            "StreetNumber": "",
            "StreetName": "",
            "ApartmentOrUnit": "",
            "ResidenceIndicator": ""
        }
        
        if not address:
            return components
        
        # Extract street number
        number_match = re.match(r'^(\d+)', address)
        if number_match:
            components["StreetNumber"] = number_match.group(1)
            address = address[len(number_match.group(1)):].strip()
        
        # Extract apartment/unit
        apt_match = re.search(r'(apt|flat|room|rm)\s*(\d+)', address, re.IGNORECASE)
        if apt_match:
            components["ApartmentOrUnit"] = f"{apt_match.group(1)} {apt_match.group(2)}"
            address = re.sub(r'(apt|flat|room|rm)\s*\d+', '', address, flags=re.IGNORECASE).strip()
        
        # Remaining is street name
        components["StreetName"] = address.strip()
        
        return components
