#!/usr/bin/env python3
"""
Phase 3: Train GradientBoostingRegressor for residual modeling
Export to lightweight JSON for runtime integration
"""
import json
import pandas as pd
import numpy as np
from decimal import Decimal
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from calculate_reimbursement import calculate_reimbursement

def build_residual_dataset():
    """Build residual dataset from training slice (first 800 cases)"""
    print("Loading public cases data...")
    with open('public_cases.json') as f:
        data = json.load(f)
    
    print("Building residual dataset...")
    rows = []
    for i, case in enumerate(data[:800]):  # training slice
        if i % 100 == 0:
            print(f"  Processing case {i}/800...")
            
        d = case['input']
        
        # Get rule-based prediction
        rule_pred = float(calculate_reimbursement(
            d['trip_duration_days'],
            Decimal(str(d['miles_traveled'])),
            Decimal(str(d['total_receipts_amount']))
        ))
        
        # Calculate residual
        expected = case['expected_output']
        residual = expected - rule_pred
        
        # Create feature set
        row = {
            'trip_duration_days': d['trip_duration_days'],
            'miles_traveled': d['miles_traveled'],
            'total_receipts_amount': d['total_receipts_amount'],
            'miles_per_day': d['miles_traveled'] / d['trip_duration_days'],
            'receipts_per_day': d['total_receipts_amount'] / d['trip_duration_days'],
            'expected_output': expected,
            'rule_prediction': rule_pred,
            'residual': residual
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    print(f"Dataset built: {len(df)} rows")
    print(f"Residual stats: mean={df['residual'].mean():.2f}, std={df['residual'].std():.2f}")
    print(f"Residual range: [{df['residual'].min():.2f}, {df['residual'].max():.2f}]")
    
    return df

def train_gbm(df):
    """Train GradientBoostingRegressor on residuals"""
    print("\nTraining GradientBoostingRegressor...")
    
    # Define features
    features = [
        'trip_duration_days', 'miles_traveled', 'total_receipts_amount',
        'miles_per_day', 'receipts_per_day'
    ]
    
    X = df[features]
    y = df['residual']
    
    print(f"Feature matrix: {X.shape}")
    print(f"Target range: [{y.min():.2f}, {y.max():.2f}]")
    
    # Train GBM with conservative settings
    gbm = GradientBoostingRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        subsample=0.8,  # Additional regularization
        max_features='sqrt'
    )
    
    gbm.fit(X, y)
    
    # Evaluate on training set
    train_pred = gbm.predict(X)
    train_mae = mean_absolute_error(y, train_pred)
    train_rmse = np.sqrt(mean_squared_error(y, train_pred))
    
    print(f"Training MAE: ${train_mae:.2f}")
    print(f"Training RMSE: ${train_rmse:.2f}")
    print(f"Training R²: {gbm.score(X, y):.3f}")
    
    return gbm, features

def export_gbm_to_json(gbm, features, filename='gbm_residual.json'):
    """Export GBM to lightweight JSON format for runtime use"""
    print(f"\nExporting GBM to {filename}...")
    
    trees = []
    for estimator in gbm.estimators_[:, 0]:  # Only one output (regression)
        tree = estimator.tree_
        nodes = []
        
        for i in range(tree.node_count):
            node = {
                'feat': int(tree.feature[i]),      # -2 for leaf nodes
                'threshold': float(tree.threshold[i]),
                'left': int(tree.children_left[i]),   # -1 for leaf nodes
                'right': int(tree.children_right[i]), # -1 for leaf nodes  
                'value': float(tree.value[i][0][0])   # prediction value
            }
            nodes.append(node)
        
        trees.append(nodes)
    
    model_data = {
        'features': features,
        'trees': trees,
        'learning_rate': gbm.learning_rate,
        'n_estimators': gbm.n_estimators,
        'max_depth': gbm.max_depth,
        'init_prediction': float(gbm._raw_predict_init(np.array([[0, 0, 0, 0, 0]]))[0])  # Initial prediction
    }
    
    with open(filename, 'w') as f:
        json.dump(model_data, f, indent=2)
    
    # Check file size
    import os
    file_size = os.path.getsize(filename)
    print(f"Model exported: {file_size} bytes ({file_size/1024:.1f} KB)")
    
    return model_data

def validate_export(gbm, features, df_sample, model_data):
    """Validate that exported model gives same predictions as sklearn"""
    print("\nValidating export...")
    
    # Test on first 5 rows
    test_rows = df_sample.head(5)
    X_test = test_rows[features]
    
    # Get sklearn predictions
    sklearn_pred = gbm.predict(X_test)
    
    # Get JSON model predictions (implement simple tree walker)
    json_pred = []
    for _, row in X_test.iterrows():
        feats = [
            row['trip_duration_days'], 
            float(row['miles_traveled']), 
            float(row['total_receipts_amount']),
            float(row['miles_per_day']), 
            float(row['receipts_per_day'])
        ]
        
        # Start with initial prediction
        total = model_data['init_prediction']
        
        # Add predictions from each tree
        for tree in model_data['trees']:
            idx = 0
            # Walk down the tree until we hit a leaf
            while True:
                node = tree[idx]
                # Check if this is a leaf node (children are -1)
                if node['left'] == -1 and node['right'] == -1:
                    # This is a leaf node, add its value (scaled by learning rate)
                    total += node['value'] * model_data['learning_rate']
                    break
                else:
                    # This is an internal node, decide which child to follow
                    if feats[node['feat']] <= node['threshold']:
                        idx = node['left']
                    else:
                        idx = node['right']
        
        json_pred.append(total)
    
    json_pred = np.array(json_pred)
    
    # Compare predictions
    max_diff = np.max(np.abs(sklearn_pred - json_pred))
    print(f"Max prediction difference: {max_diff:.6f}")
    
    if max_diff < 1e-6:  # Relaxed tolerance for floating point
        print("✅ Export validation PASSED")
    else:
        print("❌ Export validation FAILED")
        print("sklearn predictions:", sklearn_pred[:3])
        print("JSON predictions:", json_pred[:3])
        print("Difference:", sklearn_pred[:3] - json_pred[:3])
    
    return max_diff < 1e-6

def main():
    """Main training pipeline"""
    print("=== Phase 3: GBM Residual Training ===")
    
    # Step 1: Build residual dataset
    df = build_residual_dataset()
    
    # Step 2: Train GBM
    gbm, features = train_gbm(df)
    
    # Step 3: Export to JSON
    model_data = export_gbm_to_json(gbm, features)
    
    # Step 4: Validate export
    is_valid = validate_export(gbm, features, df, model_data)
    
    if is_valid:
        print("\n🎉 GBM training and export completed successfully!")
        print("Next step: Integrate gbm_residual.json into calculate_reimbursement.py")
    else:
        print("\n❌ Export validation failed - check implementation")
    
    return df, gbm, features

if __name__ == "__main__":
    df, gbm, features = main() 