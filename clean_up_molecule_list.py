import sys
import os
import pandas as pd
from constants import (
    compound_list_directory,
    list_folder,
    list_folder_name,
    extract_data_from_excel_list,
    generate_tsv_file,
    identifier_override,
    clean_up_molecule_list_script,
    default_vconf_settings,
    experimental_vconf_settings
)
from constants import use_default_vconf_settings, default_vconf_settings, experimental_vconf_settings, path_to_VCONF_outputs_folder, list_file_path, vconf_path, max_conformers, step_sampling, generate_conformers_using_vconf_script, compound_list_directory, list_folder_name
import constants
from console_utils import ConsoleStream  # Import ConsoleStream

# Check if the script is run from the GUI and set up the custom stream
if getattr(sys, 'frozen', False):
    from gui import app_instance  # Import the GUI app instance
    if app_instance:
        sys.stdout = ConsoleStream(app_instance.append_to_console)
        sys.stderr = ConsoleStream(app_instance.append_to_console)


def find_identifier_column(data, override=None):
    """
    Find the best identifier column based on priority or override.
    """
    priority_order = ['DTXSID', 'CAS', 'IUPAC', 'PREFERRED', 'NAME']
    columns = data.columns

    if override:
        for column in columns:
            if override.lower() in column.lower():
                return column

    for identifier in priority_order:
        for column in columns:
            if identifier in column.upper():
                return column

    raise KeyError("No suitable identifier column found.")


def extract_data(settings):
    """
    Extract data from an Excel file located in the specified directory and save it to a TSV file.
    """
    # Get the directory containing the SDF file and move up one directory
    base_dir = os.path.dirname(os.path.dirname(settings['SDF_FILENAME']))

    # print(base_dir)
    # print(os.listdir(base_dir))

    # Find the Excel file in the base directory
    excel_file = next((f for f in os.listdir(base_dir) if f.endswith('.xlsx')), None)
    if not excel_file:
        print("No Excel file found in the specified directory.")
        return

    # Construct the full file path
    file_path = os.path.join(base_dir, excel_file)

    # Load the Excel file, assuming headers are in the first row
    data = pd.read_excel(file_path, header=0)

    # Extract data from the appropriate identifier column and "SMILES" column
    try:
        identifier_column = find_identifier_column(data, identifier_override)
        dtxsid_data = data[identifier_column].dropna()
        smiles_data = data['SMILES'].dropna()
    except KeyError as e:
        print(f"Column not found in the Excel sheet: {e}")
        return

    # Create a new DataFrame with the extracted data
    combined_data = pd.DataFrame({
        'SMILES': smiles_data,
        identifier_column: dtxsid_data
    })

    # Generate the path for the output TSV file
    output_file = os.path.join(base_dir, f"{list_folder_name}.tsv")

    # Save the DataFrame to a TSV file without headers
    combined_data.to_csv(output_file, sep='\t', index=False, header=False)

    print(f"Data extracted and saved to {output_file}")


def generate_empty_tsv():
    """
    Generate an empty TSV file.
    """
    output_file = f"{compound_list_directory}\\{list_folder_name}\\{list_folder_name}.tsv"
    with open(output_file, 'w') as file:
        file.write('')
    print(f"Empty TSV file generated at {output_file}")


def main():
    if not clean_up_molecule_list_script:
        print("clean_up_molecule_list.py is disabled")
        return

    settings = default_vconf_settings if use_default_vconf_settings else experimental_vconf_settings

    if extract_data_from_excel_list:
        extract_data(settings)
    elif generate_tsv_file:
        generate_empty_tsv()
    else:
        print("No action taken. Set extract_data_from_excel_list or generate_tsv_file to True.")


if __name__ == "__main__":
    main()
