import csv
import itertools
import os

# Define the settings and their values
settings = {
    "NUM_STEPS": [500, 5000, 15000],
    "SEARCH_WIDTH": [0.25, 0.5, 0.75],
    "RANDOM_SEED": ["0000 0000 0000 0001", "0000 0000 0000 0002", "0000 0000 0000 0003"],
    "ENERGY_CUTOFF": [2.5, 5, 10],
    "DISTANCE_TOLERANCE": [25, 50, 100],
    "ANGLE_TOLERANCE": [5, 15, 30],
    "ENERGY_TOLERANCE": [0.1, 1, 10]
}

# Get all combinations of the settings
combinations = list(itertools.product(*settings.values()))

# Path to save the CSV file
csv_path = os.path.join(os.getcwd(), "experiments_to_run.csv")

# Write combinations to a CSV file
with open(csv_path, mode='w', newline='') as file:
    writer = csv.writer(file)

    # Write the header
    writer.writerow(settings.keys())

    # Write the setting combinations
    for combo in combinations:
        writer.writerow(combo)

print(f"CSV file saved at: {csv_path}")
print(f"Total experiments to run: {len(combinations)}")
