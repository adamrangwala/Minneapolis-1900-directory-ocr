"""
Configuration settings for Minneapolis 1900 City Directory OCR Pipeline
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
LOGS_DIR = BASE_DIR / "logs"
CHECKPOINTS_DIR = BASE_DIR / "checkpoints"

# Data subdirectories
RAW_IMAGES_DIR = DATA_DIR / "raw_images"
PROCESSED_IMAGES_DIR = DATA_DIR / "processed_images"
OCR_TEXT_DIR = DATA_DIR / "ocr_text"
OUTPUT_JSON_DIR = DATA_DIR / "output_json"

# Ground truth directories
GROUND_TRUTH_DIR = BASE_DIR / "ground_truth"
GROUND_TRUTH_JSON_DIR = GROUND_TRUTH_DIR / "structured_JSON_ground_truth"

# Test directories
TEST_IMAGES_DIR = BASE_DIR / "test_images"

# Web scraping configuration
WEB_ARCHIVE_BASE_URL = "https://box2.nmtvault.com/Hennepin2/jsp/RcWebImageViewer.jsp"
DOCUMENT_ID = "7083e412-1de2-42fe-b070-7f82e5c869a4/mnmhcl00/20130429"

# Target pages for initial submission (direct page number to sequence mapping)
TARGET_PAGES = {
    112: 112,  # Page 112 -> pg_seq 112
    113: 113,  # Page 113 -> pg_seq 113
    114: 114,  # Page 114 -> pg_seq 114
    115: 115,  # Page 115 -> pg_seq 115
    116: 116   # Page 116 -> pg_seq 116
}

# OCR Configuration
TESSERACT_CONFIG = {
    'psm': 6,  # Uniform block of text
    'oem': 3,  # Default OCR Engine Mode
    'lang': 'eng'
}

# Image preprocessing parameters
IMAGE_PREPROCESSING = {
    'blur_kernel': 3,
    'canny_low': 100,
    'canny_high': 200,
    'hough_threshold': 1200,
    'max_line_gap': 10,
    'line_thickness': 4,
    'median_blur_kernel': 5,
    'bilateral_filter_d': 9,
    'bilateral_filter_sigma_color': 75,
    'bilateral_filter_sigma_space': 75,
    'clahe_clip_limit': 2.0,
    'clahe_tile_grid_size': (8, 8),
    'morph_kernel_size': (2, 2)
}

# Column extraction thresholds
COLUMN_EXTRACTION = {
    'left_page_ad_threshold': 0.2,
    'right_page_ad_threshold': 0.75,
    'left_page_top_threshold': 0.33,
    'bottom_threshold_left': 0.85,
    'bottom_threshold_right': 0.65
}

# Batch processing configuration
BATCH_PROCESSING = {
    'batch_size': 5,
    'max_workers': 4,
    'checkpoint_interval': 10,  # Save checkpoint every 10 pages
    'retry_attempts': 3,
    'retry_delay': 1.0  # seconds
}

# JSON output format
JSON_OUTPUT_FORMAT = {
    "FirstName": "",
    "LastName": "",
    "Spouse": "",
    "Occupation": "",
    "CompanyName": "",
    "HomeAddress": {
        "StreetNumber": "",
        "StreetName": "",
        "ApartmentOrUnit": "",
        "ResidenceIndicator": ""
    },
    "WorkAddress": None,
    "Telephone": None,
    "DirectoryName": "Minneapolis 1900",
    "PageNumber": None
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'pipeline.log'),
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

# Validation thresholds
VALIDATION_THRESHOLDS = {
    'min_accuracy': 0.95,  # 95% accuracy target
    'min_entries_per_page': 10,  # Minimum expected entries per page
    'max_entries_per_page': 100,  # Maximum expected entries per page
    'required_fields': ['FirstName', 'LastName', 'DirectoryName', 'PageNumber']
}

# Common abbreviations for text cleaning and expansion
ABBREVIATIONS = {
    "acct": "accountant",
    "adv": "advertisement",
    "agt": "agent",
    "appr": "apprentice",
    "assn": "association",
    "asst": "assistant",
    "av": "avenue",
    "b": "boards",
    "bartndr": "bartender",
    "bet": "between",
    "bkbndr": "bookbinder",
    "bkpr": "bookkeeper",
    "blksmith": "blacksmith",
    "bldg": "building",
    "blk": "block",
    "boul": "boulevard",
    "cabmkr": "cabinet maker",
    "carp": "carpenter",
    "civ eng": "civil engineer",
    "clk": "clerk",
    "clnr": "cleaner",
    "collr": "collector",
    "commr": "commissioner",
    "comn": "commission",
    "comp": "compositor",
    "cond": "conductor",
    "conf": "confectioner",
    "contr": "contractor",
    "cor": "corner",
    "ct": "court",
    "dep": "deputy",
    "dept": "department",
    "dom": "domestic",
    "e": "east",
    "elev": "elevator",
    "eng": "engineer",
    "engr": "engraver",
    "exp": "express",
    "e s": "east side",
    "frt": "freight",
    "gen": "general",
    "ins": "insurance",
    "insptr": "inspector",
    "lab": "laborer",
    "mach": "machinist",
    "mech": "mechanic",
    "messr": "messenger",
    "mkr": "maker",
    "mnfr": "manufacturer",
    "mngr": "manager",
    "n": "north",
    "nr": "near",
    "n e": "northeast",
    "n s": "north side",
    "nw": "northwest",
    "opp": "opposite",
    "opr": "operator",
    "photogr": "photographer",
    "phys": "physician",
    "pk": "park",
    "pkr": "packer",
    "pl": "place",
    "P O": "Postoffice",
    "pres": "president",
    "prin": "principal",
    "prof": "professor",
    "propr": "proprietor",
    "pub": "publisher",
    "r": "residence",
    "rd": "road",
    "real est": "real estate",
    "repr": "repairer",
    "ret": "retail",
    "R M S": "railway mail service",
    "s": "south",
    "se": "southeast",
    "s s": "south side",
    "s w": "southwest",
    "slsmn": "salesman",
    "smstrs": "seamstress",
    "solr": "solicitor",
    "stenogr": "stenographer",
    "supt": "superintendent",
    "tchr": "teacher",
    "tel": "telephone",
    "tmstr": "teamster",
    "tndr": "tender",
    "trav": "traveling",
    "upholstr": "upholsterer",
    "vet surg": "veterinary surgeon",
    "w": "west",
    "Washn": "Washington",
    "whol": "wholesale",
    "wid": "widow",
    "w s": "west side"
}

# Ensure directories exist
def ensure_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        DATA_DIR, RAW_IMAGES_DIR, PROCESSED_IMAGES_DIR, OCR_TEXT_DIR, OUTPUT_JSON_DIR,
        GROUND_TRUTH_DIR, GROUND_TRUTH_JSON_DIR, TEST_IMAGES_DIR, LOGS_DIR, CHECKPOINTS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print("All directories created successfully!")
