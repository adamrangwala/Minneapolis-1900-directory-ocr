# Minneapolis 1900 City Directory OCR Pipeline

A comprehensive OCR pipeline system for extracting structured resident data from the 1900 Minneapolis city directory. This system processes pages from a web archive, extracts resident entries, and outputs structured JSON data with high accuracy.

## Project Overview

This pipeline processes scanned city directory pages through multiple stages:
1. **Web Scraping**: Downloads images from the web archive
2. **Preprocessing**: Extracts columns and enhances images for OCR
3. **OCR Processing**: Converts images to text using Tesseract
4. **JSON Parsing**: Structures text into standardized JSON format
5. **Validation**: Compares output against ground truth data

## Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Final_Round
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR**
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

4. **Set up directories**
```bash
python config/settings.py
```

### Basic Usage

**Process target pages (104-108):**
```bash
python scripts/batch_runner.py --target-pages
```

**Process a single page:**
```bash
python scripts/main_processor.py --page 104
```

**Validate output against ground truth:**
```bash
python scripts/validation_checker.py --ground-truth ground_truth/ground_truth_1900_0362.json --output data/output_json/page_362.json
```

## Architecture

### Directory Structure
```
Final_Round/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config/                   # Configuration files
│   ├── settings.py          # Main configuration
│   └── ocr_config.json      # OCR-specific settings
├── src/                     # Source code modules
│   ├── preprocessing/       # Image processing and column extraction
│   ├── ocr/                # OCR text extraction
│   ├── parsing/            # JSON parsing and structuring
│   ├── web_scraper/        # Web scraping functionality
│   └── utils/              # Batch processing and checkpoints
├── data/                   # Data directories
│   ├── raw_images/         # Downloaded images
│   ├── processed_images/   # Column-extracted images
│   ├── ocr_text/          # OCR text output
│   └── output_json/       # Final JSON output
├── ground_truth/          # Ground truth data for validation
├── test_images/           # Test images
├── scripts/               # Main processing scripts
├── logs/                  # Log files
└── checkpoints/           # Processing checkpoints
```

### Core Modules

#### Preprocessing (`src/preprocessing/`)
- **`column_extractor.py`**: Detects and extracts text columns from directory pages
- **`image_processor.py`**: Enhances images for better OCR accuracy

#### OCR (`src/ocr/`)
- **`text_extractor.py`**: Main OCR interface
- **`ocr_engine.py`**: Tesseract OCR wrapper
- **`text_cleaner.py`**: Post-processing for OCR text
- **`batch_processor.py`**: Batch OCR processing

#### Parsing (`src/parsing/`)
- **`json_parser.py`**: Main JSON parser
- **`text_analyzer.py`**: Text pattern analysis
- **`entry_extractor.py`**: Information extraction from entries

#### Web Scraper (`src/web_scraper/`)
- **`directory_scraper.py`**: Main scraping interface
- **`image_downloader.py`**: Image download with retry logic

#### Utils (`src/utils/`)
- **`batch_processor.py`**: Batch processing with checkpoints
- **`checkpoint_manager.py`**: Checkpoint management for resumable operations

## Usage Examples

### Processing Individual Pages

```bash
# Process a single page with full pipeline
python scripts/main_processor.py --page 104 --verbose

# Process without downloading (use existing image)
python scripts/main_processor.py --page 104 --no-download

# Process a range of pages
python scripts/main_processor.py --start 104 --end 108
```

### Batch Processing

```bash
# Process all target pages (104-108)
python scripts/batch_runner.py --target-pages

# Process specific pages
python scripts/batch_runner.py --pages 104 105 106

# Download target pages only
python scripts/batch_runner.py --download-only

# Check batch job progress
python scripts/batch_runner.py --progress target_pages_processing
```

### Validation

```bash
# Validate against ground truth
python scripts/validation_checker.py \
  --ground-truth ground_truth/ground_truth_1900_0362.json \
  --output data/output_json/page_362.json \
  --report validation_report.txt
```

## Configuration

### Main Settings (`config/settings.py`)
- Directory paths and structure
- Target pages for processing
- OCR and preprocessing parameters
- Batch processing settings
- Validation thresholds

### OCR Configuration (`config/ocr_config.json`)
- Tesseract parameters
- Image preprocessing options
- Text cleaning settings
- Quality control thresholds

## Output Format

Each resident entry follows this JSON structure:

```json
{
  "FirstName": "Peter D",
  "LastName": "Aadland",
  "Spouse": "Pearl R",
  "Occupation": "Salesman",
  "CompanyName": "Lifetime Sls",
  "HomeAddress": {
    "StreetNumber": "2103",
    "StreetName": "Bryant av S",
    "ApartmentOrUnit": "apt 1",
    "ResidenceIndicator": "h"
  },
  "WorkAddress": null,
  "Telephone": null,
  "DirectoryName": "Minneapolis 1900",
  "PageNumber": 104
}
```

## Performance Targets

- **Accuracy**: >95% for structured data extraction
- **Speed**: Process 10+ pages per minute
- **Memory**: Efficient batch processing
- **Reliability**: Handle interruptions gracefully with checkpoints

## Ground Truth Data

The system includes ground truth data for validation:
- **`ground_truth/1900_0362.txt`**: OCR text ground truth
- **`ground_truth/structured_JSON_ground_truth/ground_truth_1900_0362.json`**: JSON structure ground truth
- **`test_images/1900_0362.jpg`**: Test image

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and in PATH
   - Or set custom path in `config/ocr_config.json`

2. **Memory issues with large batches**
   - Reduce `batch_size` in `config/settings.py`
   - Reduce `max_workers` for parallel processing

3. **Poor OCR accuracy**
   - Adjust preprocessing parameters in `config/ocr_config.json`
   - Check image quality and resolution

4. **Web scraping failures**
   - Check internet connection
   - Verify web archive URL is accessible
   - Increase retry attempts in configuration

### Logging

Logs are saved to the `logs/` directory:
- `logs/pipeline.log`: General pipeline logs
- `logs/main_processor.log`: Main processor logs
- `logs/batch_runner.log`: Batch processing logs

Set log level with `--verbose` flag for detailed debugging.

### Checkpoints

The system automatically saves checkpoints during batch processing:
- Checkpoints stored in `checkpoints/` directory
- Resume interrupted jobs automatically
- Clean up completed jobs with batch processor

## Development

### Adding New Features

1. **New OCR Engine**: Implement in `src/ocr/ocr_engine.py`
2. **New Parser**: Add to `src/parsing/` with focused functionality
3. **New Preprocessor**: Add to `src/preprocessing/`

### Testing

Run validation against ground truth:
```bash
python scripts/validation_checker.py \
  --ground-truth ground_truth/ground_truth_1900_0362.json \
  --output your_output.json
```

### Code Style

- Follow PEP 8 guidelines
- Keep files under 200 lines
- Use focused, single-responsibility functions
- Include comprehensive docstrings
- Add type hints where appropriate

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Validate configuration settings
4. Test with ground truth data
