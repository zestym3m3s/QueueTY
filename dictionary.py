# Define VConf tooltips dictionary
vconf_tooltips = {
    'SDF_FILENAME': 'Path to the molecule list .sdf file.',
    'OUTPUT_LOG': 'Log file path.',
    'OUTPUT_SDF': 'Conformers SDF file path.',
    'vconf_batch_sdf_path': 'Batch SDF path.',
    'FIRST_MOLECULE': 'Index of the first molecule in the TSV file to be processed.\n\nDefault = 1',
    'LAST_MOLECULE': 'Last molecule in the TSV file to generate conformers for. None means all molecules in the .tsv list are run.',
    'SEARCH_MODE': 'Options are "search" or "prep". Related to finding ring conformers. \n\nsearch : computes ring conformations, links rings to form initial 3D molecular conformations, relaxes these conformations, and then carries out a full molecule conformational search starting from each initial conformation. Parameters controlling the individual ring searches are set with Ring Options.\n\nprep : computes ring conformations, links rings to form initial 3D molecular conformations, and relaxes these conformations. Parameters controlling the individual ring searches are set with Ring Options. This option is useful for quick 2D to 3D conversions and generating starting conformations for other applications, such as ligand-receptor docking algorithms, that treat rings as rigid',
    'NUM_STEPS': '***IMPORTANT***\n\nNumber of searches per molecule. Basically how thorough your conformer search is. 50,000 will search a lot, 500 will search a little. Can take a long time depending on how loose or strict your settings are.\n\nInteger number of search steps, where a step consists of a distortion of the molecule followed by energy minimization, to be carried out for each molecule in a search calculation. The number of search steps is the chief determinant of the thoroughness and duration of a calculation in search mode, but this parameter does not affect a calculation in prep mode.',
    'MIN_RING_SEARCH_STEPS': 'Minimum number of search steps per ring fragment.\n\nMinimum number of steps of distortion and minimization to be carried out for each ring fragment.\n\nDefault for “prep" mode: 50\n\nDefault for “search” mode: 1/2 of NUM_STEPS (see NUM_STEPS and SEARCH_WIDTH)',
    'SEARCH_WIDTH': 'Ratio of first stage searches.\n\nIn search mode, the initial 3D conformations built by stitching rings into the full molecule and relaxing the resulting conformations are used as starting points for full-molecule Tork searches. Each initial conformation is subjected to a preliminary Tork search, and the resulting conformations from all the initial conformations are compared. The one with the lowest energy is used as the single initial conformation for additional Tork search cycles. The SEARCH_WIDTH parameter allows the user to specify what fraction of the total NUM_STEPS search steps are allocated to the preliminary Tork searches from the initial 3D builds.\n\nA larger value of SEARCH_WIDTH causes Vconf to put more time into the preliminary broad exploration starting from the initial 3D builds.\n\nA smaller value of SEARCH_WIDTH causes Vconf to put more time into in-depth followup of the lowest energy conformation found during the preliminary searches.\n\nThe value of SEARCH_WIDTH must be between 0 and 1.0.',
    'RANDOM_SEEDS': 'Random seeds formatted as a tuple like 1234 5678 9101 1121.\n\nExplicitly providing Vconf with 4 integer random number seeds allows a prior calculation to be reproduced exactly. The seeds used in a run are written to the log file.',
    'RESTRAINED_ATOMS': 'Connected atoms to be kept rigid.\n\nA list of atom numbers (e.g., “3 4 27 29”) to be locked to their conformation in the input SDF file. At least 3 atoms must be listed, and these atoms must form a single connected fragment.',
    'SULFONAMIDE_NITROGEN': 'False = Planar, True = Pyramidal.\n\nThis option causes Vconf to treat sulfonamide nitrogen atoms as pyramidal.',
    'DIELECTRIC_COEFFICIENT': 'Distance dependent dielectric coefficient.\nDefault = 4',
    'STEREOCHEMISTRY_RESTRICTIONS': 'Each new conformation generated by Vconf in the course of the calculation is immediately checked for compliance with stereoisomer restrictions, and is discarded if it violates any operative restriction. The STEREOCHEMISTRY_RESTRICTIONS option controls which types of stereochemistry are read from the input SDF file and applied as restrictions.\n\nPossible Values:\nb : Filtering based upon both chirality and cis/trans isomerism.\nn : No chirality or cis/trans filtering.\nc : Filtering based upon only chirality\ni : Filter based upon only double bond cis/trans isomerism.\n\nDefault: b\n\nNote: Turning off these filters (e.g., STEREOCHEMISTRY_RESTRICTIONS n) may allow some alternate stereoisomers to be generated, but the coverage of the various isomers may not be good. If you wish to search across multiple stereo and cis/trans isomers, the results will be best if each configuration is listed separately in the input SDF file.\nNote: cis/trans isomers are determined from the 2D or 3D coordinates in the input SDF file. When the resulting cis/trans specifications are incorrect, extremely high energy conformations (>1000 kcal/mol) can result, and will be reported in the log file. Rarely, incorrect cis/trans specifications lead to distorted output conformations whose energies are still less than the 1000 kcal/mol output cutoff. If such a case is suspected, then: 1) check the cis/trans specification in the input SDF file, and/or 2) allow conformations with altered cis/ trans isomerism to be written out by using: STEREOCHEMISTRY_RESTRICTIONS c or STEREOCHEMISTRY_RESTRICTIONS n, as this may allow Vconf to fix the isomer state.',
    'CHIRAL_PRIORITY': 'Chirality assignment methods.\n\nThis option allows you to control what chirality information will be read from the input SDF file for use in conformational filtering. An SDF file can specify chirality with the parity field in the atom block, with stereo bond information in the bond block, and/or with the 3D coordinates of the atoms. There is no guarantee that these three chirality specifications will be mutually consistent. This is an intrinsic limitation of the SDF file format. The CHIRAL_PRIORITY flag allows the user to specify which of these specifications Vconf can use to obtain chirality information, and to assign priorities to them for use in case of inconsistency or missing information\n\nThe following options are available:\np : Use the parity field in the atom block.\nb : Use the stereo bond information in the bond block.\nc : Use 3D coordinates.\n\nAny combination of these options is allowed. If an option is not specified, chirality information will not be retrieved by that method. The order in which the options are listed on the command line determines their priorities: Vconf will attempt to recover chirality information from the first listed option, and will then fall back to the second and third, if they are listed. If the chirality of a chiral center cannot be assigned by any of the specified options, then Vconf writes a warning message to the log file and does not filter its output according to the chirality if this center. Vconf can detect and preserve the configuration of diastereomeric molecules. This function occasionally results in messages concerning the assignment of chirality to atoms which are not themselves chiral, but whose configuration, in combination with the configurations of other atoms, determines the diastereomer configuration of the molecule as a whole.\nDefault: pbc',
    'FORMAL_CHARGE': 'True = add Hs based on formal charges, False = Assign formal charges based on Hs.\n\nSpecifying FALSE causes Vconf to assign formal charges to atoms with the assumption that all hydrogen atoms are explicitly represented in the SDF file. For example, the formal charge of an ammonium will be determined by the number of hydrogen and non-hydrogen atoms to which it is bonded, along with the bond orders, irrespective of any formal charge that might be specified in the atom block of the SDF file. \n\nDefault: The default assumption is to assume that formal charges are correctly given in the atom block of the SDF file (TRUE). Vconf will then add hydrogens as needed to generate the correct valences. Using the FALSE option will cause valence checking errors and/or abnormal formal charges if the SDF file does not include all required hydrogens.',
    'DO_NOT_FILTER_OUTPUT': 'Do not filter the output conformations.\n\nDefault: False\n\nNote: Another option, KEEP_UNFILTERED_CONFORMATIONS, causes Vconf to write an additional file with the unfiltered conformations which can then be filtered separately with Vfilter. This alternative is convenient if one wishes to experiment with different filtering options without rerunning Vconf.',
    'KEEP_UNFILTERED_CONFORMATIONS': 'Save unfiltered conformations.\n\nSave an additional file of unfiltered conformations. For each molecule in the input SDF file, Vconf will write a separate file containing the unfiltered conformations and named “moleculeName_unfiltered.sdf”. (Note that the ‘_unfiltered.sdf’ file does not include the mirror images automatically generated as part of the filtering process (see computational methodolgy/Conformational Filtering) and therefore may contain fewer conformations than the ‘_confs.sdf’ file.)\n\nDefault: Do not save unfiltered conformations.',
    'ENERGY_CUTOFF': '***IMPORTANT***\n\nEnergy cutoff (kcal/mol).\n\nConformations with energies more than cutoff energy (kcal/mol) above the lowest energy will not be written out.\n\nDefault for “prep” mode: 5 kcal/mol\n\nDefault for “search” mode: 50 kcal/mol',
    'DISTANCE_TOLERANCE': '***IMPORTANT***\n\nDistance tolerance (Angstroms).\n\nTwo conformations whose radii of gyration differ by more than this many Å, are considered different and not subjected to further comparisons. Also, two conformations are considered different if their symmetry-corrected, atom-by-atom RMSD is greater than or equal to this distance in Å.\n\nDefault: 0.2 Å.',
    'ANGLE_TOLERANCE': '***IMPORTANT***\n\nAngle/Dihedral angle tolerance (Degrees).\n\nIf any pair of corresponding bond angles or dihedral angles of two molecules differ by more than this many degrees, the two conformations are regarded as different and no further comparisons are made.\n\nDefault: 30.0 degrees.',
    'ENERGY_TOLERANCE': '***IMPORTANT***\n\nEnergy tolerance (kcal/mol).\n\nMolecules that differ in energy by ENERGY_TOLERANCE kcal/mol or more are automatically considered to be distinct. Applying this criterion speeds filtering by reducing the number of conformations that need to be compared geometrically.\n\nDefault: 1.0 kcal/mol\n\nConformations that pass the energy filter are then filtered based on geometry. First, if the difference between the radii of gyration of two molecules is larger than DISTANCE_TOLERANCE, or any corresponding angles or dihedrals differ more than ANGLE_TOLERANCE, the two conformations are regarded as different. If the two conformations are not different by these criteria, then their atom-by-atom, symmetry-corrected root-mean-square deviation (rmsd) is computed. If this rmsd is greater than DISTANCE_TOLERANCE Å, then the higher energy conformation of the two is eliminated.',
    'MAX_RING_CONFS': 'Maximum number of ring conformations generated per fragment.\n\nMaximum number of ring conformation for each ring fragment. The value must be between 1 and 40.\n\nDefault: 5',
    'RING_ENERGY_CUTOFF': 'Energy cutoff for ring fragments (kcal/mol).\n\nVconf discards ring conformations more than RING_ENERGY_CUTOFF kcal/mol above the energy of the most stable conformation.\n\nDefault: 5.0 kcal/mol',
    'MAX_RING_ATOMS': 'Size limit for ring fragment.\n\nIndependent ring conformations will only be generated for ring fragments that have MAX_RING_ATOMS or fewer atoms, excluding substituents. The value of MAX_RING_ATOMS must be in the range 3 to 200. The conformations of larger ring systems are explored during the full molecule conformational search in search mode. The option to change the maximum size of ring fragment is useful in a number of situations in which search mode is used; e.g.:\n\n• The conformation of a large flexible ring which forms part of a larger molecule may be searched more thoroughly by not generating conformations for the ring fragment on its own but instead allowing it to be searched during the full-molecule Tork search. Reducing MAX_RING_ATOMS below the size of the ring accomplishes this.\n\n• When a molecule includes a mixture of large and small rings, the best results often are obtained if MAX_RING_ATOMS is set so that the smaller rings are searched independently of the full molecule while the larger rings are searched in the context of the entire molecule.\n\n• If more than 40 conformations are desired for a ring system, then setting MAX_RING_ATOMS below the size of the ring system will prevent the ring system from being processed as a ring fragment and will thus allow its conformations to be thoroughly explored during the full molecule search.\n\nDefault: The lesser of 200 and the number of heavy atoms in the molecule',
    'NO_TIME_LIMITS': 'No Time Limits.\n\nDefault: False.',
    'SETUP_TIME_LIMIT': 'Time limit for molecule setup (sec).\n\nTime limit for molecule setup, in seconds, where setup includes identification of ring fragments and alternate resonance forms, calculation of partial charges, and atom-typing. The occasional molecule that exceeds this time limit, usually due to an especially complex resonance system, is skipped to avoid delaying the run, and can be revisited later with a greater time limit or no time limit (see NO_TIME_LIMITS).\n\nDefault: 120 seconds',
    'FILTER_TIME_LIMIT': 'Time limit for conformational filtering (sec).\n\nTime limit for filtering the conformations for a molecule. Conformations of the occasional molecule that exceeds the filtering limit, usually due to complex symmetries, are written to the output unfiltered. These conformations can then be filtered separately with the standalone program Vfilter.\n\nDefault: The default is for Vconf to set FILTER_TIME_LIMIT to SETUP_TIME_LIMIT',
    'FORCEFIELD': 'Select forcefield to be used.\n\nPossible values for forcefield:\n\ngaff : Use the gaff forcefield. ‘.prmtop’ and ‘.mol2’ files for each molecule (generated by Antechamber) must be present in the same directory as the source sdf/mol file.\n\ndreiding : Use the modified Dreiding forcefield.\n\nDefault: dreiding',
    'USE_GENERALIZED_BORN_SOLVATION': 'Use generalized born solvation.\n\nTurns on the Hawkins 96 Generalized Born implicit solvation model.\n(J. Phys. Chem. 100:19824-19839, 1996)',
    'NITROGEN_LONE_PAIR': 'Include nitrogen lone pairs. \n\nA pyramidal nitrogen atom single-bonded to three different substituents can be viewed as pseudo-chiral. If the SDF file includes an explicit lone pair for such a nitrogen, Vconf treats it as chiral according to the same rules used for chiral carbons. If the SDF file does not include an explicit lone pair for such a nitrogen atom, then the default is not to treat it as chiral. However, specifying -nlp on the command line causes Vconf to attempt to establish its chirality using the current chiral priorities (see CHIRAL_PRIORITY), as detailed below. There is considerable potential for ambiguity and inconsistency when automatically adding lone pairs. Vconf handles only relatively well-defined cases that have been found to yield generally good results for a number of different compound catalogs and databases.\n\nAtom parity: If the SDF file includes the parity of the nitrogen atom and the nitrogen has three different explicit substituents, the parity is interpretable because Vconf assumes the lone pair to have an index higher than any non-hydrogen atom but lower than any hydrogen atom. If only two substituents are explicit and the third is a hydrogen atom that Vconf must add, then the atom parity could still be interpreted, but tests on compound databases indicate that the results are unreliable. Vconf therefore treats such nitrogen atoms as having an unspecified chirality.\n\nStereo bonds: Vconf interprets stereo bond information for a chiral nitrogen atom only if the input conformation is 2D on the xy plane, the nitrogen has explicit bonds to three listed atoms, and one of the bonds is a stereo (wedge) bond. In this case, Vconf assumes a lone pair with the same xy coordinates as the stereo-bonded atom, but with an oppositely oriented wedge bond, and will then determine if the nitrogen parity is well-defined.\n\n3D coordinates: Vconf uses the coordinates of the nitrogen’s three explicit substituents to ascertain the orientation of the pyramidal nitrogen. The lone pair is then positioned to establish a tetrahedral configuration, or one as near to tetrahedral as possible. If the nitrogen is essentially planar, as defined by an improper dihedral of less than 5 degrees, then the nitrogen will not be considered as “chiral” and its stereochemistry will not be locked. \n\nDefault: Do not interpret chirality information for pseudochiral nitrogen atoms unless the input file includes explicit lone pairs.',
    'KEEP_LOWEST_ENERGY_RING_COMBINATION': 'Keep lowest energy ring combination.\n\nInclude the full molecule conformation with the lowest sum of ring energies in the subsequent Tork search even if this conformation has a higher total energy than other conformations (see Computational Methodology).\n\nNote: This option is relevant only in search mode.',
    'ADD_RING_SEARCH_STEPS': 'Maximum number of additional search cycles for each ring fragment\n\nIf MIN_RING_SEARCH_STEPS of distortion and minimization have been carried out for a ring fragment without identifying any “good” conformations, additional sets of 50 steps will be carried out until at least one good conformation is found or until ADD_RING_SEARCH_STEPS step are completed. A ring conformation is considered good if its energy is less than 1000 kcal/mol and it satisfies all chirality and cis/trans criteria.\n\nDefault: 200',
    'RESONANCE_LIMIT': 'Resonance generation limit.\n\nStop generating resonance forms if any generation has more than resLimit states (see Vconf computational methodology/Molecule Setup). Otherwise resonance will run until the setup time limit is reached.\n\nDefault: 1000',
    'SUBSTITUENTS_LEVEL': 'First level substituents.\n\nThe atoms bonded to the ring atoms (“first level substituents”) can strongly affect the conformational preferences of the ring. Vconf provides several different options for these important atoms.\n\nPossible values for subLevel:\nh : Use only hydrogens as first level substituents. For the example molecule, the ring fragment would simply be cyclohexane\nu : Use united atoms for first level substituents. For the example, the first level substituents would all be hydrogen atoms, except that atom 1 would be linked to a united-atom representation of a methyl group. This option provides accuracy at low computational cost\na : Use all-atom first level substituents. All-atom methylcyclohexane would be used as the ring fragment.\n\nDefault: u'
}

tooltips = {
    "clean_up_molecule_list_script": "Enable or disable the clean-up molecule list script.",
    "extract_data_from_excel_list": "Extract SMILES and Identifiers from columns of an Excel list based on the header (top row) text.\n\nBest used in combination with CompTox's batch search tool, exporting as an Excel list.\n\nDefault Identifier Header Priority Order: 1. DTXSID, 2. CAS, 3. IUPAC, 4. PREFERRED, 5. NAME",
    "generate_tsv_file": "Generate a TSV file. If extract_data_from_excel_list is disabled this will generate an empty .tsv file.",
    "identifier_override": "Override the identifier selection priority ranking. Whatever the identifier column header is called is where the identifiers will be pulled from.",
    "generate_conformers_using_vconf_script": "Enable or disable the VCONF script.",
    "max_conformers": "Maximum number of conformers you want in the final batchfile. Set absurdly high to avoid unintentionally limiting conformer counts.",
    "step_sampling": "Step sampling takes the total number of conformers for a specific molecule and divides it by the max conformers value. Not reccomended since it biases towards higher energy (less important) conformers.",
    "use_default_vconf_settings": "Enable to use default VCONF settings (from the VCONF settings tab).",
    "skip_vconf_exe": "Skip running vconf.exe and only process '_conf' files. Use this to prevent overwriting existing VCONF search results.",
    "prepare_TMoleX_files_script": "Enable or disable the TMoleX file preparation script.",
    "generate_cosmo_format_files": "Generate COSMO format files. Highly recommended for COSMOthermX19.",
    "geometry_optimize_lowest_energy_structures": "Geometry Optimize this percent OR number of lowest energy structures. (See percent_enabled).",
    "percent_enabled": "Enable this to geometry optimize a PERCENT of the total conformers for each molecule, Disable this to optimize a NUMBER of lowest energy conformers.",
    "submit_TMoleX_files_to_cluster_script": "Enable this to submit your files to be calculated on the remote cluster nodes.",
    "check_cluster_queue_script": "Enable or disable the cluster queue check script. Leave all settings disabled to only monitor the queue. All settings below will run only after the queue is finished.",
    "copy_files_to_timestamped_folder": "Copy files to a timestamped folder.",
    "clean_temp_directory": "Deletes specified unwanted files after computing. Edit allowed files by adding to the files_to_keep variable in dictionary.py.",
    "gzip_timestamped_folder": "Gzip the timestamped folder to save space.",
    "delete_temp_dir_after_transferring_to_timestamped_folder": "Delete the temporary directory after transferring files. Be careful with large numbers of files as this may destroy your only backup.",
    "grab_files_from_cluster_script": "Enable or disable the file grabbing script for the remote server.",
    "timestamp_folder": "Specify the name of the timestamped folder. If left empty and pull_from_timestamped_folder is checked, the most recent timestamped folder will be used.",
    "pull_from_timestamped_folder": "Pull files from the timestamped folder.",
    "only_transfer_cosmo_file": "Only pulls the cosmo files from the remote server to save space on your local computer. Also reduces transferring time.",
    "write_new_inp_file_script": "Enable or disable the INP file writing script. INP files are readable with COSMOThermX19 and make importing conformer sets a breeze.",
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
    "remote_file_path": "Used to check the contents of the remote directory you enter. Leave empty to check the remote directory home.",
    "up_button": "Moves to the previous found keyword (use 'Ctrl + F' to keyword search)",
    "down_button": "Moves to the next found keyword (use 'Ctrl + F' to keyword search)"
}

# Script Toggle Variables and Sub-Variables with types
script_toggle_variables = {
    "clean_up_molecule_list_script",
    "generate_conformers_using_vconf_script",
    "prepare_TMoleX_files_script",
    "submit_TMoleX_files_to_cluster_script",
    "check_cluster_queue_script",
    "grab_files_from_cluster_script",
    "write_new_inp_file_script",
    "gzip_and_unzip_script",
    "check_remote_directory_script"
}

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
        "use_default_vconf_settings",
        "skip_vconf_exe"
    },
    "prepare_TMoleX_files_script": {
        "generate_cosmo_format_files",
        "geometry_optimize_lowest_energy_structures",
        "percent_enabled"
    },
    "submit_TMoleX_files_to_cluster_script": {
    },
    "check_cluster_queue_script": {
        "copy_files_to_timestamped_folder",
        "gzip_timestamped_folder",
        "delete_temp_dir_after_transferring_to_timestamped_folder",
        "clean_temp_directory"
    },
    "grab_files_from_cluster_script": {
        "timestamp_folder",
        "pull_from_timestamped_folder",
        "only_transfer_cosmo_file"
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
    "coord_folder", "remote_temp_dir", "define_script_path", "cosmoprep_script_path", "go_define_script_path",
    "subscript_template_path", "remote_script_template_path"
}

# Dependencies Text
dependencies_text = """
# Dependencies

server = "PLACEHOLDER"  # DO NOT CHANGE THIS!
username = "PLACEHOLDER"  # DO NOT CHANGE THIS!
password = "PLACEHOLDER"  # DO NOT CHANGE THIS!
remote_directory = "PLACEHOLDER"  # DO NOT CHANGE THIS!
remote_file_path = "PLACEHOLDER"  # DO NOT CHANGE THIS!
list_folder = fr"{compound_list_directory}\\{list_folder_name}"  # Full path to the folder containing the compound list. 
list_file = f"{list_folder_name}.tsv" 
list_file_path = fr"{compound_list_directory}\\{list_folder_name}\\{list_file}" 
path_to_VCONF_outputs_folder = fr"{compound_list_directory}\\{list_folder_name}\\VCONF_outputs" 
vconf_batch_sdf_path = fr"{path_to_VCONF_outputs_folder}\\{list_folder_name}_vconf_batchfile.sdf" 
coord_folder = fr"{list_folder}\\COORD_files" 
remote_temp_dir = f"{remote_directory}/{temp_dir}" 
define_script_path = fr"{gui_prop.path_to_python_scripts}\\define.sh" 
cosmoprep_script_path = fr"{gui_prop.path_to_python_scripts}\\cosmoprep.sh" 
subscript_template_path = fr"{gui_prop.path_to_python_scripts}\\subscript.sh" 
go_define_script_path = fr"{gui_prop.path_to_python_scripts}\\go_define.sh" 
remote_script_template_path = fr"{gui_prop.path_to_python_scripts}\\remote_script_template.sh" 
icon_path_ico = fr"{gui_prop.path_to_python_scripts}\\icon.ico"
icon_path_png = fr"{gui_prop.path_to_python_scripts}\\icon.png"
files_to_keep = {"x", "control", "energy", "job.last", "run_define.sh", "run_cosmoprep.sh", "subscript"}
"""

# Define sections and their respective variables
sections = {
    "Variables for Clean Up Molecule List Script": [
        "clean_up_molecule_list_script", "extract_data_from_excel_list", "generate_tsv_file",
        "identifier_override"
    ],
    "Variables for VCONF Script": [
        "generate_conformers_using_vconf_script", "max_conformers", "step_sampling",
        "use_default_vconf_settings", "skip_vconf_exe"
    ],
    "Variables for Preparing TMoleX Files on the Remote Server": [
        "prepare_TMoleX_files_script", "generate_cosmo_format_files", "geometry_optimize_lowest_energy_structures", "percent_enabled"
    ],
    "Variable for Submitting the Prepared TMoleX files to the Cluster": [
        "submit_TMoleX_files_to_cluster_script"
    ],
    "Variables for Checking the Cluster's Queue and Copying Files to a Timestamped Folder": [
        "check_cluster_queue_script", "copy_files_to_timestamped_folder", "gzip_timestamped_folder",
        "delete_temp_dir_after_transferring_to_timestamped_folder", "clean_temp_directory"
    ],
    "Variables for Pulling Data from the Cluster": [
        "grab_files_from_cluster_script", "timestamp_folder", "pull_from_timestamped_folder", "only_transfer_cosmo_file"
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

vconf_variables = [
    'SDF_FILENAME',
    'OUTPUT_LOG',
    'OUTPUT_SDF',
    'vconf_batch_sdf_path',
    'FIRST_MOLECULE',
    'LAST_MOLECULE',
    'FORCEFIELD',
    'USE_GENERALIZED_BORN_SOLVATION',
    'SEARCH_MODE',
    'NUM_STEPS',
    'RESTRAINED_ATOMS',
    'RANDOM_SEEDS',
    'SEARCH_WIDTH',
    'FORMAL_CHARGE',
    'SULFONAMIDE_NITROGEN',
    'CHIRAL_PRIORITY',
    'STEREOCHEMISTRY_RESTRICTIONS',
    'DIELECTRIC_COEFFICIENT',
    'NITROGEN_LONE_PAIR',
    'RESONANCE_LIMIT',
    'SUBSTITUENTS_LEVEL',
    'MIN_RING_SEARCH_STEPS',
    'ADD_RING_SEARCH_STEPS',
    'MAX_RING_CONFS',
    'MAX_RING_ATOMS',
    'RING_ENERGY_CUTOFF',
    'KEEP_LOWEST_ENERGY_RING_COMBINATION',
    'ENERGY_CUTOFF',
    'ENERGY_TOLERANCE',
    'DISTANCE_TOLERANCE',
    'ANGLE_TOLERANCE',
    'DO_NOT_FILTER_OUTPUT',
    'SETUP_TIME_LIMIT',
    'FILTER_TIME_LIMIT',
    'NO_TIME_LIMITS',
    'KEEP_UNFILTERED_CONFORMATIONS'
]

script_paths = [
    ("define.sh", "define.sh"),
    ("cosmoprep.sh", "cosmoprep.sh"),
    ("subscript.sh", "subscript.sh"),
    ("go_define.sh", "go_define.sh")
]
