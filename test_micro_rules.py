#!/usr/bin/env python3
"""
Unit tests for Phase 2 Hour 5: Micro-Rules A-D
"""
from decimal import Decimal
from calculate_reimbursement import (
    calculate_layer_1_mileage,
    calculate_layer_2_receipts,
    get_receipt_excess_rate,
    debug_calculation
)

def test_rule_a_long_trip_booster():
    """Test Rule A: Long-trip high-mileage booster"""
    print("=== Testing Rule A: Long-Trip High-Mileage Booster ===")
    
    # Case that should trigger: 7d, 1200mi, 171 mi/day (>120)
    print("Should trigger (7d, 1200mi):")
    mileage = calculate_layer_1_mileage(7, Decimal('1200'))
    print(f"  Mileage component: ${mileage}")
    
    # Case that shouldn't trigger: 6d, 1200mi (days < 7)
    print("Shouldn't trigger - days < 7 (6d, 1200mi):")
    mileage = calculate_layer_1_mileage(6, Decimal('1200'))
    print(f"  Mileage component: ${mileage}")
    
    # Case that shouldn't trigger: 7d, 600mi (miles < 700)
    print("Shouldn't trigger - miles < 700 (7d, 600mi):")
    mileage = calculate_layer_1_mileage(7, Decimal('600'))
    print(f"  Mileage component: ${mileage}")

def test_rule_b_receipt_tail_scaling():
    """Test Rule B: Receipt tail scaling by trip length"""
    print("\n=== Testing Rule B: Receipt Tail Scaling ===")
    
    # Test different trip lengths with $2000 receipts
    test_receipts = Decimal('2000.00')
    
    for days in [2, 4, 8]:
        excess_rate = get_receipt_excess_rate(days)
        receipt_component = calculate_layer_2_receipts(days, test_receipts)
        print(f"{days}d trip, ${test_receipts} receipts:")
        print(f"  Excess rate: {excess_rate}")
        print(f"  Receipt component: ${receipt_component}")

def test_rule_c_per_diem_adjustments():
    """Test Rule C: Per-diem adjustments for 8-10 day bucket"""
    print("\n=== Testing Rule C: Per-Diem Adjustments ===")
    
    # Compare old problematic cases with 0 receipts, low miles
    for days in [7, 8, 9, 10]:
        result = debug_calculation(days, Decimal('100'), Decimal('100'))
        print(f"\n{days}d, 100mi, $100 receipts - checking per-diem impact")

def test_rule_d_mileage_day_scaling():
    """Test Rule D: Mileage super-bonus day scaling"""
    print("\n=== Testing Rule D: Mileage Day-Scaling ===")
    
    # Test same mileage across different days
    test_miles = Decimal('1000')
    
    for days in [1, 2, 5]:
        mileage = calculate_layer_1_mileage(days, test_miles)
        print(f"{days}d, {test_miles}mi:")
        print(f"  Mileage component: ${mileage}")
        print(f"  Scale factor: {1 + (1/days):.2f}x")

def test_synthetic_case():
    """Test synthetic case as suggested: 7d, 1200mi, $700"""
    print("\n=== Testing Synthetic Case (7d, 1200mi, $700) ===")
    result = debug_calculation(7, Decimal('1200'), Decimal('700'))
    print("Should see long-trip booster in mileage component")

if __name__ == "__main__":
    test_rule_a_long_trip_booster()
    test_rule_b_receipt_tail_scaling()
    test_rule_c_per_diem_adjustments()
    test_rule_d_mileage_day_scaling()
    test_synthetic_case() 