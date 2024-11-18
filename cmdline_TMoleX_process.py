import os
import shlex
import io
import time
from time import sleep
from rdkit import Chem
import paramiko
from scp import SCPClient
import importlib.util
import sys
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from collections import defaultdict
import configparser

# Initialize ConfigParser to read from the sensitive_config.ini file
config = configparser.ConfigParser()
config.read('sensitive_config.ini')

# Extract the sensitive configuration settings
server = config['Sensitive'].get('server')
username = config['Sensitive'].get('username')
password = config['Sensitive'].get('password')
remote_directory = config['Sensitive'].get('remote_directory')
remote_file_path = config['Sensitive'].get('remote_file_path')

# Determine the correct path to constants.py
if getattr(sys, 'frozen', False):  # Running as an executable
    _internal_dir = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), '_internal')
else:  # Running as a script
    _internal_dir = os.path.dirname(os.path.abspath(__file__))

# Load constants
constants_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'constants.py')
spec = importlib.util.spec_from_file_location("constants", constants_path)
constants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(constants)

# Import constants
vconf_batch_sdf_path = constants.vconf_batch_sdf_path
list_folder = constants.list_folder
port = constants.port
prepare_TMoleX_files_script = constants.prepare_TMoleX_files_script
generate_cosmo_format_files = constants.generate_cosmo_format_files
define_script_path = constants.define_script_path
cosmoprep_script_path = constants.cosmoprep_script_path
subscript_template_path = constants.subscript_template_path
remote_script_template_path = constants.remote_script_template_path
go_define_script_path = constants.go_define_script_path
geometry_optimize_lowest_energy_structures = constants.geometry_optimize_lowest_energy_structures
percent_enabled = constants.percent_enabled

# Update constants with values from sensitive_config.ini
constants.remote_directory = remote_directory  # Update remote_directory
constants.remote_file_path = remote_file_path  # Update remote_file_path

# Recalculate remote_temp_dir if it depends on remote_directory
constants.remote_temp_dir = os.path.join(constants.remote_directory, constants.temp_dir).replace("\\", "/")
remote_temp_dir = constants.remote_temp_dir  # Use updated value

# Debugging statements (optional)
print(f"Server: {server}")
print(f"Username: {username}")
print(f"Remote Directory: {remote_directory}")
print(f"Remote Temp Directory: {remote_temp_dir}")


def assign_define_script(conformers, geometry_optimize_percentage, output_dir, ssh):
    """
    Assign define.sh or geometry_optimize_define.sh based on the percentage of conformers,
    and transfer the appropriate script to the remote server for each conformer.
    """

    # Calculate the number of conformers to apply geometry optimization
    n_optimize = int(len(conformers) * float(geometry_optimize_percentage) / 100)

    for i, conformer_name in enumerate(conformers):
        # Select the correct script
        define_script = constants.go_define_script_path if i < n_optimize else constants.define_script_path
        target_path = f"{output_dir}/{conformer_name}/define.sh"

        # Read the script content
        with open(define_script, 'r') as src:
            script_content = src.read()

        # Transfer the script to the remote server
        with SCPClient(ssh.get_transport()) as scp:
            scp.putfo(io.StringIO(script_content), target_path)

        # Set the transferred script as executable on the remote server
        ssh.exec_command(f"chmod +x {shlex.quote(target_path)}")

        # Log which script was assigned
        print(f"Assigned {'geometry_optimize_define.sh' if i < n_optimize else 'define.sh'} to {conformer_name} on the remote server.")


def read_script(script_path):
    """
    Read the content of a script file.
    """
    with open(script_path, 'r') as file:
        return file.read()


def write_molecule_file(mol, mol_name, output_dir):
    """
    Write molecule SDF coordinates to a "coord" file titled by the molecules name.
    """
    num_atoms = mol.GetNumAtoms()
    elements = [atom.GetSymbol() for atom in mol.GetAtoms()]
    conf = mol.GetConformer()
    coords = conf.GetPositions()

    output_content = f"{num_atoms}\n\n"
    for i in range(num_atoms):
        output_content += f"{elements[i]: <2} {coords[i][0]: >12.5f} {coords[i][1]: >12.5f} {coords[i][2]: >12.5f}\n"

    filename = os.path.join(output_dir, mol_name)
    with open(filename, 'w') as f:
        f.write(output_content)


def sdf_to_files(sdf_file, output_dir):
    """
    Convert batch file .sdf to multiple smaller .sdf files with molecule names.
    """
    print(f"Converting SDF file: {sdf_file}")
    if not os.path.exists(sdf_file):
        raise OSError(f"SDF file not found: {sdf_file}")
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    else:
        os.makedirs(output_dir)

    suppl = Chem.SDMolSupplier(sdf_file, removeHs=False)
    for mol in suppl:
        if mol is not None:
            # Attempt to get the molecule name with charge suffix
            if mol.HasProp('mol_name'):
                mol_name = mol.GetProp('mol_name')
            elif mol.HasProp('_Name'):
                mol_name = mol.GetProp('_Name')
            else:
                mol_name = f'molecule_{suppl.index(mol)}'
            print(f"Processing molecule: {mol_name}")
            write_molecule_file(mol, mol_name, output_dir)


def clear_remote_directory(ssh, remote_path):
    """
    Clear the temporary directory on the remote server.
    """
    ssh.exec_command(f"rm -rf {remote_path}/*")
    # Verify that the directory is empty
    stdin, stdout, stderr = ssh.exec_command(f"ls -A {remote_path}")
    if stdout.read().strip() == "":
        print(f"Successfully cleared remote directory: {remote_path}")
    else:
        print(f"Warning: Remote directory {remote_path} may not be completely cleared.")


def create_remote_directory(ssh, remote_dir):
    """
    Create directories on the remote server.
    """
    ssh.exec_command(f"mkdir -p {remote_dir}")
    # Verify that the directory was created
    stdin, stdout, stderr = ssh.exec_command(f"test -d {remote_dir} && echo 'exists'")
    if stdout.read().decode().strip() == "exists":
        print(f"Successfully created remote directory: {remote_dir}")
    else:
        print(f"Warning: Failed to create remote directory: {remote_dir}")


def calculate_md5(file_path):
    """Calculate the MD5 checksum of a local file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_remote_file(ssh, remote_file, local_md5):
    """Check if the remote file's MD5 checksum matches the local file's checksum."""
    stdin, stdout, stderr = ssh.exec_command(f"md5sum {remote_file}")
    remote_md5 = stdout.read().decode().strip().split()[0]
    return local_md5 == remote_md5


def transfer_files_to_remote(
    local_dir,
    remote_dir,
    ssh,
    geometry_optimize_percentage,  # Changed to geometry_optimize_percentage
    percent_enabled,
    max_workers=5,
    retries=3,
    delay=5
):
    """
    Transfer coord files to the remote server with the name 'x'. tx command will read these.
    Transfers multiple files in parallel using ThreadPoolExecutor.
    """

    def transfer_file(filename):
        local_file_path = os.path.join(local_dir, filename).replace("\\", "/")
        if os.path.isfile(local_file_path):
            remote_molecule_dir = f"{remote_dir}/{filename}"

            # Retry directory creation
            for attempt in range(retries):
                try:
                    create_remote_directory(ssh, remote_molecule_dir)
                    break  # Exit loop if successful
                except Exception as e:
                    print(
                        f"Attempt {attempt + 1}: Could not create remote directory {remote_molecule_dir}. Exception: {e}")
                    time.sleep(delay)
                    if attempt == retries - 1:
                        return  # Skip this file if all retries fail

            remote_file_path = f"{remote_molecule_dir}/x"
            print(f"Transferring file {local_file_path} to {remote_file_path}")

            # Calculate local MD5 checksum
            local_md5 = calculate_md5(local_file_path)

            # Retry file transfer
            for attempt in range(retries):
                try:
                    # Transfer file using SCPClient without the 'timeout' argument
                    with SCPClient(ssh.get_transport()) as scp:
                        scp.put(local_file_path, remote_path=remote_file_path)

                    # Verify transfer completion
                    if verify_remote_file(ssh, remote_file_path, local_md5):
                        print(f"Successfully transferred and verified {local_file_path}")
                        return  # Successful transfer, exit
                    else:
                        print(f"Warning: Verification failed for {local_file_path}. Transfer may be incomplete.")
                except Exception as e:
                    print(f"Attempt {attempt + 1}: Failed to transfer file {local_file_path}. Exception: {e}")
                    time.sleep(delay)
                    if attempt == retries - 1:
                        print(f"Error: Could not transfer {local_file_path} after {retries} attempts.")
                        return  # Skip this file if all retries fail

    # Use ThreadPoolExecutor to transfer files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(transfer_file, filename): filename for filename in os.listdir(local_dir)}

        # Monitor completion of the transfers
        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                future.result()  # This will raise any exceptions that occurred during execution
            except Exception as exc:
                print(f"Error during transfer of {filename}: {exc}")


def create_remote_script(molecule_names, remote_dir, template_path):
    """
    Create a script to run "tx", "define", and "cosmoprep" in each directory based on a template.
    """
    script_content = read_script(template_path)
    log_file = f"{remote_dir}/run_tx.log"

    # Initialize the log file
    script_content += f"echo 'Starting run_tx.sh execution at $(date)' > {log_file}\n"

    for mol_name in molecule_names:
        dirpath = f"{remote_dir}/{mol_name}"
        script_content += f"cd {shlex.quote(dirpath)}\n"

        # Add $chelp grid=3 to the control file
        script_content += "if grep -q '$chelp' control; then\n"
        script_content += "    sed -i '/$chelp/a\\    grid=3' control\n"
        script_content += "else\n"
        script_content += "    echo '$chelp' >> control\n"
        script_content += "    echo '    grid=3' >> control\n"
        script_content += "fi\n"

        # Log the start of processing for this molecule
        script_content += f"echo 'Processing molecule: {mol_name}' >> {log_file}\n"

        # Execute tx command and log output
        script_content += f"tx >> {log_file} 2>&1\n"
        script_content += "if [ $? -eq 0 ]; then\n"
        script_content += f"    echo '{mol_name}: tx Pass' >> {log_file}\n"

        # Execute define script and log output
        script_content += "    ./run_define.sh >> {log_file} 2>&1\n"
        script_content += "    if [ $? -eq 0 ]; then\n"
        script_content += f"        echo '{mol_name}: define Pass' >> {log_file}\n"
        script_content += "    else\n"
        script_content += f"        echo '{mol_name}: define failed' >> {log_file}\n"
        script_content += "    fi\n"

        # Execute cosmoprep script and log output
        script_content += "    ./run_cosmoprep.sh >> {log_file} 2>&1\n"
        script_content += "    if [ $? -eq 0 ]; then\n"
        script_content += f"        echo '{mol_name}: cosmoprep Pass' >> {log_file}\n"
        script_content += "    else\n"
        script_content += f"        echo '{mol_name}: cosmoprep failed' >> {log_file}\n"
        script_content += "    fi\n"

        # Close the if for tx command
        script_content += "else\n"
        script_content += f"    echo '{mol_name}: tx failed' >> {log_file}\n"
        script_content += "fi\n"

        # Go back to the previous directory
        script_content += "cd -\n"

        # Add control file modification if needed
        if generate_cosmo_format_files:
            script_content += f"sed -i 's|$cosmo_out file=out.ccf|$cosmo_out file={mol_name}.cosmo|' {remote_dir}/{mol_name}/control\n"
            print(f"Edited control file for {mol_name} to output cosmo files.")
        else:
            print(f"Warning: {mol_name} will generate a .ccf format file. Subsequent scripts may not work correctly.\n")

    # Log the completion of the script
    script_content += f"echo 'Completed run_tx.sh execution at $(date)' >> {log_file}\n"

    return script_content


def create_define_script(define_script_path):
    """
    Read the define script from python directory.
    """
    return read_script(define_script_path)


def create_go_define_script(go_define_script_path):
    """
    Read the go_define script from python directory.
    """
    return read_script(go_define_script_path)


def extract_charge_from_name(mol_name):
    """
    Extracts the charge from the molecule name.

    If the name includes "_pos#" or "_neg#", it extracts the charge.

    Otherwise, returns "0".
    """
    match = re.search(r'_(pos|neg)(\d+)', mol_name)
    if match:
        sign = match.group(1)
        value = match.group(2)
        if sign == 'pos':
            return f"{value}"
        elif sign == 'neg':
            return f"-{value}"
    else:
        return "0"


def create_cosmoprep_script(cosmoprep_script_path):
    """
    Read the cosmoprep script from python directory.
    """
    return read_script(cosmoprep_script_path)


def create_subscript(mol_name, subscript_template_content):
    """
    Create a subscript file for the server based on a template content.
    """
    return subscript_template_content.replace("{mol_name}", mol_name)



def transfer_script_files(
    molecule_names,
    define_script,
    go_define_script,
    cosmoprep_script,
    subscript_template_content,  # Now correctly expects content
    remote_dir,
    ssh,
    geometry_optimize_percentage,
    percent_enabled,
    max_workers=3,
    retries=3,
    delay=5,
    task_delay=0.1
):
    # Function to extract molecule name and numeric suffix for grouping and sorting
    def extract_molecule_base_and_suffix(molecule_name):
        match = re.match(r"(.+?)_(\d+)$", molecule_name)
        base_name = match.group(1) if match else molecule_name
        suffix = int(match.group(2)) if match else float('inf')
        return base_name, suffix

    # Group molecule names by their base name and sort each group by suffix
    molecule_groups = defaultdict(list)
    for mol_name in molecule_names:
        base_name, suffix = extract_molecule_base_and_suffix(mol_name)
        molecule_groups[base_name].append((mol_name, suffix))

    # Sort each molecule group by the numeric suffix
    for base_name in molecule_groups:
        molecule_groups[base_name].sort(key=lambda x: x[1])

    def transfer_individual_script(mol_name, is_optimized):
        # Choose the content for run_define.sh based on optimization criteria
        selected_define_content = go_define_script if is_optimized else define_script

        # Extract charge from mol_name
        charge_value = extract_charge_from_name(mol_name)
        # Replace {charge} in selected_define_content
        selected_define_content = selected_define_content.replace("{charge}", charge_value)

        # Remote paths for each script
        remote_molecule_dir = f"{remote_dir}/{mol_name}"
        remote_define_path = f"{remote_molecule_dir}/run_define.sh"
        remote_cosmoprep_path = f"{remote_molecule_dir}/run_cosmoprep.sh"
        remote_subscript_path = f"{remote_molecule_dir}/subscript"
        subscript_content = create_subscript(mol_name, subscript_template_content)

        # Ensure remote molecule directory exists
        create_remote_directory(ssh, remote_molecule_dir)

        # Function to transfer a single file with retries
        def transfer_single_script(local_content, remote_path):
            local_md5 = hashlib.md5(local_content.encode('utf-8')).hexdigest()
            for attempt in range(retries):
                try:
                    with SCPClient(ssh.get_transport()) as scp:
                        scp.putfo(io.StringIO(local_content), remote_path)
                    if verify_remote_file(ssh, remote_path, local_md5):
                        ssh.exec_command(f"chmod +x {shlex.quote(remote_path)}")
                        return
                    else:
                        print(f"Warning: Verification failed for {remote_path}")
                except Exception as e:
                    print(f"Attempt {attempt + 1}: Failed to transfer {remote_path}. Exception: {e}")
                    sleep(delay)
            print(f"Error: Could not transfer {remote_path} after {retries} attempts.")

        # Transfer each script
        transfer_single_script(selected_define_content, remote_define_path)
        transfer_single_script(cosmoprep_script, remote_cosmoprep_path)
        transfer_single_script(subscript_content, remote_subscript_path)

        # Log the transferred script type
        print(f"Transferred {'go_define.sh' if is_optimized else 'define.sh'} content as run_define.sh for {mol_name}")

    # Use ThreadPoolExecutor to process each molecule's scripts concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        # Iterate through each molecule group and apply optimization
        for base_name, group in molecule_groups.items():
            # Determine the number to optimize for this group
            if percent_enabled and geometry_optimize_percentage:
                n_optimize = int(len(group) * geometry_optimize_percentage / 100)
            else:
                n_optimize = 0

            # Schedule transfers for each molecule in the group
            for i, (mol_name, _) in enumerate(group):
                is_optimized = i < n_optimize
                futures[executor.submit(transfer_individual_script, mol_name, is_optimized)] = mol_name

        # Monitor completion of all futures
        for future in as_completed(futures):
            mol_name = futures[future]
            try:
                future.result()  # This will raise any exceptions from transfer_individual_script
            except Exception as e:
                print(f"Error during script transfer for {mol_name}: {e}")
            # Add a slight delay to avoid opening too many connections at once
            sleep(task_delay)


def main():
    try:
        print("Starting the cmdline_TMoleX_process script...")

        # Verify if TMoleX file preparation is enabled
        if not prepare_TMoleX_files_script:
            print("cmdline_TMoleX_process.py is disabled")
            return

        # Set geometry_optimize_percentage based on conditions
        geometry_optimize_percentage = 0  # Default if conditions are not met
        if percent_enabled and constants.geometry_optimize_lowest_energy_structures:
            geometry_optimize_percentage = int(constants.geometry_optimize_lowest_energy_structures)

        # Debugging: print the geometry optimize percentage
        print(f"Geometry Optimize Percentage: {geometry_optimize_percentage}")

        # Set up SSH connection
        print("Setting up SSH connection...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, port=port, username=username, password=password)
        print("SSH connection established.")

        # Clear remote directory
        print(f"Clearing remote directory: {remote_temp_dir}")
        clear_remote_directory(ssh, remote_temp_dir)
        print("Remote directory cleared.")

        # Convert SDF to individual molecule files
        coord_files_dir = os.path.join(list_folder, "COORD_files").replace("\\", "/")
        print(f"Converting SDF to files in: {coord_files_dir}")
        sdf_to_files(vconf_batch_sdf_path, coord_files_dir)
        print("SDF files converted successfully.")

        # Transfer files to remote server
        print(f"Transferring files to remote directory: {remote_temp_dir}")
        transfer_files_to_remote(
            coord_files_dir,
            remote_temp_dir,
            ssh,
            geometry_optimize_percentage,  # Add geometry_optimize_percentage
            percent_enabled  # Add percent_enabled
        )
        print("Coord files transferred successfully.")

        # Create scripts from templates
        print("Reading define and cosmoprep scripts...")
        define_script_content = read_script(define_script_path)
        go_define_script_content = read_script(go_define_script_path)
        cosmoprep_script_content = read_script(cosmoprep_script_path)
        subscript_template_content = read_script(subscript_template_path)  # Correct variable name
        print("Scripts read successfully.")

        # List molecule names and calculate the number for optimization
        molecule_names = [filename for filename in os.listdir(coord_files_dir) if
                          os.path.isfile(os.path.join(coord_files_dir, filename))]
        print(f"Found {len(molecule_names)} molecules to process.")

        # Batch transfer scripts to remote for each molecule
        print(f"Transferring scripts (run_define.sh, run_cosmoprep.sh, subscript.sh) for each molecule...")
        transfer_script_files(
            molecule_names,
            define_script_content,
            go_define_script_content,
            cosmoprep_script_content,
            subscript_template_content,  # Use the content, not the path
            remote_temp_dir,
            ssh,
            geometry_optimize_percentage,  # Pass the correct variable
            percent_enabled
        )
        print("Scripts transferred successfully.")

        # Create and transfer the main remote script
        print("Creating and transferring main remote script...")
        remote_script = create_remote_script(molecule_names, remote_temp_dir, remote_script_template_path)
        remote_script_path = f"{remote_temp_dir}/run_tx.sh"

        with SCPClient(ssh.get_transport()) as scp:
            local_script_md5 = hashlib.md5(remote_script.encode('utf-8')).hexdigest()
            scp.putfo(io.StringIO(remote_script), remote_script_path)
            if verify_remote_file(ssh, remote_script_path, local_script_md5):
                print(f"Successfully transferred and verified main script {remote_script_path}")
            else:
                print(f"Warning: Verification failed for main script {remote_script_path}.")

        # Ensure the main script has executable permissions
        print(f"Setting executable permissions for {remote_script_path}...")
        ssh.exec_command(f"chmod +x {remote_script_path}")

        # Execute the main script on the remote server
        print(f"Executing the main script on the remote server: {remote_script_path}")
        stdin, stdout, stderr = ssh.exec_command(f"bash {remote_script_path}")
        stdout.channel.recv_exit_status()  # Wait for the script to finish

        # Fetch and process run_tx.log content
        remote_log_path = f"{remote_temp_dir}/run_tx.log"
        print(f"Fetching logs from: {remote_log_path}")
        stdin, stdout, stderr = ssh.exec_command(f"cat {remote_log_path}")
        run_tx_log = stdout.read().decode('utf-8').strip().split("\n")

        # Track pass/fail status
        all_passed = True
        failed_molecules = []

        # Display the results for each molecule
        for line in run_tx_log:
            if "failed" in line:
                print(line)  # Print only if there was a failure
                all_passed = False
                failed_molecules.append(line.split(":")[0].strip())
            elif "Pass" in line:
                if "define Pass" in line and "cosmoprep Pass" in line:
                    mol_name = line.split(":")[0].strip()
                    print(f"{mol_name}: Pass")

        # Summary report
        if all_passed:
            print("\nAll molecules processed successfully.")
        else:
            print("\nSome molecules encountered errors:")
            for mol_name in failed_molecules:
                print(f" - {mol_name}")

        ssh.close()

    except Exception as e:
        print(f"An error occurred: {e}")
        if 'ssh' in locals():
            ssh.close()
        print("Exiting script due to error.")


if __name__ == "__main__":
    main()
