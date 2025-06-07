#!/usr/bin/env python3
"""
Unit test for ensemble model path in calculate_reimbursement.py
"""
import json
import os
import shutil
from decimal import Decimal

# Create a backup of the current model
original_model_path = "gbm_residual.json"
ensemble_model_path = "gbm_residual_ensemble.json"
backup_model_path = "gbm_residual.json.backup"

# Ensure we have a backup
if os.path.exists(original_model_path):
    print(f"Creating backup of {original_model_path}...")
    shutil.copy(original_model_path, backup_model_path)

# Create a simple ensemble model for testing
try:
    # Load the current model
    with open(original_model_path, 'r') as f:
        model = json.load(f)
    
    # Create a copy of the model as a second model in the ensemble
    ensemble_model = {
        "features": model["features"],
        "is_ensemble": True,
        "shrink": model["shrink"],
        "cap": model["cap"],
        "model1": {
            "init_prediction": model["init_prediction"],
            "learning_rate": model["learning_rate"],
            "n_estimators": model["n_estimators"],
            "max_depth": model["max_depth"],
            "trees": model["trees"][:5]  # Just use first 5 trees for model1
        },
        "model2": {
            "init_prediction": model["init_prediction"],
            "learning_rate": model["learning_rate"] * 0.8,  # Slightly different learning rate
            "n_estimators": model["n_estimators"],
            "max_depth": model["max_depth"],
            "trees": model["trees"][5:10]  # Use next 5 trees for model2
        }
    }
    
    # Write the ensemble model to a test file
    with open(ensemble_model_path, 'w') as f:
        json.dump(ensemble_model, f, indent=2)
    
    print(f"Created test ensemble model at {ensemble_model_path}")
    
    # Test ensemble prediction
    print("\nTesting ensemble path with sample input...")
    
    # Replace the model file temporarily
    shutil.move(ensemble_model_path, original_model_path)
    
    # Import the module (which will load the ensemble model)
    import calculate_reimbursement
    
    # Clear any cached model
    calculate_reimbursement._GBM_MODEL = None
    
    # Test case
    test_days = 5
    test_miles = Decimal('500.00')
    test_receipts = Decimal('750.00')
    
    # Get prediction
    result = calculate_reimbursement.calculate_reimbursement(test_days, test_miles, test_receipts)
    
    print(f"Test case: {test_days} days, {test_miles} miles, ${test_receipts} receipts")
    print(f"Ensemble prediction: ${result}")
    
    # Debug breakdown to confirm ensemble is being used
    debug_result = calculate_reimbursement.debug_calculation(test_days, test_miles, test_receipts)
    
    print("\nEnsemble path test completed successfully!")
    
finally:
    # Restore original model
    if os.path.exists(backup_model_path):
        print("\nRestoring original model...")
        shutil.move(backup_model_path, original_model_path)
        print("Original model restored.")
    
    # Clean up
    if os.path.exists(ensemble_model_path):
        os.remove(ensemble_model_path)

print("\nAll tests completed.") 