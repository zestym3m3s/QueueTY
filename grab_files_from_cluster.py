import os
import paramiko
from scp import SCPClient
from datetime import datetime
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

# Define global variable
timestamp_folder = ""


def scp_transfer_back(ssh, remote_dir, local_dir):
    """
    Transfer files back from remote to local.
    """
    local_target_dir = os.path.join(local_dir, "TMoleX_output")
    os.makedirs(local_target_dir, exist_ok=True)
    transferred = False
    with SCPClient(ssh.get_transport()) as scp:
        stdin, stdout, stderr = ssh.exec_command(f"ls -1 {remote_dir}")
        folders = stdout.read().decode().split()
        for folder in folders:
            if folder == "run_tx.sh":
                print(f"Skipping {folder}")
                continue
            remote_folder_path = f"{remote_dir}/{folder}"
            try:
                scp.get(remote_folder_path, recursive=True, local_path=local_target_dir)
                print(f"Transferred {folder} to {local_target_dir}")
                transferred = True

                # Check if the transfer was successful by verifying the existence of the transferred files locally
                if not os.path.exists(os.path.join(local_target_dir, folder)):
                    print(f"Transfer of {folder} failed. Retrying...")
                    scp.get(remote_folder_path, recursive=True, local_path=local_target_dir)

            except Exception as e:
                print(f"Failed to transfer {folder}: {e}")
    if not transferred:
        print("No files were transferred. Double check your timestamp folder.")
    return transferred


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
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {directory} && tar -xzf {tar_file} -C {directory} && rm -f {tar_file}")
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

    most_recent_folder = max(timestamped_folders, key=lambda x: datetime.strptime("_".join(x.split('_')[-5:]), "%Y_%m_%d_%H_%M"))
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
