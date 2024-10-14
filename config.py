import gui as gui_path

# VConf tooltips dictionary
vconf_tooltips = {
    'SDF_FILENAME': 'Path to the molecule list .sdf file.',
    'OUTPUT_LOG': 'Log file path.',
    'OUTPUT_SDF': 'Conformers SDF file path.',
    'vconf_batch_sdf_path': 'Batch SDF path.',
    'FIRST_MOLECULE': 'First molecule in the SDF list to generate conformers for.',
    'LAST_MOLECULE': 'Last molecule in the SDF list to generate conformers for. None means all molecules in the .tsv list.',
    'SEARCH_MODE': 'Search type.',
    'NUM_STEPS': 'Number of searches per molecule.',
    'MIN_RING_SEARCH_STEPS': 'Number of searches per ring.',
    'SEARCH_WIDTH': 'Ratio of first stage searches.',
    'RANDOM_SEEDS': 'Random seeds formatted as a tuple.',
    'RESTRAINED_ATOMS': 'Connected atoms to be kept rigid. Look up formatting.',
    'SULFONAMIDE_NITROGEN': 'False = Planar, True = Pyramidal.',
    'DIELECTRIC_COEFFICIENT': 'Distance dependent dielectric coefficient.',
    'STEREOCHEMISTRY_RESTRICTIONS': 'Stereochemical constraints.',
    'CHIRAL_PRIORITY': 'Chirality assignment methods.',
    'FORMAL_CHARGE': 'True = add Hs based on formal charges, False = Assign formal charges based on Hs.',
    'DO_NOT_FILTER_OUTPUT': 'Do not filter the output conformations.',
    'KEEP_UNFILTERED_CONFORMATIONS': 'Save unfiltered conformations.',
    'ENERGY_CUTOFF': 'Energy cutoff (kcal/mol).',
    'DISTANCE_TOLERANCE': 'Distance tolerance (Angstroms).',
    'ANGLE_TOLERANCE': 'Angle and Dihedral angle tolerance (Degrees).',
    'ENERGY_TOLERANCE': 'Energy tolerance (kcal/mol).',
    'MAX_RING_CONFS': 'Maximum number of templates for each ring fragment.',
    'RING_ENERGY_CUTOFF': 'Energy cutoff for ring fragments (kcal/mol).',
    'MAX_RING_ATOMS': 'Size limit for ring fragment.',
    'NO_TIME_LIMITS': 'No Time Limits.',
    'SETUP_TIME_LIMIT': 'Time limit for molecule setup (sec).',
    'FILTER_TIME_LIMIT': 'Time limit for conformational filtering (sec).',
    'FORCEFIELD': 'Force field.',
    'USE_GENERALIZED_BORN_SOLVATION': 'Use generalized born solvation.',
    'NITROGEN_LONE_PAIR': 'Include nitrogen lone pairs.',
    'KEEP_LOWEST_ENERGY_RING_COMBINATION': 'Keep lowest energy ring combination.',
    'ADD_RING_SEARCH_STEPS': 'Number of additional searches per ring.',
    'RESONANCE_LIMIT': 'Resonance generation limit.',
    'SUBSTITUENTS_LEVEL': 'First level substituents.'
}

tooltips = {
    "clean_up_molecule_list_script": "Enable or disable the clean-up molecule list script.",
    "extract_data_from_excel_list": "Extract data from an Excel list.",
    "generate_tsv_file": "Generate a TSV file.",
    "identifier_override": "Override the identifier selection.",
    "generate_conformers_using_vconf_script": "Enable or disable the VCONF script.",
    "max_conformers": "Maximum number of conformers.",
    "step_sampling": "Enable or disable step sampling.",
    "use_default_vconf_settings": "Use default VCONF settings.",
    "prepare_TMoleX_files_script": "Enable or disable the TMoleX file preparation script.",
    "generate_cosmo_format_files": "Generate COSMO format files.",
    "submit_TMoleX_files_to_cluster_script": "Enable or disable the TMoleX file submission script.",
    "check_cluster_queue_script": "Enable or disable the cluster queue check script.",
    "copy_files_to_timestamped_folder": "Copy files to a timestamped folder.",
    "gzip_timestamped_folder": "Gzip the timestamped folder.",
    "delete_temp_dir_after_transferring_to_timestamped_folder": "Delete the temporary directory after transferring files.",
    "grab_files_from_cluster_script": "Enable or disable the file grabbing script from the cluster.",
    "timestamp_folder": "Specify the name of the timestamped folder.",
    "pull_from_timestamped_folder": "Pull files from the timestamped folder.",
    "write_new_inp_file_script": "Enable or disable the INP file writing script.",
    "extract_cosmo_files_to_cosmo_folder": "Extract COSMO files to the COSMO folder.",
    "write_inp_file": "Write the INP file.",
    "gzip_and_unzip_script": "Enable or disable the gzip and unzip script.",
    "gzip_temp_directory": "Gzip the temporary directory.",
    "gzip_directory_by_name": "Specify a directory to gzip.",
    "unzip_temp_directory": "Unzip the temporary directory.",
    "unzip_directory_by_name": "Specify a directory to unzip.",
    "delete_file_path_toggle": "Controls whether or not to delete the file at the path specified.",
    "delete_file_path": r"Enter the path of the file/folder you would like to delete. Use / instead of \ to indicate a subdirectory.",
    "check_remote_directory_script": "Enable or disable the remote directory checking script.",
    "remote_file_path": "Used to check the contents of the remote directory you enter. Leave empty to check the remote directory home."
}

# Script Toggle Variables and Sub-Variables with types
script_toggle_variables_without_gzip = [
    "clean_up_molecule_list_script",
    "generate_conformers_using_vconf_script",
    "prepare_TMoleX_files_script",
    "submit_TMoleX_files_to_cluster_script",
    "check_cluster_queue_script",
    "grab_files_from_cluster_script",
    "write_new_inp_file_script"
]

sub_variables = {
    "clean_up_molecule_list_script": {
        "extract_data_from_excel_list",
        "generate_tsv_file",
        "identifier_override"
    },
    "generate_conformers_using_vconf_script": {
        "max_conformers",
        "step_sampling",
        "use_default_vconf_settings"
    },
    "prepare_TMoleX_files_script": {
        "generate_cosmo_format_files"
    },
    "submit_TMoleX_files_to_cluster_script": {
    },
    "check_cluster_queue_script": {
        "copy_files_to_timestamped_folder",
        "gzip_timestamped_folder",
        "delete_temp_dir_after_transferring_to_timestamped_folder"
    },
    "grab_files_from_cluster_script": {
        "timestamp_folder",
        "pull_from_timestamped_folder"
    },
    "write_new_inp_file_script": {
        "extract_cosmo_files_to_cosmo_folder",
        "write_inp_file"
    },
    "gzip_and_unzip_script": {
        "gzip_temp_directory",
        "gzip_directory_by_name",
        "unzip_temp_directory",
        "unzip_directory_by_name",
        "delete_file_path_toggle",
        "delete_file_path"
    },
    "check_remote_directory_script": {
        "remote_file_path"
    }
}

# Dependencies
dependencies = {
    "list_folder", "list_file", "list_file_path", "path_to_VCONF_outputs_folder", "vconf_batch_sdf_path",
    "coord_folder", "remote_temp_dir", "define_script_path", "cosmoprep_script_path",
    "subscript_template_path", "remote_script_template_path"
}

# Dependencies Text
dependencies_text = """
# Dependencies
list_folder = fr"{compound_list_directory}\\{list_folder_name}"  # Full path to the folder containing the compound list. # Dependency
list_file = f"{list_folder_name}.tsv" # Dependency
list_file_path = fr"{compound_list_directory}\\{list_folder_name}\\{list_file}" # Dependency
path_to_VCONF_outputs_folder = fr"{compound_list_directory}\\{list_folder_name}\\VCONF_outputs" # Dependency
vconf_batch_sdf_path = fr"{path_to_VCONF_outputs_folder}\\{list_folder_name}_vconf_batchfile.sdf" # Dependency
coord_folder = fr"{list_folder}\\COORD_files" # Dependency
remote_temp_dir = f"{remote_directory}/{temp_dir}" # Dependency
define_script_path = fr"{gui_prop.path_to_python_scripts}\\define.sh" # Dependency
cosmoprep_script_path = fr"{gui_prop.path_to_python_scripts}\\cosmoprep.sh" # Dependency
subscript_template_path = fr"{gui_prop.path_to_python_scripts}\\subscript.sh" # Dependency
remote_script_template_path = fr"{gui_prop.path_to_python_scripts}\\remote_script_template.sh" # Dependency
icon_path_ico = fr"{gui_prop.path_to_python_scripts}\\icon.ico"
icon_path_png = fr"{gui_prop.path_to_python_scripts}\\icon.png"
"""

# Define sections and their respective variables
sections = {
    "Variables for Clean Up Molecule List Script": [
        "clean_up_molecule_list_script", "extract_data_from_excel_list", "generate_tsv_file",
        "identifier_override"
    ],
    "Variables for VCONF Script": [
        "generate_conformers_using_vconf_script", "max_conformers", "step_sampling",
        "use_default_vconf_settings"
    ],
    "Variables for Preparing TMoleX Files on the Remote Server": [
        "prepare_TMoleX_files_script", "generate_cosmo_format_files"
    ],
    "Variable for Submitting the Prepared TMoleX files to the Cluster": [
        "submit_TMoleX_files_to_cluster_script"
    ],
    "Variables for Checking the Cluster's Queue and Copying Files to a Timestamped Folder": [
        "check_cluster_queue_script", "copy_files_to_timestamped_folder", "gzip_timestamped_folder",
        "delete_temp_dir_after_transferring_to_timestamped_folder"
    ],
    "Variables for Pulling Data from the Cluster": [
        "grab_files_from_cluster_script", "timestamp_folder", "pull_from_timestamped_folder"
    ],
    "Variables for Write New INP File Script": [
        "write_new_inp_file_script", "extract_cosmo_files_to_cosmo_folder", "write_inp_file"
    ],
    "Separate Variables for Gzipping and Unzipping Directories": [
        "gzip_and_unzip_script", "gzip_temp_directory", "gzip_directory_by_name",
        "unzip_temp_directory", "unzip_directory_by_name", "delete_file_path_toggle", "delete_file_path"
    ],
    "Variable to view the remote directory contents": [
        "check_remote_directory_script", "remote_file_path"
    ],
    "Commonly Edited": [
        "list_folder_name", "template_name"
    ],
    "Less Commonly Edited": [
        "temp_dir", "server", "port", "username", "password"
    ],
    "One and Done": [
        "compound_list_directory", "vconf_path", "remote_directory", "path_to_python_scripts", "path_to_python_exe"
    ]
}

vconf_variables_dict = [
    'SDF_FILENAME',
    'OUTPUT_LOG',
    'OUTPUT_SDF',
    'vconf_batch_sdf_path',
    'FIRST_MOLECULE',
    'LAST_MOLECULE',
    'SEARCH_MODE',
    'NUM_STEPS',
    'MIN_RING_SEARCH_STEPS',
    'SEARCH_WIDTH',
    'RANDOM_SEEDS',
    'RESTRAINED_ATOMS',
    'SULFONAMIDE_NITROGEN',
    'DIELECTRIC_COEFFICIENT',
    'STEREOCHEMISTRY_RESTRICTIONS',
    'CHIRAL_PRIORITY',
    'FORMAL_CHARGE',
    'DO_NOT_FILTER_OUTPUT',
    'KEEP_UNFILTERED_CONFORMATIONS',
    'ENERGY_CUTOFF',
    'DISTANCE_TOLERANCE',
    'ANGLE_TOLERANCE',
    'ENERGY_TOLERANCE',
    'MAX_RING_CONFS',
    'RING_ENERGY_CUTOFF',
    'MAX_RING_ATOMS',
    'NO_TIME_LIMITS',
    'SETUP_TIME_LIMIT',
    'FILTER_TIME_LIMIT',
    'FORCEFIELD',
    'USE_GENERALIZED_BORN_SOLVATION',
    'NITROGEN_LONE_PAIR',
    'KEEP_LOWEST_ENERGY_RING_COMBINATION',
    'ADD_RING_SEARCH_STEPS',
    'RESONANCE_LIMIT',
    'SUBSTITUENTS_LEVEL'
]

script_paths = [
    ("define.sh", fr"{gui_path.path_to_python_scripts}\define.sh"),
    ("cosmoprep.sh", fr"{gui_path.path_to_python_scripts}\cosmoprep.sh"),
    ("subscript.sh", fr"{gui_path.path_to_python_scripts}\subscript.sh")
]
