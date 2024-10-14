import paramiko
from constants import (
    server, port, username, password, remote_temp_dir, remote_directory,
    gzip_temp_directory, unzip_temp_directory, unzip_directory_by_name, gzip_directory_by_name,
    gzip_and_unzip_script, delete_file_path_toggle, delete_file_path
)


def gzip_directory(ssh, directory):
    """
    Gzip the contents of a directory and replace the original directory with the gzipped archive.
    """
    ssh.exec_command(f"tar -czf {directory}.tar.gz -C {directory} . && rm -rf {directory}")


def unzip_directory(ssh, tar_file):
    """
    Unzip a tar.gz file and restore its contents to the original directory.
    """
    directory = tar_file.replace(".tar.gz", "")
    ssh.exec_command(f"mkdir -p {directory} && tar -xzf {tar_file} -C {directory} && rm -f {tar_file}")


def delete_file_or_directory(ssh, path):
    """
    Delete a file or directory at the given path.
    """
    if path:
        # Check if the path is a directory
        stdin, stdout, stderr = ssh.exec_command(f"if [ -d {path} ]; then echo 'directory'; else echo 'file'; fi")
        result = stdout.read().decode().strip()

        if result == 'directory':
            ssh.exec_command(f"rm -r {path}")
            print(f"Deleted directory: {path}")
        elif result == 'file':
            ssh.exec_command(f"rm {path}")
            print(f"Deleted file: {path}")
        else:
            print(f"Path does not exist or is not accessible: {path}")


def main():
    if not gzip_and_unzip_script:
        print("manage_directories.py is disabled")
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, port=port, username=username, password=password)

    if gzip_temp_directory:
        print("Gzipping the temporary directory...")
        gzip_directory(ssh, remote_temp_dir)
        print(f"Temporary directory gzipped: {remote_temp_dir}.tar.gz")

    if unzip_temp_directory:
        print("Unzipping the temporary directory...")
        unzip_directory(ssh, f"{remote_temp_dir}.tar.gz")
        print(f"Temporary directory unzipped: {remote_temp_dir}")

    if unzip_directory_by_name:
        print(f"Unzipping the directory {unzip_directory_by_name}...")
        unzip_directory(ssh, f"{remote_directory}/{unzip_directory_by_name}.tar.gz")
        print(f"Directory unzipped: {unzip_directory_by_name}")

    if gzip_directory_by_name:
        print(f"Gzipping the directory {gzip_directory_by_name}...")
        gzip_directory(ssh, f"{remote_directory}/{gzip_directory_by_name}")
        print(f"Directory gzipped: {remote_directory}/{gzip_directory_by_name}.tar.gz")

    if delete_file_path_toggle and delete_file_path:
        delete_file_or_directory(ssh, f"{remote_directory}/{delete_file_path}")
        print(f"Deleted the file/folder at {remote_directory}/{delete_file_path}!")

    ssh.close()


if __name__ == "__main__":
    main()
