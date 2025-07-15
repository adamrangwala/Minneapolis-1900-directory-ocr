#!/usr/bin/env python3
"""
Test script to validate improved parser against ground truth
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from parsing.json_parser import CityDirectoryParser

def load_ground_truth():
    """Load ground truth data"""
    with open('ground_truth/1900_0113.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def test_parser_on_sample():
    """Test parser on sample OCR text"""
    parser = CityDirectoryParser(year="1900")
    
    # Parse left column
    left_entries = parser.parse_text_file('data/ocr_text/1900_0113_left_col.txt')
    
    # Parse right column  
    right_entries = parser.parse_text_file('data/ocr_text/1900_0113_right_col.txt')
    
    # Combine entries
    all_entries = left_entries + right_entries
    
    return all_entries

def calculate_accuracy(parsed_entries, ground_truth):
    """Calculate accuracy metrics"""
    
    # Create lookup for ground truth by name
    gt_lookup = {}
    for entry in ground_truth:
        key = f"{entry['FirstName']} {entry['LastName']}".strip()
        gt_lookup[key] = entry
    
    metrics = {
        'total_parsed': len(parsed_entries),
        'total_ground_truth': len(ground_truth),
        'first_name_correct': 0,
        'last_name_correct': 0,
        'company_name_correct': 0,
        'spouse_correct': 0,
        'occupation_correct': 0,
        'address_correct': 0,
        'residence_indicator_correct': 0
    }
    
    matched_entries = 0
    
    for parsed in parsed_entries:
        parsed_key = f"{parsed.get('FirstName', '')} {parsed.get('LastName', '')}".strip()
        
        # Find matching ground truth entry
        gt_entry = None
        for gt_key, gt_val in gt_lookup.items():
            if parsed_key in gt_key or gt_key in parsed_key:
                gt_entry = gt_val
                matched_entries += 1
                break
        
        if gt_entry:
            # Check each field
            if parsed.get('FirstName') == gt_entry.get('FirstName'):
                metrics['first_name_correct'] += 1
            
            if parsed.get('LastName') == gt_entry.get('LastName'):
                metrics['last_name_correct'] += 1
                
            if parsed.get('CompanyName') == gt_entry.get('CompanyName'):
                metrics['company_name_correct'] += 1
                
            if parsed.get('Spouse') == gt_entry.get('Spouse'):
                metrics['spouse_correct'] += 1
                
            if parsed.get('Occupation') == gt_entry.get('Occupation'):
                metrics['occupation_correct'] += 1
                
            # Address comparison
            parsed_addr = parsed.get('HomeAddress', {})
            gt_addr = gt_entry.get('HomeAddress', {})
            
            if (parsed_addr.get('StreetNumber') == gt_addr.get('StreetNumber') and
                parsed_addr.get('StreetName') == gt_addr.get('StreetName')):
                metrics['address_correct'] += 1
                
            if parsed_addr.get('ResidenceIndicator') == gt_addr.get('ResidenceIndicator'):
                metrics['residence_indicator_correct'] += 1
    
    metrics['matched_entries'] = matched_entries
    
    # Calculate percentages
    if matched_entries > 0:
        for key in ['first_name_correct', 'last_name_correct', 'company_name_correct', 
                   'spouse_correct', 'occupation_correct', 'address_correct', 'residence_indicator_correct']:
            metrics[f'{key}_pct'] = (metrics[key] / matched_entries) * 100
    
    return metrics

def print_sample_comparisons(parsed_entries, ground_truth, num_samples=5):
    """Print sample comparisons for debugging"""
    print("\n=== SAMPLE COMPARISONS ===")
    
    for i, parsed in enumerate(parsed_entries[:num_samples]):
        print(f"\n--- Sample {i+1} ---")
        print(f"PARSED: {parsed.get('FirstName', '')} {parsed.get('LastName', '')}")
        print(f"  Company: {parsed.get('CompanyName', 'None')}")
        print(f"  Spouse: {parsed.get('Spouse', 'None')}")
        print(f"  Occupation: {parsed.get('Occupation', 'None')}")
        print(f"  Address: {parsed.get('HomeAddress', {}).get('StreetNumber', '')} {parsed.get('HomeAddress', {}).get('StreetName', '')}")
        print(f"  Residence: {parsed.get('HomeAddress', {}).get('ResidenceIndicator', 'None')}")
        
        # Find corresponding ground truth
        parsed_key = f"{parsed.get('FirstName', '')} {parsed.get('LastName', '')}".strip()
        gt_match = None
        for gt in ground_truth:
            gt_key = f"{gt['FirstName']} {gt['LastName']}".strip()
            if parsed_key in gt_key or gt_key in parsed_key:
                gt_match = gt
                break
        
        if gt_match:
            print(f"GROUND TRUTH: {gt_match.get('FirstName', '')} {gt_match.get('LastName', '')}")
            print(f"  Company: {gt_match.get('CompanyName', 'None')}")
            print(f"  Spouse: {gt_match.get('Spouse', 'None')}")
            print(f"  Occupation: {gt_match.get('Occupation', 'None')}")
            print(f"  Address: {gt_match.get('HomeAddress', {}).get('StreetNumber', '')} {gt_match.get('HomeAddress', {}).get('StreetName', '')}")
            print(f"  Residence: {gt_match.get('HomeAddress', {}).get('ResidenceIndicator', 'None')}")
        else:
            print("GROUND TRUTH: No match found")

def main():
    """Main test function"""
    print("Testing improved parser...")
    
    # Load ground truth
    ground_truth = load_ground_truth()
    print(f"Loaded {len(ground_truth)} ground truth entries")
    
    # Test parser
    parsed_entries = test_parser_on_sample()
    print(f"Parsed {len(parsed_entries)} entries")
    
    # Calculate accuracy
    metrics = calculate_accuracy(parsed_entries, ground_truth)
    
    print("\n=== ACCURACY METRICS ===")
    print(f"Total parsed entries: {metrics['total_parsed']}")
    print(f"Total ground truth entries: {metrics['total_ground_truth']}")
    print(f"Matched entries: {metrics['matched_entries']}")
    
    if metrics['matched_entries'] > 0:
        print(f"\nField Accuracy:")
        print(f"  First Name: {metrics.get('first_name_correct_pct', 0):.1f}%")
        print(f"  Last Name: {metrics.get('last_name_correct_pct', 0):.1f}%")
        print(f"  Company Name: {metrics.get('company_name_correct_pct', 0):.1f}%")
        print(f"  Spouse: {metrics.get('spouse_correct_pct', 0):.1f}%")
        print(f"  Occupation: {metrics.get('occupation_correct_pct', 0):.1f}%")
        print(f"  Address: {metrics.get('address_correct_pct', 0):.1f}%")
        print(f"  Residence Indicator: {metrics.get('residence_indicator_correct_pct', 0):.1f}%")
        
        # Overall accuracy
        total_fields = 7
        total_correct = (metrics.get('first_name_correct_pct', 0) + 
                        metrics.get('last_name_correct_pct', 0) +
                        metrics.get('company_name_correct_pct', 0) +
                        metrics.get('spouse_correct_pct', 0) +
                        metrics.get('occupation_correct_pct', 0) +
                        metrics.get('address_correct_pct', 0) +
                        metrics.get('residence_indicator_correct_pct', 0))
        
        overall_accuracy = total_correct / total_fields
        print(f"\nOverall Accuracy: {overall_accuracy:.1f}%")
        
        if overall_accuracy >= 80:
            print("TARGET ACHIEVED: Accuracy is 80% or higher!")
        else:
            print("Target not met: Need to improve accuracy to 80%+")
    
    # Print sample comparisons
    print_sample_comparisons(parsed_entries, ground_truth)
    
    # Save parsed output for inspection
    with open('data/output_json/test_improved_output.json', 'w', encoding='utf-8') as f:
        json.dump(parsed_entries, f, indent=2, ensure_ascii=False)
    
    print(f"\nParsed output saved to: data/output_json/test_improved_output.json")

if __name__ == "__main__":
    main()