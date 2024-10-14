import os
import subprocess
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
import sys
from constants import use_default_vconf_settings, default_vconf_settings, experimental_vconf_settings, path_to_VCONF_outputs_folder, list_file_path, vconf_path, max_conformers, step_sampling, generate_conformers_using_vconf_script, compound_list_directory, list_folder_name
import constants


def debug_constants():
    print("Debugging constants:")
    print(f"list_file_path: {constants.list_file_path}")
    print(f"vconf_path: {constants.vconf_path}")
    print(f"max_conformers: {constants.max_conformers}")
    print(f"step_sampling: {constants.step_sampling}")
    print(f"generate_conformers_using_vconf_script: {constants.generate_conformers_using_vconf_script}")
    print(f"use_default_vconf_settings: {constants.use_default_vconf_settings}")
    print(f"path_to_VCONF_outputs_folder: {constants.path_to_VCONF_outputs_folder}")
    print(f"default_vconf_settings: {constants.default_vconf_settings}")
    print(f"experimental_vconf_settings: {constants.experimental_vconf_settings}")
    print(f"compound_list_directory: {constants.compound_list_directory}")
    print(f"list_folder_name: {constants.list_folder_name}")
    print(f"constants module location: {constants.__file__}")


def read_tsv_and_generate_sdf(_tsv_path, sdf_path):
    """
    Read a TSV file and generate an SDF file from the SMILES strings contained within.
    """
    tsv_path = os.path.join(constants.compound_list_directory, str(constants.list_folder_name), str(f"{constants.list_folder_name}.tsv"))
    print(f"TSV Path: {tsv_path}")
    df = pd.read_csv(tsv_path, sep='\t', header=None)
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


def build_vconf_command(settings, sdf_path, num_molecules, running_as_exe):
    """
    Build the command line string to run VConf with the specified parameters.
    """
    last_molecule = settings['LAST_MOLECULE']
    if last_molecule == "None" or last_molecule is None:
        last_molecule = num_molecules
    else:
        last_molecule = int(last_molecule)

    if running_as_exe:
        sdf_path = os.path.basename(sdf_path)
        log_filename = os.path.basename(settings["OUTPUT_LOG"])
        out_filename = os.path.basename(settings["OUTPUT_SDF"])
    else:
        sdf_path = settings["SDF_FILENAME"]
        log_filename = settings["OUTPUT_LOG"]
        out_filename = settings["OUTPUT_SDF"]

    command = [
        constants.vconf_path,
        f'{sdf_path}',
        "-f", str(settings['FIRST_MOLECULE']),
        "-l", str(last_molecule),
        "-ff", settings['FORCEFIELD'],
        "-m", settings['SEARCH_MODE'],
        "-ns", str(settings['NUM_STEPS']),
        "-log", log_filename,
        "-out", out_filename
    ]

    if settings['USE_GENERALIZED_BORN_SOLVATION']:
        command.append("-gb")

    if settings['RESTRAINED_ATOMS'] and settings['RESTRAINED_ATOMS'] != "None":
        restrained_atoms = settings['RESTRAINED_ATOMS'].split()
        if len(restrained_atoms) >= 3:
            command.extend(["-ra"] + restrained_atoms)
        else:
            print("Warning: Less than 3 restrained atoms provided. Skipping the -ra option.")
    else:
        print("No restrained atoms provided.")

    # Handle RANDOM_SEEDS logic
    if settings['RANDOM_SEEDS']:
        random_seeds = settings['RANDOM_SEEDS'].split()
        if len(random_seeds) == 4:
            command.extend(["-seed"] + random_seeds)
        else:
            command.append("-seed ran")
    else:
        command.append("-seed ran")

    command.extend([
        "-sw", str(settings['SEARCH_WIDTH']),
        "-fc" if settings['FORMAL_CHARGE'] else "",
        "-snp" if settings['SULFONAMIDE_NITROGEN'] else "",
        "-cp", settings['CHIRAL_PRIORITY'],
        "-sr", settings['STEREOCHEMISTRY_RESTRICTIONS'],
        "-dc", str(settings['DIELECTRIC_COEFFICIENT']),
        "-nlp" if settings['NITROGEN_LONE_PAIR'] else "",
        "-rl", str(settings['RESONANCE_LIMIT']),
        "-sub", settings['SUBSTITUENTS_LEVEL'],
        "-minrs", str(settings['MIN_RING_SEARCH_STEPS']),
        "-addrs", str(settings['ADD_RING_SEARCH_STEPS']),
        "-maxrc", str(settings['MAX_RING_CONFS']),
        "-maxra", str(settings['MAX_RING_ATOMS']),
        "-re", str(settings['RING_ENERGY_CUTOFF']),
        "-klr" if settings['KEEP_LOWEST_ENERGY_RING_COMBINATION'] else "",
        "-e", str(settings['ENERGY_CUTOFF']),
        "-et", str(settings['ENERGY_TOLERANCE']),
        "-dt", str(settings['DISTANCE_TOLERANCE']),
        "-at", str(settings['ANGLE_TOLERANCE']),
        "-nf" if settings['DO_NOT_FILTER_OUTPUT'] else "",
        "-u" if settings['KEEP_UNFILTERED_CONFORMATIONS'] else "",
        "-nt" if settings['NO_TIME_LIMITS'] else "",
        "-ts", str(settings['SETUP_TIME_LIMIT']),
        "-tf", str(settings['FILTER_TIME_LIMIT'])
    ])

    # Remove any empty strings that result from false flags
    command = [arg for arg in command if arg]

    print(f"Built VConf command: {' '.join(command)}")
    return command


def run_vconf_command(command, output_dir):
    """
    Run the VConf command using subprocess.
    """
    try:
        creationflags = 0
        if os.name == 'nt':  # Check if the operating system is Windows
            creationflags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            command,
            shell=False,
            cwd=output_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"Error running VConf: {stderr}")
        else:
            print(f"VConf output: {stdout}")

        print("VConf processing completed.")
    except Exception as e:
        print(f"Exception occurred while running VConf: {e}")


def combine_and_label_sdf_files(output_dir, batch_file_path, molecule_names, max_conformers, step_sampling):
    """
    Combine individual SDF files into a batch file and label them appropriately.
    """
    writer = Chem.SDWriter(batch_file_path)
    name_counts = {name: 0 for name in molecule_names}

    for file in os.listdir(output_dir):
        if file.endswith('_confs.sdf'):
            sdf_file_path = os.path.join(output_dir, str(file))
            suppl = Chem.SDMolSupplier(sdf_file_path)
            mol_list = [mol for mol in suppl if mol is not None]
            print(f"Processing file: {file} with {len(mol_list)} conformers")

            # Step sampling logic
            if step_sampling and len(mol_list) > max_conformers:
                step = len(mol_list) // max_conformers
                print(f"Step sampling enabled: Selecting every {step}th conformer")
                sampled_mol_list = [mol_list[i] for i in range(0, len(mol_list), step)][:max_conformers]
            else:
                sampled_mol_list = mol_list[:max_conformers]

            for mol in sampled_mol_list:
                name = mol.GetProp('_Name')
                name_counts[name] += 1
                new_name = f"{name}_{name_counts[name]}"
                mol.SetProp('_Name', new_name)
                mol = Chem.AddHs(mol, addCoords=True)  # Ensure implicit hydrogens are included
                writer.write(mol)

    writer.close()
    print(f"Combined and labeled SDF file {batch_file_path} generated successfully.")


def main():
    """
    Main function to orchestrate the VConf conformer generation process.
    """
    if not generate_conformers_using_vconf_script:
        print("generate_conformers_vconf.py is disabled")
        return

    debug_constants()

    settings = default_vconf_settings if use_default_vconf_settings else experimental_vconf_settings

    output_dir = os.path.dirname(settings['SDF_FILENAME'])
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory created: {output_dir}")

    print(f"Reading TSV and generating SDF file...")
    molecule_names = read_tsv_and_generate_sdf(list_file_path, settings['SDF_FILENAME'])
    print(f"Generated SDF file with molecules: {molecule_names}")

    # Calculate the number of molecules
    num_molecules = len(molecule_names)
    print(f"Number of molecules in the SDF file: {num_molecules}")

    # Update LAST_MOLECULE if it's "None"
    if settings['LAST_MOLECULE'] == "None":
        settings['LAST_MOLECULE'] = num_molecules

    running_as_exe = getattr(sys, 'frozen', False)  # Detect if running as executable

    command = build_vconf_command(settings, settings['SDF_FILENAME'], num_molecules, running_as_exe)
    run_vconf_command(command, output_dir)
    print(f"Combining and labeling SDF files into {settings['vconf_batch_sdf_path']}...")
    combine_and_label_sdf_files(output_dir, settings['vconf_batch_sdf_path'], molecule_names, max_conformers,
                                step_sampling)
    print("Process completed successfully.")

    # Print which settings were used and if step sampling was enabled
    settings_type = "default_vconf_settings" if use_default_vconf_settings else "experimental_vconf_settings"
    print(f"\nSettings used: {settings_type}")
    print(f"Step sampling enabled: {'Yes' if step_sampling else 'No'}")


if __name__ == "__main__":
    main()
