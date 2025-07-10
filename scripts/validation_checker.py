"""
Validation Checker

Compares output against ground truth and generates accuracy metrics.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import VALIDATION_THRESHOLDS

logger = logging.getLogger(__name__)


def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def load_json_file(file_path: str) -> List[Dict]:
    """Load JSON file and return entries."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        else:
            logger.warning(f"Expected list in {file_path}, got {type(data)}")
            return []
            
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []


def compare_entries(ground_truth: List[Dict], output: List[Dict]) -> Dict:
    """Compare output entries against ground truth."""
    metrics = {
        'total_ground_truth': len(ground_truth),
        'total_output': len(output),
        'field_accuracy': {},
        'exact_matches': 0,
        'partial_matches': 0,
        'missing_entries': 0,
        'extra_entries': 0
    }
    
    # Required fields for validation
    required_fields = VALIDATION_THRESHOLDS.get('required_fields', 
                                               ['FirstName', 'LastName', 'DirectoryName', 'PageNumber'])
    
    # Track field accuracy
    for field in required_fields:
        metrics['field_accuracy'][field] = {
            'correct': 0,
            'total': len(ground_truth),
            'accuracy': 0.0
        }
    
    # Compare each ground truth entry with output
    for gt_entry in ground_truth:
        best_match = find_best_match(gt_entry, output)
        
        if best_match:
            # Check field accuracy
            exact_match = True
            for field in required_fields:
                gt_value = gt_entry.get(field, "")
                output_value = best_match.get(field, "")
                
                if normalize_value(gt_value) == normalize_value(output_value):
                    metrics['field_accuracy'][field]['correct'] += 1
                else:
                    exact_match = False
            
            if exact_match:
                metrics['exact_matches'] += 1
            else:
                metrics['partial_matches'] += 1
        else:
            metrics['missing_entries'] += 1
    
    # Calculate accuracy percentages
    for field in required_fields:
        field_data = metrics['field_accuracy'][field]
        if field_data['total'] > 0:
            field_data['accuracy'] = field_data['correct'] / field_data['total']
    
    # Calculate extra entries
    metrics['extra_entries'] = max(0, len(output) - len(ground_truth))
    
    return metrics


def find_best_match(gt_entry: Dict, output_entries: List[Dict]) -> Dict:
    """Find the best matching output entry for a ground truth entry."""
    best_match = None
    best_score = 0
    
    for output_entry in output_entries:
        score = calculate_similarity_score(gt_entry, output_entry)
        if score > best_score:
            best_score = score
            best_match = output_entry
    
    # Only return match if score is above threshold
    return best_match if best_score > 0.5 else None


def calculate_similarity_score(entry1: Dict, entry2: Dict) -> float:
    """Calculate similarity score between two entries."""
    score = 0
    total_fields = 0
    
    # Compare key fields
    key_fields = ['FirstName', 'LastName', 'Occupation']
    
    for field in key_fields:
        total_fields += 1
        val1 = normalize_value(entry1.get(field, ""))
        val2 = normalize_value(entry2.get(field, ""))
        
        if val1 and val2:
            if val1 == val2:
                score += 1
            elif val1 in val2 or val2 in val1:
                score += 0.5
    
    return score / total_fields if total_fields > 0 else 0


def normalize_value(value) -> str:
    """Normalize value for comparison."""
    if value is None:
        return ""
    return str(value).lower().strip()


def generate_report(metrics: Dict, output_file: str = None) -> str:
    """Generate validation report."""
    report_lines = []
    
    report_lines.append("=== OCR Pipeline Validation Report ===")
    report_lines.append("")
    
    # Summary statistics
    report_lines.append("Summary:")
    report_lines.append(f"  Ground Truth Entries: {metrics['total_ground_truth']}")
    report_lines.append(f"  Output Entries: {metrics['total_output']}")
    report_lines.append(f"  Exact Matches: {metrics['exact_matches']}")
    report_lines.append(f"  Partial Matches: {metrics['partial_matches']}")
    report_lines.append(f"  Missing Entries: {metrics['missing_entries']}")
    report_lines.append(f"  Extra Entries: {metrics['extra_entries']}")
    report_lines.append("")
    
    # Overall accuracy
    if metrics['total_ground_truth'] > 0:
        overall_accuracy = (metrics['exact_matches'] + metrics['partial_matches']) / metrics['total_ground_truth']
        report_lines.append(f"Overall Accuracy: {overall_accuracy:.2%}")
    report_lines.append("")
    
    # Field-by-field accuracy
    report_lines.append("Field Accuracy:")
    for field, data in metrics['field_accuracy'].items():
        report_lines.append(f"  {field}: {data['correct']}/{data['total']} ({data['accuracy']:.2%})")
    report_lines.append("")
    
    # Validation against thresholds
    min_accuracy = VALIDATION_THRESHOLDS.get('min_accuracy', 0.95)
    report_lines.append("Threshold Validation:")
    
    for field, data in metrics['field_accuracy'].items():
        status = "PASS" if data['accuracy'] >= min_accuracy else "FAIL"
        report_lines.append(f"  {field}: {status} (required: {min_accuracy:.1%})")
    
    report = "\n".join(report_lines)
    
    # Save to file if specified
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Validation Checker')
    parser.add_argument('--ground-truth', required=True, 
                       help='Path to ground truth JSON file')
    parser.add_argument('--output', required=True, 
                       help='Path to output JSON file')
    parser.add_argument('--report', 
                       help='Path to save validation report')
    parser.add_argument('--verbose', action='store_true', 
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    # Load files
    logger.info(f"Loading ground truth: {args.ground_truth}")
    ground_truth = load_json_file(args.ground_truth)
    
    logger.info(f"Loading output: {args.output}")
    output = load_json_file(args.output)
    
    if not ground_truth:
        logger.error("No ground truth data loaded")
        return
    
    if not output:
        logger.error("No output data loaded")
        return
    
    # Compare and generate metrics
    logger.info("Comparing entries...")
    metrics = compare_entries(ground_truth, output)
    
    # Generate report
    report = generate_report(metrics, args.report)
    print(report)


if __name__ == "__main__":
    main()
