#!/usr/bin/env python3
"""
Phase 1 Hour 1: Quick EDA + Setup
Exploratory Data Analysis of Legacy Reimbursement System
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)

def load_data():
    """Load and structure the public cases data"""
    print("Loading public_cases.json...")
    with open('public_cases.json', 'r') as f:
        data = json.load(f)
    
    # Flatten the data structure
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
    print(f"Loaded {len(df)} cases")
    return df

def generate_basic_statistics(df):
    """Generate basic statistics for all variables"""
    print("\n" + "="*60)
    print("BASIC STATISTICS")
    print("="*60)
    
    print("\nDataset Overview:")
    print(f"Total cases: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    print("\nDescriptive Statistics:")
    print(df.describe())
    
    print("\nTrip Duration Distribution:")
    print(df['trip_duration_days'].value_counts().sort_index())
    
    print("\nData Types and Missing Values:")
    print(df.info())

def create_ratio_features(df):
    """Create key ratio features that might reveal step-wise patterns"""
    print("\n" + "="*60)
    print("RATIO FEATURE ENGINEERING")
    print("="*60)
    
    # Add ratio features
    df['miles_per_day'] = df['miles_traveled'] / df['trip_duration_days']
    df['receipts_per_day'] = df['total_receipts_amount'] / df['trip_duration_days']
    df['receipts_per_mile'] = df['total_receipts_amount'] / df['miles_traveled'].replace(0, np.nan)
    df['reimbursement_per_day'] = df['expected_output'] / df['trip_duration_days']
    
    # Add some potentially useful categorizations
    df['trip_length_category'] = pd.cut(df['trip_duration_days'], 
                                       bins=[0, 1, 3, 5, 7, float('inf')], 
                                       labels=['1_day', '2-3_days', '4-5_days', '6-7_days', '8+_days'])
    
    df['mileage_category'] = pd.cut(df['miles_traveled'], 
                                   bins=[0, 50, 100, 200, 500, float('inf')], 
                                   labels=['<50', '50-100', '100-200', '200-500', '500+'])
    
    print("Ratio Features Created:")
    print("- miles_per_day")
    print("- receipts_per_day") 
    print("- receipts_per_mile")
    print("- reimbursement_per_day")
    print("- trip_length_category")
    print("- mileage_category")
    
    print("\nRatio Feature Statistics:")
    ratio_cols = ['miles_per_day', 'receipts_per_day', 'receipts_per_mile', 'reimbursement_per_day']
    print(df[ratio_cols].describe())
    
    return df

def create_visualizations(df):
    """Create key visualizations to identify patterns and breakpoints"""
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS")
    print("="*60)
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Reimbursement vs each input variable
    plt.subplot(3, 4, 1)
    plt.scatter(df['trip_duration_days'], df['expected_output'], alpha=0.6)
    plt.xlabel('Trip Duration (days)')
    plt.ylabel('Reimbursement ($)')
    plt.title('Reimbursement vs Trip Duration')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 4, 2)
    plt.scatter(df['miles_traveled'], df['expected_output'], alpha=0.6)
    plt.xlabel('Miles Traveled')
    plt.ylabel('Reimbursement ($)')
    plt.title('Reimbursement vs Miles Traveled')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 4, 3)
    plt.scatter(df['total_receipts_amount'], df['expected_output'], alpha=0.6)
    plt.xlabel('Total Receipts ($)')
    plt.ylabel('Reimbursement ($)')
    plt.title('Reimbursement vs Total Receipts')
    plt.grid(True, alpha=0.3)
    
    # 2. Key ratio features
    plt.subplot(3, 4, 4)
    plt.scatter(df['miles_per_day'], df['expected_output'], alpha=0.6)
    plt.xlabel('Miles per Day')
    plt.ylabel('Reimbursement ($)')
    plt.title('Reimbursement vs Miles/Day')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 4, 5)
    plt.scatter(df['receipts_per_day'], df['expected_output'], alpha=0.6)
    plt.xlabel('Receipts per Day ($)')
    plt.ylabel('Reimbursement ($)')
    plt.title('Reimbursement vs Receipts/Day')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 4, 6)
    plt.scatter(df['receipts_per_mile'], df['expected_output'], alpha=0.6)
    plt.xlabel('Receipts per Mile ($)')
    plt.ylabel('Reimbursement ($)')
    plt.title('Reimbursement vs Receipts/Mile')
    plt.grid(True, alpha=0.3)
    
    # 3. Box plots by trip duration
    plt.subplot(3, 4, 7)
    df.boxplot(column='expected_output', by='trip_duration_days', ax=plt.gca())
    plt.title('Reimbursement by Trip Duration')
    plt.suptitle('')  # Remove default title
    
    plt.subplot(3, 4, 8)
    df.boxplot(column='reimbursement_per_day', by='trip_duration_days', ax=plt.gca())
    plt.title('Reimbursement per Day by Trip Duration')
    plt.suptitle('')
    
    # 4. Mileage analysis
    plt.subplot(3, 4, 9)
    df.boxplot(column='expected_output', by='mileage_category', ax=plt.gca())
    plt.title('Reimbursement by Mileage Category')
    plt.suptitle('')
    plt.xticks(rotation=45)
    
    # 5. Efficiency analysis
    plt.subplot(3, 4, 10)
    plt.scatter(df['miles_per_day'], df['reimbursement_per_day'], alpha=0.6)
    plt.xlabel('Miles per Day')
    plt.ylabel('Reimbursement per Day ($)')
    plt.title('Daily Efficiency Analysis')
    plt.grid(True, alpha=0.3)
    
    # 6. 5-day trip special analysis
    five_day_trips = df[df['trip_duration_days'] == 5]
    other_trips = df[df['trip_duration_days'] != 5]
    
    plt.subplot(3, 4, 11)
    plt.scatter(other_trips['miles_traveled'], other_trips['reimbursement_per_day'], 
                alpha=0.4, label='Other trips', color='blue')
    plt.scatter(five_day_trips['miles_traveled'], five_day_trips['reimbursement_per_day'], 
                alpha=0.8, label='5-day trips', color='red', s=50)
    plt.xlabel('Miles Traveled')
    plt.ylabel('Reimbursement per Day ($)')
    plt.title('5-Day Trip Special Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 7. Reimbursement distribution
    plt.subplot(3, 4, 12)
    plt.hist(df['expected_output'], bins=50, alpha=0.7, edgecolor='black')
    plt.xlabel('Reimbursement Amount ($)')
    plt.ylabel('Frequency')
    plt.title('Reimbursement Distribution')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('eda_visualizations.png', dpi=300, bbox_inches='tight')
    print("Saved visualizations to: eda_visualizations.png")
    plt.show()

def identify_patterns_and_breakpoints(df):
    """Analyze the data for obvious tiers and breakpoints"""
    print("\n" + "="*60)
    print("PATTERN AND BREAKPOINT ANALYSIS")
    print("="*60)
    
    # Check for common reimbursement per day values (potential base rates)
    print("\nMost common reimbursement per day values:")
    per_day_counts = df['reimbursement_per_day'].round(2).value_counts().head(20)
    print(per_day_counts)
    
    # Look for potential base per diem around $100
    base_per_diem_candidates = df['reimbursement_per_day'].round(0).value_counts().head(10)
    print(f"\nRounded reimbursement per day (potential base rates):")
    print(base_per_diem_candidates)
    
    # Analyze 5-day trips specifically
    five_day_trips = df[df['trip_duration_days'] == 5]
    print(f"\n5-Day Trip Analysis:")
    print(f"Number of 5-day trips: {len(five_day_trips)}")
    print(f"Average reimbursement: ${five_day_trips['expected_output'].mean():.2f}")
    print(f"Average reimbursement per day: ${five_day_trips['reimbursement_per_day'].mean():.2f}")
    
    # Look for mileage breakpoints around 100 miles
    print(f"\nMileage Breakpoint Analysis:")
    under_100_miles = df[df['miles_traveled'] < 100]
    over_100_miles = df[df['miles_traveled'] >= 100]
    
    print(f"Under 100 miles - Average reimbursement/mile: ${(under_100_miles['expected_output'] / under_100_miles['miles_traveled']).mean():.3f}")
    print(f"Over 100 miles - Average reimbursement/mile: ${(over_100_miles['expected_output'] / over_100_miles['miles_traveled']).mean():.3f}")
    
    # Efficiency sweet spot analysis (around 180-220 miles/day mentioned in interviews)
    print(f"\nEfficiency Sweet Spot Analysis:")
    efficiency_ranges = [
        (0, 100, "Low efficiency (<100 mi/day)"),
        (100, 180, "Moderate efficiency (100-180 mi/day)"),
        (180, 220, "Sweet spot (180-220 mi/day)"),
        (220, 300, "High efficiency (220-300 mi/day)"),
        (300, float('inf'), "Very high efficiency (>300 mi/day)")
    ]
    
    for min_eff, max_eff, label in efficiency_ranges:
        subset = df[(df['miles_per_day'] >= min_eff) & (df['miles_per_day'] < max_eff)]
        if len(subset) > 0:
            print(f"{label}: {len(subset)} cases, avg reimbursement/day: ${subset['reimbursement_per_day'].mean():.2f}")
    
    # Check for spending threshold patterns
    print(f"\nSpending Threshold Analysis by Trip Length:")
    for duration in sorted(df['trip_duration_days'].unique()):
        subset = df[df['trip_duration_days'] == duration]
        print(f"{duration}-day trips: avg receipts/day: ${subset['receipts_per_day'].mean():.2f}, avg reimbursement/day: ${subset['reimbursement_per_day'].mean():.2f}")

def setup_run_sh_template():
    """Set up the basic run.sh template for Phase 2"""
    print("\n" + "="*60)
    print("SETTING UP run.sh TEMPLATE")
    print("="*60)
    
    run_sh_content = """#!/usr/bin/env bash
# Legacy Reimbursement System Implementation
# Usage: ./run.sh <trip_duration_days> <miles_traveled> <total_receipts_amount>

# Call the Python calculation script with the three arguments
python3 calculate_reimbursement.py "$1" "$2" "$3"
"""
    
    with open('run.sh', 'w') as f:
        f.write(run_sh_content)
    
    # Make it executable
    import os
    os.chmod('run.sh', 0o755)
    
    print("Created run.sh with basic Python wrapper")
    
    # Create a stub calculation script
    stub_content = """#!/usr/bin/env python3
\"\"\"
Legacy Reimbursement Calculation - Stub for Phase 2
\"\"\"
import sys
from decimal import Decimal, ROUND_HALF_UP

def calculate_reimbursement(trip_duration_days, miles_traveled, total_receipts_amount):
    \"\"\"
    Calculate reimbursement amount based on legacy system rules
    TODO: Implement actual business logic in Phase 2
    \"\"\"
    # Placeholder calculation - will be replaced in Phase 2
    base_per_diem = Decimal('100.00')
    result = base_per_diem * Decimal(str(trip_duration_days))
    
    # Round to 2 decimal places using ROUND_HALF_UP
    return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 calculate_reimbursement.py <trip_duration_days> <miles_traveled> <total_receipts_amount>")
        sys.exit(1)
    
    trip_duration_days = int(sys.argv[1])
    miles_traveled = int(sys.argv[2])
    total_receipts_amount = float(sys.argv[3])
    
    result = calculate_reimbursement(trip_duration_days, miles_traveled, total_receipts_amount)
    print(result)
"""
    
    with open('calculate_reimbursement.py', 'w') as f:
        f.write(stub_content)
    
    print("Created calculate_reimbursement.py stub for Phase 2")

def main():
    """Main execution function for Phase 1 Hour 1"""
    print("="*60)
    print("PHASE 1 HOUR 1: QUICK EDA + SETUP")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    df = load_data()
    
    # Generate basic statistics
    generate_basic_statistics(df)
    
    # Create ratio features
    df = create_ratio_features(df)
    
    # Create visualizations
    create_visualizations(df)
    
    # Identify patterns and breakpoints
    identify_patterns_and_breakpoints(df)
    
    # Setup run.sh template
    setup_run_sh_template()
    
    print("\n" + "="*60)
    print("PHASE 1 HOUR 1 COMPLETE")
    print("="*60)
    print("Deliverables:")
    print("✓ Basic data understanding completed")
    print("✓ Visual patterns identified") 
    print("✓ Key ratio features analyzed")
    print("✓ Breakpoints and tiers identified")
    print("✓ run.sh template setup complete")
    print("\nReady for Phase 1 Hour 2: Interview Mining + Hypothesis Formation")

if __name__ == "__main__":
    main() 