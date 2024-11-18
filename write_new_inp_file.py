import os
import shutil
from collections import defaultdict
import pyperclip
import sys
import importlib

# Determine the correct path to constants.py
if getattr(sys, 'frozen', False):  # Running as an executable
    _internal_dir = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), '_internal')
else:  # Running as a script
    _internal_dir = os.path.dirname(os.path.abspath(__file__))

constants_path = os.path.join(_internal_dir, 'constants.py')

spec = importlib.util.spec_from_file_location("constants", constants_path)
constants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(constants)

from constants import (
    extract_cosmo_files_to_cosmo_folder,
    write_inp_file,
    write_new_inp_file_script,
    default_vconf_settings,
    use_default_vconf_settings,
    experimental_vconf_settings
)

settings = default_vconf_settings if constants.use_default_vconf_settings else constants.experimental_vconf_settings
list_folder = os.path.dirname(os.path.dirname(settings['SDF_FILENAME']))


def find_and_copy_cosmo_files(source_directory, target_directory):
    """Find all .cosmo files in the source directory and its subdirectories and copy them to the target directory."""
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    else:
        # Clear the target directory
        for file in os.listdir(target_directory):
            file_path = os.path.join(target_directory, file)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    cosmo_files = defaultdict(list)
    for root, _, files in os.walk(source_directory):
        for file in files:
            if file.endswith('.cosmo'):
                source_file = os.path.join(root, file)
                target_file = os.path.join(target_directory, file)
                try:
                    shutil.copy2(source_file, target_file)
                    # Group files by molecule base name
                    base_name = file.rsplit('_', 1)[0]
                    cosmo_files[base_name].append(file)
                except PermissionError:
                    print(f"PermissionError: Unable to copy {file}. It might be in use by another process.")
                    raise
    return cosmo_files


def rename_cosmo_files(cosmo_files, target_directory):
    """Rename .cosmo files according to the specified rules."""
    renamed_files = defaultdict(list)
    for base_name, files in cosmo_files.items():
        if len(files) > 1:
            for file in files:
                new_name = file.replace('_', '')
                old_path = os.path.join(target_directory, file)
                new_path = os.path.join(target_directory, new_name)
                os.rename(old_path, new_path)
                renamed_files[base_name].append(new_name)
        else:
            file = files[0]
            new_name = file.replace('_1', '')
            old_path = os.path.join(target_directory, file)
            new_path = os.path.join(target_directory, new_name)
            os.rename(old_path, new_path)
            renamed_files[base_name].append(new_name)
    return renamed_files


def generate_inp_file(cosmo_files, target_directory):
    """Write the .inp file based on the cosmo files found in the target directory."""
    list_folder = os.path.dirname(os.path.dirname(settings['SDF_FILENAME']))

    # Conditionally construct the inp_file_path based on template_name
    if constants.template_name:
        inp_file_path = os.path.join(list_folder, f"{constants.template_name}_{constants.list_folder_name}.inp")
    else:
        inp_file_path = os.path.join(list_folder, f"{constants.list_folder_name}.inp")

    with open(inp_file_path, 'w') as file:
        # First line
        file.write("ctd=BP_TZVP_19.ctd CDIR=../../../CTDATA-FILES LDIR=../../../../licensefile\n")
        # Second line
        file.write(f'FDIR="{target_directory}"\n')
        # Third line
        file.write("!!\n")
        # Lines for each .cosmo file or conformer set
        for base_name, files in cosmo_files.items():
            if len(files) > 1:
                file.write(f"[ f = {files[0]}\n")
                for cosmo_file in files[1:-1]:
                    file.write(f"  f = {cosmo_file}\n")
                file.write(f"  f = {files[-1]} ]\n")
            else:
                file.write(f"f = {files[0]}\n")
    return inp_file_path


def main():
    if not constants.write_new_inp_file_script:
        print("write_new_inp_file.py is disabled")
        return

    source_directory = os.path.join(list_folder, "TMoleX_output")
    target_directory = os.path.join(list_folder, "COSMO_files")

    # Ensure the source and target directories are different
    if source_directory == target_directory:
        print("Source and target directories must be different.")
        return

    # Extract .cosmo files if the variable is set to True
    if constants.extract_cosmo_files_to_cosmo_folder:
        cosmo_files = find_and_copy_cosmo_files(source_directory, target_directory)
        print("Successfully copied .cosmo files to COSMO_files folder")
        if not cosmo_files:
            print("No .cosmo files found in the directory.")
            return

        # Rename the .cosmo files
        renamed_cosmo_files = rename_cosmo_files(cosmo_files, target_directory)
    else:
        renamed_cosmo_files = defaultdict(list)
        for root, _, files in os.walk(target_directory):
            for file in files:
                if file.endswith('.cosmo'):
                    base_name = file.rsplit('_', 1)[0]
                    renamed_cosmo_files[base_name].append(file)

    # Write the .inp file if the variable is set to True
    if constants.write_inp_file:
        inp_file_path = generate_inp_file(renamed_cosmo_files, target_directory)
        print(f".inp file saved to {inp_file_path}")

        # Copy the .inp file path to the clipboard
        pyperclip.copy(inp_file_path)
        print("The path to the .inp file has been copied to the clipboard.")

    print(
        f"\nextract_cosmo_files_to_cosmo_folder is {'enabled' if constants.extract_cosmo_files_to_cosmo_folder else 'disabled'}")
    print(f"write_inp_file is {'enabled' if constants.write_inp_file else 'disabled'}")


if __name__ == "__main__":
    main()
