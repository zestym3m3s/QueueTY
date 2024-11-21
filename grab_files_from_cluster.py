import hashlib
import os
import paramiko
from scp import SCPClient
from datetime import datetime
import importlib.util
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
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
list_folder = constants.list_folder
timestamp_folder = constants.timestamp_folder
pull_from_timestamped_folder = constants.pull_from_timestamped_folder
grab_files_from_cluster_script = constants.grab_files_from_cluster_script
default_vconf_settings = constants.default_vconf_settings
use_default_vconf_settings = constants.use_default_vconf_settings
experimental_vconf_settings = constants.experimental_vconf_settings
only_transfer_cosmo_file_bool = constants.only_transfer_cosmo_file
constants.remote_directory = remote_directory  # Update remote_directory
constants.remote_file_path = remote_file_path  # Update remote_file_path

# Recalculate remote_temp_dir if it depends on remote_directory
constants.remote_temp_dir = os.path.join(constants.remote_directory, constants.temp_dir).replace("\\", "/")
remote_temp_dir = constants.remote_temp_dir  # Use updated value


def verify_local_directory(local_dir, remote_dir, ssh):
    """
    Verify that the local directory has been successfully transferred by comparing file counts.
    """
    # Get file count from the remote directory
    stdin, stdout, stderr = ssh.exec_command(f"find {remote_dir} -type f | wc -l")
    remote_file_count = int(stdout.read().strip())

    # Get file count from the local directory
    local_file_count = sum([len(files) for r, d, files in os.walk(local_dir)])

    return remote_file_count == local_file_count


def calculate_md5(file_path):
    """Calculate the MD5 checksum of a local file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_local_file(local_file, remote_file, ssh):
    """
    Verify that the specific local file has been successfully transferred by comparing MD5 checksums.
    """
    # Calculate local MD5 checksum
    local_md5 = calculate_md5(local_file)

    # Get the remote MD5 checksum
    stdin, stdout, stderr = ssh.exec_command(f"md5sum {remote_file}")
    remote_md5 = stdout.read().decode().strip().split()[0]

    return local_md5 == remote_md5


def only_transfer_cosmo_file(cosmo_file, local_folder_path, ssh):
    """Transfer a single .cosmo file."""
    try:
        # Create a new SCP client for each transfer to avoid stale connections
        with SCPClient(ssh.get_transport()) as scp_client:
            scp_client.get(cosmo_file, local_path=local_folder_path)
            print(f"Transferred {cosmo_file} to {local_folder_path}")

        # Verify that the .cosmo file exists locally
        local_cosmo_file = os.path.join(local_folder_path, os.path.basename(cosmo_file))
        if os.path.exists(local_cosmo_file):
            print(f"Successfully verified transfer of {os.path.basename(cosmo_file)}")
            return True
        else:
            print(f"Verification failed for {os.path.basename(cosmo_file)}. Retrying...")
            with SCPClient(ssh.get_transport()) as scp_client:
                scp_client.get(cosmo_file, local_path=local_folder_path)

            # Retry verification after second attempt
            if os.path.exists(local_cosmo_file):
                print(f"Successfully verified transfer of {os.path.basename(cosmo_file)} on retry")
                return True
            else:
                print(f"Failed to verify transfer of {os.path.basename(cosmo_file)} after retry.")
                return False
    except Exception as e:
        print(f"Failed to transfer {cosmo_file}: {e}")
        return False


def scp_transfer_back(ssh, remote_dir, local_dir, max_workers=5):
    """
    Transfer files back from remote to local, optionally transferring only .cosmo files based on `only_transfer_cosmo_file_bool`.
    """
    local_target_dir = os.path.join(local_dir, "TMoleX_output")

    # Ensure the local target directory is cleared before starting the transfer
    if os.path.exists(local_target_dir):
        for root, dirs, files in os.walk(local_target_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))

    os.makedirs(local_target_dir, exist_ok=True)

    # List folders in remote_dir
    print("Listing top-level directories...")
    stdin, stdout, stderr = ssh.exec_command(f"ls -1 {remote_dir}")
    stdout.channel.recv_exit_status()  # Ensure the command completes
    folders = stdout.read().decode().split()

    if not folders:
        print("No directories found in the specified remote directory.")
        return False

    # Prepare folders for local storage
    for folder in folders:
        if folder != "run_tx.sh":
            local_folder_path = os.path.join(local_target_dir, folder)
            os.makedirs(local_folder_path, exist_ok=True)

    # Collect transfer tasks
    transfer_tasks = []

    # Process folders in batches of 5
    for folder in folders:
        if folder == "run_tx.sh":
            print(f"Skipping {folder}")
            continue

        remote_folder_path = f"{remote_dir}/{folder}"
        local_folder_path = os.path.join(local_target_dir, folder)

        if only_transfer_cosmo_file_bool:
            # Only transfer .cosmo files
            stdin, stdout, stderr = ssh.exec_command(f"find {remote_folder_path} -maxdepth 1 -type f -name '*.cosmo'")
        else:
            # Transfer all files
            stdin, stdout, stderr = ssh.exec_command(f"find {remote_folder_path} -maxdepth 1 -type f")

        stdout.channel.recv_exit_status()
        files_to_transfer = stdout.read().decode().strip().split("\n")
        files_to_transfer = [f for f in files_to_transfer if f]  # Remove empty entries

        if not files_to_transfer:
            print(f"No files found in {remote_folder_path}.")
            continue

        for file_path in files_to_transfer:
            transfer_tasks.append((file_path, local_folder_path))

    # Execute file transfers
    print(f"Starting file transfers with max workers: {max_workers}")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(transfer_file, file_path, local_folder_path, ssh)
                   for file_path, local_folder_path in transfer_tasks]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred during file transfer: {e}")

    print("Completed file transfers.")
    return True

def transfer_file(file_path, local_folder_path, ssh):
    """General function to transfer a file."""
    try:
        with SCPClient(ssh.get_transport()) as scp_client:
            scp_client.get(file_path, local_path=local_folder_path)
            print(f"Transferred {file_path} to {local_folder_path}")
        return True
    except Exception as e:
        print(f"Failed to transfer {file_path}: {e}")
        return False


def gzip_directory(ssh, directory):
    """
    Gzip the contents of a directory and replace the original directory with the gzipped archive.
    """
    stdin, stdout, stderr = ssh.exec_command(f"tar -czf {directory}.tar.gz -C {directory} . && rm -rf {directory}")
    stdout.channel.recv_exit_status()  # Wait for the command to complete


def unzip_directory(ssh, tar_file):
    """
    Unzip a tar.gz file and restore its contents to the original directory.
    """
    directory = tar_file.replace(".tar.gz", "")
    stdin, stdout, stderr = ssh.exec_command(
        f"mkdir -p {directory} && tar -xzf {tar_file} -C {directory} && rm -f {tar_file}")
    stdout.channel.recv_exit_status()  # Wait for the command to complete


def get_most_recent_timestamped_folder(ssh, remote_directory):
    """
    Get the most recently created timestamped folder.
    """
    stdin, stdout, stderr = ssh.exec_command(f"ls -1 {remote_directory}")
    folders = stdout.read().decode().split()
    timestamped_folders = []
    for folder in folders:
        folder_name = folder.replace(".tar.gz", "")
        try:
            timestamp = "_".join(folder_name.split('_')[-5:])
            datetime.strptime(timestamp, "%Y_%m_%d_%H_%M")
            timestamped_folders.append(folder_name)
        except ValueError:
            continue

    if not timestamped_folders:
        return None

    most_recent_folder = max(timestamped_folders,
                             key=lambda x: datetime.strptime("_".join(x.split('_')[-5:]), "%Y_%m_%d_%H_%M"))
    return most_recent_folder


def main():
    global timestamp_folder
    if not grab_files_from_cluster_script:
        print("grab_files_from_cluster.py is disabled")
        return

    settings = default_vconf_settings if use_default_vconf_settings else experimental_vconf_settings
    list_folder = os.path.dirname(os.path.dirname(settings['SDF_FILENAME']))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, port=port, username=username, password=password)

    gzipped = False
    pull_timestamp_folder_from_remote_server = ""  # Initialize the variable

    if pull_from_timestamped_folder:
        # Use the defined timestamp_folder if it's not empty
        if timestamp_folder != "":
            pull_timestamp_folder_from_remote_server = f"{remote_directory}/{timestamp_folder}"
            print(f"Using defined timestamp folder: {pull_timestamp_folder_from_remote_server}")
        else:
            # If timestamp_folder is empty, use the most recent one
            timestamp_folder = get_most_recent_timestamped_folder(ssh, remote_directory)
            if not timestamp_folder:
                print("No timestamped folders found.")
                ssh.close()
                return
            pull_timestamp_folder_from_remote_server = f"{remote_directory}/{timestamp_folder}"
            print(f"Using most recent timestamp folder: {pull_timestamp_folder_from_remote_server}")

        remote_dir = pull_timestamp_folder_from_remote_server

        # Check if the timestamp folder is gzipped
        stdin, stdout, stderr = ssh.exec_command(f"ls {pull_timestamp_folder_from_remote_server}.tar.gz")
        if stdout.channel.recv_exit_status() == 0:  # The file exists and is gzipped
            gzipped = True
            print(f"\nUnzipping the timestamped folder {timestamp_folder}...")
            unzip_directory(ssh, f"{pull_timestamp_folder_from_remote_server}.tar.gz")
            remote_dir = pull_timestamp_folder_from_remote_server
    else:
        remote_dir = remote_temp_dir

    print(f"\nTransferring files back to the local machine from {remote_dir}...")
    files_transferred = scp_transfer_back(ssh, remote_dir, list_folder)

    if files_transferred:
        print(f"File transfer complete. Look in {os.path.join(list_folder, 'TMoleX_output')} for your optimized files!")

    if pull_from_timestamped_folder and gzipped:
        # Rezip the timestamped folder if it was unzipped earlier
        print(f"\nRezipping the timestamped folder {timestamp_folder}...")
        gzip_directory(ssh, pull_timestamp_folder_from_remote_server)
        print(f"Timestamped folder rezipped: {pull_timestamp_folder_from_remote_server}.tar.gz")

    ssh.close()

if __name__ == "__main__":
    main()

