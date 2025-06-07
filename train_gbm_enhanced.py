#!/usr/bin/env python3
"""
Phase 3 Enhanced: Advanced GBM residual modeling with CV grid search and feature engineering
"""
import json
import pandas as pd
import numpy as np
from decimal import Decimal
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error
from calculate_reimbursement import calculate_reimbursement
import itertools

def build_enhanced_residual_dataset():
    """Build enhanced residual dataset with interaction features and outlier trimming"""
    print("Loading public cases data...")
    with open('public_cases.json') as f:
        data = json.load(f)
    
    print("Building enhanced residual dataset...")
    rows = []
    for i, case in enumerate(data[:800]):  # training slice
        if i % 100 == 0:
            print(f"  Processing case {i}/800...")
            
        d = case['input']
        
        # Get rule-based prediction (without ML residual)
        rule_pred = float(calculate_reimbursement(
            d['trip_duration_days'],
            Decimal(str(d['miles_traveled'])),
            Decimal(str(d['total_receipts_amount']))
        ))
        
        # Calculate residual
        expected = case['expected_output']
        residual = expected - rule_pred
        
        # OUTLIER TRIMMING: Cap residuals at ±$1000 to reduce leverage of weird cases
        residual = max(min(residual, 1000.0), -1000.0)
        
        # Base features
        days = d['trip_duration_days']
        miles = d['miles_traveled']
        receipts = d['total_receipts_amount']
        miles_per_day = miles / days
        receipts_per_day = receipts / days
        
        # ENHANCED FEATURES: Interaction terms and boolean flags
        receipts_per_mile = receipts / miles if miles > 0 else 0
        high_mileage_flag = 1 if miles > 700 else 0
        high_receipts_flag = 1 if receipts > 1500 else 0
        single_day_flag = 1 if days == 1 else 0
        long_trip_flag = 1 if days >= 7 else 0
        efficiency_ratio = miles_per_day / 150.0  # Normalized around typical 150 mi/day
        
        # Create enhanced feature set
        row = {
            # Base features
            'trip_duration_days': days,
            'miles_traveled': miles,
            'total_receipts_amount': receipts,
            'miles_per_day': miles_per_day,
            'receipts_per_day': receipts_per_day,
            
            # Interaction features
            'receipts_per_mile': receipts_per_mile,
            'efficiency_ratio': efficiency_ratio,
            
            # Boolean flags (trees love these)
            'high_mileage_flag': high_mileage_flag,
            'high_receipts_flag': high_receipts_flag,
            'single_day_flag': single_day_flag,
            'long_trip_flag': long_trip_flag,
            
            # Target
            'expected_output': expected,
            'rule_prediction': rule_pred,
            'residual': residual
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    print(f"Enhanced dataset built: {len(df)} rows")
    print(f"Residual stats (after trimming): mean={df['residual'].mean():.2f}, std={df['residual'].std():.2f}")
    print(f"Residual range: [{df['residual'].min():.2f}, {df['residual'].max():.2f}]")
    
    return df

def cv_grid_search(df):
    """5-fold CV grid search for optimal hyperparameters"""
    print("\nRunning 5-fold CV grid search...")
    
    # Enhanced feature set
    features = [
        'trip_duration_days', 'miles_traveled', 'total_receipts_amount',
        'miles_per_day', 'receipts_per_day', 'receipts_per_mile', 'efficiency_ratio',
        'high_mileage_flag', 'high_receipts_flag', 'single_day_flag', 'long_trip_flag'
    ]
    
    X = df[features]
    y = df['residual']
    
    # Grid search parameters
    param_grid = {
        'n_estimators': [40, 60, 80],
        'learning_rate': [0.05, 0.1],
        'max_depth': [2, 3]
    }
    
    best_score = float('inf')
    best_params = None
    results = []
    
    # 5-fold cross validation
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    total_combinations = len(list(itertools.product(*param_grid.values())))
    print(f"Testing {total_combinations} parameter combinations...")
    
    for i, (n_est, lr, depth) in enumerate(itertools.product(*param_grid.values())):
        print(f"  {i+1}/{total_combinations}: n_estimators={n_est}, lr={lr}, max_depth={depth}")
        
        gbm = GradientBoostingRegressor(
            n_estimators=n_est,
            learning_rate=lr,
            max_depth=depth,
            random_state=42,
            subsample=0.8,
            max_features='sqrt'
        )
        
        # Cross-validation scoring (negative MAE)
        cv_scores = cross_val_score(gbm, X, y, cv=kf, scoring='neg_mean_absolute_error')
        mean_cv_mae = -cv_scores.mean()
        std_cv_mae = cv_scores.std()
        
        results.append({
            'n_estimators': n_est,
            'learning_rate': lr,
            'max_depth': depth,
            'cv_mae': mean_cv_mae,
            'cv_std': std_cv_mae
        })
        
        print(f"    CV MAE: ${mean_cv_mae:.2f} ± ${std_cv_mae:.2f}")
        
        if mean_cv_mae < best_score:
            best_score = mean_cv_mae
            best_params = {'n_estimators': n_est, 'learning_rate': lr, 'max_depth': depth}
    
    print(f"\n🎯 Best CV MAE: ${best_score:.2f}")
    print(f"🎯 Best parameters: {best_params}")
    
    return best_params, features, results

def train_enhanced_gbm(df, best_params, features):
    """Train final model with best parameters"""
    print(f"\nTraining final model with best parameters...")
    
    X = df[features]
    y = df['residual']
    
    # Train with best parameters + additional regularization
    gbm = GradientBoostingRegressor(
        **best_params,
        random_state=42,
        subsample=0.8,
        max_features='sqrt'
    )
    
    gbm.fit(X, y)
    
    # Evaluate on training set
    train_pred = gbm.predict(X)
    train_mae = mean_absolute_error(y, train_pred)
    train_rmse = np.sqrt(mean_squared_error(y, train_pred))
    
    print(f"Final training MAE: ${train_mae:.2f}")
    print(f"Final training RMSE: ${train_rmse:.2f}")
    print(f"Final training R²: {gbm.score(X, y):.3f}")
    
    # Feature importance
    print("\nTop feature importances:")
    importance_df = pd.DataFrame({
        'feature': features,
        'importance': gbm.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for _, row in importance_df.head(8).iterrows():
        print(f"  {row['feature']}: {row['importance']:.3f}")
    
    return gbm

def export_enhanced_gbm(gbm, features, filename='gbm_residual_enhanced.json'):
    """Export enhanced GBM to JSON with additional metadata"""
    print(f"\nExporting enhanced GBM to {filename}...")
    
    trees = []
    for estimator in gbm.estimators_[:, 0]:
        tree = estimator.tree_
        nodes = []
        
        for i in range(tree.node_count):
            node = {
                'feat': int(tree.feature[i]),
                'threshold': float(tree.threshold[i]),
                'left': int(tree.children_left[i]),
                'right': int(tree.children_right[i]),
                'value': float(tree.value[i][0][0])
            }
            nodes.append(node)
        
        trees.append(nodes)
    
    model_data = {
        'features': features,
        'trees': trees,
        'learning_rate': gbm.learning_rate,
        'n_estimators': gbm.n_estimators,
        'max_depth': gbm.max_depth,
        'init_prediction': float(gbm._raw_predict_init(np.zeros((1, len(features))))[0]),
        'feature_importances': gbm.feature_importances_.tolist(),
        'version': 'enhanced_v2'
    }
    
    with open(filename, 'w') as f:
        json.dump(model_data, f, indent=2)
    
    import os
    file_size = os.path.getsize(filename)
    print(f"Enhanced model exported: {file_size} bytes ({file_size/1024:.1f} KB)")
    
    return model_data

def validate_enhanced_export(gbm, features, df_sample, model_data):
    """Validate enhanced model export"""
    print("\nValidating enhanced export...")
    
    test_rows = df_sample.head(5)
    X_test = test_rows[features]
    
    sklearn_pred = gbm.predict(X_test)
    
    json_pred = []
    for _, row in X_test.iterrows():
        feature_vector = [float(row[f]) for f in features]
        
        total = model_data['init_prediction']
        
        for tree in model_data['trees']:
            idx = 0
            while True:
                node = tree[idx]
                if node['left'] == -1 and node['right'] == -1:
                    total += node['value'] * model_data['learning_rate']
                    break
                else:
                    if feature_vector[node['feat']] <= node['threshold']:
                        idx = node['left']
                    else:
                        idx = node['right']
        
        json_pred.append(total)
    
    json_pred = np.array(json_pred)
    max_diff = np.max(np.abs(sklearn_pred - json_pred))
    
    print(f"Max prediction difference: {max_diff:.8f}")
    
    if max_diff < 1e-6:
        print("✅ Enhanced export validation PASSED")
        return True
    else:
        print("❌ Enhanced export validation FAILED")
        return False

def main():
    """Enhanced training pipeline"""
    print("=== Phase 3 Enhanced: Advanced GBM Training ===")
    
    # Step 1: Build enhanced dataset with outlier trimming
    df = build_enhanced_residual_dataset()
    
    # Step 2: CV grid search for optimal parameters
    best_params, features, cv_results = cv_grid_search(df)
    
    # Step 3: Train final model
    gbm = train_enhanced_gbm(df, best_params, features)
    
    # Step 4: Export enhanced model
    model_data = export_enhanced_gbm(gbm, features)
    
    # Step 5: Validate export
    is_valid = validate_enhanced_export(gbm, features, df, model_data)
    
    if is_valid:
        print("\n🎉 Enhanced GBM training completed successfully!")
        print("🔥 Ready for integration with shrink/clip post-processing!")
        
        # Save CV results for analysis
        cv_df = pd.DataFrame(cv_results)
        cv_df.to_csv('cv_results.csv', index=False)
        print("📊 CV results saved to cv_results.csv")
        
    else:
        print("\n❌ Enhanced export validation failed")
    
    return df, gbm, features, best_params

if __name__ == "__main__":
    df, gbm, features, best_params = main() 