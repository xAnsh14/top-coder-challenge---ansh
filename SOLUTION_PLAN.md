# 🎯 Legacy Reimbursement System Reverse Engineering Plan

## Project Overview
**Challenge**: Reverse-engineer a 60-year-old travel reimbursement system to achieve ≥95% accuracy
**Time Budget**: 6-8 hours (one-day sprint)
**Data**: 1,000 public cases + employee interviews
**Target**: 95%+ exact matches on public set, strong performance on 5,000 private cases

## Implementation Preferences
- **Language**: Python (wrapped in `run.sh`)
- **Approach**: Hybrid rule-mining + light ML for residuals
- **Testing**: Iterative loops with `eval.sh` feedback
- **Accuracy Goal**: ≥95% exact matches (aim for 98-99%)

---

## 🚀 **Phase 1: Dual Discovery (2 hours)**
**Goal**: Build initial hypotheses from both data and interviews

### **Hour 1: Quick EDA + Setup**
**Tasks:**
- [ ] Extract and visualize public cases data in Python/Pandas
- [ ] Generate basic statistics:
  - Trip duration distribution
  - Mileage ranges and patterns
  - Receipt amount distributions
  - Reimbursement amount ranges
- [ ] Create key visualizations:
  - Scatter plots: reimbursement vs. each input variable
  - **Ratio features**: miles/day, receipts/day, receipts/mile (often reveal stair-steps)
  - Box plots by trip duration
- [ ] Identify obvious tiers/breakpoints visually
- [ ] Set up `run.sh` template structure

**Deliverables:**
- Basic data understanding
- Visual patterns identified
- Setup complete

### **Hour 2: Interview Mining + Hypothesis Formation**
**Tasks:**
- [ ] Systematically extract concrete claims from interviews:
  - Base per diem rates (~$100/day)
  - 5-day trip bonus pattern
  - Mileage tier structure
  - Receipt processing rules
  - Efficiency bonus thresholds
  - Spending caps by trip length
- [ ] Cross-reference interview claims with EDA findings
- [ ] Create prioritized hypothesis list
- [ ] Document "rule candidates" for implementation

**Deliverables:**
- Ranked hypothesis list
- Concrete rule specifications
- Data-interview reconciliation notes

---

## 🔧 **Phase 2: Rule Implementation (3 hours)**
**Goal**: Build interpretable rule-based model covering 85-90% of cases

### **Hour 3: Core Logic Framework**
**Tasks:**
- [ ] Set up Python calculation framework with `Decimal` precision (`ROUND_HALF_UP`)
- [ ] Implement base per diem calculation ($100/day baseline)
- [ ] Add mileage reimbursement with suspected tiers:
  - First ~100 miles at full rate (~$0.58/mile)
  - Diminishing returns curve after 100 miles
- [ ] Add basic receipt processing with caps/penalties
- [ ] Create `run.sh` wrapper script (minimal imports only!)
- [ ] Test against 100 random cases, measure baseline accuracy
- [ ] **Create error heat-map**: trip-days × receipts/day to identify missing patterns

**Target**: 50-60% exact matches

### **Hour 4: Pattern-Specific Rules**
**Tasks:**
- [ ] Implement 5-day bonus logic (special treatment for exactly 5-day trips)
- [ ] Add efficiency bonuses:
  - Sweet spot around 180-220 miles/day
  - Penalties for very low or very high efficiency
- [ ] Add spending threshold penalties by trip length:
  - Short trips: <$75/day optimal
  - Medium trips (4-6 days): <$120/day optimal
  - Long trips: <$90/day optimal
- [ ] Run `eval.sh` for first formal accuracy measurement

**Target**: 70-80% exact matches

### **Hour 5: Edge Cases + Refinement**
**Tasks:**
- [ ] Implement suspected "bugs":
  - Receipts ending in 49 or 99 cents bonus
  - Rounding quirks
- [ ] Add interaction effects between factors:
  - Trip length × efficiency interactions
  - Spending × mileage interactions
- [ ] Analyze highest-error cases from previous iteration
- [ ] Implement special case handling for outliers
- [ ] Run `eval.sh` and target accuracy improvement

**Target**: 85-90% exact matches

---

## 🤖 **Phase 3: Residual Modeling (2 hours)**
**Goal**: Squeeze out remaining errors with light ML

### **Hour 6: Residual Analysis**
**Tasks:**
- [ ] Calculate residuals: `actual_reimbursement - rule_based_prediction`
- [ ] Analyze residual patterns:
  - Plot residuals vs. input variables
  - Identify systematic biases
  - Look for non-linear patterns
- [ ] Feature engineering for ML model:
  - Interaction terms (days × miles, receipts × efficiency)
  - Polynomial features
  - Categorical encodings for trip length ranges
- [ ] Train lightweight model on residuals:
  - Decision Trees or Linear Regression (easy to export)
  - **Export coefficients/rules to plain Python data structures**
- [ ] Combine predictions: `final = rule_based + residual_model`

**Target**: Model ready for integration

### **Hour 7: Final Iteration**
**Tasks:**
- [ ] Integrate residual model with rule-based system
- [ ] Run `eval.sh`, target 95%+ exact matches
- [ ] Deep dive on remaining high-error cases:
  - Look for missed patterns
  - Consider additional special cases
- [ ] Make final rule tweaks based on error analysis
- [ ] Validate model stability across different data subsets
- [ ] Generate `private_results.txt` for submission

**Target**: 95%+ exact matches

---

## ✨ **Phase 4: Polish + Documentation (1 hour)**
**Goal**: Clean submission package

### **Hour 8: Finalization**
**Tasks:**
- [ ] Code cleanup and optimization:
  - Clear variable names and comments
  - Efficient calculation order
  - Error handling for edge cases
- [ ] Ensure `run.sh` interface works perfectly:
  - Test with various input formats
  - Verify single number output with `Decimal.quantize(0.01, ROUND_HALF_UP)`
  - Check execution time (<5 seconds requirement)
- [ ] **Clean environment test**: 15min dry-run in fresh virtualenv (stdlib only)
- [ ] Document discovered business logic:
  - Summary of implemented rules
  - Explanation of "bugs" preserved
  - Model performance metrics
- [ ] Final verification runs:
  - Complete eval.sh run
  - Spot check private_results.txt format
- [ ] Prepare submission materials

**Deliverables:**
- Clean, documented code
- Working `run.sh` script
- `private_results.txt` ready for submission
- Business logic documentation

---

## 🔧 **Implementation Technical Notes**

### **Python Structure**
```
calculate_reimbursement.py  # Main calculation logic (stdlib only!)
run.sh                     # Simple wrapper script  
analysis.py               # EDA and model development (heavy imports OK)
model_coefficients.py     # Exported ML model as simple data structures
```

### **Key Libraries & Environment Constraints**
- **Development**: `pandas`, `numpy`, `matplotlib/seaborn`, `scikit-learn`
- **Production (`run.sh`)**: `decimal` module ONLY (stdlib)
- **Critical**: Grader may have no external packages - keep `run.sh` minimal

### **Testing Strategy**
- After each major change: run `./eval.sh`
- Keep accuracy progression log
- Focus on high-error cases for iteration
- **Hold-out validation**: Reserve 200 cases to check overfitting

### **Rule Discovery Priority Order**
1. Base per diem (universal)
2. Mileage tiers (affects most cases)
3. Receipt processing (complex but important)
4. 5-day bonus (specific but mentioned frequently)
5. Efficiency bonuses (optimization opportunity)
6. Spending thresholds (penalty avoidance)
7. Edge cases and "bugs" (final accuracy gains)

### **Residual Modeling Strategy**
- Only proceed if rule-based plateaus <90%
- Use simple ensemble methods (Decision Trees, Linear Regression)
- **Export to stdlib**: Convert trained model to plain Python coefficients/lookup tables
- Validate generalization on 200-case holdout set

---

## ✅ **Success Metrics by Phase**

| Phase | Target Accuracy | Key Milestone |
|-------|----------------|---------------|
| Phase 1 | N/A | Clear hypothesis list |
| Phase 2.1 | 50-60% | Core framework working |
| Phase 2.2 | 70-80% | Major patterns implemented |
| Phase 2.3 | 85-90% | Edge cases handled |
| Phase 3.1 | N/A | Residual model trained |
| Phase 3.2 | 95%+ | Final accuracy target |
| Phase 4 | 95%+ | Submission ready |

---

## 🚨 **Risk Mitigation**

### **If Accuracy Plateaus <95%:**
- Focus on top 20 highest-error cases
- Consider additional interaction effects
- Check for data entry errors or outliers
- Implement case-by-case special handling if needed

### **If Time Runs Short:**
- Prioritize rule refinement over residual modeling
- Ensure basic framework is robust
- Document known limitations
- Submit best available solution

### **If Technical Issues:**
- Keep simpler backup approaches ready
- Test `run.sh` interface frequently
- Validate number precision throughout

---

---

## ⚠️ **Critical Constraints & Gotchas**

### **Environment Limitations**
- **Grader constraint**: May only have Python stdlib available
- **Import performance**: Heavy libraries in `run.sh` will timeout (1000 calls)
- **Solution**: Keep analysis separate, export models to plain Python data

### **Arithmetic Precision**
- **Rounding mode**: Use `ROUND_HALF_UP` (not banker's rounding) 
- **Timing**: Always round BEFORE printing to avoid $0.005 → $0.01 drift
- **Legacy compatibility**: Old systems often used "round half up"

### **Overfitting Risks**
- **Small dataset**: Only 1,000 public cases can easily memorize noise
- **Mitigation**: Reserve 200-case holdout for validation
- **Export strategy**: Convert ML models to simple lookup tables/coefficients

---

## 🔑 **Final Success Checklist**

Before submission, verify:

1. ✅ `run.sh` finishes **1,000 cases in <5s** with **network disabled**
2. ✅ `shellcheck run.sh` returns no warnings (optional but clean)
3. ✅ `python -m py_compile calculate_reimbursement.py` passes (syntax guard)
4. ✅ `eval.sh` shows **≥95% exact matches**; worst 10 cases have **<$1.00 error**
5. ✅ README contains 5-line "How it works" and rounding mode note

---

## 📋 **Pre-Execution Checklist**

- [ ] Python environment with required libraries
- [ ] `eval.sh` script tested and working
- [ ] Public cases data accessible
- [ ] Text editor/IDE ready for development
- [ ] Time blocked for focused work
- [ ] Plan reviewed and understood

**Ready to execute when given the go-ahead!** 