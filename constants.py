"""
Auto-generated constants file from GUI settings.
"""

import gui as gui_prop

# Variables for Clean Up Molecule List Script
clean_up_molecule_list_script = True
extract_data_from_excel_list = True
generate_tsv_file = True
identifier_override = ""

# Variables for VCONF Script
generate_conformers_using_vconf_script = False
max_conformers = "1000000000"
step_sampling = False
use_default_vconf_settings = True
skip_vconf_exe = False

# Variables for Preparing TMoleX Files on the Remote Server
prepare_TMoleX_files_script = False
generate_cosmo_format_files = True
geometry_optimize_lowest_energy_structures = "100"
percent_enabled = True

# Variable for Submitting the Prepared TMoleX files to the Cluster
submit_TMoleX_files_to_cluster_script = False

# Variables for Checking the Cluster's Queue and Copying Files to a Timestamped Folder
check_cluster_queue_script = False
copy_files_to_timestamped_folder = True
gzip_timestamped_folder = False
delete_temp_dir_after_transferring_to_timestamped_folder = True
clean_temp_directory = True

# Variables for Pulling Data from the Cluster
grab_files_from_cluster_script = False
timestamp_folder = ""
pull_from_timestamped_folder = True
only_transfer_cosmo_file = True

# Variables for Write New INP File Script
write_new_inp_file_script = False
extract_cosmo_files_to_cosmo_folder = True
write_inp_file = True

# Separate Variables for Gzipping and Unzipping Directories
gzip_and_unzip_script = False
gzip_temp_directory = False
gzip_directory_by_name = ""
unzip_temp_directory = False
unzip_directory_by_name = ""
delete_file_path_toggle = False
delete_file_path = ""

# Variable to view the remote directory contents
check_remote_directory_script = False

# Commonly Edited
list_folder_name = "Template"
template_name = ""

# Less Commonly Edited
temp_dir = "temp_dir"
port = 22

# One and Done
compound_list_directory = "Path to Compound_List in PyCharm"
vconf_path = "Path to vconf.exe in PyCharm"

# Default VConf Settings
default_vconf_settings = {
    'SDF_FILENAME': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template.sdf", 
    'OUTPUT_LOG': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template.log", 
    'OUTPUT_SDF': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template_vconf.sdf", 
    'vconf_batch_sdf_path': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template_vconf_batchfile.sdf", 
    'FIRST_MOLECULE': 1, 
    'LAST_MOLECULE': "None", 
    'FORCEFIELD': "dreiding", 
    'USE_GENERALIZED_BORN_SOLVATION': False, 
    'SEARCH_MODE': "search", 
    'NUM_STEPS': 50000, 
    'RESTRAINED_ATOMS': "None", 
    'RANDOM_SEEDS': "1111 1111 1111 1111", 
    'SEARCH_WIDTH': "0.5", 
    'FORMAL_CHARGE': True, 
    'SULFONAMIDE_NITROGEN': False, 
    'CHIRAL_PRIORITY': "pbc", 
    'STEREOCHEMISTRY_RESTRICTIONS': "b", 
    'DIELECTRIC_COEFFICIENT': "4.0", 
    'NITROGEN_LONE_PAIR': False, 
    'RESONANCE_LIMIT': 1000, 
    'SUBSTITUENTS_LEVEL': "u", 
    'MIN_RING_SEARCH_STEPS': 50, 
    'ADD_RING_SEARCH_STEPS': 200, 
    'MAX_RING_CONFS': 5, 
    'MAX_RING_ATOMS': 200, 
    'RING_ENERGY_CUTOFF': 1, 
    'KEEP_LOWEST_ENERGY_RING_COMBINATION': False, 
    'ENERGY_CUTOFF': 5, 
    'ENERGY_TOLERANCE': 1, 
    'DISTANCE_TOLERANCE': "0.2", 
    'ANGLE_TOLERANCE': 30, 
    'DO_NOT_FILTER_OUTPUT': False, 
    'SETUP_TIME_LIMIT': 120, 
    'FILTER_TIME_LIMIT': 120, 
    'NO_TIME_LIMITS': True, 
    'KEEP_UNFILTERED_CONFORMATIONS': False, 
}

# Experimental VConf Settings
experimental_vconf_settings = {
    'SDF_FILENAME': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template.sdf", 
    'OUTPUT_LOG': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template.log", 
    'OUTPUT_SDF': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template_vconf.sdf", 
    'vconf_batch_sdf_path': fr"Path to Compound_List in PyCharm\Template\VCONF_outputs\Template_vconf_batchfile.sdf", 
    'FIRST_MOLECULE': 1, 
    'LAST_MOLECULE': "None", 
    'FORCEFIELD': "dreiding", 
    'USE_GENERALIZED_BORN_SOLVATION': False, 
    'SEARCH_MODE': "search", 
    'NUM_STEPS': 5000, 
    'RESTRAINED_ATOMS': "None", 
    'RANDOM_SEEDS': "1111 1111 1111 1111", 
    'SEARCH_WIDTH': "0.5", 
    'FORMAL_CHARGE': True, 
    'SULFONAMIDE_NITROGEN': False, 
    'CHIRAL_PRIORITY': "pbc", 
    'STEREOCHEMISTRY_RESTRICTIONS': "b", 
    'DIELECTRIC_COEFFICIENT': "4.0", 
    'NITROGEN_LONE_PAIR': False, 
    'RESONANCE_LIMIT': 1000, 
    'SUBSTITUENTS_LEVEL': "u", 
    'MIN_RING_SEARCH_STEPS': 50, 
    'ADD_RING_SEARCH_STEPS': 200, 
    'MAX_RING_CONFS': 5, 
    'MAX_RING_ATOMS': 200, 
    'RING_ENERGY_CUTOFF': 1, 
    'KEEP_LOWEST_ENERGY_RING_COMBINATION': False, 
    'ENERGY_CUTOFF': 5, 
    'ENERGY_TOLERANCE': 1, 
    'DISTANCE_TOLERANCE': "0.2", 
    'ANGLE_TOLERANCE': 30, 
    'DO_NOT_FILTER_OUTPUT': False, 
    'SETUP_TIME_LIMIT': 120, 
    'FILTER_TIME_LIMIT': 120, 
    'NO_TIME_LIMITS': True, 
    'KEEP_UNFILTERED_CONFORMATIONS': False, 
}

define_sh_content = """define << EOF\n\n\na coord\ndesy\nired\n*\nno\nb all def2-TZVP\n*\neht\n\n{charge}\n\n\nrex\n-int\n*\n-polish\n*\n*\n*\n*\n*\n*\n*\nscf\niter\n200\n\ndft\nfunc\nb3-lyp\non\n\nri\non\n\n*\nEOF"""
cosmoprep_sh_content = """cosmoprep << EOF\n\n\n\n\n\n\n\n\n\n\n\nr all o\n*\n\n\nEOF"""
subscript_sh_content = """#!/bin/bash\n#\n#$ -q speedy\n#$ -cwd\n#$ -j y\n#$ -S /bin/bash\n#$ -N {mol_name}\n#$ -pe orte 10\n#$ -R y\n\n######## ENTER YOUR TURBOMOLE INSTALLATION PATH HERE ##########\nexport TURBODIR=/state/partition1/TURBOMOLE/TURBOMOLE\n###############################################################\nexport PATH=$TURBODIR/scripts:$PATH\nexport PARA_ARCH=MPI\nexport PATH=$TURBODIR/bin/`sysname`:$PATH\nexport PARNODES=10\nulimit -s unlimited\nmodule load openmpi-x86_64\npwd\njobex -c 400 -ri > job.out"""
go_define_sh_content = """define << EOF\n\n\na coord\ndesy\nired\n*\nno\nb all def2-TZVP\n*\neht\n\n{charge}\n\n\nscf\niter\n200\n\ndft\non\n\nri\non\n\n*\nEOF"""
# Dependencies

server = "PLACEHOLDER"  # DO NOT CHANGE THIS!
username = "PLACEHOLDER"  # DO NOT CHANGE THIS!
password = "PLACEHOLDER"  # DO NOT CHANGE THIS!
remote_directory = "PLACEHOLDER"  # DO NOT CHANGE THIS!
remote_file_path = "PLACEHOLDER"  # DO NOT CHANGE THIS!
list_folder = fr"{compound_list_directory}\{list_folder_name}"  # Full path to the folder containing the compound list. 
list_file = f"{list_folder_name}.tsv" 
list_file_path = fr"{compound_list_directory}\{list_folder_name}\{list_file}" 
path_to_VCONF_outputs_folder = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs" 
vconf_batch_sdf_path = fr"{path_to_VCONF_outputs_folder}\{list_folder_name}_vconf_batchfile.sdf" 
coord_folder = fr"{list_folder}\COORD_files" 
remote_temp_dir = f"{remote_directory}/{temp_dir}" 
define_script_path = fr"{gui_prop.path_to_python_scripts}\define.sh" 
cosmoprep_script_path = fr"{gui_prop.path_to_python_scripts}\cosmoprep.sh" 
subscript_template_path = fr"{gui_prop.path_to_python_scripts}\subscript.sh" 
go_define_script_path = fr"{gui_prop.path_to_python_scripts}\go_define.sh" 
remote_script_template_path = fr"{gui_prop.path_to_python_scripts}\remote_script_template.sh" 
icon_path_ico = fr"{gui_prop.path_to_python_scripts}\icon.ico"
icon_path_png = fr"{gui_prop.path_to_python_scripts}\icon.png"
files_to_keep = {"x", "control", "energy", "job.last", "run_define.sh", "run_cosmoprep.sh", "subscript"}
