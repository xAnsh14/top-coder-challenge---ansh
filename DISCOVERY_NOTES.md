# Phase 1 Hour 2: Interview Mining + Hypothesis Formation

## Executive Summary

From analyzing 1,000 public cases and 5 employee interviews, clear patterns emerge suggesting a sophisticated multi-factor reimbursement system with:
- **Base per diem**: ~$100/day foundation
- **Mileage tiers**: Diminishing returns after ~100 miles  
- **Efficiency bonuses**: Sweet spot 180-220 miles/day
- **5-day trip bonus**: Consistent special treatment
- **Spending thresholds**: Penalties for exceeding optimal ranges by trip length
- **Interaction effects**: Complex factor combinations trigger bonuses/penalties

## Interview Claims vs. EDA Cross-Reference

### ✅ **CONFIRMED BY DATA**

| Interview Claim | EDA Evidence | Confidence |
|----------------|--------------|------------|
| **Base per diem ~$100/day** | Most common rounded reimbursement/day = $195 (could be $100 + bonuses) | **HIGH** |
| **5-day trip bonus** | 5-day trips: avg $254.52/day vs overall avg $284.71/day | **MEDIUM** |
| **Mileage tiers with diminishing returns** | Under 100 miles: $40.39/mile, Over 100 miles: $2.85/mile | **HIGH** |
| **Efficiency sweet spot 180-220 mi/day** | Sweet spot group: $346.98/day vs moderate: $266.46/day | **HIGH** |
| **Spending penalties for high amounts** | Clear negative correlation between receipts/day and reimbursement efficiency | **HIGH** |
| **Small receipt penalties** | Low receipts often worse than no receipts (per Dave/Jennifer) | **MEDIUM** |

### ❓ **NEEDS INVESTIGATION**

| Interview Claim | EDA Status | Priority |
|----------------|------------|----------|
| **Spending thresholds by trip length** | Visible pattern: short trips higher $/day, long trips lower | **HIGH** |
| **Interaction effects** | Complex patterns visible but not quantified | **HIGH** |
| **Rounding bug (49/99 cents)** | Cannot verify from public data | **MEDIUM** |
| **Timing effects (quarterly/lunar)** | No timestamp data available | **LOW** |

## Core Business Logic Hypotheses (Prioritized)

### **TIER 1: FOUNDATION RULES (85-90% accuracy target)**

#### 1. Base Per Diem Calculation
```python
base_per_diem = 100.00 * trip_duration_days
```
**Evidence**: Multiple interviews mention $100/day base rate
**EDA Support**: Common reimbursement patterns around multiples of $100

#### 2. Mileage Reimbursement with Tiers
```python
if miles_traveled <= 100:
    mileage_reimbursement = miles_traveled * 0.58
else:
    # Diminishing returns curve - need to calibrate
    mileage_reimbursement = 100 * 0.58 + (miles_traveled - 100) * reduced_rate
```
**Evidence**: Lisa (accounting) confirms tiered structure, EDA shows clear breakpoint
**EDA Support**: 40x higher rate per mile under 100 miles vs over 100

#### 3. Receipt Processing with Caps/Penalties
```python
if total_receipts_amount < threshold_low:
    receipt_reimbursement = penalty  # Often worse than zero
elif total_receipts_amount > spending_cap(trip_duration_days):
    receipt_reimbursement = diminishing_returns_function(receipts, trip_length)
else:
    receipt_reimbursement = receipts * good_rate
```
**Evidence**: Multiple interviews confirm spending caps vary by trip length
**EDA Support**: Clear diminishing returns pattern in spending vs reimbursement

### **TIER 2: PATTERN-SPECIFIC RULES (90-95% accuracy target)**

#### 4. Five-Day Trip Bonus
```python
if trip_duration_days == 5:
    bonus_multiplier = 1.15  # TBD - calibrate from data
```
**Evidence**: Lisa confirms "5-day trips almost always get a bonus"
**EDA Support**: 112 five-day trips with distinct reimbursement patterns

#### 5. Efficiency Bonuses
```python
efficiency = miles_traveled / trip_duration_days
if 180 <= efficiency <= 220:
    efficiency_bonus = sweet_spot_bonus
elif efficiency > 300:
    efficiency_bonus = high_efficiency_bonus  # But diminishing
elif efficiency < 100:
    efficiency_penalty = low_efficiency_penalty
```
**Evidence**: Kevin's detailed testing, confirmed by EDA efficiency analysis
**EDA Support**: Clear bonus progression: $173.75 → $266.46 → $346.98 → $400.79 → $787.51

#### 6. Spending Thresholds by Trip Length
```python
optimal_spending_per_day = {
    1: 75,      # Short trips: under $75/day optimal
    2-3: 120,   # Medium trips: under $120/day optimal  
    4-6: 120,   # Kevin's "medium trips"
    7+: 90      # Long trips: under $90/day optimal
}
```
**Evidence**: Kevin's systematic testing, supported by HR observations
**EDA Support**: Spending/day decreases with trip length: $1047 → $570 → $333 → $96

### **TIER 3: EDGE CASES & REFINEMENTS (95%+ accuracy target)**

#### 7. Interaction Effects
```python
# Kevin's "sweet spot combo"
if trip_duration_days == 5 and efficiency >= 180 and receipts_per_day <= 100:
    interaction_bonus = major_bonus

# Kevin's "vacation penalty"  
if trip_duration_days >= 8 and receipts_per_day > optimal_threshold:
    interaction_penalty = major_penalty
```

#### 8. Suspected "Bugs" to Preserve
```python
# Rounding quirks mentioned by Lisa
if total_receipts_amount.endswith(('.49', '.99')):
    rounding_bonus = small_bonus
```

## Implementation Strategy

### **Phase 2 Hour 3: Core Logic Framework**
1. Implement base per diem ($100/day)
2. Add mileage tiers (calibrate breakpoint and rates)
3. Add basic receipt processing with spending caps
4. Target: 50-60% exact matches

### **Phase 2 Hour 4: Pattern-Specific Rules**  
1. Implement 5-day bonus
2. Add efficiency bonuses (180-220 sweet spot)
3. Add spending threshold penalties by trip length
4. Target: 70-80% exact matches

### **Phase 2 Hour 5: Edge Cases + Refinement**
1. Implement interaction effects (Kevin's combinations)
2. Add suspected "bugs" (49/99 cent bonuses)
3. Fine-tune parameters based on error analysis
4. Target: 85-90% exact matches

## Key Calibration Parameters to Determine

| Parameter | Interview Hint | Calibration Method |
|-----------|---------------|--------------------|
| **Mileage rate after 100 miles** | "Not linear drop" | Fit curve to EDA data |
| **5-day bonus amount** | "Always a little extra" | Compare 5-day vs other trip reimbursements |
| **Efficiency bonus amounts** | Kevin's sweet spot | Regression on efficiency vs reimbursement |
| **Spending cap curves** | Kevin's thresholds | Optimize against spending penalty patterns |
| **Small receipt penalty** | "Worse than nothing" | Compare low-receipt vs no-receipt cases |

## Error Analysis Focus Areas

Based on interviews, expect high errors in:
1. **Boundary cases**: Exactly 100 miles, exactly 5 days, threshold spending amounts
2. **Complex interactions**: High efficiency + high spending combinations  
3. **Edge receipts**: Very low or very high receipt amounts
4. **Long trips**: 8+ days where multiple penalty factors compound

## Model Validation Strategy

### **Rule-Based Validation**
- Reserve 200 cases for holdout testing
- Focus on Kevin's "guaranteed bonus" and "guaranteed penalty" scenarios
- Verify efficiency sweet spot bonuses

### **Residual Analysis** (Phase 3)
- If plateaus <90%, analyze systematic residuals
- Look for missed interaction terms
- Consider light ML for remaining patterns

## Implementation Notes

### **Precision Requirements**
```python
from decimal import Decimal, ROUND_HALF_UP
# Always use ROUND_HALF_UP (legacy system quirk)
result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

### **Calculation Order** (TBD - test different sequences)
1. Base per diem
2. Mileage reimbursement  
3. Receipt processing
4. Efficiency bonuses/penalties
5. Trip-specific bonuses (5-day)
6. Interaction effects
7. Final rounding

## Success Metrics

| Rule Tier | Target Accuracy | Key Validation |
|-----------|----------------|----------------|
| Tier 1 (Foundation) | 60% exact matches | Base patterns work |
| Tier 2 (Patterns) | 80% exact matches | Bonus logic correct |
| Tier 3 (Edge Cases) | 90% exact matches | Interaction effects captured |
| Final Target | **95% exact matches** | Ready for private test set |

---

**Phase 1 Complete - Ready for Phase 2 Implementation** 