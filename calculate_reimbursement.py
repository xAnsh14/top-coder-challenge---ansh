#!/usr/bin/env python3
"""
Legacy Reimbursement Calculation - Phase 3: ML Residual Integration
Rule-based foundation + GradientBoostingRegressor residual modeling
"""
import sys
import json
import os
from decimal import Decimal, ROUND_HALF_UP
import numpy as np

# Global variable to cache loaded model
_GBM_MODEL = None

# Helper function for consistent rounding
TWO_CENTS = Decimal('0.01')

def _r(x):
    """Helper for rounding to cents"""
    return x.quantize(TWO_CENTS, rounding=ROUND_HALF_UP)

def _load_gbm_model():
    """Load GBM model from JSON file (cached)"""
    global _GBM_MODEL
    if _GBM_MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), 'gbm_residual.json')
        try:
            with open(model_path, 'r') as f:
                _GBM_MODEL = json.load(f)
        except FileNotFoundError:
            # Model file not found - return None to skip ML residual
            _GBM_MODEL = None
    return _GBM_MODEL

def _predict_ml_residual(days, miles, receipts):
    """Predict ML residual using exported GBM model (supports ensemble)"""
    model = _load_gbm_model()
    if model is None:
        # No model available - return 0 residual
        return Decimal('0.00')
    
    # Calculate derived features
    miles_per_day = float(miles) / days if days > 0 else 0.0
    receipts_per_day = float(receipts) / days if days > 0 else 0.0
    
    # Feature vector (must match training order)
    # Build feature dictionary first to handle potential feature order differences
    feature_dict = {
        'trip_duration_days': days,
        'miles_traveled': float(miles),
        'total_receipts_amount': float(receipts),
        'miles_per_day': miles_per_day,
        'receipts_per_day': receipts_per_day,
        'log_receipts': np.log1p(float(receipts)),
        'log_miles': np.log1p(float(miles)),
        'is_one_day_big': int(days == 1 and float(receipts) > 1000),
        'is_long_hi_eff': int(days >= 7 and miles_per_day > 150)
    }
    
    # Get ordered features list from model
    model_features = model.get('features', [
        'trip_duration_days',
        'miles_traveled',
        'total_receipts_amount',
        'miles_per_day',
        'receipts_per_day'
    ])
    
    # Create ordered feature vector
    features = [feature_dict.get(fname, 0.0) for fname in model_features]
    
    # Check if we're using an ensemble model
    if model.get('is_ensemble', False):
        # Get predictions from both models and average them
        prediction1 = _predict_single_model(model['model1'], features)
        prediction2 = _predict_single_model(model['model2'], features)
        total_prediction = (prediction1 + prediction2) / 2
    else:
        # Use standard single-model prediction
        total_prediction = _predict_single_model(model, features)
    
    # Convert to Decimal for consistency
    ml_residual = Decimal(str(total_prediction))
    
    # Apply shrink and cap from model parameters or use defaults
    SHRINK = Decimal(str(model.get('shrink', 0.90)))
    CAP = Decimal(str(model.get('cap', 600)))
    
    # Apply shrinking factor
    ml_residual *= SHRINK
    
    # Apply capping to limit maximum effect
    ml_residual = max(min(ml_residual, CAP), -CAP)
    
    return ml_residual

def _predict_single_model(model, features):
    """Helper function to predict with a single GBM model"""
    # Start with initial prediction
    total_prediction = model['init_prediction']
    
    # Walk through each tree and accumulate predictions
    for tree in model['trees']:
        node_idx = 0
        
        # Navigate tree until we hit a leaf
        while True:
            node = tree[node_idx]
            
            # Check if this is a leaf node (children are -1)
            if node['left'] == -1 and node['right'] == -1:
                # Leaf node: add scaled prediction value
                total_prediction += node['value'] * model['learning_rate']
                break
            else:
                # Internal node: decide which child to follow
                if features[node['feat']] <= node['threshold']:
                    node_idx = node['left']
                else:
                    node_idx = node['right']
    
    return total_prediction

# Layer 0: Dynamic Per-Diem Rates (MICRO-TUNED for 8-10 day bucket)
BASE_PER_DIEM_RATES = {
    1: Decimal('120.00'),   # Single day
    2: Decimal('100.00'), 3: Decimal('100.00'),   # Short trips
    4: Decimal('110.00'), 5: Decimal('110.00'), 6: Decimal('110.00'),   # Medium trips
    7: Decimal('75.00'), 8: Decimal('60.00'), 9: Decimal('55.00'),   # Long trips (8-9 reduced)
    10: Decimal('55.00'), 11: Decimal('60.00'), 12: Decimal('60.00'), 
    13: Decimal('55.00'), 14: Decimal('50.00')   # Extended trips
}

# Layer 1: Mileage Tier Rates
MILEAGE_TIER_BREAKPOINT = Decimal('100')
MILEAGE_RATE_LOW = Decimal('0.58')   # Under 100 miles
MILEAGE_RATE_HIGH = Decimal('0.15')  # Over 100 miles

# HIGH MILEAGE BONUS SYSTEM (refined with day-scaling)
HIGH_MILEAGE_BONUS_THRESHOLD = Decimal('500')  # Miles where bonus kicks in
HIGH_MILEAGE_BONUS_BASE_RATE = Decimal('0.30')  # Base rate for scaling

# LONG-TRIP HIGH-MILEAGE BOOSTER (NEW - Rule A)
LONG_TRIP_BONUS_THRESHOLD_DAYS = 7
LONG_TRIP_BONUS_THRESHOLD_MILES = Decimal('700')
LONG_TRIP_BONUS_RATE = Decimal('0.25')
LONG_TRIP_MIN_MILES_PER_DAY = Decimal('120')

# Layer 2: Daily Receipt Caps with scaled tail rates (Rule B)
DAILY_RECEIPT_CAPS = {
    1: Decimal('200.00'),   # Single day
    2: Decimal('150.00'), 3: Decimal('150.00'),   # Short trips
    4: Decimal('120.00'), 5: Decimal('120.00'), 6: Decimal('120.00'),   # Medium trips
    7: Decimal('100.00')    # Longer trips (used for 7+ days)
}

RECEIPT_BASE_RATE = Decimal('0.60')  # 60% reimbursement up to cap

# Receipt tail rates by trip length (Rule B - ADJUSTED)
RECEIPT_EXCESS_RATES = {
    'single': (1, 1, Decimal('0.00')),     # 1 day: 0% above cap
    'short': (2, 3, Decimal('0.40')),      # 2-3 days: 40% above cap (increased from 0%)
    'medium': (4, 6, Decimal('0.10')),     # 4-6 days: 10% above cap  
    'long': (7, 30, Decimal('0.20'))       # 7+ days: 20% above cap
}

# Layer 3: Efficiency Bonus System
EFFICIENCY_SWEET_SPOT_MIN = Decimal('180')
EFFICIENCY_SWEET_SPOT_MAX = Decimal('220')
EFFICIENCY_BONUS_RATE = Decimal('0.15')

def get_base_per_diem_rate(trip_duration_days):
    """Get base per-diem rate for trip duration"""
    if trip_duration_days in BASE_PER_DIEM_RATES:
        return BASE_PER_DIEM_RATES[trip_duration_days]
    elif trip_duration_days > 14:
        return Decimal('45.00')
    else:
        return Decimal('50.00')

def get_daily_receipt_cap(trip_duration_days):
    """Get daily receipt cap for trip duration"""
    if trip_duration_days in DAILY_RECEIPT_CAPS:
        return DAILY_RECEIPT_CAPS[trip_duration_days]
    else:
        return DAILY_RECEIPT_CAPS[7]

def get_receipt_excess_rate(trip_duration_days):
    """Get receipt excess rate based on trip length (Rule B)"""
    for trip_type, (min_days, max_days, rate) in RECEIPT_EXCESS_RATES.items():
        if min_days <= trip_duration_days <= max_days:
            return rate
    return RECEIPT_EXCESS_RATES['long'][2]  # Default to long trip rate

def calculate_layer_0_per_diem(trip_duration_days):
    """Layer 0: Calculate base per-diem component"""
    daily_rate = get_base_per_diem_rate(trip_duration_days)
    total_per_diem = daily_rate * Decimal(str(trip_duration_days))
    return total_per_diem

def calculate_layer_1_mileage(trip_duration_days, miles_traveled):
    """Layer 1: Calculate mileage with tiers, high-mileage bonus, and day-scaling (Rule D)"""
    miles = Decimal(str(miles_traveled))
    days = trip_duration_days
    
    # Basic tier calculation
    if miles <= MILEAGE_TIER_BREAKPOINT:
        mileage_reimbursement = miles * MILEAGE_RATE_LOW
    else:
        first_tier = MILEAGE_TIER_BREAKPOINT * MILEAGE_RATE_LOW
        second_tier = (miles - MILEAGE_TIER_BREAKPOINT) * MILEAGE_RATE_HIGH
        mileage_reimbursement = first_tier + second_tier
    
    # HIGH MILEAGE BONUS with day-scaling (Rule D)
    if miles > HIGH_MILEAGE_BONUS_THRESHOLD:
        # Scale bonus by inverse of days - single-day marathons get bigger bonus
        day_scale_factor = Decimal('1.0') + (Decimal('1.0') / Decimal(str(days)))
        scaled_bonus_rate = HIGH_MILEAGE_BONUS_BASE_RATE * day_scale_factor
        high_mileage_bonus = (miles - HIGH_MILEAGE_BONUS_THRESHOLD) * scaled_bonus_rate
        mileage_reimbursement += high_mileage_bonus
    
    # LONG-TRIP HIGH-MILEAGE BOOSTER (Rule A)
    if (days >= LONG_TRIP_BONUS_THRESHOLD_DAYS and 
        miles > LONG_TRIP_BONUS_THRESHOLD_MILES and
        (miles / Decimal(str(days))) > LONG_TRIP_MIN_MILES_PER_DAY):
        long_trip_bonus = (miles - LONG_TRIP_BONUS_THRESHOLD_MILES) * LONG_TRIP_BONUS_RATE
        mileage_reimbursement += long_trip_bonus
    
    return mileage_reimbursement

def calculate_layer_2_receipts(trip_duration_days, total_receipts_amount):
    """Layer 2: Receipt processing with daily caps and scaled tail rates (Rule B + 1-day tiers)"""
    days = trip_duration_days
    receipts = Decimal(str(total_receipts_amount)) if not isinstance(total_receipts_amount, Decimal) else total_receipts_amount
    
    # SPECIAL CASE: 1-day receipt tiers (business logic for same-day travel)
    if days == 1:
        # Tiered structure for single-day trips
        receipt_component = Decimal('0.00')
        remaining = receipts
        
        # Tier 1: First $500 at 60%
        tier1_limit = Decimal('500.00')
        tier1_rate = Decimal('0.60')
        tier1_amount = min(remaining, tier1_limit)
        receipt_component += tier1_amount * tier1_rate
        remaining -= tier1_amount
        
        if remaining > Decimal('0.00'):
            # Tier 2: Next $1000 ($500-$1500) at 40%
            tier2_limit = Decimal('1000.00')
            tier2_rate = Decimal('0.40')
            tier2_amount = min(remaining, tier2_limit)
            receipt_component += tier2_amount * tier2_rate
            remaining -= tier2_amount
            
            if remaining > Decimal('0.00'):
                # Tier 3: Above $1500 at 20%
                tier3_rate = Decimal('0.20')
                receipt_component += remaining * tier3_rate
    
    else:
        # STANDARD LOGIC: Multi-day trips with daily caps
        daily_cap = get_daily_receipt_cap(days)
        total_cap = daily_cap * Decimal(str(days))
        
        # Get appropriate excess rate for this trip length
        excess_rate = get_receipt_excess_rate(days)
        
        if receipts <= total_cap:
            # Within cap: 60% reimbursement
            receipt_component = receipts * RECEIPT_BASE_RATE
        else:
            # Above cap: 60% up to cap + scaled rate on excess
            capped_portion = total_cap * RECEIPT_BASE_RATE
            excess_portion = (receipts - total_cap) * excess_rate
            receipt_component = capped_portion + excess_portion
    
    # Legacy bonus for receipts ending in 49 or 99 cents (all trip lengths)
    receipt_cents = int((receipts % Decimal('1.00')) * Decimal('100'))
    if receipt_cents in [49, 99]:
        receipt_component += Decimal('5.00')
    
    return receipt_component

def calculate_layer_3_efficiency_bonus(trip_duration_days, miles_traveled):
    """Layer 3: Efficiency bonus system"""
    days = trip_duration_days
    miles = Decimal(str(miles_traveled)) if not isinstance(miles_traveled, Decimal) else miles_traveled
    
    if days == 0:
        return Decimal('0.00')
    
    miles_per_day = miles / Decimal(str(days))
    
    # Sweet spot efficiency bonus
    if EFFICIENCY_SWEET_SPOT_MIN <= miles_per_day <= EFFICIENCY_SWEET_SPOT_MAX:
        # Calculate base mileage for bonus (need to call with days for new signature)
        base_mileage = calculate_layer_1_mileage(days, miles)
        efficiency_bonus = base_mileage * EFFICIENCY_BONUS_RATE
        return efficiency_bonus
    
    # Small penalty for very low efficiency
    elif miles_per_day < Decimal('50.00'):
        base_mileage = calculate_layer_1_mileage(days, miles)
        inefficiency_penalty = base_mileage * Decimal('0.05')
        return -inefficiency_penalty
    
    return Decimal('0.00')

def calculate_layer_4_special_cases(trip_duration_days, miles_traveled, total_receipts_amount):
    """Layer 4: Special case handling"""
    days = trip_duration_days
    miles = Decimal(str(miles_traveled)) if not isinstance(miles_traveled, Decimal) else miles_traveled
    receipts = Decimal(str(total_receipts_amount)) if not isinstance(total_receipts_amount, Decimal) else total_receipts_amount
    
    special_adjustment = Decimal('0.00')
    
    # 5-day trip bonus
    if days == 5:
        special_adjustment += Decimal('15.00')
    
    # High-value trip bonus
    total_trip_value = receipts + miles
    if total_trip_value > Decimal('1500.00'):
        special_adjustment += Decimal('25.00')
    
    # Single-day high-activity bonus
    if days == 1 and (miles > Decimal('500') or receipts > Decimal('1000')):
        special_adjustment += Decimal('50.00')
    
    return special_adjustment

def calculate_reimbursement(trip_duration_days, miles_traveled, total_receipts_amount):
    """Calculate reimbursement amount using rule-based foundation + ML residual correction"""
    # Convert inputs to appropriate types for precise arithmetic
    days = int(trip_duration_days)
    miles = miles_traveled if isinstance(miles_traveled, Decimal) else Decimal(str(miles_traveled))
    receipts = total_receipts_amount if isinstance(total_receipts_amount, Decimal) else Decimal(str(total_receipts_amount))
    
    # Layer 0: Base per-diem calculation
    per_diem_component = _r(calculate_layer_0_per_diem(days))
    
    # Layer 1: Mileage reimbursement (now takes days for scaling)
    mileage_component = _r(calculate_layer_1_mileage(days, miles))
    
    # Layer 2: Receipt processing with scaled tail rates
    receipt_component = _r(calculate_layer_2_receipts(days, receipts))
    
    # Layer 3: Efficiency bonus system
    efficiency_component = _r(calculate_layer_3_efficiency_bonus(days, miles))
    
    # Layer 4: Special case handling
    special_component = _r(calculate_layer_4_special_cases(days, miles, receipts))
    
    # PHASE 3: ML Residual Correction
    ml_residual = _r(_predict_ml_residual(days, miles, receipts))
    
    # Total reimbursement
    total_reimbursement = (per_diem_component + mileage_component + 
                          receipt_component + efficiency_component + 
                          special_component + ml_residual)
    
    return total_reimbursement

def debug_calculation(trip_duration_days, miles_traveled, total_receipts_amount):
    """Debug version that shows component breakdown"""
    days = int(trip_duration_days)
    miles = Decimal(str(miles_traveled))
    receipts = Decimal(str(total_receipts_amount))
    
    per_diem = calculate_layer_0_per_diem(days)
    mileage = calculate_layer_1_mileage(days, miles)
    receipt = calculate_layer_2_receipts(days, receipts)
    efficiency = calculate_layer_3_efficiency_bonus(days, miles)
    special = calculate_layer_4_special_cases(days, miles, receipts)
    ml_residual = _predict_ml_residual(days, miles, receipts)
    
    print(f"Debug breakdown for {days}d, {miles}mi, ${receipts}:")
    print(f"  Per-diem: ${per_diem}")
    print(f"  Mileage: ${mileage}")
    print(f"  Receipts: ${receipt}")
    print(f"  Efficiency: ${efficiency}")
    print(f"  Special: ${special}")
    print(f"  ML Residual: ${ml_residual}")
    print(f"  Total: ${per_diem + mileage + receipt + efficiency + special + ml_residual}")
    
    return per_diem + mileage + receipt + efficiency + special + ml_residual

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 calculate_reimbursement.py <trip_duration_days> <miles_traveled> <total_receipts_amount>")
        sys.exit(1)
    
    try:
        trip_duration_days = int(sys.argv[1])
        miles_traveled = Decimal(sys.argv[2])
        total_receipts_amount = Decimal(sys.argv[3])
        
        result = calculate_reimbursement(trip_duration_days, miles_traveled, total_receipts_amount)
        print(result)
        
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid input - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
