import time
import paramiko
import importlib.util
import os
import sys
import configparser

# Initialize ConfigParser to read from the sensitive_config.ini file
config = configparser.ConfigParser()
config.read('sensitive_config.ini')

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

constants_path = os.path.join(_internal_dir, 'constants.py')

spec = importlib.util.spec_from_file_location("constants", constants_path)
constants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(constants)

# Import constants
port = constants.port
submit_TMoleX_files_to_cluster_script = constants.submit_TMoleX_files_to_cluster_script
# Update constants with values from sensitive_config.ini
constants.remote_directory = remote_directory  # Update remote_directory
constants.remote_file_path = remote_file_path  # Update remote_file_path

# Recalculate remote_temp_dir if it depends on remote_directory
constants.remote_temp_dir = os.path.join(constants.remote_directory, constants.temp_dir).replace("\\", "/")
remote_temp_dir = constants.remote_temp_dir  # Use updated value

def submit_jobs(ssh, molecule_names, remote_dir):
    """
    Submit jobs using qsub, avoiding submission of run_tx.sh.
    """
    for mol_name in molecule_names:
        if mol_name != "run_tx.sh":
            command = f"cd {remote_dir}/{mol_name} && qsub subscript"
            stdin, stdout, stderr = ssh.exec_command(command)
            print(f"Submitted job for {mol_name}")
            print(f"stdout: {stdout.read().decode()}")
            print(f"stderr: {stderr.read().decode()}")
            time.sleep(0.5)


def main():
    if not submit_TMoleX_files_to_cluster_script:
        print("submit_remote_jobs_to_cluster.py is disabled")
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, port=port, username=username, password=password)

    # Gather molecule names from the remote directory
    print(f"Checking remote directory: {remote_temp_dir}")
    stdin, stdout, stderr = ssh.exec_command(f"ls -l {remote_temp_dir}")
    directory_contents = stdout.read().decode()
    print(f"Directory contents: \n{directory_contents}")
    molecule_names = [line.split()[-1] for line in directory_contents.splitlines() if line.startswith('d')]
    print(f"Molecule names: {molecule_names}")

    if not molecule_names:
        print("No molecules found in the remote directory.")
    else:
        submit_jobs(ssh, molecule_names, remote_temp_dir)

    ssh.close()


if __name__ == "__main__":
    main()
