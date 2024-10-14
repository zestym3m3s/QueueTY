Made by Tristan Vick, ALERT lab (Advised by Dr. Diana Aga, Dr. Scott Simpson) Version beta-1.0 06/13/2024


QueueTy (pronounced Cutie, short for Queue, Thank You) is a program that lets users automate the computational calculations of molecules using VCONF, Turbomole and Cosmotherm. It extracts molecules from Excel files, generates a desired number of conformers for those molecules, sends those conformers to a remote server running SunGrid engine, sends those conformers to be computed by a cluster of compute nodes, and extracts the computed molecules back onto the users local computer, and packages the molecules into .inp files to be opened with CosmoThermX19 for property calculations. 

This is a beta version so please report bugs to tsvick@buffalo.edu whenever you encounter them. Try to be as detailed as possible!


/////////////////////////////
Installing / Getting Started
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

Installing Python:
1. Install Python to your computer.
2. Make sure you get the path to the python.exe executable and replace path_to_python_exe with the correct path
	EX: C:\Users\username\AppData\Local\Programs\Python\Python312\python.exe

Installing VCONF v2:
1. Install VCONF to your computer
2. Make sure you get the path to the vconf.exe executable at replace the vconf_path with the correct path
	EX: C:\Chemistry\Vconf_v2\vconf.exe

Directing to the Python Scripts:
1. QueueTy saves its settings as Python files so you may need to have Python installed before running any of the scripts. Once you're all set with installing Python, you need to make sure you tell QueueTy where to save its data to and read files from. I will try to fix this to be standalone.
2. This is just the path to the scripts folder in this directory. Make sure that you direct it to the script folder otherwise the script won't be able to save or load anything.
	EX: C:\Users\username\OneDrive\Desktop\QueueTy\scripts

Once all of these have been installed and correctly directed to, you should be all set. 


///////////////////////////////////////
More Information / Explanations / Tips
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

The GUI has 4 tabs:

1. Script Settings:
	- Script Parameters section lets you turn on and off different scripts to perform different automation actions.
	-  Editable Variables section lets you define paths to certain files and executables so the script can run properly and send files to the right places. Also includes the credentials that you can use to access the remote server.
	- Directory Editing section allows you to view the remote server contents and dig through them, and to gzip and unzip or delete files/folders on the remote server without having to open any programs.

2. Console:
	- Outputs the important script messages and tells you the progress of the scripts you’re running.

3. VConf Settings:
	- Lets you edit the vconf settings without opening vconf. Has default settings and experimental settings so you can tinker without dealing with re-entering settings.

4. Edit Files:
	- Lets you edit the define script (automate generation of tmole files) and cosmoprep script (automate generation of cosmo files) 
	- Also lets you edit the subscript file



Other Functionalities:
1. Save Default Settings / Load Default Settings:
	- If you want to save some default options like a backup while you tinker with things you can always reload them later.
2. Save on Exit:
	- I haven't figured out a clean way to save automatically on a timer but I have it so when you exit the GUI it autosaves the settings you had so you don’t lose progress.
3. VCONF path stuff:
	- Whenever you change the list folder name or the compound list directory path the GUI will automatically update the VCONF settings paths to show those changes. This unfortunately will return any vconf settings to what they were before you last exited/saved changes so double check things.
4. Little Tricks: 
	- There are some tricks I added to make the script more useful.
		- For clean_up_molecule_list_script
			* If extract_data_from_excel_list is unchecked and generate_tsv_file is checked it will generate a blank TSV file in the same directory.
			* identifier_override automatically prioritized DTXSID > CAS > IUPAC > Preferred > Name if it is left blank. It will search the Excel for a column with that text in the header to auto-label the data. If you have something custom like "ID" just enter ID and it will look for a column named ID instead of following that priority.
		- For max_conformers
			* The script will always include the lowest energy conformer regardless as the first entry.
		- For step_sampling
			* Step Sampling will take the highest energy conformer and the lowest and will divide that value by the max_conformers value. It will pick out conformers every that ratio.

		- For check_cluster_queue_script
			* The script will check every 5 minutes for updates to the queue. It will take 5 minutes before it displays anything in the console, so don't worry if it just stops abruptly here.

		- For timestamped_folder
			* If timestamped_folder is left blank the script will identify the most recent timestamped folder and will extract from that if pull_from_timestamped_folder is also enabled.

		- For remote_directory
			* This must have forwards slashes (/) instead of backslashes otherwise it won't work.

		- For gzip_and_unzip_scripts
			* Enabling this will disable the other scripts to prevent any issues.
			* When you enter a directory name in any of these text boxes don't include the file type (.tar.gz or similar).
		- For remote_file_path
			* To see the contents of a directory just enable, define a path, and run the script. It should output in console file information. Correct notation is really important here.
			* Leave blank to just see the remote_directory path contents.
			* When you enter a directory name in any of these text boxes don't include the file type (.tar.gz or similar).
			* You won't be able to look inside tar.gz files.
			* If you enter a path like temp_tmole_dir/Water_1 the script will look inside of Water_1 which helps for navigating your directory.



For the File Editor Tab:
These files are made to mimic what it would be like to type define in Cygwin and then follow the tree of options. The text files basically send the commands for you in a specific order. Any blank lines are like hitting the Enter key. For more information use this link:

https://www.turbomole.org/wp-content/uploads/2019/10/Tutorial_7-4.pdf

or Google Turbomole documentation or Turbomole tutorial. 



For the VCONF Settings tab:
The settings are a bit intimidating. If you would like help understanding them refer to the documentation from verachem for vconf_v2. Link provided:

https://www.verachem.com/wp-content/uploads/2013/05/vconf_v2.pdf

		

