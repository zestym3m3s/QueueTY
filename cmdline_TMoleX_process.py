import os
import shlex
import io
import time  # Import the time module for adding delays
from rdkit import Chem
import paramiko
from scp import SCPClient
import importlib.util
import sys

# Determine the correct path to constants.py
if getattr(sys, 'frozen', False):  # Running as an executable
    _internal_dir = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), '_internal')
else:  # Running as a script
    _internal_dir = os.path.dirname(os.path.abspath(__file__))

constants_path = os.path.join(_internal_dir, 'constants.py')

spec = importlib.util.spec_from_file_location("constants", constants_path)
constants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(constants)

# Import constants
vconf_batch_sdf_path = constants.vconf_batch_sdf_path
list_folder = constants.list_folder
server = constants.server
port = constants.port
username = constants.username
password = constants.password
remote_temp_dir = constants.remote_temp_dir
prepare_TMoleX_files_script = constants.prepare_TMoleX_files_script
generate_cosmo_format_files = constants.generate_cosmo_format_files
define_script_path = constants.define_script_path
cosmoprep_script_path = constants.cosmoprep_script_path
subscript_template_path = constants.subscript_template_path
remote_script_template_path = constants.remote_script_template_path

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
            mol_name = mol.GetProp('_Name') if mol.HasProp('_Name') else f'molecule_{suppl.index(mol)}'
            write_molecule_file(mol, mol_name, output_dir)

def clear_remote_directory(ssh, remote_path):
    """
    Clear the temporary directory on the remote server.
    """
    stdin, stdout, stderr = ssh.exec_command(f"rm -rf {remote_path}/*")
    stdout.channel.recv_exit_status()
    time.sleep(1)  # Add delay

def create_remote_directory(ssh, remote_dir):
    """
    Create directories on the remote server.
    """
    ssh.exec_command(f"mkdir -p {remote_dir}")
    time.sleep(1)  # Add delay
    print(f"Created remote directory: {remote_dir}")

def transfer_files_to_remote(local_dir, remote_dir, ssh):
    """
    Transfer coord files to the remote server with the name 'x'. tx command will read these.
    """
    with SCPClient(ssh.get_transport()) as scp:
        for filename in os.listdir(local_dir):
            local_file_path = os.path.join(local_dir, filename).replace("\\", "/")
            if os.path.isfile(local_file_path):
                remote_molecule_dir = f"{remote_dir}/{filename}"
                create_remote_directory(ssh, remote_molecule_dir)  # Ensure remote directory exists
                print(f"Transferring file {local_file_path} to {remote_molecule_dir}/x")
                scp.put(local_file_path.replace("\\", "/"), remote_path=f"{remote_molecule_dir}/x")
                time.sleep(1)  # Add delay between file transfers

def create_remote_script(molecule_names, remote_dir, template_path):
    """
    Create a script to run "tx", "define", and "cosmoprep" in each directory based on a template.
    """
    script_content = read_script(template_path)
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

        script_content += "tx\n"
        script_content += "if [ $? -eq 0 ]; then\n"
        script_content += "    echo 'tx ended normally'\n"
        script_content += "    ./run_define.sh\n"
        script_content += "    if [ $? -eq 0 ]; then\n"
        script_content += "        echo 'define ended normally'\n"
        script_content += "        ./run_cosmoprep.sh\n"
        script_content += "        if [ $? -eq 0 ]; then\n"
        script_content += "            echo 'cosmoprep ended normally'\n"
        script_content += "        else\n"
        script_content += "            echo 'cosmoprep failed'\n"
        script_content += "        fi\n"
        script_content += "    else\n"
        script_content += "        echo 'define failed'\n"
        script_content += "    fi\n"
        script_content += "else\n"
        script_content += "    echo 'tx failed'\n"
        script_content += "fi\n"
        script_content += "cd -\n"
        if generate_cosmo_format_files:
            script_content += f"sed -i 's|$cosmo_out file=out.ccf|$cosmo_out file={mol_name}.cosmo|' {remote_dir}/{mol_name}/control\n"
            print(f"Edited control file for {mol_name}")
        else:
            print(f"Warning: {mol_name} will generate a .ccf format file. Subsequent scripts may not work correctly.\n")
    return script_content

def create_define_script(define_script_path):
    """
    Read the define script from python directory.
    """
    return read_script(define_script_path)

def create_cosmoprep_script(cosmoprep_script_path):
    """
    Read the cosmoprep script from python directory.
    """
    return read_script(cosmoprep_script_path)

def create_subscript(mol_name, subscript_template_path):
    """
    Create a subscript file for the server based on a template in the python directory.
    """
    template_content = read_script(subscript_template_path)
    return template_content.replace("{mol_name}", mol_name)

def main():
    if not prepare_TMoleX_files_script:
        print("cmdline_TMoleX_process.py is disabled")
        return

    # Set up SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, port=port, username=username, password=password)

    # Clear remote directory
    print(f"Clearing remote directory: {remote_temp_dir}")
    clear_remote_directory(ssh, remote_temp_dir)

    # Convert SDF to individual molecule files
    coord_files_dir = os.path.join(list_folder, "COORD_files").replace("\\", "/")
    print(f"Converting SDF to files in: {coord_files_dir}")
    sdf_to_files(constants.vconf_batch_sdf_path, coord_files_dir)

    # Transfer files to remote server
    print(f"Transferring files to remote directory: {remote_temp_dir}")
    transfer_files_to_remote(coord_files_dir, remote_temp_dir, ssh)

    # Create scripts from templates
    define_script = create_define_script(define_script_path)
    cosmoprep_script = create_cosmoprep_script(cosmoprep_script_path)

    molecule_names = [filename for filename in os.listdir(coord_files_dir) if os.path.isfile(os.path.join(coord_files_dir, filename))]

    remote_script = create_remote_script(molecule_names, remote_temp_dir, remote_script_template_path)
    remote_script_path = f"{remote_temp_dir}/run_tx.sh"

    # Transfer main script to remote server
    with SCPClient(ssh.get_transport()) as scp:
        scp.putfo(io.StringIO(remote_script), remote_script_path)
        time.sleep(1)  # Add delay after transferring script

    for mol_name in molecule_names:
        remote_define_path = f"{remote_temp_dir}/{mol_name}/run_define.sh"
        remote_cosmoprep_path = f"{remote_temp_dir}/{mol_name}/run_cosmoprep.sh"
        remote_subscript_path = f"{remote_temp_dir}/{mol_name}/subscript"
        subscript_content = create_subscript(mol_name, subscript_template_path)

        with SCPClient(ssh.get_transport()) as scp:
            scp.putfo(io.StringIO(define_script), remote_define_path)
            time.sleep(1)  # Add delay after transferring define script
            scp.putfo(io.StringIO(cosmoprep_script), remote_cosmoprep_path)
            time.sleep(1)  # Add delay after transferring cosmoprep script
            scp.putfo(io.StringIO(subscript_content), remote_subscript_path)
            time.sleep(1)  # Add delay after transferring subscript

        ssh.exec_command(f"chmod +x {remote_define_path}")
        time.sleep(1)  # Add delay after making define script executable
        ssh.exec_command(f"chmod +x {remote_cosmoprep_path}")
        time.sleep(1)  # Add delay after making cosmoprep script executable
        ssh.exec_command(f"chmod +x {remote_subscript_path}")
        time.sleep(1)  # Add delay after making subscript executable

    ssh.exec_command(f"chmod +x {remote_script_path}")
    time.sleep(1)  # Add delay after making the main script executable

    stdin, stdout, stderr = ssh.exec_command(f"bash {remote_script_path}")
    time.sleep(1)  # Add delay after starting the script execution
    stdout_text = stdout.read().decode('utf-8')
    stderr_text = stderr.read().decode('utf-8')

    print(f"stdout: {stdout_text}")  # Output from the script execution DEBUG
    print(f"stderr for {mol_name}:\n{stderr_text}")  # Error output from the script execution DEBUG (More Useful)

    # List contents of each folder in remote_temp_dir
    for mol_name in molecule_names:
        remote_folder_path = f"{remote_temp_dir}/{mol_name}"
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 {remote_folder_path}")
        time.sleep(1)  # Add delay after each folder listing command
        folder_contents = stdout.read().decode('utf-8').strip().split('\n')
        folder_contents_str = ', '.join(folder_contents)
        print(f"{remote_folder_path}: {folder_contents_str}")

    ssh.close()

if __name__ == "__main__":
    main()
