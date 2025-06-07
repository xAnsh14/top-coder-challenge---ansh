#!/usr/bin/env python3
"""
Quick Diagnostics: 5-day bonus and dynamic per-diem
"""

import json
import pandas as pd
import numpy as np

def load_data():
    with open('public_cases.json', 'r') as f:
        data = json.load(f)
    
    rows = []
    for case in data:
        row = {
            'trip_duration_days': case['input']['trip_duration_days'],
            'miles_traveled': case['input']['miles_traveled'],
            'total_receipts_amount': case['input']['total_receipts_amount'],
            'expected_output': case['expected_output']
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df['miles_per_day'] = df['miles_traveled'] / df['trip_duration_days']
    df['receipts_per_day'] = df['total_receipts_amount'] / df['trip_duration_days']
    df['reimbursement_per_day'] = df['expected_output'] / df['trip_duration_days']
    
    return df

def quick_five_day_test(df):
    print("="*50)
    print("5-DAY BONUS INVESTIGATION")
    print("="*50)
    
    five_day = df[df['trip_duration_days'] == 5]
    four_day = df[df['trip_duration_days'] == 4]
    six_day = df[df['trip_duration_days'] == 6]
    
    print(f"5-day trips: {len(five_day)} cases, avg ${five_day['reimbursement_per_day'].mean():.2f}/day")
    print(f"4-day trips: {len(four_day)} cases, avg ${four_day['reimbursement_per_day'].mean():.2f}/day")
    print(f"6-day trips: {len(six_day)} cases, avg ${six_day['reimbursement_per_day'].mean():.2f}/day")
    
    # Test Kevin's sweet spot criteria
    five_day_sweet = five_day[
        (five_day['miles_per_day'] >= 180) & 
        (five_day['miles_per_day'] <= 220) &
        (five_day['receipts_per_day'] <= 100)
    ]
    
    print(f"\n5-day trips meeting Kevin's criteria: {len(five_day_sweet)} cases")
    if len(five_day_sweet) > 0:
        print(f"  Avg reimbursement/day: ${five_day_sweet['reimbursement_per_day'].mean():.2f}")
    
    # Test for flat bonus using residuals
    def estimate_residual(row):
        # Rough mileage estimate
        if row['miles_traveled'] <= 100:
            mileage = row['miles_traveled'] * 0.58
        else:
            mileage = 100 * 0.58 + (row['miles_traveled'] - 100) * 0.15
        
        base_per_diem = 80 * row['trip_duration_days']  # Provisional
        residual = row['expected_output'] - base_per_diem - mileage
        return residual
    
    five_day['residual'] = five_day.apply(estimate_residual, axis=1)
    four_day['residual'] = four_day.apply(estimate_residual, axis=1)
    six_day['residual'] = six_day.apply(estimate_residual, axis=1)
    
    print(f"\nResidual analysis:")
    print(f"5-day avg residual: ${five_day['residual'].mean():.2f}")
    print(f"4-day avg residual: ${four_day['residual'].mean():.2f}")
    print(f"6-day avg residual: ${six_day['residual'].mean():.2f}")

def quick_per_diem_test(df):
    print("\n" + "="*50)
    print("DYNAMIC PER-DIEM INVESTIGATION")
    print("="*50)
    
    # Remove mileage component to isolate per-diem
    df['residual'] = df['expected_output'] - 0.15 * df['miles_traveled']
    df['resid_per_day'] = df['residual'] / df['trip_duration_days']
    
    print("After removing $0.15/mile mileage component:")
    print(f"Min residual/day: ${df['resid_per_day'].min():.2f}")
    print(f"Max residual/day: ${df['resid_per_day'].max():.2f}")
    
    print(f"\nResidual per day by trip duration:")
    for duration in sorted(df['trip_duration_days'].unique()):
        subset = df[df['trip_duration_days'] == duration]
        low_spending = subset[subset['receipts_per_day'] < 50]
        
        print(f"{duration}-day: ${subset['resid_per_day'].median():.2f} median", end="")
        if len(low_spending) >= 3:
            print(f", ${low_spending['resid_per_day'].median():.2f} low-spending median ({len(low_spending)} cases)")
        else:
            print(f" ({len(subset)} cases)")

def main():
    print("QUICK DIAGNOSTICS: 5-DAY BONUS & DYNAMIC PER-DIEM")
    
    df = load_data()
    quick_five_day_test(df)
    quick_per_diem_test(df)
    
    print("\n" + "="*50)
    print("KEY INSIGHTS")
    print("="*50)
    print("1. Check if 5-day trips have higher or lower reimbursement/day")
    print("2. Check if residuals show systematic patterns by trip length") 
    print("3. These insights will guide Layer 0 implementation")

if __name__ == "__main__":
    main() 