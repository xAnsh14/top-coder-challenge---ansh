#!/usr/bin/env python3
"""
Capture baseline readings before Layer 2 implementation
Records training/holdout accuracy and top error cases for Layer 2 guidance
"""

import json
from calculate_reimbursement import calculate_reimbursement

def analyze_error_cases(cases, dataset_name):
    """Analyze error patterns and return top error cases"""
    
    print(f"\n=== {dataset_name.upper()} ANALYSIS ===")
    
    exact_matches = 0
    close_matches = 0
    total_error = 0
    error_cases = []
    
    for i, case in enumerate(cases):
        days = case['input']['trip_duration_days']
        miles = case['input']['miles_traveled'] 
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        try:
            result = calculate_reimbursement(days, miles, receipts)
            got = float(result)
            error = abs(expected - got)
            
            error_cases.append({
                'index': i,
                'days': days,
                'miles': miles,
                'receipts': receipts,
                'expected': expected,
                'got': got,
                'error': error
            })
            
            total_error += error
            
            if error <= 0.01:
                exact_matches += 1
            elif error <= 1.00:
                close_matches += 1
                
        except Exception as e:
            print(f"Error in case {i}: {e}")
    
    # Sort by error descending
    error_cases.sort(key=lambda x: x['error'], reverse=True)
    
    # Results
    total_cases = len(cases)
    avg_error = total_error / total_cases if total_cases > 0 else 0
    exact_pct = exact_matches / total_cases * 100 if total_cases > 0 else 0
    close_pct = close_matches / total_cases * 100 if total_cases > 0 else 0
    
    print(f"Total cases: {total_cases}")
    print(f"Exact matches (±$0.01): {exact_matches} ({exact_pct:.1f}%)")
    print(f"Close matches (±$1.00): {close_matches} ({close_pct:.1f}%)")
    print(f"Average error: ${avg_error:.2f}")
    
    # Top 5 worst cases
    print(f"\nTop 5 worst error cases:")
    for i, case in enumerate(error_cases[:5]):
        print(f"  {i+1}. {case['days']}d, {case['miles']}mi, ${case['receipts']:.2f} receipts")
        print(f"      Expected: ${case['expected']:.2f}, Got: ${case['got']:.2f}, Error: ${case['error']:.2f}")
    
    return {
        'total_cases': total_cases,
        'exact_matches': exact_matches,
        'exact_pct': exact_pct,
        'close_matches': close_matches,
        'close_pct': close_pct,
        'avg_error': avg_error,
        'top_errors': error_cases[:10]  # Keep top 10 for analysis
    }

def main():
    """Capture baseline readings"""
    print("="*60)
    print("BASELINE READINGS CAPTURE")
    print("Phase 2 Hour 3 → Hour 4 Transition")
    print("="*60)
    
    # Load datasets
    with open('public_cases.json', 'r') as f:
        all_cases = json.load(f)
    
    with open('dev_holdout.json', 'r') as f:
        holdout_cases = json.load(f)
    
    # Create training set (all cases minus holdout)
    holdout_indices = set()
    for holdout_case in holdout_cases:
        for i, case in enumerate(all_cases):
            if (case['input']['trip_duration_days'] == holdout_case['input']['trip_duration_days'] and
                case['input']['miles_traveled'] == holdout_case['input']['miles_traveled'] and
                abs(case['input']['total_receipts_amount'] - holdout_case['input']['total_receipts_amount']) < 0.01 and
                abs(case['expected_output'] - holdout_case['expected_output']) < 0.01):
                holdout_indices.add(i)
                break
    
    training_cases = [case for i, case in enumerate(all_cases) if i not in holdout_indices]
    
    print(f"Training set: {len(training_cases)} cases")
    print(f"Holdout set: {len(holdout_cases)} cases")
    
    # Analyze both datasets
    training_results = analyze_error_cases(training_cases, "training")
    holdout_results = analyze_error_cases(holdout_cases, "holdout")
    
    print(f"\n" + "="*60)
    print("BASELINE SUMMARY")
    print("="*60)
    print(f"Training → {training_results['exact_pct']:.1f}% exact, ${training_results['avg_error']:.2f} avg error")
    print(f"Holdout  → {holdout_results['exact_pct']:.1f}% exact, ${holdout_results['avg_error']:.2f} avg error")
    
    print(f"\nError Pattern Analysis:")
    print(f"- Large errors indicate missing receipt processing")
    print(f"- High-mileage cases likely need efficiency bonuses")
    print(f"- Uniform negative bias expected (we're not processing receipts)")
    
    # Identify patterns in top error cases
    print(f"\nTop Error Case Patterns:")
    all_top_errors = training_results['top_errors'][:5] + holdout_results['top_errors'][:5]
    
    high_receipt_cases = [c for c in all_top_errors if c['receipts'] > 500]
    high_mileage_cases = [c for c in all_top_errors if c['miles'] > 500]
    long_trip_cases = [c for c in all_top_errors if c['days'] > 7]
    
    print(f"- High receipt cases (>$500): {len(high_receipt_cases)}")
    print(f"- High mileage cases (>500mi): {len(high_mileage_cases)}")
    print(f"- Long trip cases (>7 days): {len(long_trip_cases)}")
    
    print(f"\n🎯 Layer 2 Priority:")
    print(f"1. Receipt processing (biggest error component)")
    print(f"2. Efficiency bonuses for high-mileage cases")
    print(f"3. Trip-length-specific receipt caps")

if __name__ == "__main__":
    main() 