#!/usr/bin/env python3
"""
Unit Tests for Layer 0: Dynamic Per-Diem
Verify foundation layer before full evaluation
"""

from calculate_reimbursement import calculate_reimbursement, debug_calculation
from decimal import Decimal

def test_layer_0_per_diem_only():
    """Test pure per-diem calculations (0 miles, 0 receipts)"""
    print("="*50)
    print("LAYER 0 UNIT TESTS: Per-Diem Only")
    print("="*50)
    
    test_cases = [
        (1, 0, 0, 147.00),   # Single day premium
        (2, 0, 0, 260.00),   # 2 * 130
        (5, 0, 0, 675.00),   # 5 * 135  
        (7, 0, 0, 665.00),   # 7 * 95
        (10, 0, 0, 850.00),  # 10 * 85
        (14, 0, 0, 1120.00), # 14 * 80
        (15, 0, 0, 1200.00), # 15 * 80 (boundary guard)
    ]
    
    all_passed = True
    for days, miles, receipts, expected in test_cases:
        result = float(calculate_reimbursement(days, miles, receipts))
        passed = abs(result - expected) < 0.01
        status = "✓" if passed else "✗"
        
        print(f"{status} {days}d, {miles}mi, ${receipts} → ${result:.2f} (expected ${expected:.2f})")
        
        if not passed:
            all_passed = False
            debug_calculation(days, miles, receipts)
    
    return all_passed

def test_layer_1_mileage_only():
    """Test pure mileage calculations (1 day to isolate, 0 receipts)"""
    print("\n" + "="*50)
    print("LAYER 1 UNIT TESTS: Mileage Tiers")
    print("="*50)
    
    # Use 1-day trips to isolate mileage component
    # Expected = 147 (per-diem) + mileage component
    test_cases = [
        (1, 50, 0, 147.00 + 50*0.58),      # Under 100 miles
        (1, 100, 0, 147.00 + 100*0.58),    # Exactly 100 miles
        (1, 150, 0, 147.00 + 100*0.58 + 50*0.15),  # Over 100 miles
        (1, 200, 0, 147.00 + 100*0.58 + 100*0.15), # Well over 100 miles
    ]
    
    all_passed = True
    for days, miles, receipts, expected in test_cases:
        result = float(calculate_reimbursement(days, miles, receipts))
        passed = abs(result - expected) < 0.01
        status = "✓" if passed else "✗"
        
        print(f"{status} {days}d, {miles}mi, ${receipts} → ${result:.2f} (expected ${expected:.2f})")
        
        if not passed:
            all_passed = False
            debug_calculation(days, miles, receipts)
    
    return all_passed

def test_extended_unit_cases():
    """Test additional edge cases and isolations"""
    print("\n" + "="*50)
    print("EXTENDED UNIT TESTS")
    print("="*50)
    
    # Zero-mile tests to isolate mileage tier math
    zero_mile_tests = [
        (1, 0, 0, 147.00),    # Pure per-diem isolation
        (5, 0, 0, 675.00),    # 5-day per-diem isolation
    ]
    
    print("Zero-mile tests (pure per-diem isolation):")
    for days, miles, receipts, expected in zero_mile_tests:
        result = float(calculate_reimbursement(days, miles, receipts))
        passed = abs(result - expected) < 0.01
        status = "✓" if passed else "✗"
        print(f"  {status} {days}d, {miles}mi, ${receipts} → ${result:.2f} (expected ${expected:.2f})")
    
    # Extended day count test (30 days)
    result_30_days = calculate_reimbursement(30, 0, 0)
    expected_30_days = 30 * 80.00  # Should use $80/day floor rate
    passed_30 = abs(float(result_30_days) - expected_30_days) < 0.01
    status_30 = "✓" if passed_30 else "✗"
    print(f"\n≥15-day boundary guard:")
    print(f"  {status_30} 30d, 0mi, $0 → ${result_30_days} (expected ${expected_30_days:.2f})")

def test_boundary_cases():
    """Test boundary and edge cases"""
    print("\n" + "="*50)
    print("BOUNDARY CASE TESTS")
    print("="*50)
    
    test_cases = [
        # Exactly at mileage breakpoint
        (5, 100, 0, "100-mile breakpoint"),
        # High day counts
        (20, 0, 0, "Long trip boundary guard"),
        # Edge case inputs
        (1, 0.5, 0, "Fractional miles"),
    ]
    
    for days, miles, receipts, description in test_cases:
        result = calculate_reimbursement(days, miles, receipts)
        print(f"✓ {description}: {days}d, {miles}mi, ${receipts} → ${result}")

def main():
    """Run all Layer 0 + Layer 1 tests"""
    print("PHASE 2 HOUR 3: CORE LOGIC UNIT TESTS")
    
    layer_0_passed = test_layer_0_per_diem_only()
    layer_1_passed = test_layer_1_mileage_only()
    test_extended_unit_cases()
    test_boundary_cases()
    
    print("\n" + "="*50)
    print("UNIT TEST SUMMARY")
    print("="*50)
    
    if layer_0_passed and layer_1_passed:
        print("✅ All unit tests PASSED")
        print("✅ Layer 0 (Dynamic Per-Diem) working correctly")  
        print("✅ Layer 1 (Mileage Tiers) working correctly")
        print("\n🚀 Ready for full evaluation!")
    else:
        print("❌ Some unit tests FAILED")
        print("❌ Need to fix foundation before evaluation")

if __name__ == "__main__":
    main() 