import psutil
import os
import subprocess
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
import sys
from constants import use_default_vconf_settings, default_vconf_settings, experimental_vconf_settings, path_to_VCONF_outputs_folder, list_file_path, vconf_path, max_conformers, step_sampling, generate_conformers_using_vconf_script, compound_list_directory, list_folder_name, skip_vconf_exe
import constants
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import threading
import signal
from rdkit import RDLogger
from datetime import datetime

# Define a global observer for graceful shutdown
observer = None
max_conformers = int(constants.max_conformers.strip('"'))


# Function to terminate all running vconf processes
def terminate_vconf_processes():
    for process in psutil.process_iter(['name']):
        if process.info['name'] and 'vconf' in process.info['name'].lower():
            print(f"Terminating process: {process.info['name']} (PID: {process.pid})")
            process.terminate()
            process.wait()  # Wait for the process to be fully terminated

terminate_vconf_processes()  # Call this function at the start of the script

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


class VConfLogHandler(FileSystemEventHandler):
    def __init__(self, log_file_path):
        super().__init__()
        self.log_file_path = log_file_path
        self.last_position = 0  # Track the last read position in the file

    def on_modified(self, event):
        # Check if the event is for the specific log file we're monitoring
        if event.src_path == self.log_file_path:
            self.print_new_log_content()

    def print_new_log_content(self):
        # Check if the log file exists to prevent errors
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r') as log_file:
                    log_file.seek(self.last_position)  # Start from the last read position
                    new_content = log_file.read()
                    if new_content:
                        print("New log entries:")
                        print(new_content)
                        self.last_position = log_file.tell()  # Update the last position
            except IOError as e:
                print(f"Error reading log file: {e}")

def monitor_log_file():
    log_file_path = os.path.join(constants.compound_list_directory, list_folder_name, "VCONF_outputs", f"{list_folder_name}.log")

    # Wait until the log file directory exists
    log_dir = os.path.dirname(log_file_path)
    while not os.path.exists(log_dir):
        print(f"Waiting for directory {log_dir} to be created...")
        time.sleep(2)

    # Wait for the log file to be created or until vconf.exe finishes
    while not os.path.exists(log_file_path):
        if not any(proc.info['name'] and 'vconf' in proc.info['name'].lower() for proc in psutil.process_iter(['name'])):
            print("vconf.exe is no longer running, stopping log file monitoring.")
            return
        print(f"Waiting for log file {log_file_path} to be created...")
        time.sleep(2)

    # Start monitoring once the log file is present
    event_handler = VConfLogHandler(log_file_path)
    observer = Observer()
    observer.schedule(event_handler, log_dir, recursive=False)
    observer.start()
    print(f"Monitoring changes in {log_file_path}...")

    try:
        while any(proc.info['name'] and 'vconf' in proc.info['name'].lower() for proc in psutil.process_iter(['name'])):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        print("Log file monitoring stopped.")

def stop_observer(signum, frame):
    """
    Stop the observer when the script is terminated.
    """
    global observer
    if observer:
        observer.stop()
        observer.join()
    print("Log file monitoring stopped.")

def clean_molecule_name(name):
    """
    Clean the molecule name by replacing invalid characters and adding prefix if needed.
    """
    if name[0].isdigit():
        name = 'X' + name
    name = name.replace('-', '_').replace(' ', '_').replace(':', '_')
    return name


def read_tsv_and_generate_sdf(sdf_path):
    """
    Read TSV files in the compound directory and generate an SDF file from the SMILES strings contained within.
    """
    tsv_files = [f for f in os.listdir(constants.list_folder) if f.endswith('.tsv')]
    if not tsv_files:
        print("No TSV files found in the compound directory.")
        return []

    molecule_names = []
    writer = Chem.SDWriter(sdf_path)

    for tsv_file in tsv_files:
        tsv_path = os.path.join(constants.list_folder, tsv_file)
        print(f"Reading TSV file: {tsv_path}")
        df = pd.read_csv(tsv_path, sep='\t', header=None)

        for index, row in df.iterrows():
            mol = Chem.MolFromSmiles(row.iloc[0])  # First column is SMILES
            if mol:
                mol = Chem.AddHs(mol)  # Add hydrogens
                AllChem.EmbedMolecule(mol, randomSeed=42)
                AllChem.UFFOptimizeMolecule(mol)  # Optimize the geometry to ensure it's properly 3D

                # Detect charge
                charge = Chem.GetFormalCharge(mol)
                charge_suffix = f"_pos{charge}" if charge > 0 else f"_neg{abs(charge)}" if charge < 0 else ""

                # Clean and set the molecule name
                cleaned_name = clean_molecule_name(row.iloc[1])  # Second column is the molecule name
                mol.SetProp("_Name", cleaned_name + charge_suffix)

                writer.write(mol)
                molecule_names.append(cleaned_name + charge_suffix)
            else:
                print(f"Error processing SMILES: {row.iloc[0]}")

    writer.close()
    print(f"SDF file {sdf_path} generated successfully.")
    print(f"List of molecule names: {molecule_names}")
    return molecule_names  # Return the list of molecule names


def rename_vconf_output_files(output_dir):
    """
    Rename SDF files in the VCONF_outputs folder that contain invalid characters or start with numbers.
    """
    for file in os.listdir(output_dir):
        if file.endswith('_confs.sdf'):
            molecule_name = file.split('_confs.sdf')[0]
            cleaned_name = clean_molecule_name(molecule_name)
            if cleaned_name != molecule_name:
                old_path = os.path.join(output_dir, file)
                new_file_name = f"{cleaned_name}_confs.sdf"
                new_path = os.path.join(output_dir, new_file_name)
                os.rename(old_path, new_path)
                print(f"Renamed file: {file} to {new_file_name}")

def monitor_vconf_outputs(molecule_names):
    """
    Monitor the VCONF_outputs folder for new file additions and report details about the files.
    """
    output_dir = os.path.join(constants.compound_list_directory, list_folder_name, "VCONF_outputs")
    seen_files = set()

    print(f"Monitoring VCONF_outputs directory: {output_dir} for new files...")
    try:
        while True:
            current_files = set(os.listdir(output_dir))
            new_files = current_files - seen_files

            for new_file in new_files:
                if new_file.endswith('_confs.sdf'):
                    sdf_file_path = os.path.join(output_dir, new_file)
                    molecule_name = new_file.split('_confs.sdf')[0]
                    if molecule_name in molecule_names:
                        with open(sdf_file_path, 'r') as sdf_file:
                            for line in sdf_file:
                                if line.startswith('> <Energy>'):
                                    lowest_energy = float(sdf_file.readline().strip())
                                    break
                        num_conformers = sum(1 for mol in Chem.SDMolSupplier(sdf_file_path) if mol is not None)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{timestamp}] New file: {new_file} - Number of {molecule_name} conformers: {num_conformers}, Lowest energy: {lowest_energy}")

            seen_files = current_files
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopped monitoring VCONF_outputs directory.")

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
    rename_vconf_output_files(output_dir)  # Rename files before combining

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
                step = int(len(mol_list) // max_conformers)  # Force step to be an integer
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
    # Set up signal handling to ensure the observer stops on script termination
    signal.signal(signal.SIGINT, stop_observer)
    signal.signal(signal.SIGTERM, stop_observer)
    RDLogger.DisableLog('rdApp.warning')

    # Start monitoring the VCONF log file in a separate thread
    monitor_thread = threading.Thread(target=monitor_log_file, daemon=True)
    monitor_thread.start()

    # Rest of the main function for running the VConf conformer generation process
    if not generate_conformers_using_vconf_script:
        print("generate_conformers_vconf.py is disabled")
        return

    # Add your function calls and VCONF execution logic here as usual
    debug_constants()

    settings = default_vconf_settings if use_default_vconf_settings else experimental_vconf_settings

    output_dir = os.path.dirname(settings['SDF_FILENAME'])
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory created: {output_dir}")

    print(f"Reading TSV and generating SDF file...")
    molecule_names = read_tsv_and_generate_sdf(settings['SDF_FILENAME'])
    print(f"Generated SDF file with molecules: {molecule_names}")

    # Start monitoring VCONF_outputs for new files in a separate thread
    monitor_outputs_thread = threading.Thread(target=monitor_vconf_outputs, args=(molecule_names,), daemon=True)
    monitor_outputs_thread.start()

    # Calculate the number of molecules
    num_molecules = len(molecule_names)
    print(f"Number of molecules in the SDF file: {num_molecules}")

    # Update LAST_MOLECULE if it's "None"
    if settings['LAST_MOLECULE'] == "None":
        settings['LAST_MOLECULE'] = num_molecules

    running_as_exe = getattr(sys, 'frozen', False)  # Detect if running as executable

    if skip_vconf_exe:
        print("VConf execution is skipped as per user request.")
    else:
        command = build_vconf_command(settings, settings['SDF_FILENAME'], num_molecules, running_as_exe)
        run_vconf_command(command, output_dir)

    print(f"Combining and labeling SDF files into {settings['vconf_batch_sdf_path']}...")
    combine_and_label_sdf_files(output_dir, settings['vconf_batch_sdf_path'], molecule_names, max_conformers, step_sampling)
    print("Process completed successfully.")

    # Print which settings were used and if step sampling was enabled
    settings_type = "default_vconf_settings" if use_default_vconf_settings else "experimental_vconf_settings"
    print(f"\nSettings used: {settings_type}")
    print(f"Step sampling enabled: {'Yes' if step_sampling else 'No'}")

if __name__ == "__main__":
    main()
