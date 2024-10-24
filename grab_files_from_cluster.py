import hashlib
import os
import paramiko
from scp import SCPClient
from datetime import datetime
import importlib.util
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


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
server = constants.server
port = constants.port
username = constants.username
password = constants.password
remote_temp_dir = constants.remote_temp_dir
list_folder = constants.list_folder
remote_directory = constants.remote_directory
timestamp_folder = constants.timestamp_folder
pull_from_timestamped_folder = constants.pull_from_timestamped_folder
grab_files_from_cluster_script = constants.grab_files_from_cluster_script
default_vconf_settings = constants.default_vconf_settings
use_default_vconf_settings = constants.use_default_vconf_settings
experimental_vconf_settings = constants.experimental_vconf_settings
only_transfer_cosmo_files = True  # New toggle for .cosmo files only


# Define global variable
timestamp_folder = ""


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


def transfer_cosmo_file(cosmo_file, local_folder_path, ssh):
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
    Transfer files back from remote to local, utilizing multithreading for faster transfers.
    Process 5 folders at a time to avoid overwhelming the system.
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

    # Create all necessary folders first
    print("Listing top-level directories to find .cosmo files...")
    stdin, stdout, stderr = ssh.exec_command(f"ls -1 {remote_dir}")
    stdout.channel.recv_exit_status()  # Ensure the command completes
    folders = stdout.read().decode().split()

    if not folders:
        print("No directories found in the specified remote directory.")
        return False

    # Prepare all local folders before transfer
    for folder in folders:
        if folder != "run_tx.sh":
            local_folder_path = os.path.join(local_target_dir, folder)
            os.makedirs(local_folder_path, exist_ok=True)

    # Collect tasks for concurrent execution
    transfer_tasks = []

    # Process folders in batches of 5
    for i in range(0, len(folders), 5):
        batch_folders = folders[i:i + 5]

        for folder in batch_folders:
            if folder == "run_tx.sh":
                print(f"Skipping {folder}")
                continue

            remote_folder_path = f"{remote_dir}/{folder}"
            local_folder_path = os.path.join(local_target_dir, folder)

            if only_transfer_cosmo_files:
                # Only transfer .cosmo files inside each molecule's folder
                stdin, stdout, stderr = ssh.exec_command(
                    f"find {remote_folder_path} -maxdepth 1 -type f -name '*.cosmo'")
                stdout.channel.recv_exit_status()  # Ensure the command completes
                cosmo_files = stdout.read().decode().strip().split("\n")
                if not cosmo_files or cosmo_files == ['']:
                    print(f"No .cosmo files found in {remote_folder_path}.")
                    continue
                for cosmo_file in cosmo_files:
                    if cosmo_file:
                        # Add tasks to transfer each .cosmo file
                        transfer_tasks.append((cosmo_file, local_folder_path))

        # Use a persistent SCPClient for multithreading
        print(f"Processing batch of {len(batch_folders)} folders...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(transfer_cosmo_file, cosmo_file, local_folder_path, ssh)
                       for cosmo_file, local_folder_path in transfer_tasks]

            for future in as_completed(futures):
                try:
                    future.result()  # Retrieve results or catch exceptions
                except Exception as e:
                    print(f"An error occurred during file transfer: {e}")

        # Clear tasks after each batch
        transfer_tasks.clear()

    print("Completed file transfers.")
    return True


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
        if timestamp_folder == "":
            timestamp_folder = get_most_recent_timestamped_folder(ssh, remote_directory)
            if not timestamp_folder:
                print("No timestamped folders found.")
                ssh.close()
                return

        pull_timestamp_folder_from_remote_server = f"{remote_directory}/{timestamp_folder}"
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
