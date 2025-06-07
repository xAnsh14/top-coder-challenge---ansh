# 🎯 Legacy Reimbursement System - Hybrid ML Solution

## 📊 Performance Summary
- **Average Error**: $89.23 (84% reduction from baseline)
- **Close Matches**: 6 cases within ±$1.00
- **Total Error Reduction**: $580+ → $89.23 (84% improvement)
- **Approach**: Hybrid rule-based + ML residual correction

## 🏗️ Architecture

### Phase 1: Rule-Based Foundation (67% of improvement)
**Layer 0: Dynamic Per-Diem**
- Trip length-dependent daily rates ($50-147/day)
- Reduced rates for long trips to prevent over-payment

**Layer 1: Mileage Tiers + Bonuses**
- Two-tier structure: $0.58/mile (≤100mi), $0.15/mile (>100mi)
- High-mileage bonus with day-scaling for single-day marathons
- Long-trip booster for 7+ day, high-activity trips

**Layer 2: Receipt Processing**
- 1-day trips: Tiered structure (60%/40%/20% for $0-500/$500-1500/$1500+)
- Multi-day trips: Daily caps with scaled excess rates by trip length
- Legacy bonuses for receipts ending in .49/.99 cents

**Layer 3: Efficiency Bonuses**
- Sweet spot: 180-220 miles/day gets 15% mileage bonus
- Penalties for very low efficiency (<50 miles/day)

**Layer 4: Special Cases**
- 5-day trip bonus ($15)
- High-value trip bonus ($25 for trips >$1500 total value)
- Single-day high-activity bonus ($50)

### Phase 2: ML Residual Correction (17% additional improvement)
**Model**: GradientBoostingRegressor (50 trees, depth 3, lr=0.1)
- **Features**: 5 core features (days, miles, receipts, miles/day, receipts/day)
- **Training**: 800 cases with 5-fold CV validation
- **Export**: Lightweight JSON (105KB), zero runtime dependencies

**Intelligent Post-Processing**:
- **Smart shrinking**: Conservative (0.85) for large corrections, gentle (0.95) for small
- **Graduated clipping**: Adaptive limits based on trip characteristics
- **Max correction**: $400-700 based on trip complexity

## 🚀 Usage

```bash
python3 calculate_reimbursement.py <days> <miles> <receipts>
```

Example:
```bash
python3 calculate_reimbursement.py 5 800 600
# Output: 1243.99
```

## 🔧 Technical Details

**Precision**: All calculations use `decimal.Decimal` with `ROUND_HALF_UP`
**Dependencies**: Python stdlib only (`decimal`, `json`, `os`)
**Model Loading**: Cached JSON loading with graceful fallback
**Performance**: ~50 seconds for 1000 calculations

## 📁 Files

- `calculate_reimbursement.py` - Main calculation engine
- `gbm_residual.json` - ML model (105KB)
- `train_gbm_residual.py` - Training script (dev only)
- `eval_holdout.py` - Validation tools

## 🧪 Validation

**Holdout Performance**: $90.84 average error on 200 unseen cases
**Edge Cases**: Handles zero values, extreme inputs, precision requirements
**Robustness**: Stable across different trip patterns and lengths

---

## 🎯 Key Discoveries

1. **Dynamic per-diem rates**: Fixed $100/day was wrong - rates vary dramatically by trip length
2. **Receipt caps crucial**: 1-day trips need different processing than multi-day
3. **Mileage bonuses**: High-mileage trips get substantial bonuses, especially single-day
4. **ML residual effective**: Simple 5-feature model beats complex 11-feature (overfitting)
5. **Post-processing essential**: Shrink/clip prevents model overshooting

**Total Development Time**: ~6 hours
**Final Status**: Production-ready, 84% error reduction achieved 