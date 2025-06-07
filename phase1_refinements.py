#!/usr/bin/env python3
"""
Phase 1 Refinements: Critical Diagnostics
Investigate 5-day bonus mystery and dynamic per-diem hypothesis
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal, ROUND_HALF_UP

def load_data_with_guards():
    """Load data with proper guards against edge cases"""
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
    
    # Guard against division by zero and ensure consistent dtypes
    df['expected_output'] = df['expected_output'].astype(float)
    df['miles_per_day'] = df['miles_traveled'] / df['trip_duration_days']
    df['receipts_per_day'] = df['total_receipts_amount'] / df['trip_duration_days']
    df['reimbursement_per_day'] = df['expected_output'] / df['trip_duration_days']
    
    # Guard against zero miles for receipts_per_mile
    df['receipts_per_mile'] = df['total_receipts_amount'] / df['miles_traveled'].replace(0, np.nan)
    
    return df

def create_holdout_split(df):
    """Create 200-case holdout for validation"""
    print("="*60)
    print("CREATING HOLDOUT SPLIT")
    print("="*60)
    
    # Stratified sample to ensure good representation
    holdout_indices = []
    
    # Ensure representation across trip lengths
    for duration in sorted(df['trip_duration_days'].unique()):
        subset = df[df['trip_duration_days'] == duration]
        n_holdout = max(1, int(len(subset) * 0.2))  # 20% or at least 1
        holdout_indices.extend(subset.sample(n=min(n_holdout, len(subset))).index.tolist())
    
    # Ensure we have exactly 200 cases
    if len(holdout_indices) < 200:
        remaining_indices = df.index.difference(holdout_indices).tolist()
        additional_needed = 200 - len(holdout_indices)
        additional_indices = np.random.choice(remaining_indices, min(additional_needed, len(remaining_indices)), replace=False)
        holdout_indices.extend(additional_indices.tolist())
    elif len(holdout_indices) > 200:
        holdout_indices = np.random.choice(holdout_indices, 200, replace=False).tolist()
    
    holdout_df = df.loc[holdout_indices].copy()
    train_df = df.drop(holdout_indices).copy()
    
    print(f"Training set: {len(train_df)} cases")
    print(f"Holdout set: {len(holdout_df)} cases")
    
    # Save holdout to file
    holdout_data = []
    for idx, row in holdout_df.iterrows():
        case = {
            "input": {
                "trip_duration_days": int(row['trip_duration_days']),
                "miles_traveled": float(row['miles_traveled']),
                "total_receipts_amount": float(row['total_receipts_amount'])
            },
            "expected_output": float(row['expected_output'])
        }
        holdout_data.append(case)
    
    with open('dev_holdout.json', 'w') as f:
        json.dump(holdout_data, f, indent=2)
    
    print("Saved holdout set to: dev_holdout.json")
    return train_df, holdout_df

def diagnostic_1_five_day_bonus(df):
    """Investigate the 5-day bonus mystery"""
    print("\n" + "="*60)
    print("DIAGNOSTIC 1: FIVE-DAY BONUS MYSTERY")
    print("="*60)
    
    five_day = df[df['trip_duration_days'] == 5].copy()
    four_day = df[df['trip_duration_days'] == 4].copy()
    six_day = df[df['trip_duration_days'] == 6].copy()
    
    print(f"5-day trips: {len(five_day)} cases")
    print(f"4-day trips: {len(four_day)} cases") 
    print(f"6-day trips: {len(six_day)} cases")
    
    # Test 1: Conditional bonus (efficiency + low spending)
    print("\n--- Test 1: Conditional Bonus (efficiency + spending) ---")
    
    # Filter 5-day trips meeting Kevin's criteria
    five_day_sweet_spot = five_day[
        (five_day['miles_per_day'] >= 180) & 
        (five_day['miles_per_day'] <= 220) &
        (five_day['receipts_per_day'] <= 100)
    ]
    
    five_day_other = five_day[
        ~((five_day['miles_per_day'] >= 180) & 
          (five_day['miles_per_day'] <= 220) &
          (five_day['receipts_per_day'] <= 100))
    ]
    
    print(f"5-day trips meeting Kevin's criteria: {len(five_day_sweet_spot)} cases")
    if len(five_day_sweet_spot) > 0:
        print(f"  Avg reimbursement/day: ${five_day_sweet_spot['reimbursement_per_day'].mean():.2f}")
        print(f"  Avg total reimbursement: ${five_day_sweet_spot['expected_output'].mean():.2f}")
    
    print(f"5-day trips NOT meeting criteria: {len(five_day_other)} cases")
    if len(five_day_other) > 0:
        print(f"  Avg reimbursement/day: ${five_day_other['reimbursement_per_day'].mean():.2f}")
        print(f"  Avg total reimbursement: ${five_day_other['expected_output'].mean():.2f}")
    
    # Test 2: Flat bonus hypothesis
    print("\n--- Test 2: Flat Bonus Hypothesis ---")
    
    # Estimate components to look for flat bonus
    # Using provisional rates
    mileage_low_rate = 0.58  # Standard rate for < 100 miles
    mileage_high_rate = 0.15  # Estimated rate for > 100 miles
    
    def estimate_base_components(row):
        """Rough estimate of base + mileage to isolate potential bonuses"""
        # Provisional mileage calculation
        if row['miles_traveled'] <= 100:
            mileage_component = row['miles_traveled'] * mileage_low_rate
        else:
            mileage_component = 100 * mileage_low_rate + (row['miles_traveled'] - 100) * mileage_high_rate
        
        # Provisional per-diem (we'll refine this in diagnostic 2)
        provisional_per_diem = 80 * row['trip_duration_days']  # Conservative estimate
        
        # Residual that might contain bonuses/penalties
        residual = row['expected_output'] - provisional_per_diem - mileage_component
        return residual
    
    five_day['residual'] = five_day.apply(estimate_base_components, axis=1)
    four_day['residual'] = four_day.apply(estimate_base_components, axis=1)
    six_day['residual'] = six_day.apply(estimate_base_components, axis=1)
    
    print(f"5-day trips avg residual: ${five_day['residual'].mean():.2f}")
    print(f"4-day trips avg residual: ${four_day['residual'].mean():.2f}")
    print(f"6-day trips avg residual: ${six_day['residual'].mean():.2f}")
    
    # Look for consistent positive residual in 5-day trips
    five_day_positive_residual = five_day[five_day['residual'] > 0]
    print(f"5-day trips with positive residual: {len(five_day_positive_residual)} / {len(five_day)}")
    if len(five_day_positive_residual) > 0:
        print(f"  Avg positive residual: ${five_day_positive_residual['residual'].mean():.2f}")
    
    # Visualization
    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.scatter(four_day['miles_traveled'], four_day['reimbursement_per_day'], alpha=0.6, label='4-day', color='blue')
    plt.scatter(five_day['miles_traveled'], five_day['reimbursement_per_day'], alpha=0.8, label='5-day', color='red')
    plt.scatter(six_day['miles_traveled'], six_day['reimbursement_per_day'], alpha=0.6, label='6-day', color='green')
    plt.xlabel('Miles Traveled')
    plt.ylabel('Reimbursement per Day ($)')
    plt.title('5-Day vs Adjacent Lengths')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 2)
    trip_lengths = [4, 5, 6]
    residuals = [four_day['residual'].mean(), five_day['residual'].mean(), six_day['residual'].mean()]
    plt.bar(trip_lengths, residuals, color=['blue', 'red', 'green'], alpha=0.7)
    plt.xlabel('Trip Duration (days)')
    plt.ylabel('Avg Residual ($)')
    plt.title('Residual After Base + Mileage')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 3)
    if len(five_day_sweet_spot) > 0 and len(five_day_other) > 0:
        plt.bar(['5-day\nSweet Spot', '5-day\nOther'], 
                [five_day_sweet_spot['reimbursement_per_day'].mean(), 
                 five_day_other['reimbursement_per_day'].mean()],
                color=['darkred', 'lightcoral'], alpha=0.7)
        plt.ylabel('Reimbursement per Day ($)')
        plt.title('5-Day Conditional Analysis')
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('five_day_diagnostic.png', dpi=300, bbox_inches='tight')
    plt.show()

def diagnostic_2_dynamic_per_diem(df):
    """Investigate dynamic per-diem hypothesis"""
    print("\n" + "="*60)
    print("DIAGNOSTIC 2: DYNAMIC PER-DIEM HYPOTHESIS")
    print("="*60)
    
    # Remove provisional mileage component to isolate per-diem + receipt patterns
    mileage_provisional = 0.15  # Conservative high-tier rate
    
    df['residual_after_mileage'] = df['expected_output'] - mileage_provisional * df['miles_traveled']
    df['resid_per_day'] = df['residual_after_mileage'] / df['trip_duration_days']
    
    print("After removing provisional mileage ($0.15/mile):")
    print(f"Min residual per day: ${df['resid_per_day'].min():.2f}")
    print(f"Max residual per day: ${df['resid_per_day'].max():.2f}")
    print(f"Mean residual per day: ${df['resid_per_day'].mean():.2f}")
    
    # Look for patterns by trip duration
    print("\nResidual per day by trip duration:")
    for duration in sorted(df['trip_duration_days'].unique()):
        subset = df[df['trip_duration_days'] == duration]
        print(f"{duration}-day trips: ${subset['resid_per_day'].mean():.2f} avg, ${subset['resid_per_day'].median():.2f} median ({len(subset)} cases)")
    
    # Create visualization
    plt.figure(figsize=(15, 10))
    
    # Box plot of residual per day by trip duration
    plt.subplot(2, 2, 1)
    df.boxplot(column='resid_per_day', by='trip_duration_days', ax=plt.gca())
    plt.axhline(100, ls='--', c='red', label='$100 baseline')
    plt.axhline(80, ls='--', c='orange', label='$80 baseline')
    plt.axhline(60, ls='--', c='yellow', label='$60 baseline')
    plt.title('Residual per Day (after mileage) by Trip Duration')
    plt.suptitle('')
    plt.ylabel('Residual per Day ($)')
    plt.legend()
    
    # Scatter plot: trip duration vs residual per day
    plt.subplot(2, 2, 2)
    plt.scatter(df['trip_duration_days'], df['resid_per_day'], alpha=0.6)
    plt.axhline(100, ls='--', c='red', alpha=0.7)
    plt.xlabel('Trip Duration (days)')
    plt.ylabel('Residual per Day ($)')
    plt.title('Residual per Day vs Trip Duration')
    plt.grid(True, alpha=0.3)
    
    # Look at low-spending cases to isolate per-diem
    plt.subplot(2, 2, 3)
    low_spending = df[df['receipts_per_day'] < 50]  # Low receipt cases
    if len(low_spending) > 0:
        low_spending.boxplot(column='resid_per_day', by='trip_duration_days', ax=plt.gca())
        plt.axhline(100, ls='--', c='red')
        plt.title('Low-Spending Cases: Residual per Day')
        plt.suptitle('')
        print(f"\nLow-spending cases (<$50/day receipts): {len(low_spending)} cases")
        for duration in sorted(low_spending['trip_duration_days'].unique()):
            subset = low_spending[low_spending['trip_duration_days'] == duration]
            if len(subset) >= 3:  # Only report if we have reasonable sample
                print(f"  {duration}-day: ${subset['resid_per_day'].mean():.2f} avg ({len(subset)} cases)")
    
    # Histogram of residual per day values
    plt.subplot(2, 2, 4)
    plt.hist(df['resid_per_day'], bins=50, alpha=0.7, edgecolor='black')
    plt.axvline(100, color='red', linestyle='--', label='$100')
    plt.axvline(80, color='orange', linestyle='--', label='$80')
    plt.axvline(60, color='yellow', linestyle='--', label='$60')
    plt.xlabel('Residual per Day ($)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Residual per Day')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dynamic_per_diem_diagnostic.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Attempt to identify base per-diem structure
    print("\n--- Attempting to identify base per-diem structure ---")
    
    # Group by trip duration and look at modal/median values
    per_diem_estimates = {}
    for duration in sorted(df['trip_duration_days'].unique()):
        subset = df[df['trip_duration_days'] == duration]
        low_spending_subset = subset[subset['receipts_per_day'] < 50]
        
        if len(low_spending_subset) >= 3:
            # Use low-spending cases as they should be closest to base per-diem
            estimated_base = low_spending_subset['resid_per_day'].median()
            per_diem_estimates[duration] = estimated_base
            print(f"{duration}-day trips: estimated base per-diem ${estimated_base:.2f}/day")
        else:
            # Fall back to all cases if we don't have enough low-spending ones
            estimated_base = subset['resid_per_day'].quantile(0.25)  # Lower quartile
            per_diem_estimates[duration] = estimated_base
            print(f"{duration}-day trips: estimated base per-diem ${estimated_base:.2f}/day (all cases, 25th percentile)")
    
    return per_diem_estimates

def main():
    """Run all diagnostics"""
    print("PHASE 1 REFINEMENTS: CRITICAL DIAGNOSTICS")
    print("Investigating 5-day bonus mystery and dynamic per-diem hypothesis")
    
    # Load data with proper guards
    df = load_data_with_guards()
    
    # Create holdout split
    train_df, holdout_df = create_holdout_split(df)
    
    # Run diagnostics on training data
    diagnostic_1_five_day_bonus(train_df)
    per_diem_estimates = diagnostic_2_dynamic_per_diem(train_df)
    
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    print("\n5-Day Bonus Investigation:")
    print("- Check five_day_diagnostic.png for visual patterns")
    print("- Look for conditional vs flat bonus evidence in output above")
    
    print("\nDynamic Per-Diem Investigation:")
    print("- Check dynamic_per_diem_diagnostic.png for base rate patterns")
    print("- Estimated base per-diem structure:")
    for duration, rate in per_diem_estimates.items():
        print(f"  {duration}-day trips: ${rate:.2f}/day")
    
    print(f"\nHoldout split created: 200 cases in dev_holdout.json")
    print(f"Training set: {len(train_df)} cases for rule development")
    
    print("\nNext steps:")
    print("1. Review diagnostic plots")
    print("2. Decide on 5-day bonus implementation (conditional/flat/none)")
    print("3. Implement dynamic per-diem as Layer 0")
    print("4. Proceed with Phase 2 Hour 3 - Core Logic Framework")

if __name__ == "__main__":
    main() 