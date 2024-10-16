import os
import subprocess
import pandas as pd
import shutil  # For copying the SDF file
import numpy as np
from scipy import stats
from rdkit import Chem
from rdkit.Chem import AllChem
import itertools  # To generate the combinations of settings
import constants  # Import constants for vconf settings
import csv

# Define the path to the Experiments directory
experiments_dir = os.path.join(os.path.dirname(constants.vconf_batch_sdf_path), "Experiments")

# Ensure the Experiments directory exists
if not os.path.exists(experiments_dir):
    os.makedirs(experiments_dir)

# Define the settings for the experiment
settings_options = {
    "NUM_STEPS": [5000],  # [500, 5000, 15000],
    "SEARCH_WIDTH": [0.5],  # [0.25, 0.5, 0.75],
    "RANDOM_SEED": ["0000 0000 0000 0001", "0000 0000 0000 0002", "0000 0000 0000 0003"],  # Your custom seeds
    "ENERGY_CUTOFF": [5],  # [2.5, 5, 10],
    "DISTANCE_TOLERANCE": [1],  # [0.1, 1, 10],
    "ANGLE_TOLERANCE": [5],  # [5, 15, 30],
    "ENERGY_TOLERANCE": [0.5]  # [0.1, 1, 10]
}

# Generate all combinations of the settings
combinations = list(itertools.product(*settings_options.values()))


def get_next_experiment_number():
    """ Get the next experiment number based on existing files. """
    existing_files = os.listdir(experiments_dir)
    experiment_numbers = [int(f.split('_')[1].split('.')[0]) for f in existing_files if f.startswith('Experiment_')]
    return max(experiment_numbers, default=0) + 1


def build_vconf_command(settings, sdf_path):
    """
    Build the command line string to run VConf with the specified parameters.
    This ensures that only the experiment-specific settings are modified while the rest are taken from constants.py.
    """
    # Load default settings from experimental_vconf_settings
    vconf_settings = constants.experimental_vconf_settings.copy()

    # Update only the specific settings for the current experiment
    vconf_settings.update(settings)

    sdf_path = vconf_settings["SDF_FILENAME"]
    log_filename = vconf_settings["OUTPUT_LOG"]
    out_filename = vconf_settings["OUTPUT_SDF"]

    # Build the base command
    command = [
        constants.vconf_path,
        f'{sdf_path}',
        "-f", str(vconf_settings['FIRST_MOLECULE']),
        "-l", str(vconf_settings['LAST_MOLECULE']),
        "-ff", vconf_settings['FORCEFIELD'],
        "-m", vconf_settings['SEARCH_MODE'],
        "-ns", str(vconf_settings['NUM_STEPS']),
        "-log", log_filename,
        "-out", out_filename
    ]

    # Optional flags based on settings
    if vconf_settings['USE_GENERALIZED_BORN_SOLVATION']:
        command.append("-gb")

    if vconf_settings['RESTRAINED_ATOMS'] and vconf_settings['RESTRAINED_ATOMS'] != "None":
        restrained_atoms = vconf_settings['RESTRAINED_ATOMS'].split()
        if len(restrained_atoms) >= 3:
            command.extend(["-ra"] + restrained_atoms)
        else:
            print("Warning: Less than 3 restrained atoms provided. Skipping the -ra option.")
    else:
        print("No restrained atoms provided.")

    # Adding your provided RANDOM_SEED
    random_seed = settings['RANDOM_SEED'].split()
    if len(random_seed) == 4:
        command.extend(["-seed"] + random_seed)
    else:
        command.append("-seed ran")

    # Adding additional command arguments from the settings
    command.extend([
        "-sw", str(vconf_settings['SEARCH_WIDTH']),
        "-fc" if vconf_settings['FORMAL_CHARGE'] else "",
        "-snp" if vconf_settings['SULFONAMIDE_NITROGEN'] else "",
        "-cp", vconf_settings['CHIRAL_PRIORITY'],
        "-sr", vconf_settings['STEREOCHEMISTRY_RESTRICTIONS'],
        "-dc", str(vconf_settings['DIELECTRIC_COEFFICIENT']),
        "-nlp" if vconf_settings['NITROGEN_LONE_PAIR'] else "",
        "-rl", str(vconf_settings['RESONANCE_LIMIT']),
        "-sub", vconf_settings['SUBSTITUENTS_LEVEL'],
        "-minrs", str(vconf_settings['MIN_RING_SEARCH_STEPS']),
        "-addrs", str(vconf_settings['ADD_RING_SEARCH_STEPS']),
        "-maxrc", str(vconf_settings['MAX_RING_CONFS']),
        "-maxra", str(vconf_settings['MAX_RING_ATOMS']),
        "-re", str(vconf_settings['RING_ENERGY_CUTOFF']),
        "-klr" if vconf_settings['KEEP_LOWEST_ENERGY_RING_COMBINATION'] else "",
        "-e", str(vconf_settings['ENERGY_CUTOFF']),
        "-et", str(vconf_settings['ENERGY_TOLERANCE']),
        "-dt", str(vconf_settings['DISTANCE_TOLERANCE']),
        "-at", str(vconf_settings['ANGLE_TOLERANCE']),
        "-nf" if vconf_settings['DO_NOT_FILTER_OUTPUT'] else "",
        "-u" if vconf_settings['KEEP_UNFILTERED_CONFORMATIONS'] else "",
        "-nt" if vconf_settings['NO_TIME_LIMITS'] else "",
        "-ts", str(vconf_settings['SETUP_TIME_LIMIT']),
        "-tf", str(vconf_settings['FILTER_TIME_LIMIT'])
    ])

    # Remove any empty strings from the command list
    command = [arg for arg in command if arg]

    # Print the fully built command
    print(f"Built VConf command: {' '.join(command)}")

    return command


def run_vconf_command(command, output_dir):
    """ Run the VConf command and capture output. """
    process = subprocess.Popen(
        command,
        cwd=output_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error running VConf: {stderr}")
    else:
        print(f"VConf output: {stdout}")

    print("VConf processing completed.")


def read_tsv_and_generate_sdf(tsv_file_path, sdf_path):
    """ Read a TSV file and generate an SDF file from the SMILES strings contained within. """
    df = pd.read_csv(tsv_file_path, sep='\t', header=None)
    writer = Chem.SDWriter(sdf_path)

    molecule_names = []
    for index, row in df.iterrows():
        mol = Chem.MolFromSmiles(row.iloc[0])  # First column is SMILES
        if mol:
            mol = Chem.AddHs(mol)  # Add hydrogens
            AllChem.ETKDGv3()
            AllChem.EmbedMolecule(mol, randomSeed=42)
            AllChem.UFFOptimizeMolecule(mol)  # Optimize the geometry to ensure it's properly 3D
            mol.SetProp("_Name", row.iloc[1])  # Second column is the molecule name
            writer.write(mol)
            molecule_names.append(row.iloc[1])
        else:
            print(f"Error processing SMILES: {row.iloc[0]}")

    writer.close()
    print(f"SDF file {sdf_path} generated successfully.")
    print(f"List of molecule names: {molecule_names}")
    return molecule_names  # Return the list of molecule names


def analyze_sdf(sdf_path, experiment_number):
    """ Analyze the resulting SDF file and calculate statistics. """
    # Load the SDF file
    suppl = Chem.SDMolSupplier(sdf_path, removeHs=False, sanitize=False)
    conformers = [mol for mol in suppl if mol is not None]

    if not conformers:
        raise ValueError(f"No valid molecules found in the SDF file: {sdf_path}")

    # Extract energy from each conformer
    def get_energy(mol):
        return float(mol.GetProp("Energy")) if mol.HasProp("Energy") else None

    def calculate_energy_stats(conformers):
        energies = [get_energy(mol) for mol in conformers if get_energy(mol) is not None]
        if not energies:
            return None, None, None, None, None, []

        min_energy = min(energies)
        max_energy = max(energies)
        avg_energy = np.mean(energies)
        slope, intercept, r_value, _, _ = stats.linregress(range(len(energies)), energies)

        return min_energy, max_energy, avg_energy, slope, r_value ** 2, energies

    min_energy, max_energy, avg_energy, slope, r_squared, energies = calculate_energy_stats(conformers)
    num_unique_conformers = len(set(energies))

    # Prepare data for the CSV
    exp_settings = constants.experimental_vconf_settings
    data = [
        experiment_number,
        exp_settings.get('NUM_STEPS'),
        exp_settings.get('SEARCH_WIDTH'),
        exp_settings.get('RANDOM_SEED'),
        exp_settings.get('ENERGY_CUTOFF'),
        exp_settings.get('DISTANCE_TOLERANCE'),
        exp_settings.get('ANGLE_TOLERANCE'),
        exp_settings.get('ENERGY_TOLERANCE'),
        min_energy, max_energy, avg_energy, num_unique_conformers, slope, r_squared
    ]

    # Append data to CSV
    append_to_csv(sdf_path, data, [
        "Experiment Number", "NUM_STEPS", "SEARCH_WIDTH", "RANDOM_SEED", "ENERGY_CUTOFF",
        "DISTANCE_TOLERANCE", "ANGLE_TOLERANCE", "ENERGY_TOLERANCE", "Min Energy", "Max Energy", "Avg Energy",
        "Unique Conformers", "Energy Slope", "R^2"
    ], energies)


def append_to_csv(sdf_path, data, headers, energies):
    """ Append the calculated data to a CSV file. """
    csv_path = os.path.join(os.path.dirname(sdf_path), "experiment_log.csv")
    file_exists = os.path.isfile(csv_path)
    energy_headers = [f"Conformer_{i+1}_Energy" for i in range(len(energies))]
    energy_data = energies + [''] * (len(energy_headers) - len(energies))  # Pad if necessary

    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers + energy_headers)
        writer.writerow(data + energy_data)


def main():
    experiment_number = get_next_experiment_number()

    # Step 1: Convert TSV to SDF and place in VCONF_outputs folder
    tsv_file_path = os.path.join(constants.compound_list_directory, str(constants.list_folder_name), str(f"{constants.list_folder_name}.tsv"))
    sdf_path = os.path.join(constants.path_to_VCONF_outputs_folder, "input_molecules.sdf")
    read_tsv_and_generate_sdf(tsv_file_path, sdf_path)

    for combo in combinations:
        # Update settings for this experiment
        settings = dict(zip(settings_options.keys(), combo))
        constants.experimental_vconf_settings.update(settings)

        # Run VConf command
        output_dir = constants.path_to_VCONF_outputs_folder
        command = build_vconf_command(constants.experimental_vconf_settings, sdf_path)
        run_vconf_command(command, output_dir)

        # After VConf runs, look for the resulting "_confs.sdf" file
        confs_sdf = os.path.join(output_dir, "PFOA_confs.sdf")  # Example file name
        if os.path.exists(confs_sdf):
            # Rename the _confs.sdf to experiment_#.sdf
            new_sdf_path = os.path.join(experiments_dir, f"Experiment_{experiment_number}.sdf")
            shutil.move(confs_sdf, new_sdf_path)  # Rename and move the file

            # Analyze the new SDF and append data to CSV
            analyze_sdf(new_sdf_path, experiment_number)
        else:
            print(f"Error: {confs_sdf} not found after running VConf.")

        experiment_number += 1  # Move to the next experiment

    print("All experiments completed.")


if __name__ == "__main__":
    main()
