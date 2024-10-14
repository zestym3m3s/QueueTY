import paramiko
import time
import sys
import os
from datetime import datetime
from collections import Counter
import importlib.util

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
remote_directory = constants.remote_directory
copy_files_to_timestamped_folder = constants.copy_files_to_timestamped_folder
check_cluster_queue_script = constants.check_cluster_queue_script
gzip_timestamped_folder = constants.gzip_timestamped_folder
delete_temp_dir_after_transferring_to_timestamped_folder = constants.delete_temp_dir_after_transferring_to_timestamped_folder
list_folder_name = constants.list_folder_name


def check_queue_status(ssh):
    """
    Check the status of the queue using qstat.
    """
    stdin, stdout, stderr = ssh.exec_command("qstat")
    queue_status = stdout.read().decode().strip().split('\n')
    return [line.split()[4] for line in queue_status[2:] if line.strip()]


def create_timestamped_directory(ssh, base_dir):
    """
    Create a timestamped directory in the remote directory.
    """
    timestamp = datetime.now().strftime(f"{list_folder_name}_%Y_%m_%d_%H_%M")
    new_dir = f"{base_dir}/{timestamp}"
    print(f"Creating timestamped directory: {new_dir}")
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {new_dir}")
    stdout.channel.recv_exit_status()  # Wait for the command to complete
    return new_dir


def gzip_directory(ssh, directory):
    """
    Gzip the contents of a directory and replace the original directory with the gzipped archive.
    """
    print(f"Starting gzipping of directory: {directory}")
    stdin, stdout, stderr = ssh.exec_command(f"tar -czf {directory}.tar.gz -C {directory} . && rm -rf {directory}")
    stdout.channel.recv_exit_status()  # Wait for the command to complete
    print(f"Finished gzipping of directory: {directory}")


def copy_processed_files(ssh, source_dir, target_dir):
    """
    Copy processed molecule folders to the new timestamped directory.
    """
    print(f"Starting copy from {source_dir} to {target_dir}")
    stdin, stdout, stderr = ssh.exec_command(f"cp -r {source_dir}/* {target_dir}")
    stdout.channel.recv_exit_status()  # Wait for the command to complete
    print(f"Finished copy from {source_dir} to {target_dir}")

    # Verify that the files were copied successfully
    stdin, stdout, stderr = ssh.exec_command(f"ls -1 {target_dir}")
    copied_files = stdout.read().decode().strip().split()
    if not copied_files:
        raise RuntimeError(f"Copying files from {source_dir} to {target_dir} failed. No files were found in the target directory.")
    else:
        print(f"Verified: Files successfully copied to {target_dir}.")


def delete_directory_contents(ssh, directory):
    """
    Delete the contents of a directory.
    """
    print(f"Starting deletion of directory contents: {directory}")
    stdin, stdout, stderr = ssh.exec_command(f"rm -rf {directory}/*")
    stdout.channel.recv_exit_status()  # Wait for the command to complete
    print(f"Finished deletion of directory contents: {directory}")


def main():
    if not check_cluster_queue_script:
        print("check_cluster_queue.py is disabled")
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, port=port, username=username, password=password)

    start_time = datetime.now()

    # Initial print before entering the loop
    job_states = check_queue_status(ssh)
    elapsed_time = datetime.now() - start_time
    elapsed_minutes = divmod(elapsed_time.total_seconds(), 60)[0]
    state_counts = Counter(job_states)
    state_summary = " | ".join(f"{state}: {count}" for state, count in state_counts.items())
    print(
        f"\rJob states at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {int(elapsed_minutes)} minutes since submission | {state_summary}",
        end='', flush=True)

    while True:
        job_states = check_queue_status(ssh)
        if not job_states:
            elapsed_time = datetime.now() - start_time
            elapsed_seconds = divmod(elapsed_time.total_seconds(), 1)[0]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\rAll Jobs Complete at {timestamp} in {int(elapsed_seconds)} seconds", end='')
            if copy_files_to_timestamped_folder:
                print("\nGenerating a timestamped folder!")
                timestamped_dir = create_timestamped_directory(ssh, remote_directory)
                copy_processed_files(ssh, remote_temp_dir, timestamped_dir)
                print(f"\nProcessed files copied to: {timestamped_dir}")
                if gzip_timestamped_folder:
                    print("Gzipping the timestamped folder...")
                    gzip_directory(ssh, timestamped_dir)
                    print(f"Timestamped folder gzipped: {timestamped_dir}.tar.gz")
            else:
                print("\nDid not generate a timestamped folder!")
            if delete_temp_dir_after_transferring_to_timestamped_folder:
                print("Deleting contents of the temporary directory...")
                delete_directory_contents(ssh, remote_temp_dir)
                print(f"Contents of {remote_temp_dir} deleted.")
            break
        else:
            elapsed_time = datetime.now() - start_time
            elapsed_minutes = divmod(elapsed_time.total_seconds(), 60)[0]
            state_counts = Counter(job_states)
            state_summary = " | ".join(f"{state}: {count}" for state, count in state_counts.items())
            print(
                f"\rJob states at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {int(elapsed_minutes)} minutes since submission | {state_summary}",
                end='', flush=True)
        time.sleep(120)

    print()
    ssh.close()


if __name__ == "__main__":
    main()
