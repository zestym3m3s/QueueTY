import os
import csv
import shutil  # For copying the SDF batch file
import numpy as np
from scipy import stats
from rdkit import Chem
import constants  # Import your constants.py where vconf_batch_sdf_path and experimental_vconf_settings are defined

# Path to the experiments directory
experiments_dir = os.path.join(os.path.dirname(constants.vconf_batch_sdf_path), "Experiments")

# Ensure the Experiments directory exists
if not os.path.exists(experiments_dir):
    os.makedirs(experiments_dir)


# Function to get the next experiment number
def get_next_experiment_number():
    existing_files = os.listdir(experiments_dir)
    experiment_numbers = [int(f.split('_')[1].split('.')[0]) for f in existing_files if f.startswith('Experiment_')]
    return max(experiment_numbers, default=0) + 1


# Load conformers from the SDF file specified in constants.py
sdf_path = constants.vconf_batch_sdf_path
if not os.path.exists(sdf_path):
    raise FileNotFoundError(f"File not found: {sdf_path}")

# Copy the SDF file to the Experiments folder with a new name
experiment_number = get_next_experiment_number()
new_sdf_path = os.path.join(experiments_dir, f"Experiment_{experiment_number}.sdf")
shutil.copy(sdf_path, new_sdf_path)

# Load the molecules from the SDF file
suppl = Chem.SDMolSupplier(sdf_path, removeHs=False, sanitize=False)
conformers = [mol for mol in suppl if mol is not None]

if not conformers:
    raise ValueError("No valid molecules found in the SDF file.")


# Function to extract energy from the SDF data
def get_energy(mol):
    energy = float(mol.GetProp("Energy")) if mol.HasProp("Energy") else None
    return energy


# Function to calculate statistics on energies
def calculate_energy_stats(conformers):
    energies = [get_energy(mol) for mol in conformers if get_energy(mol) is not None]
    if not energies:
        return None, None, None, None, None, []

    min_energy = min(energies)
    max_energy = max(energies)
    avg_energy = np.mean(energies)
    slope, intercept, r_value, _, _ = stats.linregress(range(len(energies)), energies)

    return min_energy, max_energy, avg_energy, slope, r_value ** 2, energies


# Function to calculate the number of unique conformers (unique energies)
def calculate_unique_conformers(conformers):
    unique_energies = set(get_energy(mol) for mol in conformers if get_energy(mol) is not None)
    return len(unique_energies)


# Function to append data to the CSV
def append_to_csv(sdf_path, data, headers, energies):
    csv_path = os.path.join(os.path.dirname(sdf_path), "conformer_data.csv")

    # Check if the file exists to determine if headers need to be written
    file_exists = os.path.isfile(csv_path)

    # Ensure the energies start from column T (20th column)
    energy_headers = [f"Conformer_{i + 1}_Energy" for i in range(len(energies))]
    energy_data = energies + [''] * (len(energy_headers) - len(energies))  # Pad with empty strings if necessary

    # Append data to the CSV
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write headers only if the file is new
        if not file_exists:
            writer.writerow(headers + energy_headers)

        # Append the new data (including energies starting at column T)
        writer.writerow(data + energy_data)


# Main function to run the analysis
def run_analysis(conformers):
    # Calculate energy statistics and unique conformers
    min_energy, max_energy, avg_energy, slope, r_squared, energies = calculate_energy_stats(conformers)
    num_unique_conformers = calculate_unique_conformers(conformers)

    # Collect experimental settings from constants.py
    exp_settings = constants.experimental_vconf_settings
    num_steps = exp_settings.get('NUM_STEPS')
    search_width = exp_settings.get('SEARCH_WIDTH')
    random_seeds = exp_settings.get('RANDOM_SEEDS')
    energy_cutoff = exp_settings.get('ENERGY_CUTOFF')
    distance_tolerance = exp_settings.get('DISTANCE_TOLERANCE')
    angle_tolerance = exp_settings.get('ANGLE_TOLERANCE')
    energy_tolerance = exp_settings.get('ENERGY_TOLERANCE')

    # Prepare data to be written to the CSV, including the experiment number
    data = [
        experiment_number,  # Add experiment number as the first column
        num_steps, search_width, random_seeds, energy_cutoff, distance_tolerance,
        angle_tolerance, energy_tolerance, min_energy, max_energy, avg_energy,
        num_unique_conformers, slope, r_squared
    ]

    # Headers for the CSV file (ensure each column is uniquely labeled)
    headers = [
        "Experiment Number",  # Add Experiment Number as the first header
        "NUM_STEPS", "SEARCH_WIDTH", "RANDOM_SEEDS", "ENERGY_CUTOFF", "DISTANCE_TOLERANCE",
        "ANGLE_TOLERANCE", "ENERGY_TOLERANCE", "Min Energy", "Max Energy", "Avg Energy",
        "Unique Conformers", "Energy Slope", "R^2"
    ]

    # Append the data to the CSV file, including energy values starting from column T
    append_to_csv(sdf_path, data, headers, energies)


# Run the analysis
run_analysis(conformers)
