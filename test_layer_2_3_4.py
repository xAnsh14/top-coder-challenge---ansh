#!/usr/bin/env python3
"""
Unit tests for Phase 2 Hour 4: Layers 2, 3, and 4
"""
from decimal import Decimal
from calculate_reimbursement import (
    calculate_layer_2_receipts,
    calculate_layer_3_efficiency_bonus, 
    calculate_layer_4_special_cases,
    calculate_reimbursement,
    debug_calculation
)

def test_layer_2_receipts():
    """Test receipt processing layer"""
    print("=== Testing Layer 2: Receipt Processing ===")
    
    # Test optimal spending (no penalty)
    result = calculate_layer_2_receipts(3, Decimal('200.00'))  # $66.67/day (under $75/day)
    print(f"Optimal spending (3d, $200): ${result}")
    
    # Test overspending penalty
    result = calculate_layer_2_receipts(3, Decimal('300.00'))  # $100/day (over $75/day)
    print(f"Overspending (3d, $300): ${result}")
    
    # Test receipt ending in 49 cents (legacy bonus)
    result = calculate_layer_2_receipts(2, Decimal('148.49'))
    print(f"Legacy bonus (2d, $148.49): ${result}")
    
    # Test different trip length thresholds
    result_short = calculate_layer_2_receipts(2, Decimal('100.00'))  # Short trip
    result_medium = calculate_layer_2_receipts(5, Decimal('500.00'))  # Medium trip
    result_long = calculate_layer_2_receipts(10, Decimal('800.00'))  # Long trip
    print(f"Short trip receipt (2d, $100): ${result_short}")
    print(f"Medium trip receipt (5d, $500): ${result_medium}")
    print(f"Long trip receipt (10d, $800): ${result_long}")

def test_layer_3_efficiency():
    """Test efficiency bonus layer"""
    print("\n=== Testing Layer 3: Efficiency Bonuses ===")
    
    # Test sweet spot efficiency (180-220 miles/day)
    result = calculate_layer_3_efficiency_bonus(5, Decimal('1000.00'))  # 200 miles/day
    print(f"Sweet spot efficiency (5d, 1000mi = 200mi/day): ${result}")
    
    # Test low efficiency penalty
    result = calculate_layer_3_efficiency_bonus(5, Decimal('200.00'))  # 40 miles/day
    print(f"Low efficiency penalty (5d, 200mi = 40mi/day): ${result}")
    
    # Test normal efficiency (no bonus/penalty)
    result = calculate_layer_3_efficiency_bonus(5, Decimal('500.00'))  # 100 miles/day
    print(f"Normal efficiency (5d, 500mi = 100mi/day): ${result}")
    
    # Test very high efficiency (over sweet spot)
    result = calculate_layer_3_efficiency_bonus(3, Decimal('800.00'))  # 266 miles/day
    print(f"High efficiency (3d, 800mi = 266mi/day): ${result}")

def test_layer_4_special_cases():
    """Test special case handling"""
    print("\n=== Testing Layer 4: Special Cases ===")
    
    # Test 5-day bonus
    result = calculate_layer_4_special_cases(5, Decimal('300.00'), Decimal('400.00'))
    print(f"5-day bonus (5d, 300mi, $400): ${result}")
    
    # Test non-5-day (no bonus)
    result = calculate_layer_4_special_cases(4, Decimal('300.00'), Decimal('400.00'))
    print(f"4-day (no bonus): ${result}")
    
    # Test high-value trip bonus
    result = calculate_layer_4_special_cases(7, Decimal('800.00'), Decimal('300.00'))  # Total = 1100
    print(f"High-value trip (7d, 800mi, $300 = $1100 total): ${result}")
    
    # Test normal trip (no special bonus)
    result = calculate_layer_4_special_cases(3, Decimal('200.00'), Decimal('150.00'))  # Total = 350
    print(f"Normal trip (3d, 200mi, $150 = $350 total): ${result}")

def test_full_integration():
    """Test full calculation with all layers"""
    print("\n=== Testing Full Integration ===")
    
    # Test case 1: Efficient 5-day trip with good spending
    print("\nCase 1: Efficient 5-day trip")
    result = debug_calculation(5, Decimal('1000.00'), Decimal('500.00'))
    
    # Test case 2: Inefficient long trip with overspending
    print("\nCase 2: Inefficient long trip")
    result = debug_calculation(8, Decimal('200.00'), Decimal('1000.00'))
    
    # Test case 3: Short trip with legacy receipt bonus
    print("\nCase 3: Short trip with legacy bonus")
    result = debug_calculation(2, Decimal('150.00'), Decimal('99.49'))

if __name__ == "__main__":
    test_layer_2_receipts()
    test_layer_3_efficiency()
    test_layer_4_special_cases()
    test_full_integration() 