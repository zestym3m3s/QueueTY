import paramiko
from constants import check_remote_directory_script, port
import os
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
