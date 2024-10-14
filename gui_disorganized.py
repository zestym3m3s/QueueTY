import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from threading import Thread
from tkinter import PhotoImage
import paramiko
import subprocess
import os
import importlib.util
import warnings
import psutil  # Add this import

from dictionary import vconf_variables, vconf_tooltips, tooltips, script_toggle_variables_without_gzip, sub_variables, dependencies, dependencies_text, sections, script_paths
import constants as const

script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
path_to_python_scripts = script_dir

class Constants:
    def __init__(self):
        self.default_vconf_settings = {}
        self.experimental_vconf_settings = {}

const_2 = Constants()
vconf_settings = Constants()


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect_to_server()
        self.title("QueueTy")
        self.geometry("1200x800")
        self.state('zoomed')  # Open the GUI in maximized window mode

        # Set the window icon
        self.icon_image = PhotoImage(file='icon.png')
        self.iconphoto(False, self.icon_image)

        # Set the taskbar icon (only works with .ico files on Windows)
        try:
            self.wm_iconbitmap("icon.ico")
        except Exception as e:
            print(f"Error loading taskbar icon (ICO): {e}")

        # Initialize attributes for script toggles and editable variables
        self.script_toggle_vars = {}
        self.editable_vars = {}
        self.script_texts = {}
        self.script_toggle_vars_widgets = {}  # Initialize the dictionary to store toggle widgets
        self.sub_var_frames = {}  # Initialize sub_var_frames
        self.disabled_toggles = {}  # Initialize disabled_toggles

        self.gzip_and_unzip_var = tk.BooleanVar()  # Initialize here

        # Load settings from constants_last.txt
        self.load_settings("constants_last.txt")

        # Create tabs
        self.tabs = ttk.Notebook(self)
        self.script_settings_tab = ttk.Frame(self.tabs)
        self.file_editor_tab = ttk.Frame(self.tabs)
        self.console_tab = ttk.Frame(self.tabs)  # Add new console tab
        self.vconf_settings_tab = ttk.Frame(self.tabs)  # Add new VConf settings tab
        self.tabs.add(self.script_settings_tab, text="Script Settings")
        self.tabs.add(self.console_tab, text="Console")  # Add new console tab to the notebook
        self.tabs.add(self.vconf_settings_tab, text="VConf Settings")  # Add new VConf settings tab to the notebook
        self.tabs.add(self.file_editor_tab, text="File Editor")
        self.tabs.pack(expand=1, fill="both")

        # Make the Script Settings tab scrollable
        self.script_settings_canvas = tk.Canvas(self.script_settings_tab)
        self.script_settings_scrollbar = ttk.Scrollbar(self.script_settings_tab, orient="vertical",
                                                       command=self.script_settings_canvas.yview)
        self.scrollable_script_settings_frame = ttk.Frame(self.script_settings_canvas)

        self.scrollable_script_settings_frame.bind(
            "<Configure>",
            lambda e: self.script_settings_canvas.configure(
                scrollregion=self.script_settings_canvas.bbox("all")
            )
        )

        self.script_settings_canvas.create_window((0, 0), window=self.scrollable_script_settings_frame, anchor="nw")
        self.script_settings_canvas.configure(yscrollcommand=self.script_settings_scrollbar.set)

        self.script_settings_canvas.pack(side="left", fill="both", expand=True)
        self.script_settings_scrollbar.pack(side="right", fill="y")

        # Enable scrolling with mouse wheel for the script settings tab
        self.script_settings_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel_script_settings)

        # Main container for Script Settings tab
        self.main_frame = ttk.Frame(self.scrollable_script_settings_frame)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left frame for Script Parameters
        self.script_parameters_frame = ttk.LabelFrame(self.main_frame, text="Script Parameters")
        self.script_parameters_frame.grid(row=3, column=0, rowspan=1, padx=10, pady=10, sticky="nsew")

        # Right frame for Editable Variables and Directory Editing
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

        # Top-right frame for Editable Variables
        self.editable_variables_frame = ttk.LabelFrame(self.right_frame, text="Editable Variables")
        self.editable_variables_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Bottom-right frame for Directory Editing
        self.directory_editing_frame = ttk.LabelFrame(self.right_frame, text="Directory Editing")
        self.directory_editing_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Buttons for saving and running
        self.save_button = ttk.Button(self.main_frame, text="Save Settings", command=self.save_settings)
        self.save_button.grid(row=0, column=0, pady=10)
        self.run_button = ttk.Button(self.main_frame, text="Run Script", command=self.run_script)
        self.run_button.grid(row=1, column=0, pady=10)
        self.terminate_button = ttk.Button(self.main_frame, text="Terminate Script",
                                           command=self.terminate_script)  # Add this line
        self.terminate_button.grid(row=2, column=0, pady=10)  # Add this line
        self.save_default_button = ttk.Button(self.main_frame, text="Save New Default Settings",
                                              command=self.save_default_settings)
        self.save_default_button.grid(row=0, column=1, pady=10)
        self.load_default_button = ttk.Button(self.main_frame, text="Load Default Settings",
                                              command=self.load_default_settings)
        self.load_default_button.grid(row=1, column=1, pady=10)

        # Enable resizing of columns and rows
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.sub_var_frames = {}
        self.initial_toggle_states = {}
        self.special_toggle_vars = script_toggle_variables_without_gzip

        # Create sections for the GUI
        self.create_script_parameters_section()
        self.create_directory_editing_section()
        self.create_editable_variables_section()
        self.create_file_editor_section()
        self.create_console_tab()  # Add this line to create console tab
        self.create_vconf_settings_section()  # Add this line to create VConf settings tab

        # Bind the close event to save settings to constants_last.txt
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def browse_directory(self, var_name):
        initial_dir = self.editable_vars["compound_list_directory"].get() if var_name == "list_folder_name" else "/"
        directory = filedialog.askdirectory(initialdir=initial_dir, title="Select Directory")
        if directory:
            directory = directory.replace('/', '\\')
            if var_name == "list_folder_name":
                folder_name = os.path.basename(directory)
                self.editable_vars[var_name].delete(0, tk.END)
                self.editable_vars[var_name].insert(0, folder_name)
            else:
                self.editable_vars[var_name].delete(0, tk.END)
                self.editable_vars[var_name].insert(0, directory)
            if var_name in ["compound_list_directory", "list_folder_name"]:
                self.update_vconf_paths()

    def browse_file(self, var_name):
        file_path = filedialog.askopenfilename(initialdir="/", title="Select File",
                                               filetypes=[("Executables", "*.exe")])
        if file_path:
            file_path = file_path.replace('/', '\\')
            self.editable_vars[var_name].delete(0, tk.END)
            self.editable_vars[var_name].insert(0, file_path)

    def browse_remote_directory(self, var_name):
        initial_dir = self.editable_vars["remote_directory"].get() if var_name != "remote_directory" else "/"
        remote_path = self.remote_directory_dialog(initial_dir, browse_files=(var_name != "remote_directory"))
        if remote_path:
            if var_name == "remote_directory" and remote_path.endswith('/'):
                remote_path = remote_path.rstrip('/')
            elif var_name in ["delete_file_path", "gzip_directory_by_name", "unzip_directory_by_name",
                              "timestamp_folder"]:
                remote_directory = self.editable_vars["remote_directory"].get()
                if remote_directory and remote_path.startswith(remote_directory):
                    remote_path = remote_path[len(remote_directory):].lstrip('/')
                if var_name == "timestamp_folder" and remote_path.endswith(".tar.gz"):
                    remote_path = remote_path[:-7]
            self.editable_vars[var_name].delete(0, tk.END)
            self.editable_vars[var_name].insert(0, remote_path.replace('\\', '/'))
            if var_name in ["compound_list_directory", "list_folder_name", "remote_directory"]:
                self.update_vconf_paths()

    def connect_to_server(self):
        server = const.server
        port = const.port
        username = const.username
        password = const.password
        try:
            self.ssh_client.connect(server, port, username, password)
        except Exception as e:
            self.append_to_console(f"Failed to connect to server: {e}")

    def remote_directory_dialog(self, initial_dir, browse_files=False):
        current_dir = initial_dir
        selected = None

        def refresh_listbox():
            nonlocal current_dir
            stdin, stdout, stderr = self.ssh_client.exec_command(f'ls -p {current_dir}')
            dir_list = stdout.read().decode().splitlines()
            dir_listbox.delete(0, tk.END)
            dir_listbox.insert(tk.END, '..')
            for item in dir_list:
                if browse_files or item.endswith('/'):
                    dir_listbox.insert(tk.END, item)

        def go_into_folder():
            nonlocal current_dir
            selected_item = dir_listbox.get(tk.ACTIVE)
            if selected_item and selected_item != '..':
                selected_dir = os.path.join(current_dir, selected_item).replace('\\', '/')
                stdin, stdout, stderr = self.ssh_client.exec_command(f'cd {selected_dir} && pwd')
                if not stderr.read().decode():
                    current_dir = selected_dir
                    current_dir_label.config(text=f"Current directory: {current_dir}")
                    refresh_listbox()

        def go_up_folder():
            nonlocal current_dir
            current_dir = os.path.dirname(current_dir).replace('\\', '/')
            current_dir_label.config(text=f"Current directory: {current_dir}")
            refresh_listbox()

        def select_folder():
            nonlocal selected, current_dir
            try:
                selected_item = dir_listbox.get(tk.ACTIVE)
                if selected_item and selected_item != '..':
                    selected = os.path.join(current_dir, selected_item).replace('\\', '/')
                else:
                    selected = current_dir
            except:
                selected = current_dir
            dialog.destroy()

        dialog = tk.Toplevel(self)
        dialog.title("Remote Directory Browser")
        dialog.geometry("400x300")

        current_dir_label = tk.Label(dialog, text=f"Current directory: {current_dir}", font=("TkDefaultFont", 12))
        current_dir_label.pack(pady=5)

        dir_frame = ttk.Frame(dialog)
        dir_frame.pack(fill="both", expand=True, padx=10, pady=10)

        dir_listbox = tk.Listbox(dir_frame)
        dir_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(dir_frame, orient="vertical", command=dir_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        dir_listbox.config(yscrollcommand=scrollbar.set)

        refresh_listbox()

        dir_listbox.bind("<Double-Button-1>", lambda event: go_into_folder())
        dir_listbox.bind("<Return>", lambda event: go_into_folder())

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=5)

        into_button = ttk.Button(button_frame, text="Go Into Folder", command=go_into_folder)
        into_button.pack(side="left", padx=5)

        up_button = ttk.Button(button_frame, text="Go Up Folder", command=go_up_folder)
        up_button.pack(side="left", padx=5)

        select_button = ttk.Button(button_frame, text="Select Folder", command=select_folder)
        select_button.pack(side="right", padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: dialog.destroy())
        cancel_button.pack(side="right", padx=5)

        self.wait_window(dialog)

        return selected

    def create_vconf_settings_section(self):
        self.vconf_settings_canvas = tk.Canvas(self.vconf_settings_tab)
        self.vconf_settings_scrollbar = ttk.Scrollbar(self.vconf_settings_tab, orient="vertical",
                                                      command=self.vconf_settings_canvas.yview)
        self.scrollable_vconf_settings_frame = ttk.Frame(self.vconf_settings_canvas)

        self.scrollable_vconf_settings_frame.bind(
            "<Configure>",
            lambda e: self.vconf_settings_canvas.configure(
                scrollregion=self.vconf_settings_canvas.bbox("all")
            )
        )

        self.vconf_settings_canvas.create_window((0, 0), window=self.scrollable_vconf_settings_frame, anchor="nw")
        self.vconf_settings_canvas.configure(yscrollcommand=self.vconf_settings_scrollbar.set)

        self.vconf_settings_canvas.pack(side="left", fill="both", expand=True)
        self.vconf_settings_scrollbar.pack(side="right", fill="y")

        # Enable scrolling with mouse wheel
        self.bind_all("<MouseWheel>", self.on_mouse_wheel_script_settings)

        # Create columns
        self.scrollable_vconf_settings_frame.columnconfigure(0, weight=1)
        self.scrollable_vconf_settings_frame.columnconfigure(1, weight=1)

        # Create subsections in different columns
        self.create_vconf_subsection(self.scrollable_vconf_settings_frame, "Default VConf Settings",
                                     const_2.default_vconf_settings, 0)
        self.create_vconf_subsection(self.scrollable_vconf_settings_frame, "Experimental VConf Settings",
                                     const_2.experimental_vconf_settings, 1)

    def on_mouse_wheel_script_settings(self, event):
        current_tab = self.tabs.select()
        if current_tab == str(self.script_settings_tab):
            self.script_settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif current_tab == str(self.vconf_settings_tab):
            self.vconf_settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def terminate_script(self):
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['pid'] != current_pid and proc.info['name'].lower() == 'python.exe':
                try:
                    proc.terminate()
                    proc.wait(timeout=5)  # Wait up to 5 seconds for the process to terminate
                    self.append_to_console(f"Terminated process: {proc.info['pid']}")
                except psutil.NoSuchProcess:
                    self.append_to_console(f"Process {proc.info['pid']} does not exist")
                except psutil.TimeoutExpired:
                    self.append_to_console(f"Failed to terminate process {proc.info['pid']} within timeout")

    def create_vconf_subsection(self, parent, title, variables, column):
        subsection_frame = ttk.LabelFrame(parent, text=title)
        subsection_frame.grid(row=0, column=column, padx=10, pady=5, sticky="nsew")

        row_counter = 0
        for var_name, var_value in variables.items():
            var_label = ttk.Label(subsection_frame, text=var_name, font=("TkDefaultFont", 10))
            var_label.grid(row=row_counter, column=0, sticky="w", padx=5, pady=2)

            # Use the tooltips dictionary
            tooltip_text = vconf_tooltips.get(var_name, f"This is the {var_name.replace('_', ' ').title()}.")
            self.create_tooltip(var_label, tooltip_text)

            var_entry = ttk.Entry(subsection_frame, font=("TkDefaultFont", 10), width=40)
            var_entry.insert(0, str(var_value))
            var_entry.grid(row=row_counter, column=1, sticky="w", padx=5, pady=2)
            self.create_tooltip(var_entry, tooltip_text)

            self.editable_vars[f"{title}_{var_name}"] = var_entry

            row_counter += 1

    def create_console_tab(self):
        self.console_text = tk.Text(self.console_tab, state='disabled', wrap='word')
        self.console_text.pack(expand=1, fill='both')
        self.run_button_console = ttk.Button(self.console_tab, text="Run Script", command=self.run_script)
        self.run_button_console.pack(pady=5)
        self.terminate_button_console = ttk.Button(self.console_tab, text="Terminate Script", command=self.terminate_script)
        self.terminate_button_console.pack(pady=5)

    def append_to_console(self, text):
        self.console_text.config(state='normal')
        self.console_text.insert(tk.END, text + "\n")
        self.console_text.config(state='disabled')
        self.console_text.see(tk.END)

    def run_script(self):
        self.save_settings()  # Save general settings
        self.console_text.config(state='normal')
        self.console_text.delete('1.0', tk.END)
        self.console_text.config(state='disabled')
        thread = Thread(target=self.execute_script, args=([],), daemon=True)
        thread.start()

    def execute_script(self, command):
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
        script_path = os.path.join(script_dir, 'main.py')  # Construct the path to main.py

        def handle_warnings(message, category, filename, lineno, file=None, line=None):
            self.append_to_console(f"Warning: {message} in {filename}, line {lineno}")

        # Capture warnings
        warnings.showwarning = handle_warnings

        try:
            # Use the current Python interpreter to run the script
            process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Capture and log stdout
            def capture_stdout(pipe):
                for line in iter(pipe.readline, ''):
                    self.append_to_console(line.strip())
                pipe.close()

            # Capture and log stderr
            def capture_stderr(pipe):
                for line in iter(pipe.readline, ''):
                    self.append_to_console(f"ERROR: {line.strip()}")
                pipe.close()

            stdout_thread = Thread(target=capture_stdout, args=(process.stdout,))
            stderr_thread = Thread(target=capture_stderr, args=(process.stderr,))
            stdout_thread.start()
            stderr_thread.start()

            stdout_thread.join()
            stderr_thread.join()
            process.wait()
        except Exception as e:
            self.append_to_console(f"An error occurred: {e}")

    def create_script_parameters_section(self):
        self.script_row_counter = 0

        for attr in script_toggle_variables_without_gzip:
            value = getattr(const, attr, None)
            if value is not None:
                self.create_toggle_with_sub_variables(self.script_parameters_frame, attr, value)
                self.initial_toggle_states[attr] = value
                self.script_row_counter += 2

        self.script_settings_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel_script_settings)

    def add_browse_button_to_var(self, var_name, parent_frame):
        var_entry = self.editable_vars.get(var_name)
        if var_entry:
            browse_button = ttk.Button(parent_frame, text="Browse",
                                       command=lambda: self.browse_remote_directory(var_name))
            var_entry.grid(row=var_entry.grid_info()["row"], column=1, sticky="w", padx=5, pady=2)
            browse_button.grid(row=var_entry.grid_info()["row"], column=2, sticky="w", padx=5, pady=2)

    def create_directory_editing_section(self):
        self.gzip_and_unzip_var = tk.BooleanVar(value=const.gzip_and_unzip_script)
        self.create_toggle_with_sub_variables(self.directory_editing_frame, "gzip_and_unzip_script",
                                              const.gzip_and_unzip_script, is_directory_editing=True)
        self.sub_var_frames["gzip_and_unzip_script"] = self.directory_editing_frame.winfo_children()[1]
        self.script_toggle_vars_widgets["gzip_and_unzip_script"] = self.directory_editing_frame.winfo_children()[0]

        self.check_remote_directory_var = tk.BooleanVar(value=const.check_remote_directory_script)
        self.create_toggle_with_sub_variables(self.directory_editing_frame, "check_remote_directory_script",
                                              const.check_remote_directory_script, is_directory_editing=True)
        self.sub_var_frames["check_remote_directory_script"] = self.directory_editing_frame.winfo_children()[3]
        self.script_toggle_vars_widgets["check_remote_directory_script"] = \
            self.directory_editing_frame.winfo_children()[2]

    def create_editable_variables_section(self):
        self.create_editable_subsection(self.editable_variables_frame, "Commonly Edited", [
            ("list_folder_name", const.list_folder_name,
             "This is the name of the folder where important files are stored."),
            ("template_name", const.template_name, "Change this if you change up the basis set.")
        ])

        self.create_editable_subsection(self.editable_variables_frame, "Less Commonly Edited", [
            ("temp_dir", const.temp_dir,
             "This is just what we call the temporary directory. Don't need to change this."),
            ("server", const.server, "Don't change this."),
            ("port", const.port, "default SSH port"),
            ("username", const.username, "Whatever your username is."),
            ("password", const.password, "Whatever your password is.")
        ])

        self.create_editable_subsection(self.editable_variables_frame, "One and Done", [
            ("compound_list_directory", const.compound_list_directory,
             "This is the directory that list_folder_name is in."),
            ("vconf_path", const.vconf_path, "This is the path to the Vconf executable."),
            ("remote_directory", const.remote_directory,
             "Make sure you have a directory on the server called turbomol!"),
        ], long_entries=True)

        # Add trace on list_folder_name and compound_list_directory to update VCONF settings
        self.editable_vars["list_folder_name"].bind("<FocusOut>", self.update_vconf_paths)
        self.editable_vars["compound_list_directory"].bind("<FocusOut>", self.update_vconf_paths)

    def create_editable_subsection(self, parent, title, variables, long_entries=False):
        subsection_frame = ttk.LabelFrame(parent, text=title)
        subsection_frame.pack(fill="x", expand=True, padx=10, pady=5)

        row_counter = 0
        for var_name, var_value, tooltip in variables:
            var_label = ttk.Label(subsection_frame, text=var_name, font=("TkDefaultFont", 10))
            var_label.grid(row=row_counter, column=0, sticky="w", padx=5, pady=2)
            self.create_tooltip(var_label, tooltip)

            entry_width = 50 if long_entries else 20
            var_entry = ttk.Entry(subsection_frame, font=("TkDefaultFont", 10), width=entry_width)
            var_entry.insert(0, str(var_value))
            var_entry.grid(row=row_counter, column=1, sticky="w", padx=5, pady=2)
            self.create_tooltip(var_entry, tooltip)

            self.editable_vars[var_name] = var_entry

            if var_name == "remote_directory":
                browse_button = ttk.Button(subsection_frame, text="Browse",
                                           command=lambda var=var_name: self.browse_remote_directory(var))
                browse_button.grid(row=row_counter, column=2, sticky="w", padx=5, pady=2)
                # Add trace for remote_directory
                var_entry.bind("<FocusOut>", self.save_remote_directory)

            elif var_name in ["compound_list_directory", "list_folder_name"]:
                browse_button = ttk.Button(subsection_frame, text="Browse",
                                           command=lambda var=var_name: self.browse_directory(var))
                browse_button.grid(row=row_counter, column=2, sticky="w", padx=5, pady=2)
            elif var_name == "vconf_path":
                browse_button = ttk.Button(subsection_frame, text="Browse",
                                           command=lambda var=var_name: self.browse_file(var))
                browse_button.grid(row=row_counter, column=2, sticky="w", padx=5, pady=2)

            row_counter += 1

    def save_remote_directory(self, event=None):
        remote_directory = self.editable_vars["remote_directory"].get().rstrip('/')
        self.editable_vars["remote_directory"].delete(0, tk.END)
        self.editable_vars["remote_directory"].insert(0, remote_directory)
        self.save_to_constants_last()

    def create_toggle_with_sub_variables(self, parent, toggle, value, is_directory_editing=False):
        if toggle == "gzip_and_unzip_script":
            toggle_var = self.gzip_and_unzip_var
        else:
            toggle_var = tk.BooleanVar(value=value)
            self.script_toggle_vars[toggle] = toggle_var

        toggle_check = tk.Checkbutton(
            parent,
            text=toggle,
            variable=toggle_var,
            command=lambda: self.toggle_sub_variables(toggle_var, sub_vars_frame, toggle, is_directory_editing),
            font=("TkDefaultFont", 10)
        )
        toggle_check.grid(row=self.script_row_counter, column=0, sticky="w", padx=5, pady=2)

        # Add tooltip for toggle checkbutton
        tooltip_text = tooltips.get(toggle, "")
        self.create_tooltip(toggle_check, tooltip_text)

        sub_vars_frame = ttk.Frame(parent)
        sub_vars_frame.grid(row=self.script_row_counter + 1, column=0, padx=20, sticky="nsew")

        sub_vars_frame.widgets = []  # List to keep track of sub-variable widgets

        sub_row = 0
        sorted_sub_vars = sorted(sub_variables.get(toggle, []))  # Sort the sub-variables
        for sub_var in sorted_sub_vars:
            sub_value = getattr(const, sub_var, None)
            sub_var_label = ttk.Label(sub_vars_frame, text=sub_var, font=("TkDefaultFont", 10))
            sub_var_label.grid(row=sub_row, column=0, sticky="w", padx=5, pady=2)
            sub_vars_frame.widgets.append(sub_var_label)

            tooltip_text = tooltips.get(sub_var, "")
            self.create_tooltip(sub_var_label, tooltip_text)

            entry_width = 30 if sub_var == "timestamp_folder" else 20

            if isinstance(sub_value, bool):
                sub_var_entry = tk.BooleanVar(value=sub_value)
                sub_var_check = tk.Checkbutton(sub_vars_frame, variable=sub_var_entry, font=("TkDefaultFont", 10))
                sub_var_check.grid(row=sub_row, column=1, sticky="w", padx=5, pady=2)
                self.create_tooltip(sub_var_check, tooltip_text)
                sub_vars_frame.widgets.append(sub_var_check)
                self.editable_vars[sub_var] = sub_var_entry
            elif isinstance(sub_value, int):
                sub_var_entry = ttk.Entry(sub_vars_frame, font=("TkDefaultFont", 10), width=entry_width)
                sub_var_entry.insert(0, str(sub_value))
                sub_var_entry.grid(row=sub_row, column=1, sticky="w", padx=5, pady=2)
                self.create_tooltip(sub_var_entry, tooltip_text)
                sub_vars_frame.widgets.append(sub_var_entry)
                self.editable_vars[sub_var] = sub_var_entry
            elif sub_value is None or isinstance(sub_value, str):
                sub_var_entry = ttk.Entry(sub_vars_frame, font=("TkDefaultFont", 10), width=entry_width)
                if sub_value is not None:
                    sub_var_entry.insert(0, sub_value)
                sub_var_entry.grid(row=sub_row, column=1, sticky="w", padx=5, pady=2)
                self.create_tooltip(sub_var_entry, tooltip_text)
                sub_vars_frame.widgets.append(sub_var_entry)
                self.editable_vars[sub_var] = sub_var_entry

                # Add browse button for specific sub-variables
                if sub_var in ["timestamp_folder", "remote_file_path", "delete_file_path", "gzip_directory_by_name",
                               "unzip_directory_by_name"]:
                    browse_button = ttk.Button(sub_vars_frame, text="Browse",
                                               command=lambda sv=sub_var: self.browse_remote_directory(sv))
                    browse_button.grid(row=sub_row, column=2, sticky="w", padx=5, pady=2)
                    sub_vars_frame.widgets.append(browse_button)

            sub_row += 1

        # Gray out sub-variables if toggle is False
        self.set_widget_state(sub_vars_frame, "normal" if toggle_var.get() else "disabled")

        if not is_directory_editing:
            self.sub_var_frames[toggle] = sub_vars_frame
            self.script_toggle_vars_widgets[toggle] = toggle_check  # Store the toggle checkbutton

        self.script_row_counter += 2

    def toggle_sub_variables(self, toggle_var, sub_vars_frame, toggle, is_directory_editing=False):
        if toggle == "gzip_and_unzip_script":
            self.toggle_script_parameters(toggle_var.get())
            self.set_widget_state(sub_vars_frame, "normal" if toggle_var.get() else "disabled")
        else:
            state = "normal" if toggle_var.get() else "disabled"
            if self.gzip_and_unzip_var.get() and not is_directory_editing:
                state = "disabled"
                toggle_var.set(False)
            self.set_widget_state(sub_vars_frame, state)

        # Ensure sub-variables maintain their order from the dictionary
        ordered_sub_vars = [widget for sub_var in sub_variables[toggle] for widget in sub_vars_frame.widgets if
                            widget.cget("text") == sub_var]
        for widget in ordered_sub_vars:
            widget.tkraise()  # Raise the widget to maintain order

    def toggle_script_parameters(self, enable):
        if enable:
            self.disabled_toggles = {toggle: var.get() for toggle, var in self.script_toggle_vars.items() if
                                     toggle != "gzip_and_unzip_script"}
            for toggle, var in self.script_toggle_vars.items():
                if toggle != "gzip_and_unzip_script":
                    self.set_widget_state(self.sub_var_frames[toggle], "disabled")
                    self.script_toggle_vars_widgets[toggle].config(state="disabled")
                    var.set(False)
        else:
            for toggle, was_enabled in self.disabled_toggles.items():
                self.script_toggle_vars[toggle].set(was_enabled)
                self.set_widget_state(self.sub_var_frames[toggle], "normal" if was_enabled else "disabled")
                self.script_toggle_vars_widgets[toggle].config(state="normal")

    def set_widget_state(self, frame, state):
        for widget in frame.winfo_children():
            try:
                widget.config(state=state)
            except tk.TclError:
                pass

    def create_tooltip(self, widget, text):
        tool_tip = ToolTip(widget)

        def enter(event):
            tool_tip.showtip(text)

        def leave(event):
            tool_tip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def update_vconf_paths(self, event=None):
        list_folder_name = self.editable_vars["list_folder_name"].get()
        compound_list_directory = self.editable_vars["compound_list_directory"].get()

        const_2.SDF_FILENAME = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}.sdf"
        const_2.OUTPUT_LOG = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}.log"
        const_2.OUTPUT_SDF = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}_vconf.sdf"
        const_2.vconf_batch_sdf_path = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}_vconf_batchfile.sdf"

        const_2.default_vconf_settings["SDF_FILENAME"] = const_2.SDF_FILENAME
        const_2.default_vconf_settings["OUTPUT_LOG"] = const_2.OUTPUT_LOG
        const_2.default_vconf_settings["OUTPUT_SDF"] = const_2.OUTPUT_SDF
        const_2.default_vconf_settings["vconf_batch_sdf_path"] = const_2.vconf_batch_sdf_path

        const_2.experimental_vconf_settings["SDF_FILENAME"] = const_2.SDF_FILENAME
        const_2.experimental_vconf_settings["OUTPUT_LOG"] = const_2.OUTPUT_LOG
        const_2.experimental_vconf_settings["OUTPUT_SDF"] = const_2.OUTPUT_SDF
        const_2.experimental_vconf_settings["vconf_batch_sdf_path"] = const_2.vconf_batch_sdf_path

        self.save_to_constants()
        self.save_to_constants_last()

        # Only reload the relevant VConf settings
        self.reload_relevant_vconf_settings()

    def reload_relevant_vconf_settings(self):
        for key in ["SDF_FILENAME", "OUTPUT_LOG", "OUTPUT_SDF", "vconf_batch_sdf_path"]:
            for setting_type in ["Default VConf Settings", "Experimental VConf Settings"]:
                widget_key = f"{setting_type}_{key}"
                if widget_key in self.editable_vars:
                    if setting_type == "Default VConf Settings":
                        self.editable_vars[widget_key].delete(0, tk.END)
                        self.editable_vars[widget_key].insert(0, const_2.default_vconf_settings[key])
                    elif setting_type == "Experimental VConf Settings":
                        self.editable_vars[widget_key].delete(0, tk.END)
                        self.editable_vars[widget_key].insert(0, const_2.experimental_vconf_settings[key])

    def save_settings(self):
        print("Saving settings...")  # Debug statement

        # Update the script toggle variables
        for toggle in self.script_toggle_vars:
            setattr(const, toggle, self.script_toggle_vars[toggle].get())

        # Update gzip_and_unzip_script separately
        const.gzip_and_unzip_script = self.gzip_and_unzip_var.get()

        # Update the sub variables
        for sub_var, widget in self.editable_vars.items():
            value = widget.get()

            # Convert to appropriate type if needed
            if isinstance(widget, tk.BooleanVar):
                value = widget.get()
            elif value.isdigit():
                value = int(value)
            elif value.lower() in ["true", "false"]:
                value = value.lower() == "true"

            setattr(const, sub_var, value)

        # Update VCONF settings
        for sub_var in vconf_variables:
            default_widget = self.editable_vars.get(f"Default VConf Settings_{sub_var}")
            experimental_widget = self.editable_vars.get(f"Experimental VConf Settings_{sub_var}")

            if default_widget:
                value = default_widget.get()
                if value.isdigit():
                    value = int(value)
                elif value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                const_2.default_vconf_settings[sub_var] = value

            if experimental_widget:
                value = experimental_widget.get()
                if value.isdigit():
                    value = int(value)
                elif value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                const_2.experimental_vconf_settings[sub_var] = value

        # Save the contents of the text widgets for the scripts
        for filepath, text_widget in self.script_texts.items():
            self.save_file_content(filepath, text_widget)

        # Save to constants_last.txt
        self.save_to_constants_last()

        # After saving, update constants.py with the loaded values
        self.save_to_constants()

    def save_to_constants(self):
        self.save_to_python_file("constants.py")

    def save_to_constants_last(self):
        self.save_to_file("constants_last.txt")

    def format_vconf_value(self, value):
        if value is None:
            return "None"
        if isinstance(value, str):
            if value == "None":
                return "None"
            if "\\" in value:
                return f'fr"{value}"'
            else:
                return f'"{value}"'
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, tuple):
            return f"({', '.join(map(str, value))})"
        else:
            return value

    def save_default_settings(self):
        self.save_to_file("default_settings.txt")

    def save_to_file(self, filename):
        try:
            with open(filename, "w") as file:
                for key, value in self.script_toggle_vars.items():
                    file.write(f"{key}={value.get()}\n")

                for key, entry in self.editable_vars.items():
                    if isinstance(entry, tk.BooleanVar):
                        file.write(f"{key}={entry.get()}\n")
                    else:
                        file.write(f"{key}={entry.get()}\n")

                # Save VConf settings
                for key, value in const_2.default_vconf_settings.items():
                    file.write(f"default_vconf_settings_{key}={self.format_value(value)}\n")
                for key, value in const_2.experimental_vconf_settings.items():
                    file.write(f"experimental_vconf_settings_{key}={self.format_value(value)}\n")

                # Save the contents of the text widgets for the scripts
                for script_path, text_widget in self.script_texts.items():
                    content = text_widget.get("1.0", tk.END).strip()
                    content = content.replace('\n', '\\n')  # Replace newlines with \n for text file storage
                    file.write(f"{os.path.basename(script_path).replace('.', '_')}_content={content}\n")

                # Save gzip_and_unzip_script separately
                file.write(f"gzip_and_unzip_script={self.gzip_and_unzip_var.get()}\n")

            print(f"Settings saved to {filename}")  # Debug statement
        except Exception as e:
            print(f"Failed to save settings to {filename}: {e}")  # Debug statement

    def save_to_python_file(self, filename):
        try:
            with open(filename, "w") as file:
                file.write('"""\nAuto-generated constants file from GUI settings.\n"""\n\n')

                # Import dependencies from dictionary
                file.write(
                    "import gui as gui_prop\n\n")

                # Write the variables to the file
                for section, variables in sections.items():
                    file.write(f"# {section}\n")
                    for attr in variables:
                        value = getattr(const, attr, None)
                        if value is not None:
                            formatted_value = self.format_value(value)
                            file.write(f"{attr} = {formatted_value}\n")
                    file.write("\n")

                # Save default VCONF settings in an organized manner
                file.write("# Default VConf Settings\n")
                file.write("default_vconf_settings = {\n")
                for key in vconf_variables:
                    value = const_2.default_vconf_settings.get(key, None)
                    formatted_value = self.format_vconf_value(value)
                    file.write(f"    '{key}': {formatted_value},\n")
                file.write("}\n\n")

                # Save experimental VCONF settings in an organized manner
                file.write("# Experimental VConf Settings\n")
                file.write("experimental_vconf_settings = {\n")
                for key in vconf_variables:
                    value = const_2.experimental_vconf_settings.get(key, None)
                    formatted_value = self.format_vconf_value(value)
                    file.write(f"    '{key}': {formatted_value},\n")
                file.write("}\n\n")

                # Save script contents as strings with newline handling
                for script_path, text_widget in self.script_texts.items():
                    script_name = os.path.basename(script_path).replace('.', '_')
                    content = text_widget.get("1.0", tk.END).strip()
                    content = content.replace('"""', '\\"\\"\\"')  # Handle triple quotes in the content
                    content = content.replace('\n', '\\n')  # Replace newlines with \n
                    file.write(f'{script_name}_content = """{content}"""\n')

                # Include the dependencies section from dictionary
                file.write(dependencies_text.strip() + "\n")

            print(f"Settings saved to {filename}")  # Debug statement
        except Exception as e:
            print(f"Failed to save settings to {filename}: {e}")  # Debug statement

    def format_value(self, value):
        if isinstance(value, str):
            if "\\" in value:
                return f'fr"{value}"'
            else:
                return f'"{value}"'
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, tuple):
            return f"({', '.join(map(str, value))})"
        else:
            return str(value)

    def load_file_content(self, filepath, text_widget):
        try:
            with open(filepath, "r") as file:
                content = file.read()
                text_widget.delete("1.0", tk.END)
                text_widget.insert(tk.END, content)
                print(f"Loaded content from {filepath}")  # Debug statement
        except Exception as e:
            print(f"Failed to load content from {filepath}: {e}")  # Debug statement

    def save_file_content(self, filepath, text_widget):
        try:
            with open(filepath, "w") as file:
                content = text_widget.get("1.0", tk.END)
                file.write(content)
                print(f"Saved content to {filepath}")  # Debug statement
        except Exception as e:
            print(f"Failed to save content to {filepath}: {e}")  # Debug statement

    def create_file_editor_section(self):
        # Scrollbar setup for File Editor tab
        file_editor_canvas = tk.Canvas(self.file_editor_tab)
        file_editor_scrollbar = ttk.Scrollbar(self.file_editor_tab, orient="vertical", command=file_editor_canvas.yview)
        file_editor_scrollable_frame = ttk.Frame(file_editor_canvas)

        file_editor_scrollable_frame.bind(
            "<Configure>",
            lambda e: file_editor_canvas.configure(
                scrollregion=file_editor_canvas.bbox("all")
            )
        )

        file_editor_canvas.create_window((0, 0), window=file_editor_scrollable_frame, anchor="nw")
        file_editor_canvas.configure(yscrollcommand=file_editor_scrollbar.set)

        file_editor_canvas.pack(side="left", fill="both", expand=True)
        file_editor_scrollbar.pack(side="right", fill="y")

        # Configure the grid
        file_editor_scrollable_frame.columnconfigure(0, weight=1)
        file_editor_scrollable_frame.columnconfigure(1, weight=1)
        file_editor_scrollable_frame.columnconfigure(2, weight=1)

        for i, (script_name, script_path) in enumerate(script_paths):
            self.create_script_editor(file_editor_scrollable_frame, script_name, script_path, i)

        # Save Files button
        self.save_files_button = ttk.Button(file_editor_scrollable_frame, text="Save Files", command=self.save_files)
        self.save_files_button.grid(row=1, column=1, pady=10, sticky="ew")

    def create_script_editor(self, parent, script_name, script_path, column):
        frame = ttk.LabelFrame(parent, text=script_name)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")

        text_widget = tk.Text(frame, wrap="none", width=40)  # Adjust the width to fit three columns
        text_widget.pack(fill="both", expand=True)

        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
        script_path = os.path.join(script_dir, script_path)  # Construct the path to the script

        self.script_texts[script_path] = text_widget

        # Load the initial content of the script
        self.load_file_content(script_path, text_widget)

    def save_files(self):
        for filepath, text_widget in self.script_texts.items():
            self.save_file_content(filepath, text_widget)

    def load_settings(self, settings_file="constants_last.txt"):
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script

        try:
            with open(settings_file, "r") as file:
                lines = file.readlines()

            settings = {}
            for line in lines:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    value = self.strip_quotes(value)
                    settings[key] = value

            # Update const with values from settings
            for key, value in settings.items():
                if key in self.script_toggle_vars:
                    self.script_toggle_vars[key].set(value == 'True')
                    setattr(const, key, value == 'True')  # Set attribute in const
                    # Update the state of sub-variables based on the toggle state
                    if key in self.sub_var_frames:
                        self.toggle_sub_variables(self.script_toggle_vars[key], self.sub_var_frames[key], key)
                elif key in self.editable_vars:
                    if isinstance(self.editable_vars[key], tk.BooleanVar):
                        self.editable_vars[key].set(value == 'True')
                    else:
                        self.editable_vars[key].delete(0, tk.END)
                        self.editable_vars[key].insert(0, value)
                    setattr(const, key, value)  # Set attribute in const
                elif key == "gzip_and_unzip_script":
                    self.gzip_and_unzip_var.set(value == 'True')
                    setattr(const, key, value == 'True')  # Set attribute in const
                    if "gzip_and_unzip_script" in self.sub_var_frames:
                        self.toggle_sub_variables(self.gzip_and_unzip_var, self.sub_var_frames["gzip_and_unzip_script"],
                                                  "gzip_and_unzip_script")
                elif key.startswith("default_vconf_settings_"):
                    key_short = key.replace("default_vconf_settings_", "")
                    const_2.default_vconf_settings[key_short] = self.convert_value(value)
                elif key.startswith("experimental_vconf_settings_"):
                    key_short = key.replace("experimental_vconf_settings_", "")
                    const_2.experimental_vconf_settings[key_short] = self.convert_value(value)
                elif key.endswith("_content"):
                    script_path = os.path.join(script_dir,
                                               key.replace('_content', '').replace('_', '.'))
                    if script_path in self.script_texts:
                        content = value.replace('\\n', '\n')
                        self.script_texts[script_path].delete("1.0", tk.END)
                        self.script_texts[script_path].insert(tk.END, content)
                else:
                    setattr(const, key, self.convert_value(value))

            print(f"Loaded settings from {settings_file}")  # Debug statement
        except FileNotFoundError:
            print(f"{settings_file} not found")  # Debug statement
        except Exception as e:
            print(f"Failed to load settings from {settings_file}: {e}")  # Debug statement

    def strip_quotes(self, value):
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith('fr"') and value.endswith('"'):
            return value[3:-1]
        return value

    def convert_value(self, value):
        if value.isdigit():
            return int(value)
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.lower() == "none":
            return None
        return value

    def load_default_settings(self):
        self.load_settings("default_settings.txt")
        # Reload the VConf settings tab to show the updated paths
        self.reload_vconf_settings()

    def strip_quotes(self, value):
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith('fr"') and value.endswith('"'):
            return value[3:-1]
        return value

    def convert_value(self, value):
        if value.isdigit():
            return int(value)
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.lower() == "none":
            return None
        return value

    def load_default_settings(self):
        self.load_settings("default_settings.txt")

    def on_closing(self):
        self.save_settings()
        self.destroy()

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def showtip(self, text):
        if self.tip_window or not text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = ttk.Label(tw, text=text, background="yellow", relief="solid", borderwidth=1)
        label.pack()

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

if __name__ == "__main__":
    app = GUI()
    app.mainloop()
