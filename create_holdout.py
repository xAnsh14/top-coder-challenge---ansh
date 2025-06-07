#!/usr/bin/env python3
import json
import random

random.seed(42)

with open('public_cases.json', 'r') as f:
    data = json.load(f)

# Create 200-case holdout
holdout_indices = random.sample(range(len(data)), 200)
holdout_data = [data[i] for i in holdout_indices]

with open('dev_holdout.json', 'w') as f:
    json.dump(holdout_data, f, indent=2)

print(f'Created holdout set: 200 cases')
print(f'Training set: {len(data) - 200} cases') 