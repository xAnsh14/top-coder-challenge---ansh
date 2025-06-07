#!/usr/bin/env python3
"""
Evaluate against holdout set to confirm baseline accuracy
"""
import json
from decimal import Decimal
from calculate_reimbursement import calculate_reimbursement

def evaluate_holdout():
    """Evaluate our implementation against the 200-case holdout set"""
    
    # Load holdout data
    with open('dev_holdout.json', 'r') as f:
        holdout_cases = json.load(f)
    
    print(f"Evaluating against {len(holdout_cases)} holdout cases...")
    
    exact_matches = 0
    close_matches = 0
    total_error = 0
    max_error = 0
    max_error_case = None
    errors = []
    
    for i, case in enumerate(holdout_cases):
        days = case['input']['trip_duration_days']
        miles = case['input']['miles_traveled'] 
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Run our implementation
        try:
            result = calculate_reimbursement(days, miles, receipts)
            got = float(result)
            error = abs(expected - got)
            errors.append(error)
            total_error += error
            
            if error <= 0.01:
                exact_matches += 1
            elif error <= 1.00:
                close_matches += 1
                
            if error > max_error:
                max_error = error
                max_error_case = (i, days, miles, receipts, expected, got)
                
        except Exception as e:
            print(f"Exception in case {i}: {e}")
    
    # Results
    total_cases = len(holdout_cases)
    avg_error = total_error / total_cases if total_cases > 0 else 0
    
    print(f"\nHOLDOUT SET RESULTS:")
    print(f"Total cases: {total_cases}")
    print(f"Exact matches (±$0.01): {exact_matches} ({exact_matches/total_cases*100:.1f}%)")
    print(f"Close matches (±$1.00): {close_matches} ({close_matches/total_cases*100:.1f}%)")
    print(f"Average error: ${avg_error:.2f}")
    print(f"Maximum error: ${max_error:.2f}")
    
    if max_error_case:
        i, days, miles, receipts, expected, got = max_error_case
        print(f"Max error case: {days}d, {miles}mi, ${receipts} → expected ${expected}, got ${got}")

if __name__ == "__main__":
    evaluate_holdout() 