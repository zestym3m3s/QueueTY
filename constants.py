"""
Auto-generated constants file from GUI settings.
"""

import gui as gui_prop

# Variables for Clean Up Molecule List Script
clean_up_molecule_list_script = False
extract_data_from_excel_list = False
generate_tsv_file = False
identifier_override = ""

# Variables for VCONF Script
generate_conformers_using_vconf_script = True
max_conformers = 1500
step_sampling = False
use_default_vconf_settings = False

# Variables for Preparing TMoleX Files on the Remote Server
prepare_TMoleX_files_script = False
generate_cosmo_format_files = True

# Variable for Submitting the Prepared TMoleX files to the Cluster
submit_TMoleX_files_to_cluster_script = False

# Variables for Checking the Cluster's Queue and Copying Files to a Timestamped Folder
check_cluster_queue_script = False
copy_files_to_timestamped_folder = True
gzip_timestamped_folder = False
delete_temp_dir_after_transferring_to_timestamped_folder = False

# Variables for Pulling Data from the Cluster
grab_files_from_cluster_script = False
timestamp_folder = ""
pull_from_timestamped_folder = True

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
remote_file_path = ""

# Commonly Edited
list_folder_name = "40mix"
template_name = "def2-TZVP"

# Less Commonly Edited
temp_dir = "temp_tmole_dir"
server = ""
port = 22
username = ""
password = ""

# One and Done
compound_list_directory = fr"C:\Chemistry\Compound Lists"
vconf_path = fr"C:\Chemistry\Vconf_v2\vconf.exe"
remote_directory = "/home/tsvick/turbomol"

# Default VConf Settings
default_vconf_settings = {
    'SDF_FILENAME': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix.sdf", 
    'OUTPUT_LOG': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix.log", 
    'OUTPUT_SDF': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix_vconf.sdf", 
    'vconf_batch_sdf_path': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix_vconf_batchfile.sdf", 
    'FIRST_MOLECULE': 1, 
    'LAST_MOLECULE': None, 
    'SEARCH_MODE': "search", 
    'NUM_STEPS': 50000, 
    'MIN_RING_SEARCH_STEPS': 50, 
    'SEARCH_WIDTH': "0.5", 
    'RANDOM_SEEDS': "0000 0000 0000 0001", 
    'RESTRAINED_ATOMS': None, 
    'SULFONAMIDE_NITROGEN': False, 
    'DIELECTRIC_COEFFICIENT': "4.0", 
    'STEREOCHEMISTRY_RESTRICTIONS': "b", 
    'CHIRAL_PRIORITY': "pbc", 
    'FORMAL_CHARGE': True, 
    'DO_NOT_FILTER_OUTPUT': False, 
    'KEEP_UNFILTERED_CONFORMATIONS': False, 
    'ENERGY_CUTOFF': 3, 
    'DISTANCE_TOLERANCE': "2.5", 
    'ANGLE_TOLERANCE': "30.0", 
    'ENERGY_TOLERANCE': "5.0", 
    'MAX_RING_CONFS': 5, 
    'RING_ENERGY_CUTOFF': 1, 
    'MAX_RING_ATOMS': 200, 
    'NO_TIME_LIMITS': True, 
    'SETUP_TIME_LIMIT': 120, 
    'FILTER_TIME_LIMIT': 120, 
    'FORCEFIELD': "dreiding", 
    'USE_GENERALIZED_BORN_SOLVATION': False, 
    'NITROGEN_LONE_PAIR': False, 
    'KEEP_LOWEST_ENERGY_RING_COMBINATION': False, 
    'ADD_RING_SEARCH_STEPS': 200, 
    'RESONANCE_LIMIT': 1000, 
    'SUBSTITUENTS_LEVEL': "u", 
}

# Experimental VConf Settings
experimental_vconf_settings = {
    'SDF_FILENAME': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix.sdf", 
    'OUTPUT_LOG': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix.log", 
    'OUTPUT_SDF': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix_vconf.sdf", 
    'vconf_batch_sdf_path': fr"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\40mix_vconf_batchfile.sdf", 
    'FIRST_MOLECULE': 33, 
    'LAST_MOLECULE': 33, 
    'SEARCH_MODE': "search", 
    'NUM_STEPS': 500, 
    'MIN_RING_SEARCH_STEPS': 50, 
    'SEARCH_WIDTH': "0.5", 
    'RANDOM_SEEDS': "0000 0000 0000 0001", 
    'RESTRAINED_ATOMS': None, 
    'SULFONAMIDE_NITROGEN': False, 
    'DIELECTRIC_COEFFICIENT': "4.0", 
    'STEREOCHEMISTRY_RESTRICTIONS': "b", 
    'CHIRAL_PRIORITY': "pbc", 
    'FORMAL_CHARGE': True, 
    'DO_NOT_FILTER_OUTPUT': False, 
    'KEEP_UNFILTERED_CONFORMATIONS': False, 
    'ENERGY_CUTOFF': 5, 
    'DISTANCE_TOLERANCE': 25, 
    'ANGLE_TOLERANCE': 15, 
    'ENERGY_TOLERANCE': 3, 
    'MAX_RING_CONFS': 5, 
    'RING_ENERGY_CUTOFF': 1, 
    'MAX_RING_ATOMS': 200, 
    'NO_TIME_LIMITS': True, 
    'SETUP_TIME_LIMIT': 120, 
    'FILTER_TIME_LIMIT': 120, 
    'FORCEFIELD': "dreiding", 
    'USE_GENERALIZED_BORN_SOLVATION': False, 
    'NITROGEN_LONE_PAIR': False, 
    'KEEP_LOWEST_ENERGY_RING_COMBINATION': False, 
    'ADD_RING_SEARCH_STEPS': 200, 
    'RESONANCE_LIMIT': 1000, 
    'SUBSTITUENTS_LEVEL': "u", 
}

define_sh_content = """define << EOF\n\n\na coord\ndesy\nired\n*\nno\nb all def2-TZVP\n*\neht\n\n\n\nscf\niter\n200\n\ndft\non\n\nri\non\n\n*\nEOF"""
cosmoprep_sh_content = """cosmoprep << EOF\n\n\n\n\n\n\n\n\n\n\n\nr all o\n*\n\n\nEOF"""
subscript_sh_content = """#!/bin/bash\n#\n#$ -q speedy\n#$ -cwd\n#$ -j y\n#$ -S /bin/bash\n#$ -N {mol_name}\n#$ -pe orte 10\n#$ -R y\n\n######## ENTER YOUR TURBOMOLE INSTALLATION PATH HERE ##########\nexport TURBODIR=/state/partition1/TURBOMOLE/TURBOMOLE\n###############################################################\nexport PATH=$TURBODIR/scripts:$PATH\nexport PARA_ARCH=MPI\nexport PATH=$TURBODIR/bin/`sysname`:$PATH\nexport PARNODES=10\nulimit -s unlimited\nmodule load openmpi-x86_64\npwd\njobex -c 400 -ri > job.out"""
# Dependencies
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
remote_script_template_path = fr"{gui_prop.path_to_python_scripts}\remote_script_template.sh" 
icon_path_ico = fr"{gui_prop.path_to_python_scripts}\icon.ico"
icon_path_png = fr"{gui_prop.path_to_python_scripts}\icon.png"
remote_script_template_path = fr"{gui_prop.path_to_python_scripts}\remote_script_template.sh"
