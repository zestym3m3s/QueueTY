import paramiko
from constants import server, port, username, password, remote_directory, remote_file_path, \
    check_remote_directory_script
import os


def list_directory(remote_directory, remote_file_path):
    if not check_remote_directory_script:
        print("The script is not allowed to run.")
        return

    # Connect to the SSH server
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, port=port, username=username, password=password)

        # Ensure the path is correctly joined with a /
        full_path = os.path.join(remote_directory, remote_file_path).replace("\\", "/")

        # Execute the ls command
        command = f'ls -l {full_path}'
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8')
        errors = stderr.read().decode('utf-8')

        if output:
            print(output)
        if errors:
            print(f"Error occurred: {errors}")

        # Close the SSH connection
        ssh.close()

    except Exception as e:
        print(f"Error connecting to SSH server: {e}")

# Run the function once


list_directory(remote_directory, remote_file_path)
