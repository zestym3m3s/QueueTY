import tkinter as tk
from tkinter import ttk, filedialog, PhotoImage, font
import paramiko
import subprocess
import os
import warnings
import psutil
import sys
import shutil
import time
import constants as const
import constants as const_2
import termination
import datetime
from screeninfo import get_monitors
import configparser
import threading
import queue

from dictionary import (
    vconf_variables,
    vconf_tooltips,
    tooltips,
    script_toggle_variables_without_gzip,
    sub_variables,
    dependencies_text,
    sections,
    script_paths
)

app_instance = None
script_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))  # Get the directory of the current script

if getattr(sys, 'frozen', False):
    path_to_python_scripts = os.path.join(script_dir, '_internal')
else:
    path_to_python_scripts = script_dir

closing_flag = False  # Global flag to track if the GUI is closing


class SplashScreen(tk.Toplevel):
    def __init__(self, master, image_path, timeout=3000):
        super().__init__(master)
        self.timeout = timeout
        self.image_path = image_path
        self.init_ui()
        self.after(self.timeout, self.destroy)

    def init_ui(self):
        self.geometry("256x400")
        self.overrideredirect(True)
        self.lift()
        self.attributes('-topmost', True)

        # Find a monitor with height 1080, if available, otherwise use the screen with the mouse
        preferred_screen = next((m for m in get_monitors() if m.height == 1080), None)
        active_screen = preferred_screen if preferred_screen else next((m for m in get_monitors() if m.is_primary),
                                                                       get_monitors()[0])

        # Center the splash screen on the selected screen
        x = active_screen.x + (active_screen.width // 2) - (256 // 2)
        y = active_screen.y + (active_screen.height // 2) - (400 // 2)
        self.geometry(f"256x400+{x}+{y}")

        # Load and display the image
        img = PhotoImage(file=self.image_path)
        label_img = tk.Label(self, image=img)
        label_img.image = img  # Keep a reference to avoid garbage collection
        label_img.place(relx=0.5, rely=0.5, anchor='center', y=-50)  # Center the image vertically

        # Text frame and labels
        text_frame = tk.Frame(self, bg="white", height=100)
        text_frame.pack(fill='x', side='bottom')

        label_text_1 = tk.Label(text_frame, text="Loading QueueTY...", font=("Helvetica", 12, "bold"), bg="white")
        label_text_1.pack(pady=(10, 0))
        label_text_2 = tk.Label(text_frame, text="by Tristan Vick", font=("Helvetica", 10), bg="white")
        label_text_2.pack(pady=(5, 0))
        label_text_3 = tk.Label(text_frame, text="University at Buffalo's Aga Lab 2024", font=("Helvetica", 10),
                                bg="white")
        label_text_3.pack(pady=(5, 10))

    @staticmethod
    def show_splash_screen(root, image_path):
        splash = SplashScreen(root, image_path)
        splash.update()
        return splash


class ConsoleStream:
    def __init__(self, append_func, delete_last_func, keyword="\u200B"):
        self.app_instance = app_instance  # Store app_instance for use in after()
        self.append_func = append_func
        self.delete_last_func = delete_last_func
        self.keyword = keyword
        self.is_logging = False
        self.log_file = None
        self.last_message = ""  # Track last message to avoid duplicates

    def write(self, message):
        if message != self.last_message:  # Only display if different from last message
            self.last_message = message
            if self.keyword in message:
                self.append_func(message)  # Append only when keyword is present
                self.app_instance.after(50, self.delete_last_func)  # Use instance variable for after()

            # Save to log file if logging is active
            if self.is_logging and self.log_file:
                try:
                    self.log_file.write(message + '\n')
                    self.log_file.flush()
                except Exception as e:
                    sys.__stdout__.write(f"Failed to write to log file: {e}\n")

    def flush(self):
        if self.is_logging and self.log_file:
            self.log_file.flush()

    def start_logging(self, log_file_path, header_info=""):
        try:
            self.log_file = open(log_file_path, "w")
            self.is_logging = True
            if header_info:
                self.log_file.write(header_info + '\n')
            sys.__stdout__.write(f"Logging started for task at {log_file_path}\n")
        except Exception as e:
            sys.__stdout__.write(f"Failed to start logging at {log_file_path}: {e}\n")

    def stop_logging(self):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        self.is_logging = False


class Constants:
    def __init__(self):
        self.default_vconf_settings = {}
        self.experimental_vconf_settings = {}


class ToolTip:
    def __init__(self, widget, wrap_length=750):
        """
        Initialize the ToolTip.

        Parameters:
        - widget: The widget to which the tooltip is attached.
        - wrap_length: The maximum line length in pixels before wrapping occurs.
        """
        self.widget = widget
        self.wrap_length = wrap_length  # Maximum width in pixels for wrapping
        self.tip_window = None

        # Use the widget's font if available; otherwise, use a default font
        try:
            self.font = font.Font(font=self.widget['font'])
        except tk.TclError:
            self.font = font.nametofont("TkDefaultFont")  # Use default Tkinter font

        # Calculate wraplength based on the desired character width
        average_char_width = self.font.measure('n')  # Approximate average character width
        self.wrap_length = wrap_length or (30 * average_char_width)

    def showtip(self, text):
        """
        Display the tooltip with the given text.

        Parameters:
        - text: The text to display in the tooltip.
        """
        if self.tip_window or not text:
            return

        # Calculate the default position of the tooltip (below the widget)
        try:
            # Get the bounding box of the widget's "insert" cursor
            bbox = self.widget.bbox("insert")
            if bbox:
                x, y, _cx, cy = bbox
            else:
                # If "insert" is not applicable (e.g., for buttons), use widget's center
                x = self.widget.winfo_width() // 2
                y = self.widget.winfo_height() // 2

            # Calculate absolute position
            x = x + self.widget.winfo_rootx() + 25
            y = y + cy + self.widget.winfo_rooty() + 25
        except Exception as e:
            print(f"Error calculating tooltip position: {e}")
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + 25

        # Create a new top-level window for the tooltip
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations

        # Initially position the tooltip
        tw.wm_geometry(f"+{x}+{y}")

        # Create a Label widget within the tooltip window
        label = ttk.Label(
            tw,
            text=text,
            background="yellow",
            relief="solid",
            borderwidth=1,
            wraplength=self.wrap_length,  # Set the wrap length dynamically
            justify='left',               # Align text to the left
            padding=(5, 3)                # Add some padding for better aesthetics
        )
        label.pack(ipadx=1)

        # Ensure the tooltip window has been drawn to get its size
        tw.update_idletasks()

        # Get the tooltip window's dimensions
        tw_width = tw.winfo_width()
        tw_height = tw.winfo_height()

        # Get the screen's dimensions
        screen_width = tw.winfo_screenwidth()
        screen_height = tw.winfo_screenheight()

        # Get the current position of the tooltip
        tooltip_x = tw.winfo_x()
        tooltip_y = tw.winfo_y()

        # Check if the tooltip goes beyond the bottom of the screen
        if (tooltip_y + tw_height) > screen_height:
            # Reposition the tooltip above the widget
            new_y = y - tw_height - cy - 25  # Adjust the y-coordinate upwards
            if new_y < 0:
                new_y = 0  # Prevent tooltip from going off the top edge
            tw.wm_geometry(f"+{x}+{new_y}")

        # Optionally, check for horizontal overflow and adjust x if necessary
        if (tooltip_x + tw_width) > screen_width:
            new_x = screen_width - tw_width - 10  # 10 pixels padding from the edge
            if new_x < 0:
                new_x = 0  # Prevent tooltip from going off the left edge
            tw.wm_geometry(f"+{new_x}+{tw.wm_geometry().split('+')[2]}")

    def hidetip(self):
        """Hide the tooltip."""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# noinspection PyAttributeOutsideInit,PyProtectedMember,PyTypeChecker
class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        global app_instance
        app_instance = self  # Set the global reference to the current instance
        self.init_general_settings()
        self.init_paths_and_icons()
        self.load_sensitive_config()
        self.init_attributes()
        self.init_tabs()
        self.load_settings(self.constants_last_path if getattr(sys, 'frozen', False) else "constants_last.txt")
        self.bind_gui_events()
        self.connect_to_server()


    # region ---- General Initialization Functions ----

    def init_general_settings(self):
        """Initialize general settings for the GUI, including title, geometry, SSH connection, and flags."""
        self.title("QueueTY")

        # Set default window dimensions
        default_width, default_height = 1080, 960

        # Find a monitor with height 1080, if available, otherwise use the screen with the mouse
        preferred_screen = next((m for m in get_monitors() if m.height == 1080), None)
        active_screen = preferred_screen if preferred_screen else next((m for m in get_monitors() if m.is_primary),
                                                                       get_monitors()[0])

        # Calculate usable screen height excluding the taskbar
        usable_height = active_screen.height - 50  # Assume a typical taskbar height of ~50px

        # Set the window dimensions, adjusting to the active screen's dimensions if needed
        window_width = min(default_width, active_screen.width)
        window_height = min(default_height, usable_height)

        # Position the window at the top of the screen, centered horizontally
        x_position = active_screen.x + (active_screen.width - window_width) // 2
        y_position = active_screen.y  # Start at the top of the screen

        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        self.resizable(False, False)
        self.maxsize(window_width, window_height)

        # Initialize other attributes
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.is_task_running = False
        self.is_task_complete = False
        self.is_queue_active = False
        self.current_task_start_time = None
        self.script_process = None
        self.console_output_stream = ConsoleStream(self.append_to_console, self.delete_last_line)
    def init_paths_and_icons(self):
        """Initialize paths and icons, including settings paths, script paths, and window icons."""
        # Determine base path and icon path
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.join(sys._MEIPASS)  # Access to _MEIPASS needed for PyInstaller
            icon_path = os.path.join(self.base_path, 'icon.png')
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = 'icon.png'

        # Initialize paths to settings files and scripts
        self.constants_last_path = os.path.join(self.base_path, 'constants_last.txt')
        self.constants_path = os.path.join(self.base_path, 'constants.py')
        self.default_settings_path = os.path.join(self.base_path, 'default_settings.txt')
        self.main_path = os.path.join(self.base_path, 'main.py')
        self.gzip_and_unzip_path = os.path.join(self.base_path, 'gzip_and_unzip.py')
        self.check_remote_directory_path = os.path.join(self.base_path, 'check_remote_directory.py')
        self.clean_up_molecule_list_path = os.path.join(self.base_path, 'clean_up_molecule_list.py')
        self.generate_conformers_vconf_path = os.path.join(self.base_path, 'generate_conformers_vconf.py')
        self.cmdline_TMoleX_process_path = os.path.join(self.base_path, 'cmdline_TMoleX_process.py')
        self.submit_remote_jobs_to_cluster_path = os.path.join(self.base_path, 'submit_remote_jobs_to_cluster.py')
        self.check_cluster_queue_path = os.path.join(self.base_path, 'check_cluster_queue.py')
        self.grab_files_from_cluster_path = os.path.join(self.base_path, 'grab_files_from_cluster.py')
        self.write_new_inp_file_path = os.path.join(self.base_path, 'write_new_inp_file.py')
        self.dictionary_path = os.path.join(self.base_path, 'dictionary.py')

        # Set the window icon
        self.window_icon_image = PhotoImage(file=icon_path)
        self.iconphoto(False, self.window_icon_image)

        # Set taskbar icon (.ico files only on Windows)
        try:
            self.wm_iconbitmap("icon.ico")
        except tk.TclError as e:
            print(f"Failed to set icon: {e}")

    def init_attributes(self):
        """Initialize instance attributes for UI components, script settings, and GUI configurations."""
        self.script_settings_canvas = None
        self.script_settings_scrollbar = None
        self.scrollable_script_settings_frame = None
        self.main_frame = None
        self.script_parameters_frame = None
        self.right_frame = None
        self.editable_variables_frame = None
        self.directory_editing_frame = None
        self.save_button = None
        self.run_button = None
        self.terminate_button = None
        self.save_to_queue_button = None
        self.save_default_button = None
        self.load_default_button = None
        self.console_text = None
        self.console_scrollbar = None
        self.auto_scroll = tk.BooleanVar(value=True)
        self.run_button_console = None
        self.terminate_button_console = None
        self.vconf_settings_canvas = None
        self.vconf_settings_scrollbar = None
        self.scrollable_vconf_settings_frame = None

        # Initialize attributes for script toggles and editable variables
        self.script_toggle_vars = {}
        self.editable_vars = {}
        self.script_texts = {}
        self.script_toggle_vars_widgets = {}
        self.sub_var_frames = {}
        self.disabled_toggles = {}
        self.sub_var_frames = {}
        self.initial_toggle_states = {}
        self.special_toggle_vars = script_toggle_variables_without_gzip
        self.gzip_and_unzip_var = tk.BooleanVar()
        self.check_remote_directory_var = tk.BooleanVar()

        # Queue-related attributes
        self.current_task = None
        self.previous_selection = None
        self.status_labels = {}
        self.status_frame = ttk.Frame(self.master)
        self.status_frame.pack(fill='both', expand=False)
        self.settings_label_text = tk.StringVar(value="Settings")
        self.log_label_text = tk.StringVar(value="Log")
        self.queue_dir = os.path.join(os.path.dirname(__file__), 'saves')
        self.log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(self.queue_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # Terminal-related attributes
        self.ssh_channel = None
        self.last_focus_out_time = None
        self.is_autocompleting = False
        self.autocomplete_buffer = ''
        self.prompt_pattern = r'^[\w\W]*[@\$] '  # Adjust based on your shell prompt
        paramiko.Transport._preferred_kex = ('diffie-hellman-group14-sha1', 'diffie-hellman-group-exchange-sha256')
        paramiko.Transport._preferred_keys = ('ssh-rsa',)
        paramiko.Transport._preferred_ciphers = ('aes128-ctr', 'aes192-ctr', 'aes256-ctr')
        paramiko.Transport._preferred_macs = ('hmac-sha2-256', 'hmac-sha2-512')

    def init_tabs(self):
        style = ttk.Style()
        style.theme_use("alt")

        # Configure tab style
        style.configure(
            "TNotebook.Tab",
            padding=(4, 3),  # Adjust padding (horizontal, vertical)
            font=("Arial", 10, "bold"),  # Bold the tab text
            background="#3BA870",  # Custom tab background color
            foreground="#4D4D4D",  # Custom tab text color
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#57F6A4")],  # Highlight color for selected tab
            foreground=[("selected", "black")],
        )

        # **Custom Style for Checkbuttons**
        style.configure(
            "Custom.TCheckbutton",
            background="black",  # Match your GUI background
            foreground="black",  # Text color
            font=("TkDefaultFont", 12),
            borderwidth=0,  # Remove border
            relief="flat",  # Flat appearance
        )

        style.map(
            "Custom.TCheckbutton",
            background=[("active", "#D9D9D9"),
                        ("!active", "#D9D9D9")],
            foreground=[("active", "black"),
                        ("!active", "black")],
        )

        style = ttk.Style()
        style.configure(
            "Custom.TLabelframe",
            borderwidth=0,  # Remove the border
            background="#D9D9D9"
        )
        style.configure(
            "Custom.TLabelframe.Label",
            background="#D9D9D9"  # Match the background color for the label
        )

        self.script_parameters_frame = ttk.LabelFrame(
            self.main_frame, text="Script Parameters", width=540, style="Custom.TLabelframe"
        )

        self.tabs = ttk.Notebook(self)
        self.script_settings_tab = ttk.Frame(self.tabs)
        self.console_tab = ttk.Frame(self.tabs)
        self.vconf_settings_tab = ttk.Frame(self.tabs)
        self.file_editor_tab = ttk.Frame(self.tabs)
        self.queue_tab = ttk.Frame(self.tabs)
        self.terminal_tab = ttk.Frame(self.tabs)
        self.tutorial_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.script_settings_tab, text="Script Settings")
        self.tabs.add(self.console_tab, text="Console")
        self.tabs.add(self.vconf_settings_tab, text="VConf Settings")
        self.tabs.add(self.file_editor_tab, text="File Editor")
        self.tabs.add(self.queue_tab, text="Queue")
        self.tabs.add(self.terminal_tab, text="Remote Server Terminal")
        self.tabs.add(self.tutorial_tab, text="Tutorial / Help")

        self.tabs.pack(expand=1, fill="both")

        # Initialize the individual sections
        self.create_script_settings_tab()
        self.create_console_tab()
        self.create_vconf_settings_tab()
        self.create_file_editor_tab()
        self.create_queue_tab()
        self.create_terminal_tab()
        self.create_tutorial_tab()

    def bind_gui_events(self):
        """Bind events like window close to save settings and execute cleanup."""
        self.protocol("WM_DELETE_WINDOW", self.handle_window_closing)

    # endregion

    # region ---- Script Settings Tab ----
    def create_script_settings_tab(self):
        """Initialize the Script Settings tab layout, adding frames for parameters, editable variables,
        and directory editing with scrolling support only for Script Parameters."""

        # Main container for Script Settings tab
        self.main_frame = ttk.Frame(self.script_settings_tab, width=1080)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=0)

        # Create a custom style for smaller buttons
        style = ttk.Style()
        style.configure('Small.TButton', padding=(2, 2), font=('TkDefaultFont', 9))
        style.configure('Browse.TButton', padding=(1, 1), font=('TkDefaultFont', 7))
        style.configure('Medium.TButton', padding=(3, 3), font=('TkDefaultFont', 12))


        # Define custom styles for frames and label frames
        style.configure(
            "Custom.TLabelframe",
            background="#D9D9D9",
            borderwidth=2,  # Add a visible border
            relief="groove"  # Add a groove effect for the border
        )
        style.configure("Custom.TLabelframe.Label", background="#D9D9D9")
        style.configure("Custom.TFrame", background="#D9D9D9")

        # Top frame for buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=0, columnspan=2, sticky="")

        # Configure columns in button_frame to expand equally
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)

        # Frame for the left column buttons
        left_buttons_frame = ttk.Frame(self.button_frame)
        left_buttons_frame.grid(row=0, column=0, padx=(0, 200), pady=1, sticky="ns")

        # Frame for the right column buttons
        right_buttons_frame = ttk.Frame(self.button_frame)
        right_buttons_frame.grid(row=0, column=1, padx=(200, 0), pady=1, sticky="ns")

        # Configure frames to expand and fill their columns
        left_buttons_frame.columnconfigure(0, weight=1)
        right_buttons_frame.columnconfigure(0, weight=1)

        # Left side buttons (aligned to left)
        self.save_button = ttk.Button(left_buttons_frame, text="Save Settings", command=self.save_settings,
                                      style='Small.TButton')
        self.save_button.grid(row=0, column=0, sticky='', pady=2)

        self.run_button = ttk.Button(left_buttons_frame, text="Run Script", command=self.run_script,
                                     style='Small.TButton')
        self.run_button.grid(row=1, column=0, sticky='', pady=2)

        self.terminate_button = ttk.Button(left_buttons_frame, text="Terminate Script", command=self.terminate_script,
                                           style='Small.TButton')
        self.terminate_button.grid(row=2, column=0, sticky='', pady=2)

        # Right side buttons (aligned to right)
        self.save_default_button = ttk.Button(right_buttons_frame, text="Save New Default Settings",
                                              command=self.save_default_settings, style='Small.TButton')
        self.save_default_button.grid(row=0, column=1, sticky='', pady=2)

        self.load_default_button = ttk.Button(right_buttons_frame, text="Load Default Settings",
                                              command=self.load_default_settings, style='Small.TButton')
        self.load_default_button.grid(row=1, column=1, sticky='', pady=2)

        # Save to Queue button with text box
        self.button_text_frame = ttk.Frame(right_buttons_frame)
        self.button_text_frame.grid(row=2, column=1, sticky='', pady=2)

        self.save_to_queue_button = ttk.Button(self.button_text_frame, text="Save to Queue", command=self.save_to_queue,
                                               style='Small.TButton')
        self.save_to_queue_button.pack(side="left")

        # Replace Text widget with Entry widget for single-line input
        self.text_box = ttk.Entry(self.button_text_frame, width=15, font=('TkDefaultFont', 12))
        self.text_box.pack(side="left", padx=5)

        # Left frame for Script Parameters with content
        self.script_parameters_frame = ttk.LabelFrame(
            self.main_frame, text="Script Parameters", width=540, style="Custom.TLabelframe"
        )
        self.script_parameters_frame.grid(row=3, rowspan=2, column=0, padx=10, pady=2, sticky="nsew")

        # Set the background color for the script parameters canvas and frame
        self.script_parameters_canvas = tk.Canvas(
            self.script_parameters_frame, bg="#D9D9D9", highlightthickness=0
        )
        self.scrollable_script_parameters_frame = ttk.Frame(self.script_parameters_canvas, style="Custom.TFrame")

        # Create window for the scrollable frame anchored at the top
        self.script_parameters_canvas.create_window((0, 0), window=self.scrollable_script_parameters_frame, anchor="nw")

        # Pack canvas without scrollbar
        self.script_parameters_canvas.pack(side="left", fill="both", expand=True)

        # Right frame for Editable Variables and Directory Editing
        self.editable_right_frame = ttk.Frame(self.main_frame, width=540)
        self.editable_right_frame.grid(row=3, column=1, padx=10, pady=2, sticky="nsew")

        self.editable_variables_frame = ttk.LabelFrame(
            self.editable_right_frame, text="Editable Variables", style="Custom.TLabelframe"
        )
        self.editable_variables_frame.pack(fill="both", expand=False, padx=10, pady=0)

        self.directory_editing_frame = ttk.LabelFrame(
            self.editable_right_frame, text="Directory Editing", style="Custom.TLabelframe"
        )
        self.directory_editing_frame.pack(fill="both", expand=False, padx=10, pady=0)

        # Configure main content columns in row 3 to be equal
        self.main_frame.grid_columnconfigure(0, weight=1, uniform="equal")
        self.main_frame.grid_columnconfigure(1, weight=1, uniform="equal")
        # Set row 3 to not expand vertically
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=3)
        self.main_frame.grid_rowconfigure(5, weight=3)
        self.main_frame.grid_rowconfigure(6, weight=3)

        # Initialize sections
        self.create_script_parameters_section()
        self.create_directory_editing_section()
        self.create_editable_variables_section()

    # 1. Tab Layout and Initialization
    def create_script_parameters_section(self):
        """Setup the Script Parameters section, initializing the toggle settings for various script parameters."""
        self.script_row_counter = 0

        for attr in script_toggle_variables_without_gzip:
            value = getattr(const, attr, None)
            if value is not None:
                self.create_toggle_with_sub_variables(self.scrollable_script_parameters_frame, attr, value)
                self.initial_toggle_states[attr] = value
                self.script_row_counter += 2

        # Bind mouse wheel scroll only within Script Parameters section
        #self.script_parameters_canvas.bind("<MouseWheel>", self.on_mouse_wheel_script_parameters)

    # def on_mouse_wheel_script_parameters(self, event):
    #     """Scroll the script parameters section with the mouse wheel."""
    #     self.script_parameters_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_editable_variables_section(self):
        """Initialize the Editable Variables section, displaying fields that users can edit directly within the GUI."""
        self.create_editable_subsection(self.editable_variables_frame, "Commonly Edited", [
            ("list_folder_name", const.list_folder_name,
             "This is the name of the folder where QueueTY will read and write to. The folder can be thought of as your experiment."),
            ("template_name", const.template_name, "Not too important. Can be left empty. Basically just adds text to the front of the INP file.")
        ])

        self.create_editable_subsection(self.editable_variables_frame, "Less Commonly Edited", [
            ("temp_dir", const.temp_dir,
             "Builds a temporary directory to store transient data in at the path described by remote_directory (see below). Can be renamed."),
            ("server", const.server, "Your server address eg. buffalo.edu"),
            ("port", const.port, "default SSH port is 22"),
            ("username", const.username, "Whatever your username is"),
            ("password", const.password, "Whatever your password is")
        ])

        self.create_editable_subsection(self.editable_variables_frame, "One and Done", [
            ("compound_list_directory", const.compound_list_directory,
             "This is the directory that list_folder_name is in."),
            ("vconf_path", const.vconf_path, "This is the path to the Vconf executable."),
            ("remote_directory", const.remote_directory,
             "This is where on the remote server you would like to put the temp_dir folder. Basically the 'compound_list_directory' of the remote server.\n\nOnce you provide your credentials and press 'Save Settings' you will be able to access the Browse button."),
        ])

        # Add trace on list_folder_name and compound_list_directory to update VCONF settings
        self.editable_vars["list_folder_name"].bind("<FocusOut>", self.update_vconf_paths)
        self.editable_vars["compound_list_directory"].bind("<FocusOut>", self.update_vconf_paths)

    def create_directory_editing_section(self):
        """Setup Directory Editing section with toggles for options like gzip and remote directory checks."""
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

    def create_editable_subsection(self, parent, title, variables):
        """Create a labeled subsection within a parent frame, displaying editable variables with optional browse buttons."""
        subsection_frame = ttk.LabelFrame(parent, text=title)
        subsection_frame.pack(fill="x", expand=False, padx=10, pady=10)

        # Helper function to adjust entry width with min and max constraints
        def adjust_entry_width(entry, min_width=20, max_width=30):
            """Adjust the width of an entry widget based on its content length, constrained by min and max width."""
            content_length = len(entry.get())
            new_width = max(min(content_length + 1, max_width), min_width)  # Adjust width, within min/max bounds
            entry.config(width=new_width)

        row_counter = 0
        for var_name, var_value, tooltip in variables:
            var_label = ttk.Label(subsection_frame, text=var_name, font=("TkDefaultFont", 10))
            var_label.grid(row=row_counter, column=0, sticky="w", padx=5, pady=2)
            self.create_tooltip(var_label, tooltip)

            var_entry = ttk.Entry(subsection_frame, font=("TkDefaultFont", 10), width=11)  # Start with min width
            var_entry.insert(0, str(var_value))

            # Apply dynamic resizing with specified min and max widths
            adjust_entry_width(var_entry)
            var_entry.grid(row=row_counter, column=1, sticky="w", padx=5, pady=2)
            var_entry.bind("<KeyRelease>", lambda e, entry=var_entry: adjust_entry_width(entry))

            self.create_tooltip(var_entry, tooltip)
            self.editable_vars[var_name] = var_entry

            if var_name == "remote_directory":
                browse_button = ttk.Button(subsection_frame, text="Browse",
                                           command=lambda var=var_name: self.browse_remote_directory(var),
                                           style='Browse.TButton')
                browse_button.grid(row=row_counter, column=2, sticky="w", padx=5, pady=2)
                var_entry.bind("<FocusOut>", self.save_remote_directory)

            elif var_name in ["compound_list_directory", "list_folder_name", "remote_file_path"]:
                browse_button = ttk.Button(subsection_frame, text="Browse",
                                           command=lambda var=var_name: self.browse_directory(var),
                                           style='Browse.TButton')
                browse_button.grid(row=row_counter, column=2, sticky="w", padx=5, pady=2)

            elif var_name == "vconf_path":
                browse_button = ttk.Button(subsection_frame, text="Browse",
                                           command=lambda var=var_name: self.browse_file(var),
                                           style='Browse.TButton')
                browse_button.grid(row=row_counter, column=2, sticky="w", padx=5, pady=2)

            row_counter += 1

    # 2. Toggle and Parameter Functions
    def create_toggle_with_sub_variables(self, parent, toggle, value, is_directory_editing=False):
        """Create a toggle checkbox with sub-variables that depend on its state, dynamically resizing text entries."""
        # Determine if the value should be a BooleanVar or Entry based on its type
        toggle_check = None
        if isinstance(value, bool):
            toggle_var = tk.BooleanVar(value=value)
        else:
            toggle_var = tk.IntVar(value=value)  # Use IntVar for integers like 0 and 1

        self.script_toggle_vars[toggle] = toggle_var

        # Create the main toggle checkbox for Boolean values only
        if isinstance(value, bool):
            toggle_var = tk.BooleanVar(value=value)
            self.script_toggle_vars[toggle] = toggle_var

            # **Use ttk.Checkbutton with Custom Style**
            toggle_check = ttk.Checkbutton(
                parent,
                text=toggle,
                variable=toggle_var,
                command=lambda: self.toggle_sub_variables(toggle_var, sub_vars_frame, toggle, is_directory_editing),
                style="Custom.TCheckbutton"  # Apply the custom style
            )
            toggle_check.grid(row=self.script_row_counter, column=0, sticky="w", padx=5, pady=2)
            tooltip_text = tooltips.get(toggle, "")
            self.create_tooltip(toggle_check, tooltip_text)
            self.script_toggle_vars_widgets[toggle] = toggle_check

        else:
            # For integer values, create an Entry widget instead of a checkbox
            entry_widget = ttk.Entry(parent, textvariable=toggle_var, font=("TkDefaultFont", 10))
            entry_widget.grid(row=self.script_row_counter, column=0, sticky="w", padx=5, pady=2)
            tooltip_text = tooltips.get(toggle, "")
            self.create_tooltip(entry_widget, tooltip_text)
            self.script_toggle_vars_widgets[toggle] = entry_widget

        # Frame for sub-variables associated with this toggle
        sub_vars_frame = ttk.Frame(parent)
        sub_vars_frame.grid(row=self.script_row_counter + 1, column=0, padx=20, sticky="nsew")
        sub_vars_frame.widgets = []  # Track sub-variable widgets for this toggle

        # Helper function to adjust entry width with constraints
        def adjust_entry_width(entry, min_width=20, max_width=30):
            content_length = len(entry.get())
            new_width = max(min(content_length + 1, max_width), min_width)
            entry.config(width=new_width)

        # Create each sub-variable control based on its type
        sub_row = 0
        sorted_sub_vars = sorted(
            sub_variables.get(toggle, []))  # Retrieve sub-variables from `sub_variables` dictionary
        for sub_var in sorted_sub_vars:
            sub_value = getattr(const, sub_var, None)
            sub_var_label = ttk.Label(sub_vars_frame, text=sub_var, font=("TkDefaultFont", 10))
            sub_var_label.grid(row=sub_row, column=0, sticky="w", padx=5, pady=2)
            sub_vars_frame.widgets.append(sub_var_label)

            # Debug message
            # print(f"Created label for sub-variable '{sub_var}'")

            tooltip_text = tooltips.get(sub_var, "")
            self.create_tooltip(sub_var_label, tooltip_text)

            if sub_value in [True, False]:  # Boolean values become checkboxes
                sub_var_entry = tk.BooleanVar(value=sub_value)
                sub_var_check = ttk.Checkbutton(
                    sub_vars_frame,
                    variable=sub_var_entry,
                    style="Custom.TCheckbutton",  # Apply the custom style
                )

                sub_var_check.grid(row=sub_row, column=1, sticky="w", padx=5, pady=2)
                self.create_tooltip(sub_var_check, tooltip_text)
                sub_vars_frame.widgets.append(sub_var_check)
                self.editable_vars[sub_var] = sub_var_entry

                # Debug message
                # print(f"Created checkbox for sub-variable '{sub_var}' with initial value '{sub_value}'")

            elif isinstance(sub_value, int):  # Integer values get an integer-specific entry field
                sub_var_entry = ttk.Entry(sub_vars_frame, font=("TkDefaultFont", 10))
                sub_var_entry.insert(0, str(sub_value))
                adjust_entry_width(sub_var_entry)
                sub_var_entry.grid(row=sub_row, column=1, sticky="w", padx=5, pady=2)
                sub_var_entry.bind("<KeyRelease>", lambda e, entry=sub_var_entry: adjust_entry_width(entry))
                self.create_tooltip(sub_var_entry, tooltip_text)
                sub_vars_frame.widgets.append(sub_var_entry)
                self.editable_vars[sub_var] = sub_var_entry

                # Debug message
                # print(f"Created integer entry for sub-variable '{sub_var}' with initial value '{sub_value}'")

            elif sub_var in ["timestamp_folder", "delete_file_path", "gzip_directory_by_name",
                             "unzip_directory_by_name", "remote_file_path"]:
                # Text entry with a browse button for file/directory paths
                sub_var_entry = ttk.Entry(sub_vars_frame, font=("TkDefaultFont", 10))
                if sub_value is not None:
                    sub_var_entry.insert(0, sub_value)
                adjust_entry_width(sub_var_entry)
                sub_var_entry.grid(row=sub_row, column=1, sticky="w", padx=5, pady=2)
                sub_var_entry.bind("<KeyRelease>", lambda e, entry=sub_var_entry: adjust_entry_width(entry))
                self.create_tooltip(sub_var_entry, tooltip_text)
                sub_vars_frame.widgets.append(sub_var_entry)
                self.editable_vars[sub_var] = sub_var_entry

                # Add browse button
                browse_button = ttk.Button(sub_vars_frame, text="Browse",
                                           command=lambda sv=sub_var: self.browse_remote_directory(sv), style='Browse.TButton')
                browse_button.grid(row=sub_row, column=2, sticky="w", padx=5, pady=2)
                sub_vars_frame.widgets.append(browse_button)

                # Debug message
                # print(f"Created file path entry with browse button for '{sub_var}' with initial value '{sub_value}'")

            else:  # All other values become text entries
                sub_var_entry = ttk.Entry(sub_vars_frame, font=("TkDefaultFont", 10))
                if sub_value is not None:
                    sub_var_entry.insert(0, str(sub_value))
                adjust_entry_width(sub_var_entry)
                sub_var_entry.grid(row=sub_row, column=1, sticky="w", padx=5, pady=2)
                sub_var_entry.bind("<KeyRelease>", lambda e, entry=sub_var_entry: adjust_entry_width(entry))
                self.create_tooltip(sub_var_entry, tooltip_text)
                sub_vars_frame.widgets.append(sub_var_entry)
                self.editable_vars[sub_var] = sub_var_entry

                # Debug message
                # print(f"Created text entry for sub-variable '{sub_var}' with initial value '{sub_value}'")

            sub_row += 1

        # Control the enabled/disabled state of sub-variables based on the main toggle's value
        self.set_widget_state(sub_vars_frame, "normal" if toggle_var.get() else "disabled")

        # Add the sub-variable frame and toggle widget for reference
        self.sub_var_frames[toggle] = sub_vars_frame
        self.script_toggle_vars_widgets[toggle] = toggle_check

        # Increment row counter for layout
        self.script_row_counter += 2

    def toggle_sub_variables(self, toggle_var, sub_vars_frame, toggle, is_directory_editing=False):
        """Toggle visibility and interactivity of sub-variables when a main toggle is activated or deactivated."""
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
        """Enable or disable script parameters, primarily for controlling the gzip and directory check toggles."""
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

    # 3. Directory Editing and Path Browsing Functions
    def add_browse_button_to_var(self, var_name, parent_frame):
        """Add a browse button next to specified variables, allowing users to navigate and select directories or files."""
        var_entry = self.editable_vars.get(var_name)
        if var_entry:
            browse_button = ttk.Button(parent_frame, text="Browse",
                                       command=lambda: self.browse_remote_directory(var_name))
            var_entry.grid(row=var_entry.grid_info()["row"], column=1, sticky="w", padx=5, pady=2)
            browse_button.grid(row=var_entry.grid_info()["row"], column=2, sticky="w", padx=5, pady=2)

    # noinspection PyUnresolvedReferences
    def browse_remote_directory(self, var_name):
        """Open a dialog to browse remote directories, updating the associated variable entry with the selected path."""
        if not self.ssh_connected:
            self.connect_to_server()

        if not self.ssh_connected:
            self.append_to_console("SSH connection is not established. Please check your credentials.")
            return

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

    def browse_directory(self, var_name):
        initial_dir = self.editable_vars["compound_list_directory"].get() if var_name == "list_folder_name" else "/"
        directory = filedialog.askdirectory(initialdir=initial_dir, title="Select Directory",
                                            parent=self)  # Set parent to self
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

    # Utility Functions
    @staticmethod
    def set_widget_state(frame, state):
        """Set the state (enabled/disabled) for all child widgets in a frame."""
        for widget in frame.winfo_children():
            try:
                widget.config(state=state)
            except tk.TclError as e:
                print(f"Failed to set widget state: {e}")

    # endregion

    # region ---- Console Tab ----

    # 1. Console Initialization Functions
    def create_console_tab(self):
        """Initialize the console tab with a text display, scrollbar, and run/terminate buttons."""

        # Configure the grid for the console_tab
        self.console_tab.rowconfigure(0, weight=4)  # Console text widget row
        self.console_tab.rowconfigure(1, weight=1)  # Buttons row
        self.console_tab.columnconfigure(0, weight=1)  # Main content column
        self.console_tab.columnconfigure(1, weight=0)  # Scrollbar column

        # Define custom styles for console buttons with larger font size
        style = ttk.Style()

        # Style for main console buttons
        style.configure('Console.TButton',
                        background='#D9D9D9',
                        foreground='black',
                        font=('TkDefaultFont', 12),  # Increased font size to 12
                        padding=(3, 3))  # Increased padding for better appearance
        style.map('Console.TButton',
                  background=[('active', '#C0C0C0'), ('pressed', '#A0A0A0')])

        # Style for search-related buttons
        style.configure('Search.TButton',
                        background='#D9D9D9',
                        foreground='black',
                        font=('TkDefaultFont', 12),  # Increased font size to 12
                        padding=(3, 3))
        style.map('Search.TButton',
                  background=[('active', '#C0C0C0'), ('pressed', '#A0A0A0')])

        # Update 'Small.TButton' to have font size 12
        style.configure('Medium.TButton',
                        padding=(3, 3),
                        font=('TkDefaultFont', 12))  # Increased font size to 12

        # Set up the console text widget within the console_tab with white background
        self.console_text = tk.Text(self.console_tab, wrap='word', bg="white", relief="flat")
        self.console_text.grid(row=0, column=0, sticky='nsew')

        # Set up a scrollbar for the console and link it to the console_text
        self.console_scrollbar = ttk.Scrollbar(self.console_tab, command=self.console_text.yview)
        self.console_scrollbar.grid(row=0, column=1, sticky='ns')
        self.console_text.config(yscrollcommand=self.console_scrollbar.set)

        # Set up the button frame with matching background color
        self.button_frame = tk.Frame(self.console_tab, bg="#D9D9D9")
        self.button_frame.grid(row=1, column=0, columnspan=2, sticky='n')

        # Configure columns in button_frame for proper alignment
        for i in range(6):  # Adjust the range if you have more columns
            self.button_frame.columnconfigure(i, weight=1)

        # Run Script button
        self.run_button_console = ttk.Button(
            self.button_frame,
            text="Run Script",
            command=self.run_script,
            style='Console.TButton'
        )
        self.run_button_console.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

        # Terminate Script button
        self.terminate_button_console = ttk.Button(
            self.button_frame,
            text="Terminate Script",
            command=self.terminate_script,
            style='Console.TButton'
        )
        self.terminate_button_console.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Stop Queue button
        self.stop_queue_button = ttk.Button(
            self.button_frame,
            text="Stop Queue",
            command=self.stop_task_queue,
            style='Console.TButton'
        )
        self.stop_queue_button.grid(row=0, column=2, padx=5, pady=5, sticky='ew')

        # Auto-scroll checkbox
        self.auto_scroll_checkbox = ttk.Checkbutton(
            self.button_frame,
            text="Snap View to End",
            variable=self.auto_scroll,
            command=self.on_auto_scroll_toggle,
            style='Custom.TCheckbutton'  # Assuming you have a Custom.TCheckbutton style
        )
        self.auto_scroll_checkbox.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Next Match button
        self.down_button = ttk.Button(
            self.button_frame,
            text="Next Match",
            command=self.navigate_to_next_match,
            style='Console.TButton'
        )
        self.down_button.grid(row=0, column=4, padx=5, pady=5, sticky='ew')

        # Previous Match button
        self.up_button = ttk.Button(
            self.button_frame,
            text="Previous Match",
            command=self.navigate_to_previous_match,
            style='Console.TButton'
        )
        self.up_button.grid(row=0, column=5, padx=5, pady=5, sticky='ew')

        # Bind Ctrl+F to open the search bar
        self.console_text.bind('<Control-f>', self.open_search_bar)

        # Add tooltips if you have them defined
        self.create_tooltip(self.up_button, tooltips.get("up_button", ""))
        self.create_tooltip(self.down_button, tooltips.get("down_button", ""))
        self.create_tooltip(self.stop_queue_button, tooltips.get("stop_queue_button", ""))

        # Create a hidden search bar frame with consistent background
        self.search_bar_frame = tk.Frame(self.button_frame, bg="#D9D9D9")
        self.search_bar_frame.grid(row=1, column=0, columnspan=6, pady=5, sticky='ew')
        self.search_bar_frame.grid_columnconfigure(0, weight=1)
        self.search_bar_frame.grid_columnconfigure(1, weight=1)
        self.search_bar_frame.grid_columnconfigure(2, weight=1)
        self.search_bar_frame.grid_columnconfigure(3, weight=1)

        # Add widgets to the search_bar_frame
        tk.Label(self.search_bar_frame, text="Search:", bg="#D9D9D9").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.search_entry = tk.Entry(self.search_bar_frame, width=30, font=('TkDefaultFont', 15))
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        search_button = ttk.Button(
            self.search_bar_frame,
            text="Find",
            command=self.perform_search,
            style='Search.TButton'  # Using the updated Search.TButton style
        )
        search_button.grid(row=0, column=2, padx=5, pady=5, sticky='ew')

        # Close button to hide the search bar
        close_button = ttk.Button(
            self.search_bar_frame,
            text="Close",
            command=self.hide_search_bar,
            style='Search.TButton'
        )
        close_button.grid(row=0, column=3, padx=5, pady=5, sticky='ew')

        # Initially hide the search bar
        self.search_bar_frame.grid_remove()

    # 2. Message Management Functions
    def append_to_console(self, message):
        """Append a message to the console, ensuring no consecutive duplicates."""
        # Enable the text widget to insert new text
        self.console_text.config(state='normal')
        self.console_text.insert(tk.END, message + "\n")

        # Check if there is a current search term and re-apply highlights if needed
        current_search_term = self.get_current_search_term()
        if current_search_term:
            self.search_in_console(current_search_term)

        # Restore the text widget to read-only
        self.console_text.config(state='disabled')

        # Auto-scroll if the checkbox is checked
        if self.auto_scroll.get():
            self.console_text.see(tk.END)

    def on_auto_scroll_toggle(self):
        """Handle the toggling of the auto-scroll checkbox."""
        # Optional: Add any actions you want to perform when the checkbox is toggled
        print(f"Auto-scroll is now {'enabled' if self.auto_scroll.get() else 'disabled'}.")

    def delete_last_line(self):
        """Delete the last line in the console, often used in animations."""
        self.console_text.config(state='normal')
        self.console_text.delete("end-3l", "end-1l")
        self.console_text.config(state='disabled')

    def open_search_dialog(self, event=None):
        """Open a dialog to search for a keyword in the console output."""
        # Check if search dialog already exists
        if hasattr(self, 'search_dialog') and self.search_dialog.winfo_exists():
            self.search_dialog.deiconify()
            self.search_dialog.lift()
            return

        # Create a top-level window for the search dialog
        self.search_dialog = tk.Toplevel(self)
        self.search_dialog.title("Search")

        # Position the dialog above the main window
        x = self.winfo_rootx() + 200
        y = self.winfo_rooty() + 200
        self.search_dialog.geometry(f"+{x}+{y}")

        # Prevent interaction with the main window
        self.search_dialog.transient(self)
        self.search_dialog.grab_set()

        # Label and entry for the search term
        tk.Label(self.search_dialog, text="Enter search term:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = tk.Entry(self.search_dialog, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.focus_set()

        # Search button
        search_button = ttk.Button(
            self.search_dialog,
            text="Search",
            command=lambda: [self.search_in_console(search_entry.get()), self.search_dialog.destroy()]
        )
        search_button.grid(row=0, column=2, padx=5, pady=5)

        # Bind the Return key to trigger the search and close the dialog
        search_entry.bind('<Return>',
                          lambda event: [self.search_in_console(search_entry.get()), self.search_dialog.destroy()])

    def search_in_console(self, search_term):
        """Search for the given term in the console output and highlight matches."""
        # Remove previous highlights
        self.console_text.tag_remove('highlight', '1.0', tk.END)

        # Clear any previous match indices
        self.match_indices = []
        self.current_match_index = -1  # Reset current match index

        if not search_term:
            self.current_search_term = ''  # Clear the stored search term if empty
            return  # If the search term is empty, do nothing

        # Store the current search term
        self.current_search_term = search_term

        # Make the text widget editable temporarily
        self.console_text.config(state='normal')

        # Define a tag for highlighting
        self.console_text.tag_configure('highlight', background='yellow', foreground='black')

        # Start from the beginning of the text widget
        start_pos = '1.0'
        while True:
            # Find the next occurrence of the search term
            idx = self.console_text.search(search_term, start_pos, stopindex=tk.END, nocase=1)
            if not idx:
                break  # No more occurrences found

            # Calculate the end position of the matched text
            end_pos = f"{idx}+{len(search_term)}c"

            # Apply the highlight tag to the matched text
            self.console_text.tag_add('highlight', idx, end_pos)

            # Store this match index
            self.match_indices.append(idx)

            # Move the starting position forward
            start_pos = end_pos

        # Restore the text widget to read-only
        self.console_text.config(state='disabled')

        # Move to the first match, if any
        if self.match_indices:
            self.current_match_index = 0
            self.move_to_match(self.current_match_index)

    def move_to_match(self, match_index):
        """Move to a specific match and highlight it."""
        if not self.match_indices:
            return  # No matches to navigate

        # Ensure match_index is within bounds
        if match_index < 0 or match_index >= len(self.match_indices):
            return

        # Get the start and end positions of the current match
        start_pos = self.match_indices[match_index]
        end_pos = f"{start_pos}+{len(self.current_search_term)}c"

        # Remove previous 'current' highlight and add the current match highlight
        self.console_text.tag_remove('current_match', '1.0', tk.END)
        self.console_text.tag_configure('current_match', background='orange')
        self.console_text.tag_add('current_match', start_pos, end_pos)

        # Scroll to the match
        self.console_text.see(start_pos)

    def navigate_to_next_match(self):
        """Move to the next match in the console."""
        # Ensure match_indices exists and is not empty
        if getattr(self, 'match_indices', None):
            # Increment the index and wrap around if needed
            self.current_match_index = (self.current_match_index + 1) % len(self.match_indices)
            self.move_to_match(self.current_match_index)

    def navigate_to_previous_match(self):
        """Move to the next match in the console."""
        # Ensure match_indices exists and is not empty
        if getattr(self, 'match_indices', None):
            # Increment the index and wrap around if needed
            self.current_match_index = (self.current_match_index - 1) % len(self.match_indices)
            self.move_to_match(self.current_match_index)

    def get_current_search_term(self):
        """Return the current search term."""
        return getattr(self, 'current_search_term', '')

    def open_search_bar(self, event=None):
        """Show the search bar below the buttons at the bottom of the console tab."""
        self.search_bar_frame.grid(row=1, column=0, columnspan=5, pady=(10, 5), sticky='ew')
        self.search_entry.focus_set()  # Focus on the search entry

    def perform_search(self):
        """Perform the search in the console output."""
        search_term = self.search_entry.get()
        self.search_in_console(search_term)

    def hide_search_bar(self):
        """Hide the search bar and remove any search highlights."""
        self.search_bar_frame.grid_forget()  # Remove the search bar from the grid
        self.clear_search_highlights()  # Clear search highlights

    def clear_search_highlights(self):
        """Remove all search highlights (yellow and orange) from the console."""
        self.console_text.tag_remove('highlight', '1.0', tk.END)  # Remove yellow highlights
        self.console_text.tag_remove('current_match', '1.0', tk.END)  # Remove orange highlight

    # 4. Output Capture and Handling Functions
    def capture_output(self, pipe, is_error=False):
        """Capture output from a given pipe, appending to the console and monitoring for task completion."""
        try:
            for line in iter(pipe.readline, ''):
                if closing_flag:
                    break

                message = f"ERROR: {line.strip()}" if is_error else line.strip()

                # Avoid displaying consecutive duplicates in the console
                if message != self.console_text.get("end-2l", "end-1l"):
                    self.append_to_console(message)

                # Log to file if logging is active
                if self.console_output_stream.is_logging:
                    self.console_output_stream.write(message)
                    self.console_output_stream.flush()

                # Check for the task completion signal and set flag
                if "All active scripts passed!" in message and not self.is_task_complete:
                    self.is_task_complete = True
                    self.after(100, lambda: self.on_task_completed(self.current_task))
                    break

            pipe.close()
        except Exception as output_exception:
            # Append to console any output capture errors, differentiating stderr from stdout
            self.append_to_console(f"{'Stderr' if is_error else 'Stdout'} capture error: {output_exception}")

    # endregion

    # region ---- VCONF Settings Tab ----

    # 1. Tab Initialization Functions
    def create_vconf_settings_tab(self):
        """Set up the VCONF settings tab with fixed-size frames for default and experimental settings sections."""

        # Configure the grid for the vconf_settings_tab
        self.vconf_settings_tab.rowconfigure(0, weight=0)
        self.vconf_settings_tab.columnconfigure(0, weight=1)
        self.vconf_settings_tab.columnconfigure(1, weight=1)

        # Add default and experimental VCONF settings sections
        self.create_vconf_subsection(self.vconf_settings_tab, "Default VConf Settings",
                                     const_2.default_vconf_settings, 0)
        self.create_vconf_subsection(self.vconf_settings_tab, "Experimental VConf Settings",
                                     const_2.experimental_vconf_settings, 1)

    def create_vconf_subsection(self, parent, title, variables, column):
        """Create a fixed-size labeled subsection within the VCONF tab, displaying VCONF settings with entry fields."""

        # Create a LabelFrame for the subsection
        subsection_frame = ttk.LabelFrame(parent, text=title)
        subsection_frame.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")

        # Set fonts and widths
        label_font = ("TkDefaultFont", 8)
        entry_font = ("TkDefaultFont", 8)
        entry_width = 40  # Increased to make text boxes twice as wide as before

        # Populate subsection with settings and tooltips
        row_counter = 0
        for var_name, var_value in variables.items():
            var_label = ttk.Label(subsection_frame, text=var_name, font=label_font)
            var_label.grid(row=row_counter, column=0, sticky="w", padx=5, pady=2)

            tooltip_text = vconf_tooltips.get(var_name, f"This is the {var_name.replace('_', ' ').title()}.")
            self.create_tooltip(var_label, tooltip_text)  # Tooltip on label only

            var_entry = ttk.Entry(subsection_frame, font=entry_font, width=entry_width)
            var_entry.insert(0, str(var_value))
            var_entry.grid(row=row_counter, column=1, sticky="w", padx=5, pady=2)

            # Tooltip creation for entry is removed/commented out
            # self.create_tooltip(var_entry, tooltip_text)  # Disabled tooltip on entry

            self.editable_vars[f"{title}_{var_name}"] = var_entry
            row_counter += 1

        # Optionally, adjust column weights if needed
        subsection_frame.columnconfigure(0, weight=1)
        subsection_frame.columnconfigure(1, weight=1)

    # 3. Settings Management and Update Functions
    def update_vconf_paths(self, _event=None):
        """Update paths for VCONF-related settings based on user input in the GUI."""
        list_folder_name = self.editable_vars["list_folder_name"].get()
        compound_list_directory = self.editable_vars["compound_list_directory"].get()

        # Update file paths in const_2
        const_2.SDF_FILENAME = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}.sdf"
        const_2.OUTPUT_LOG = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}.log"
        const_2.OUTPUT_SDF = fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}_vconf.sdf"
        const_2.vconf_batch_sdf_path = \
            fr"{compound_list_directory}\{list_folder_name}\VCONF_outputs\{list_folder_name}_vconf_batchfile.sdf"

        const_2.default_vconf_settings["SDF_FILENAME"] = const_2.SDF_FILENAME
        const_2.default_vconf_settings["OUTPUT_LOG"] = const_2.OUTPUT_LOG
        const_2.default_vconf_settings["OUTPUT_SDF"] = const_2.OUTPUT_SDF
        const_2.default_vconf_settings["vconf_batch_sdf_path"] = const_2.vconf_batch_sdf_path

        const_2.experimental_vconf_settings["SDF_FILENAME"] = const_2.SDF_FILENAME
        const_2.experimental_vconf_settings["OUTPUT_LOG"] = const_2.OUTPUT_LOG
        const_2.experimental_vconf_settings["OUTPUT_SDF"] = const_2.OUTPUT_SDF
        const_2.experimental_vconf_settings["vconf_batch_sdf_path"] = const_2.vconf_batch_sdf_path

        # Save and reload settings
        self.save_to_constants()
        self.save_to_constants_last()
        self.reload_relevant_vconf_settings()

    def reload_vconf_settings(self):
        """Reload all VCONF settings in the tab, refreshing displayed values."""
        self.reload_relevant_vconf_settings()

    def reload_relevant_vconf_settings(self):
        """Reload specific VCONF paths, refreshing entries for both default and experimental settings."""
        for key in ["SDF_FILENAME", "OUTPUT_LOG", "OUTPUT_SDF", "vconf_batch_sdf_path"]:
            for setting_type in ["Default VConf Settings", "Experimental VConf Settings"]:
                widget_key = f"{setting_type}_{key}"
                if widget_key in self.editable_vars:
                    entry_widget = self.editable_vars[widget_key]
                    new_value = const_2.default_vconf_settings[key] if setting_type == "Default VConf Settings" \
                        else const_2.experimental_vconf_settings[key]
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, new_value)

    # 4. Utility and Formatting Functions
    @staticmethod
    def format_vconf_value(value):
        """Format a value for VCONF settings based on its type for consistent representation."""
        if value is None:
            return "None"
        if isinstance(value, str):
            return f'fr"{value}"' if "\\" in value else f'"{value}"'
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, int):
            return str(value)
        elif isinstance(value, tuple):
            return f"({', '.join(map(str, value))})"
        else:
            return value

    @staticmethod
    def format_value(value):
        """Format value based on type for consistent saving."""
        if isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, int):
            return f"{value}"
        elif isinstance(value, str):
            return fr'"{value}"'
        return str(value)  # Fallback for other types

    # endregion

    # region ---- File Editor Tab ----

    # 1. Tab Initialization Function
    def create_file_editor_tab(self):
        """Set up the File Editor tab with 4 equal-sized scrollable text fields for editing files."""
        # Define the main container frame with a 2x2 grid layout
        self.file_editor_main_frame = ttk.Frame(self.file_editor_tab, padding="5")
        self.file_editor_main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure the grid layout to make 2x2 sections equal in size
        num_rows, num_cols = 2, 2
        for row in range(num_rows):
            self.file_editor_main_frame.grid_rowconfigure(row, weight=0)
        for col in range(num_cols):
            self.file_editor_main_frame.grid_columnconfigure(col, weight=1)

        self.file_editor_main_frame.grid_rowconfigure(3, weight=1)

        # Dictionary to store references to text widgets for saving later
        self.script_texts = {}

        # Create 4 text editors in a 2x2 grid
        for i, (script_name, script_path) in enumerate(script_paths[:4]):  # Limit to 4 files
            row = i // num_cols
            col = i % num_cols

            # Create a labeled frame for each text editor section
            editor_frame = ttk.LabelFrame(self.file_editor_main_frame, text=script_name, padding="5")
            editor_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Frame to hold the text widget and scrollbar together
            text_frame = ttk.Frame(editor_frame)
            text_frame.pack(fill="both", expand=True)

            # Text widget to display and edit the file content with slightly increased height
            text_widget = tk.Text(text_frame, wrap="word", height=15)  # Adjusted height for better fit
            text_widget.pack(side="left", fill="both", expand=True)

            # Scrollbar inside the text frame, attached to the text widget
            scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
            scrollbar.pack(side="right", fill="y")
            text_widget.config(yscrollcommand=scrollbar.set)

            # Load file content into the text widget
            with open(script_path, "r") as file:
                text_widget.insert("1.0", file.read())

            # Store the text widget reference for later use
            self.script_texts[script_path] = text_widget

        # Save Files button below the grid to save changes made in the editor sections
        self.save_files_button = ttk.Button(self.file_editor_main_frame, text="Save Files", command=self.save_files)
        self.save_files_button.grid(row=2, column=0, columnspan=num_cols, pady=10, sticky="ew")

        # Configure additional row for the Save Files button
        self.file_editor_main_frame.grid_rowconfigure(2, weight=0)

    # 2. File Saving and Content Management Functions
    def save_files(self):
        """Save the contents of all text widgets in the File Editor tab to their respective file paths."""
        for filepath, text_widget in self.script_texts.items():
            self.save_file_content(filepath, text_widget)

    @staticmethod
    def save_file_content(filepath, text_widget):
        """Save the current content of a text widget to a specified file path."""
        try:
            # Remove trailing newline or whitespace from the text widget content
            content = text_widget.get("1.0", tk.END).strip()
            with open(filepath, "w") as file:
                file.write(content)
            print(f"Saved content to {filepath}")  # Debug statement
        except Exception as e:
            print(f"Failed to save content to {filepath}: {e}")  # Debug statement

    # endregion

    # region ---- Queue Tab ----

    # 1. Tab Layout and Initialization

    def create_queue_tab(self):
        """Initialize the layout for the Queue tab, setting up resizable columns for Queue, Settings, and Log sections."""
        # Create a horizontal PanedWindow to hold the columns with increased sashwidth
        self.previous_selection = None

        paned_window = tk.PanedWindow(
            self.queue_tab,
            orient=tk.HORIZONTAL,
            sashwidth=10,
            handlesize=20,
            handlepad=10,
            bg="#D9D9D9"  # Set background color for the sashes
        )
        paned_window.pack(fill=tk.BOTH, expand=False)

        # Left column frame (Queue)
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, minsize=200)  # Set the width for the Queue section

        # Middle column frame (Settings)
        middle_frame = ttk.Frame(paned_window)
        paned_window.add(middle_frame, minsize=10)  # Set narrower width for the Settings section

        # Right column frame (Log and Queue Status)
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, minsize=10)  # Set wider width for Log and Queue Status sections

        # Left side: Queue Listbox and Control Buttons in a labeled frame
        queue_frame = ttk.LabelFrame(left_frame, text="Queue", padding="10")
        queue_frame.pack(fill="both", expand=True)

        # Queue Listbox with adjusted height and no focus on selection
        self.queue_listbox = tk.Listbox(
            queue_frame,
            selectmode=tk.EXTENDED,
            width=15,
            height=20,
            takefocus=False,
            exportselection=False
        )
        self.queue_listbox.pack(padx=5, pady=0, fill="both", expand=True)
        self.queue_listbox.bind('<Delete>', self.delete_task_from_queue)
        self.queue_listbox.bind('<<ListboxSelect>>', self.on_task_selected)

        # Bind click event to detect clicks on empty space
        self.queue_listbox.bind("<Button-1>", self.on_queue_click)

        # Task control buttons
        button_width = 12
        button_frame = ttk.Frame(queue_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        for text, command in [
            ("Move Up", self.move_up),
            ("Move Down", self.move_down),
            ("Delete Task", self.delete_task_from_queue),
            ("Run Queue", self.run_task_queue),
            ("Stop Queue", self.stop_task_queue),
            ("Load Settings", self.load_selected_file_to_queue),
            ("Save File Changes", self.save_file_changes)
        ]:
            ttk.Button(button_frame, text=text, command=command, width=button_width).pack(fill="x", padx=2, pady=1)

        # Middle Column for Settings Display in a labeled frame
        self.settings_frame = ttk.LabelFrame(middle_frame, text="Settings", padding="10")
        self.settings_frame.pack(fill="both", expand=True)

        # Create a Frame within settings_frame to hold Text widget and Scrollbar
        text_frame = ttk.Frame(self.settings_frame)
        text_frame.pack(fill="both", expand=True)

        # Configure grid for text_frame
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        # Text widget for displaying settings content with specified width
        self.file_content_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            height=12,
            width=35,
            exportselection=False
        )
        self.file_content_text.grid(row=0, column=0, sticky="nsew")

        # Bind click and focus out events
        self.file_content_text.bind("<Button-1>", self.enable_text_editing)
        self.file_content_text.bind("<FocusOut>", self.disable_text_editing)

        # Configure the "small_font" tag for settings text
        self.file_content_text.tag_configure("small_font", font=("Arial", 8))

        # Scrollbar for the Text widget
        file_content_scroll_y = ttk.Scrollbar(text_frame, orient="vertical", command=self.file_content_text.yview)
        file_content_scroll_y.grid(row=0, column=1, sticky="ns")
        self.file_content_text.config(yscrollcommand=file_content_scroll_y.set)

        # Right Column for Log Display and Queue Status
        # Create a vertical PanedWindow inside the right frame with increased sashwidth
        right_paned_window = tk.PanedWindow(
            right_frame,
            orient=tk.VERTICAL,
            sashwidth=10,
            handlesize=20,
            handlepad=10,
            bg="#D9D9D9"  # Set background color for the sashes
        )
        right_paned_window.pack(fill="both", expand=True)

        # Log frame
        self.log_frame = ttk.LabelFrame(right_paned_window, text="Log", padding="10")
        right_paned_window.add(self.log_frame, minsize=50)

        # Create a Frame within log_frame to hold Text widget and Scrollbar
        log_text_frame = ttk.Frame(self.log_frame)
        log_text_frame.pack(fill="both", expand=True)

        # Configure grid for log_text_frame
        log_text_frame.rowconfigure(0, weight=1)
        log_text_frame.columnconfigure(0, weight=1)

        # Text widget for displaying log content
        self.log_content_text = tk.Text(
            log_text_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=30,
            width=30,
            exportselection=False
        )
        self.log_content_text.grid(row=0, column=0, sticky="nsew")

        # Bind click and focus out events
        self.log_content_text.bind("<Button-1>", self.enable_text_editing)
        self.log_content_text.bind("<FocusOut>", self.disable_text_editing)

        # Configure the "small_font" tag for log text
        self.log_content_text.tag_configure("small_font", font=("Arial", 8))

        # Scrollbar for the Text widget
        log_content_scroll_y = ttk.Scrollbar(log_text_frame, orient="vertical", command=self.log_content_text.yview)
        log_content_scroll_y.grid(row=0, column=1, sticky="ns")
        self.log_content_text.config(yscrollcommand=log_content_scroll_y.set)

        # Queue Status section in a labeled frame
        queue_status_frame = ttk.LabelFrame(right_paned_window, text="Queue Status", padding="10")
        right_paned_window.add(queue_status_frame, minsize=50)

        # Create a Frame within queue_status_frame to hold Text widget and Scrollbar
        status_text_frame = ttk.Frame(queue_status_frame)
        status_text_frame.pack(fill="both", expand=True)

        # Configure grid for status_text_frame
        status_text_frame.rowconfigure(0, weight=1)
        status_text_frame.columnconfigure(0, weight=1)

        # Text widget for displaying queue status
        self.progress_text = tk.Text(
            status_text_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=10,
            width=30,
            exportselection=False
        )
        self.progress_text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar for the Text widget
        progress_scroll_y = ttk.Scrollbar(status_text_frame, orient="vertical", command=self.progress_text.yview)
        progress_scroll_y.grid(row=0, column=1, sticky="ns")
        self.progress_text.config(yscrollcommand=progress_scroll_y.set)

    def update_task_labels(self):
        """Update the labels for Settings, Log, and Queue Status based on the selected task."""
        selected_index = self.queue_listbox.curselection()
        if selected_index:
            task_name = self.queue_listbox.get(selected_index[0])  # Extract the task name

            # Update file content text
            self.file_content_text.config(state=tk.NORMAL)  # Enable editing to update content
            self.file_content_text.delete("1.0", tk.END)
            self.file_content_text.insert("1.0", f"{task_name} Settings")
            self.file_content_text.config(state=tk.DISABLED)  # Disable editing after updating

            # Update log content text
            self.log_content_text.config(state=tk.NORMAL)
            self.log_content_text.delete("1.0", tk.END)
            self.log_content_text.insert("1.0", f"{task_name} Log")
            self.log_content_text.config(state=tk.DISABLED)
        else:
            # Default labels if no task is selected
            self.file_content_text.config(state=tk.NORMAL)
            self.file_content_text.delete("1.0", tk.END)
            self.file_content_text.insert("1.0", "Settings")
            self.file_content_text.config(state=tk.DISABLED)

            self.log_content_text.config(state=tk.NORMAL)
            self.log_content_text.delete("1.0", tk.END)
            self.log_content_text.insert("1.0", "Log")
            self.log_content_text.config(state=tk.DISABLED)

            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.delete("1.0", tk.END)
            self.progress_text.insert("1.0", "Queue Status")
            self.progress_text.config(state=tk.DISABLED)

    def update_queue_numbers(self):
        """Renumber the queue list items after any modification."""
        for index in range(self.queue_listbox.size()):
            item_text = self.queue_listbox.get(index)
            if ". " in item_text:
                item_text = item_text.split(". ", 1)[1]
            # Insert the new number prefix
            new_text = f"{index + 1}. {item_text}"
            self.queue_listbox.delete(index)
            self.queue_listbox.insert(index, new_text)

    # 2. Queue Display and Task Selection Functions
    def on_task_selected(self, _=None):
        """When a task is selected, update the headers and content with the selected task's files."""
        selected_indices = self.queue_listbox.curselection()

        # Determine the currently selected task
        if selected_indices:
            current_selection = selected_indices[0]
        else:
            current_selection = None

        # Check if the selection has changed
        if current_selection == self.previous_selection:
            # Selection hasn't changed; do nothing
            return

        # Update the previous_selection
        self.previous_selection = current_selection

        if selected_indices:
            # Display selected file content, which will also update the log content
            self.display_selected_file_content()
        else:
            # Selection cleared; unload content
            self.clear_content()

    def display_selected_file_content(self):
        """Display content for the selected file and log in the queue list."""
        selected_index = self.queue_listbox.curselection()
        if not selected_index:
            return

        # Extract the selected item's display name
        selected_item = self.queue_listbox.get(selected_index[0])
        try:
            display_name = selected_item.split(". ", 1)[1]
        except IndexError:
            print(f"Selected item '{selected_item}' does not contain '. ' to split.")  # Debugging statement
            display_name = selected_item  # Fallback to full name

        print(f"Display name extracted: {display_name}")  # Debugging statement

        # Construct the file path
        file_name = f"{display_name}"
        file_path = os.path.join(self.queue_dir, file_name)

        try:
            # Read and display the settings content in the file_content_text widget
            with open(file_path, "r") as file:
                content = file.read()
            self.file_content_text.config(state=tk.NORMAL)  # Enable editing temporarily
            self.file_content_text.delete("1.0", tk.END)  # Clear existing content
            # Insert content with the small font tag
            self.file_content_text.insert("1.0", content, "small_font")
            self.file_content_text.config(state=tk.DISABLED)  # Disable editing after inserting content
            print(f"Settings content loaded for '{display_name}'.")  # Debugging statement

            # Ensure log content is updated for the selected file
            self.show_log_content(display_name)  # Update log content here
        except FileNotFoundError:
            print(f"Settings file not found: {file_path}")  # Debugging statement
            self.file_content_text.config(state=tk.NORMAL)
            self.file_content_text.delete("1.0", tk.END)
            self.file_content_text.insert("1.0", "Settings file not found.", "small_font")
            self.file_content_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error reading settings file '{file_path}': {e}")  # Debugging statement

    def clear_content(self):
        """Clear the content in the Text widgets."""
        self.file_content_text.config(state=tk.NORMAL)
        self.file_content_text.delete("1.0", tk.END)
        self.file_content_text.config(state=tk.DISABLED)

        self.log_content_text.config(state=tk.NORMAL)
        self.log_content_text.delete("1.0", tk.END)
        self.log_content_text.config(state=tk.DISABLED)

        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete("1.0", tk.END)
        self.progress_text.config(state=tk.DISABLED)

    def move_up(self):
        """Move the selected task up in the queue."""
        selected_index = self.queue_listbox.curselection()
        if selected_index and selected_index[0] > 0:
            index = selected_index[0]
            item = self.queue_listbox.get(index)
            self.queue_listbox.delete(index)
            self.queue_listbox.insert(index - 1, item)
            self.update_queue_numbers()  # Renumber after moving
            self.queue_listbox.select_set(index - 1)  # Keep the moved item selected

    def move_down(self):
        """Move the selected task down in the queue."""
        selected_index = self.queue_listbox.curselection()
        if selected_index and selected_index[0] < self.queue_listbox.size() - 1:
            index = selected_index[0]
            item = self.queue_listbox.get(index)
            self.queue_listbox.delete(index)
            self.queue_listbox.insert(index + 1, item)
            self.update_queue_numbers()  # Renumber after moving
            self.queue_listbox.select_set(index + 1)  # Keep the moved item selected

    def delete_task_from_queue(self, _=None):
        """Remove selected tasks from the queue display and clear content if no other task is selected."""
        selected_indices = self.queue_listbox.curselection()

        if selected_indices:
            # Delete selected items in reverse order to maintain proper indices
            for index in reversed(selected_indices):
                self.queue_listbox.delete(index)

            # Renumber the queue items to maintain consistent numbering
            self.update_queue_numbers()

            # Check if there is another task selected after deletion
            remaining_size = self.queue_listbox.size()
            if remaining_size > 0:
                # Select the next available item, or the last one if at the end
                new_selection_index = min(selected_indices[0], remaining_size - 1)
                self.queue_listbox.select_set(new_selection_index)
                self.on_task_selected()  # Update content for the newly selected task
            else:
                # If no tasks are left, clear both settings and log content
                self.file_content_text.config(state=tk.NORMAL)
                self.file_content_text.delete("1.0", tk.END)
                self.file_content_text.config(state=tk.DISABLED)

                self.log_content_text.config(state=tk.NORMAL)
                self.log_content_text.delete("1.0", tk.END)
                self.log_content_text.config(state=tk.DISABLED)

            print("Removed selected tasks from queue display.")

    def update_file_order(self):
        """Ensure queue items maintain correct numbering after reordering."""
        for index in range(self.queue_listbox.size()):
            filename = self.queue_listbox.get(index)
            self.queue_listbox.delete(index)
            self.queue_listbox.insert(index, f"{index + 1}. {filename}")

    def enable_text_editing(self, event):
        """Enable editing in the Text widget when it is clicked."""
        widget = event.widget
        widget.config(state=tk.NORMAL)

    def disable_text_editing(self, event):
        """Disable editing in the Text widget when it loses focus."""
        widget = event.widget
        widget.config(state=tk.DISABLED)

    def on_queue_click(self, event):
        """Handle clicks on the queue Listbox to deselect when clicking on empty space."""
        # Get the click coordinates relative to the Listbox
        click_x, click_y = event.x, event.y

        try:
            # Get the index of the item at the clicked position
            index = self.queue_listbox.index(f"@{click_x},{click_y}")
        except tk.TclError:
            # If the Listbox is empty or the click is outside any item, clear selection
            self.queue_listbox.selection_clear(0, tk.END)
            self.previous_selection = None
            self.clear_content()
            return "break"  # Prevent default behavior

        # Retrieve the bounding box of the item at the determined index
        bbox = self.queue_listbox.bbox(index)

        if bbox:
            x, y, width, height = bbox
            # Check if the click is within the item's bounding box
            if y <= click_y < y + height:
                # Click is on an actual item; let the Listbox handle the selection
                return
            else:
                # Click is on empty space below the last item; clear selection
                self.queue_listbox.selection_clear(0, tk.END)
                self.previous_selection = None
                self.clear_content()
                return "break"  # Prevent default behavior
        else:
            # If bbox is None, treat as empty space
            self.queue_listbox.selection_clear(0, tk.END)
            self.previous_selection = None
            self.clear_content()
            return "break"  # Prevent default behavior

    # 3. Task Running and Management Functions
    def run_task_queue(self):
        """Run tasks sequentially from the queue."""
        if self.is_queue_active:
            self.append_to_console("Queue is already running.")
            return

        # Initialize task control
        self.is_queue_active = True
        self.current_task_index = 0  # Track current task index

        # Start running the first task
        self.run_next_task()

    def run_next_task(self):
        """Initiate the next task in the queue."""
        if not self.is_queue_active or self.current_task_index >= self.queue_listbox.size():
            self.is_queue_active = False
            self.append_to_console("All tasks completed.")
            return

        self.is_task_complete = False

        task_text = self.queue_listbox.get(self.current_task_index)
        display_name = task_text.split(". ", 1)[1]
        self.current_task = display_name
        self.current_task_start_time = time.time()

        # Prepare header_info
        task_start_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        task_file_name = self.current_task
        task_file_path = os.path.join(self.queue_dir, self.current_task)
        header_info = f"Task started at: {task_start_time_str}\n" \
                      f"Task name: {task_file_name}\n" \
                      f"Task file path: {task_file_path}\n"

        # Set log file path and start logging
        log_file_path = os.path.join(self.log_dir, f"{self.current_task}.log")
        self.console_output_stream.start_logging(log_file_path, header_info=header_info)

        # Overwrite constants.py with the contents of the task's file
        self.update_constants_file(self.current_task)

        # Wait 3 seconds after updating constants.py before running the script
        self.append_to_console(f"constants.py updated with {self.current_task}. Waiting for 3 seconds.")
        self.after(3000, lambda: self.start_task_script(from_queue=True))

    def start_task_script(self, from_queue=False):
        """Runs the main script after constants.py has been updated and delay has passed."""
        self.update_task_status(self.current_task, "Running")
        self.run_script(from_queue=from_queue)  # Pass from_queue to control save_settings

    def update_task_runtime(self):
        """Display and update the runtime for the current task at regular intervals."""
        if not self.is_queue_active:
            return
        elapsed_time = time.time() - self.current_task_start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        message = f"{self.current_task} - Running - {elapsed_str}\n"

        # Append message to progress_text box
        self.progress_text.config(state='normal')
        self.progress_text.insert(tk.END, message)
        self.progress_text.config(state='disabled')
        self.progress_text.see(tk.END)  # Auto-scroll to the bottom

        # Schedule the next update in 1 second
        self.after(1000, self.update_task_runtime)

    def stop_task_queue(self):
        """Stop the queue and terminate the current task script if active."""
        self.is_queue_active = False
        self.terminate_script()
        print("Queue stopped.")
        self.update_task_status(self.current_task, "Stopped")

    def on_task_completed(self, selected_file):
        """Handle task completion, logging elapsed time and proceeding to the next task if applicable."""
        elapsed_time = time.time() - self.current_task_start_time
        elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

        if self.current_task_start_time is None:
            print("Warning: Task start time was not initialized.")
            return

        # Write elapsed time to the log file
        if self.console_output_stream.is_logging and self.console_output_stream.log_file:
            self.console_output_stream.log_file.write(f"Task completed in: {elapsed_time_str}\n")

        # Stop logging
        self.console_output_stream.stop_logging()

        # Update task status
        self.update_task_status(selected_file, "Completed", elapsed_time)

        # Only update queue list if running from the queue
        if hasattr(self, "current_task_index") and self.is_queue_active:
            # Mark the completed task
            self.queue_listbox.itemconfig(self.current_task_index, {'fg': 'gray'})

            # Move to the next task
            self.current_task_index += 1
            self.append_to_console("Task completed. Starting the next task.")

            # Start the next task
            self.run_next_task()
        else:
            # Handle single run completion
            self.append_to_console("Single task completed.")

    def update_task_status(self, filename, status, elapsed_time=None):
        """Update the status display for a task in the queue."""
        message = f"{filename} - {status}"
        if elapsed_time:
            message += f" - Elapsed Time: {elapsed_time:.2f}s"
        message += "\n"

        # Append message to progress_text box
        self.progress_text.config(state='normal')
        self.progress_text.insert(tk.END, message)
        self.progress_text.config(state='disabled')
        self.progress_text.see(tk.END)  # Auto-scroll to the bottom

    # 4. File Loading and Saving Functions
    def load_queue_files(self, specific_file=None):
        """Load and display the list of tasks in the queue."""
        if specific_file:
            # Only add the specific file to the queue listbox
            index = self.queue_listbox.size()  # Get current size to determine the index for the new item
            display_text = f"{index + 1}. {specific_file}"
            self.queue_listbox.insert(tk.END, display_text)

            # Check if the file has a corresponding completed log file
            log_file_path = os.path.join(self.log_dir, f"{specific_file}.log")
            if os.path.exists(log_file_path):
                # Gray out completed tasks
                self.queue_listbox.itemconfig(index, {'fg': 'gray'})
        else:
            # Clear the listbox and reload all files
            self.queue_listbox.delete(0, tk.END)
            queue_files = sorted(os.listdir(self.queue_dir))

            for index, filename in enumerate(queue_files):
                display_text = f"{index + 1}. {filename}"
                self.queue_listbox.insert(tk.END, display_text)

                # Check if the file has a corresponding completed log file
                log_file_path = os.path.join(self.log_dir, f"{filename}.log")
                if os.path.exists(log_file_path):
                    # Gray out completed tasks
                    self.queue_listbox.itemconfig(index, {'fg': 'gray'})
    def load_selected_file_to_queue(self):
        """Load multiple selected files into the queue from 'Saved Settings' folder."""
        load_paths = filedialog.askopenfilenames(
            initialdir=self.queue_dir,
            title="Select settings files to load into the queue"
        )

        if load_paths:
            try:
                for load_path in load_paths:
                    file_name = os.path.basename(load_path)
                    display_name = os.path.splitext(file_name)[0]

                    queue_file_path = os.path.join(self.queue_dir, file_name)
                    if not os.path.exists(queue_file_path):
                        shutil.copyfile(load_path, queue_file_path)

                    self.queue_listbox.insert(tk.END, f"{self.queue_listbox.size() + 1}. {display_name}")
                    print(f"Loaded {file_name} into the queue.")

                    # Update task content and headers for each newly loaded task
                    self.load_task_content(display_name)

            except Exception as e:
                print(f"Error loading files into the queue: {e}")

    def load_task_content(self, task_name):
        """Load settings and log content for the specified task."""
        # Update the header labels based on the loaded task name
        self.settings_frame.config(text=f"{task_name} Settings")
        self.log_frame.config(text=f"{task_name} Log")

        # Load the settings file content
        settings_path = os.path.join(self.queue_dir, f"{task_name}")
        try:
            with open(settings_path, "r") as settings_file:
                settings_content = settings_file.read()
            self.file_content_text.config(state=tk.NORMAL)
            self.file_content_text.delete("1.0", tk.END)
            self.file_content_text.insert("1.0", settings_content, "small_font")
            self.file_content_text.config(state=tk.DISABLED)
        except FileNotFoundError:
            self.file_content_text.config(state=tk.NORMAL)
            self.file_content_text.delete("1.0", tk.END)
            self.file_content_text.insert("1.0", "Settings file not found.", "small_font")
            self.file_content_text.config(state=tk.DISABLED)

        # Load the log file content
        log_path = os.path.join(self.log_dir, f"{task_name}.log")
        try:
            with open(log_path, "r") as log_file:
                log_content = log_file.read()
            self.log_content_text.config(state=tk.NORMAL)
            self.log_content_text.delete("1.0", tk.END)
            self.log_content_text.insert("1.0", log_content, "small_font")
            self.log_content_text.config(state=tk.DISABLED)
        except FileNotFoundError:
            self.log_content_text.config(state=tk.NORMAL)
            self.log_content_text.delete("1.0", tk.END)
            self.log_content_text.insert("1.0", "Log file not found.", "small_font")
            self.log_content_text.config(state=tk.DISABLED)

    def load_file_to_constants(self, filename):
        """Load settings from a selected file into constants.py."""
        try:
            file_path = os.path.join(self.queue_dir, filename)
            with open(file_path, "r") as file:
                content = file.read()

            # Write contents to constants.py
            with open(self.constants_path, "w") as constants_file:
                constants_file.write(content)
            self.append_to_console(f"Loaded settings from {filename} into constants.py.")
        except Exception as e:
            self.append_to_console(f"Error loading settings: {e}")

    def save_file_changes(self):
        """Save changes made in the Text widgets to the respective files."""
        selected_index = self.queue_listbox.curselection()
        if not selected_index:
            print("No file selected.")
            return

        # Get the selected task name
        task_name = self.queue_listbox.get(selected_index[0]).split(". ", 1)[1]

        # Paths for settings and log files
        settings_path = os.path.join(self.queue_dir, f"{task_name}")
        log_path = os.path.join(self.log_dir, f"{task_name}.log")

        # Save the content of the settings box
        with open(settings_path, "w") as settings_file:
            settings_content = self.file_content_text.get("1.0", tk.END).strip()
            settings_file.write(settings_content)
            print(f"Saved changes to {settings_path}")

        # Save the content of the log box if it's been modified
        if self.log_content_text.cget("state") == tk.NORMAL:  # Only if it was made editable
            with open(log_path, "w") as log_file:
                log_content = self.log_content_text.get("1.0", tk.END).strip()
                log_file.write(log_content)
                print(f"Saved changes to {log_path}")

    def update_constants_file(self, selected_file):
        """Overwrite constants.py with the selected task's settings."""
        try:
            # Load the settings from the queue file into constants.py
            self.load_file_to_constants(selected_file)

            # Verify that constants.py was updated
            with open(self.constants_path, "r") as const_file:
                updated_content = const_file.read()
            if updated_content:
                self.append_to_console("constants.py successfully updated for the next task.")
            else:
                raise ValueError("constants.py is empty after attempted update.")
        except Exception as e:
            self.append_to_console(f"Error updating constants.py for {selected_file}: {e}")
            raise  # Re-raise to prevent running the task if the update fails

    def show_log_content(self, filename):
        """Display the log content for the specified task."""
        log_file_path = os.path.join(self.log_dir, f"{filename}.log")
        print(f"Attempting to load log file: {log_file_path}")  # Debugging statement
        try:
            # Read and display the log content in the log_content_text widget
            with open(log_file_path, "r") as log_file:
                log_content = log_file.read()
            self.log_content_text.config(state=tk.NORMAL)  # Enable editing
            self.log_content_text.delete("1.0", tk.END)  # Clear existing content
            # Insert log content with the small font tag
            self.log_content_text.insert("1.0", log_content, "small_font")
            self.log_content_text.config(state=tk.DISABLED)  # Disable editing
            print(f"Log content loaded successfully for '{filename}'.")  # Debugging statement
        except FileNotFoundError:
            print(f"Log file not found for '{filename}'.")  # Debugging statement
            self.log_content_text.config(state=tk.NORMAL)  # Enable editing
            self.log_content_text.delete("1.0", tk.END)  # Clear existing content
            # Optionally, insert a message indicating the log file is missing
            self.log_content_text.insert("1.0", "Log file not found.", "small_font")
            self.log_content_text.config(state=tk.DISABLED)  # Disable editing
        except Exception as e:
            print(f"Error reading log content for '{filename}': {e}")  # Debugging statement
            self.log_content_text.config(state=tk.NORMAL)  # Enable editing
            self.log_content_text.delete("1.0", tk.END)  # Clear existing content
            self.log_content_text.insert("1.0", f"Error loading log: {e}", "small_font")
            self.log_content_text.config(state=tk.DISABLED)  # Disable editing

    def show_file_content(self, content):
        """Display specific content in the status area, creating a new text widget if necessary."""
        # Ensure status_frame exists before accessing
        if not hasattr(self, 'status_frame'):
            raise AttributeError("status_frame is not defined.")

        # Clear the status_frame by destroying all its child widgets
        for widget in self.status_frame.winfo_children():
            widget.destroy()

        # Create a new text widget to display the content
        text_widget = tk.Text(self.status_frame, wrap=tk.WORD, height=10, width=50)
        text_widget.insert("1.0", content)
        text_widget.pack()

    # endregion

    # region ---- Cygwin Tab ----

    def create_terminal_tab(self):
        """Create the SSH Terminal tab with command history."""
        import threading
        import queue
        import webbrowser

        self.terminal_frame = ttk.Frame(self.terminal_tab)
        self.terminal_frame.pack(fill='both', expand=True)

        # Create a frame at the top for the buttons
        button_frame = ttk.Frame(self.terminal_frame)
        button_frame.pack(pady=10)  # Add vertical padding for better spacing

        # Configure grid to center buttons
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        # Add Disconnect button
        disconnect_button = ttk.Button(
            button_frame, text="Disconnect", command=self.disconnect_ssh_session
        )
        disconnect_button.grid(row=0, column=0, padx=5, pady=5)

        # Add Reconnect button
        reconnect_button = ttk.Button(
            button_frame, text="Reconnect", command=self.reconnect_ssh_session
        )
        reconnect_button.grid(row=0, column=1, padx=5, pady=5)

        # Add Helpful Commands button
        helpful_commands_button = ttk.Button(
            button_frame,
            text="Helpful Commands",
            command=lambda: webbrowser.open('https://www.voxforge.org/home/docs/cygwin-cheat-sheet')
        )
        helpful_commands_button.grid(row=0, column=2, padx=5, pady=5)

        # Frame for terminal output and scrollbar
        terminal_display_frame = ttk.Frame(self.terminal_frame)
        terminal_display_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Text widget to display terminal output
        self.terminal_output = tk.Text(
            terminal_display_frame, wrap='char', state='disabled', bg='black', fg='white',
            insertbackground='white'
        )
        self.terminal_output.pack(side='left', fill='both', expand=True)

        # Scrollbar for terminal output
        terminal_scrollbar = ttk.Scrollbar(terminal_display_frame, orient='vertical', command=self.terminal_output.yview)
        self.terminal_output['yscrollcommand'] = terminal_scrollbar.set
        terminal_scrollbar.pack(side='right', fill='y')

        # Entry widget to send input
        self.terminal_input = tk.Entry(
            self.terminal_frame, bg='black', fg='white', insertbackground='white'
        )
        self.terminal_input.pack(fill='x', padx=5, pady=5)
        self.terminal_input.focus_set()

        # Bind events for input
        self.terminal_input.bind('<Return>', self.send_input_to_ssh)
        # Removed the Tab binding for autocomplete
        self.terminal_input.bind('<Up>', self.navigate_command_history_up)
        self.terminal_input.bind('<Down>', self.navigate_command_history_down)

        # Focus handling
        self.terminal_input.bind('<FocusIn>', self.on_input_focus_in)
        self.terminal_input.bind('<FocusOut>', self.on_input_focus_out)

        # Timer to handle timeout
        self.last_focus_out_time = None
        self.check_timeout()

        # Queue for thread-safe communication
        self.ssh_output_queue = queue.Queue()

        # Initialize command history
        from collections import deque
        self.command_history = deque(maxlen=100)
        self.history_index = None

        # Start SSH connection in a separate thread
        threading.Thread(target=self.start_ssh_session, daemon=True).start()

        # Start updating terminal output
        self.update_terminal_output()

    def start_ssh_session(self):
        """Start the SSH session and read output."""
        import time
        import socket
        import paramiko

        # For legacy SSH servers that choke unless you allow ssh-rsa (SHA1).
        # This mirrors: -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa
        disabled_algorithms = {
            # Server host-key signature algos (HostKeyAlgorithms equivalent)
            "keys": ["rsa-sha2-256", "rsa-sha2-512"],
            # Client public-key auth signature algos (PubkeyAcceptedAlgorithms equivalent)
            # (Doesn't hurt even if you're using password auth; remove if you want.)
            "pubkeys": ["rsa-sha2-256", "rsa-sha2-512"],
        }

        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.load_system_host_keys()  # optional; keeps behavior closer to OpenSSH
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh_client.connect(
                hostname=self.ssh_server,
                port=getattr(self, "ssh_port", 22),
                username=self.ssh_username,
                password=self.ssh_password,
                look_for_keys=False,
                allow_agent=False,
                banner_timeout=200,
                auth_timeout=200,
                timeout=20,  # TCP connect timeout
                disabled_algorithms=disabled_algorithms,
            )

            # Open a pseudo-terminal with appropriate dimensions
            self.ssh_channel = self.ssh_client.invoke_shell(term="xterm", width=80, height=24)
            self.ssh_channel.settimeout(0.0)  # Non-blocking

            while self.ssh_channel and not self.ssh_channel.closed:
                if self.ssh_channel.recv_ready():
                    data = self.ssh_channel.recv(4096).decode("utf-8", errors="ignore")
                    self.ssh_output_queue.put(data)
                if not self.ssh_channel.active:
                    break
                time.sleep(0.1)

        except paramiko.ssh_exception.NoValidConnectionsError as e:
            # This is the classic "Unable to connect to port 22" wrapper.
            # Show underlying per-address socket errors for real diagnostics.
            details = getattr(e, "errors", None)
            self.ssh_output_queue.put(f"SSH connection error: {e}\nDetails: {details}\n")
            self.ssh_channel = None

        except (socket.timeout, TimeoutError) as e:
            self.ssh_output_queue.put(f"SSH connection timeout: {e}\n")
            self.ssh_channel = None

        except paramiko.SSHException as e:
            self.ssh_output_queue.put(f"SSH negotiation/authentication error: {e}\n")
            self.ssh_channel = None

        except Exception as e:
            self.ssh_output_queue.put(f"SSH connection error: {e}\n")
            self.ssh_channel = None

    def clean_ansi_escape_codes(self, text):
        """Remove ANSI escape codes and control characters from the text."""
        import re
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B[@-Z\\-_]|\x1B\[[0-?]*[ -/]*[@-~]')
        text = ansi_escape.sub('', text)
        # Remove control characters (except newline and carriage return)
        control_chars = ''.join(map(chr, list(range(0, 9)) + list(range(11, 32)) + [127]))
        control_char_re = re.compile('[%s]' % re.escape(control_chars))
        return control_char_re.sub('', text)

    def update_terminal_output(self):
        """Update the terminal output from the SSH session."""
        try:
            while True:
                data = self.ssh_output_queue.get_nowait()
                clean_data = self.clean_ansi_escape_codes(data)
                self.append_terminal_output(clean_data)
        except queue.Empty:
            pass
        # Schedule the next check
        self.after(100, self.update_terminal_output)

    def detect_shell_prompt(self, text):
        """Detect if the shell prompt has reappeared."""
        import re
        # Adjust the regex to match your specific prompt format
        # Example: 'tsvick@priestley:~[tsvick@priestley ~]'
        # The prompt may vary, so adjust accordingly
        prompt_regex = r'^[\w-]+@[\w-]+:[\w~/]+[\$#] '  # Modify based on actual prompt
        return re.match(prompt_regex, text.strip()) is not None

    def process_autocomplete_output(self):
        """Process autocomplete output and update Entry widget."""
        lines = self.autocomplete_buffer.strip().split('\n')
        # Remove any empty lines
        lines = [line for line in lines if line.strip()]
        # The last line is the prompt; previous line(s) are autocomplete output
        if len(lines) >= 2:
            autocomplete_lines = lines[:-1]
            if len(autocomplete_lines) == 1:
                # Single completion; update Entry widget
                completed_text = autocomplete_lines[0]
                self.terminal_input.delete(0, tk.END)
                self.terminal_input.insert(0, completed_text)
            else:
                # Multiple possibilities; display them in the terminal output
                self.append_terminal_output('\n'.join(autocomplete_lines) + '\n')
        else:
            # No autocomplete output; perhaps nothing matched
            pass
        # Clear the autocomplete buffer
        self.autocomplete_buffer = ''

    def send_input_to_ssh(self, event=None):
        """Send input from the Entry widget to the SSH session."""
        if self.ssh_channel and self.ssh_channel.active:
            input_data = self.terminal_input.get()
            if input_data.strip():  # Only add non-empty commands
                self.command_history.append(input_data.strip())
            self.history_index = None  # Reset history navigation
            self.ssh_channel.send(input_data + '\n')
            self.terminal_input.delete(0, tk.END)
        else:
            self.append_terminal_output("\nSSH session is not active.\n")

    def on_input_focus_in(self, event):
        """Handle focus in event."""
        self.last_focus_out_time = None

    def on_input_focus_out(self, event):
        """Handle focus out event."""
        self.last_focus_out_time = time.time()

    def check_timeout(self):
        """Check if the input has been deselected for more than 3 minutes."""
        if self.last_focus_out_time:
            elapsed = time.time() - self.last_focus_out_time
            if elapsed >= 180:  # 3 minutes
                self.close_ssh_session()
                return  # Stop checking after closing
        self.after(1000, self.check_timeout)

    def close_ssh_session(self):
        """Close the SSH session."""
        if self.ssh_channel:
            self.ssh_channel.close()
            self.ssh_channel = None
        self.append_terminal_output("\nSSH session closed.\n")

    def load_sensitive_config(self):
        """Load sensitive configuration from sensitive_config.ini"""
        config = configparser.ConfigParser()
        config_path = os.path.join(self.base_path, 'sensitive_config.ini')
        config.read(config_path)

        self.ssh_username = config.get('Sensitive', 'username')
        self.ssh_password = config.get('Sensitive', 'password')
        self.ssh_server = config.get('Sensitive', 'server')

    def disconnect_ssh_session(self):
        """Disconnect the SSH session."""
        self.close_ssh_session()

    def reconnect_ssh_session(self):
        """Reconnect the SSH session."""
        if self.ssh_channel and self.ssh_channel.active:
            self.append_terminal_output("\nSSH session is already active.\n")
            return

        # Clear the terminal output if desired
        self.append_terminal_output("\nReconnecting SSH session...\n")

        # Start SSH connection in a separate thread
        import threading
        threading.Thread(target=self.start_ssh_session, daemon=True).start()

    def append_terminal_output(self, text):
        """Append text to the terminal output safely, excluding prompts."""
        # Check if the text matches the prompt pattern
        if not self.detect_shell_prompt(text):
            self.terminal_output.config(state='normal')
            self.terminal_output.insert(tk.END, text)
            self.terminal_output.see(tk.END)
            self.terminal_output.config(state='disabled')

    def navigate_command_history_up(self, event):
        """Navigate to the previous command in history."""
        if not self.command_history:
            return "break"

        if self.history_index is None:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1

        command = self.command_history[self.history_index]
        self.terminal_input.delete(0, tk.END)
        self.terminal_input.insert(0, command)
        return "break"

    def navigate_command_history_down(self, event):
        """Navigate to the next command in history."""
        if not self.command_history:
            return "break"

        if self.history_index is None:
            return "break"

        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            command = self.command_history[self.history_index]
            self.terminal_input.delete(0, tk.END)
            self.terminal_input.insert(0, command)
        else:
            self.history_index = None
            self.terminal_input.delete(0, tk.END)
        return "break"

    # endregion

    # region ---- Tutorial Tab ----

    def create_tutorial_tab(self):
        """Create the Tutorial tab with the QueueTY icon, ALERT icon, video button, LinkedIn button,
        ALERT group link, and Simpson group link on the left (1/4), and the README.md content on the right (3/4).
        Only the text box is scrollable."""
        import webbrowser
        from PIL import Image, ImageTk
        import tkinter.font as tkFont
        import re  # Import re module for regex operations

        # Create the main container frame
        self.tutorial_frame = ttk.Frame(self.tutorial_tab)
        self.tutorial_frame.pack(fill='both', expand=True)

        # Configure grid layout with 2 columns: left (1/4) and right (3/4)
        self.tutorial_frame.columnconfigure(0, weight=1)  # Left column (1/4)
        self.tutorial_frame.columnconfigure(1, weight=3)  # Right column (3/4)
        self.tutorial_frame.rowconfigure(0, weight=1)

        # Left Frame (1/4 width)
        left_frame = ttk.Frame(self.tutorial_frame, padding=10)
        left_frame.grid(row=0, column=0, sticky='nsew')

        # Load and display the icon.png image in the left frame
        icon_path = os.path.join(self.base_path, 'icon.png')
        alert_icon_path = os.path.join(self.base_path, 'ALERT_icon.png')
        print(f"Icon Path: {icon_path}")  # Debugging statement
        print(f"ALERT Icon Path: {alert_icon_path}")  # Debugging statement

        try:
            # Open and resize the icon.png image
            img = Image.open(icon_path)
            img = img.resize((200, int(200 * img.height / img.width)), Image.LANCZOS)
            self.tutorial_icon_image = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Failed to load icon.png: {e}")
            self.tutorial_icon_image = None

        if self.tutorial_icon_image:
            icon_label = ttk.Label(left_frame, image=self.tutorial_icon_image)
            icon_label.pack(pady=(0, 20))
        else:
            icon_label = ttk.Label(
                left_frame,
                text="Icon Image Not Available",
                foreground="red",
                wraplength=180,
                justify='center'
            )
            icon_label.pack(pady=(0, 20))

        # Load and display the ALERT_icon.png image in the left frame below icon.png
        try:
            alert_img = Image.open(alert_icon_path)
            alert_img = alert_img.resize((200, int(200 * alert_img.height / alert_img.width)), Image.LANCZOS)
            self.alert_icon_image = ImageTk.PhotoImage(alert_img)
        except Exception as e:
            print(f"Failed to load ALERT_icon.png: {e}")
            self.alert_icon_image = None

        if self.alert_icon_image:
            alert_icon_label = ttk.Label(left_frame, image=self.alert_icon_image)
            alert_icon_label.pack(pady=(0, 20))
        else:
            alert_icon_label = ttk.Label(
                left_frame,
                text="ALERT Icon Image Not Available",
                foreground="red",
                wraplength=180,
                justify='center'
            )
            alert_icon_label.pack(pady=(0, 20))

        # Play Video Button
        play_button = ttk.Button(
            left_frame,
            text="Play Tutorial Video",
            command=lambda: webbrowser.open('https://youtu.be/AgEC9rrwIg8')
        )
        play_button.pack(pady=(10, 10))

        # LinkedIn Profile Button
        linkedin_button = ttk.Button(
            left_frame,
            text="My LinkedIn Profile",
            command=lambda: webbrowser.open('https://www.linkedin.com/in/tristan-vick-b76b2b226/')
        )
        linkedin_button.pack(pady=(0, 10))

        # ALERT Group Page Button
        alert_group_button = ttk.Button(
            left_frame,
            text="ALERT Group Website",
            command=lambda: webbrowser.open(
                'https://www.buffalo.edu/renew/research/alert--aga-lab-for-environmental-research-and-testing.html')
        )
        alert_group_button.pack(pady=(0, 10))

        # Simpson Group Page Button
        simpson_group_button = ttk.Button(
            left_frame,
            text="Simpson Group Website",
            command=lambda: webbrowser.open('https://sites.google.com/view/simpson-research/home?authuser=0')
        )
        simpson_group_button.pack(pady=(0, 10))

        # Right Frame (3/4 width)
        right_frame = ttk.Frame(self.tutorial_frame, padding=10)
        right_frame.grid(row=0, column=1, sticky='nsew')

        # Ensure the right_frame expands to fill available space
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        # Read the contents of README.md
        readme_path = os.path.join(self.base_path, 'README.md')
        print(f"README Path: {readme_path}")  # Debugging statement
        try:
            with open(readme_path, 'r', encoding='utf-8') as file:
                readme_content = file.read()
        except Exception as e:
            readme_content = "README.md not found or could not be read."
            print(f"Failed to read README.md: {e}")  # Debugging statement

        # Remove image links from the Markdown content
        # This regex matches Markdown image syntax ![Alt Text](image_path)
        readme_content = re.sub(r'!\[.*?\]\(.*?\)', '', readme_content)

        # Optionally, you can convert Markdown to plain text
        # For a simple approach, remove other Markdown syntax like headers and formatting
        readme_content = re.sub(r'#+ ', '', readme_content)  # Remove Markdown headers
        readme_content = re.sub(r'\*\*(.*?)\*\*', r'\1', readme_content)  # Bold text
        readme_content = re.sub(r'\*(.*?)\*', r'\1', readme_content)  # Italic text
        readme_content = re.sub(r'`(.*?)`', r'\1', readme_content)  # Inline code
        readme_content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', readme_content)  # Links

        # Define a font for the README text
        try:
            small_font = tkFont.Font(family="Helvetica", size=10)
        except:
            small_font = ("Helvetica", 10)

        # Create a Frame for the text widget and scrollbar
        text_frame = ttk.Frame(right_frame)
        text_frame.pack(fill='both', expand=True)

        # Create the Text widget and Scrollbar
        readme_text = tk.Text(
            text_frame,
            wrap='word',
            font=small_font,
            borderwidth=1,
            relief="solid",
            bg=self.cget('bg'),  # Match the background color to ttk.Frame
            fg='black'
        )
        readme_text.insert('1.0', readme_content)
        readme_text.configure(state='disabled')  # Make it read-only
        readme_text.pack(side='left', fill='both', expand=True)

        # Add scrollbar to the text widget
        text_scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=readme_text.yview)
        text_scrollbar.pack(side='right', fill='y')
        readme_text.configure(yscrollcommand=text_scrollbar.set)

    # endregion

    # region ---- General Functions ----
    def save_to_queue(self):
        """Save current settings to a text file in the 'Saved Settings' folder with the name from the text box."""
        self.save_settings()
        queue_name = self.text_box.get().strip()

        if not queue_name:
            print("Please enter a valid name in the text box.")
            return

        queue_file_path = os.path.join(self.queue_dir, queue_name)

        try:
            shutil.copyfile(self.constants_path, queue_file_path)
            print(f"Saved constants.py to {queue_file_path}")
            self.load_queue_files(queue_name)  # Add only the new file to the display
        except Exception as e:
            print(f"Failed to save to queue: {e}")

    def load_default_settings(self):
        self.load_settings(self.default_settings_path if getattr(sys, 'frozen', False) else "default_settings.txt")
        # Reload the VConf settings tab to show the updated paths
        self.reload_vconf_settings()

    def save_default_settings(self):
        """Save current settings as default settings, including sensitive settings."""
        self.save_to_file(self.default_settings_path if getattr(sys, 'frozen', False) else "default_settings.txt")
        self.save_sensitive_settings()

    def load_sensitive_settings(self):
        """Load sensitive settings from 'sensitive_config.ini' and update placeholders in constants."""
        config = configparser.ConfigParser()
        sensitive_config_file = os.path.join(self.base_path, 'sensitive_config.ini')

        if os.path.exists(sensitive_config_file):
            config.read(sensitive_config_file)
            if 'Sensitive' in config:
                for key in ['server', 'username', 'password', 'remote_directory', 'remote_file_path']:
                    if key in config['Sensitive']:
                        value = config['Sensitive'][key]
                        if getattr(const, key) == "PLACEHOLDER":  # Replace only if placeholder
                            setattr(const, key, self.convert_value(value))  # Updated code
                        if key in self.editable_vars:
                            if isinstance(self.editable_vars[key], tk.Entry):
                                self.editable_vars[key].delete(0, tk.END)
                                self.editable_vars[key].insert(0, value)
                            elif isinstance(self.editable_vars[key], tk.BooleanVar):
                                self.editable_vars[key].set(value == 'True')
                # Update dependent variables if necessary
                const.remote_temp_dir = f"{const.remote_directory}/{const.temp_dir}"

    def save_sensitive_settings(self):
        """Save sensitive settings to 'sensitive_config.ini'."""
        config = configparser.ConfigParser()
        config['Sensitive'] = {}
        for key in ['server', 'username', 'password', 'remote_directory', 'remote_file_path']:
            if key in self.editable_vars:
                if isinstance(self.editable_vars[key], tk.Entry):
                    value = self.editable_vars[key].get()
                elif isinstance(self.editable_vars[key], tk.BooleanVar):
                    value = self.editable_vars[key].get()
                else:
                    value = ''
                config['Sensitive'][key] = value
                setattr(const, key, value)
        sensitive_config_file = os.path.join(self.base_path, 'sensitive_config.ini')
        with open(sensitive_config_file, 'w') as configfile:
            config.write(configfile)

    def save_settings(self):
        print("Saving settings...")

        sensitive_keys = ['server', 'username', 'password', 'remote_directory', 'remote_file_path']

        # Update the script toggle variables
        for toggle in self.script_toggle_vars:
            if toggle not in sensitive_keys:
                setattr(const, toggle, self.script_toggle_vars[toggle].get())

        # Update gzip_and_unzip_script separately
        if 'gzip_and_unzip_script' not in sensitive_keys:
            const.gzip_and_unzip_script = self.gzip_and_unzip_var.get()

        # Update the sub variables
        for sub_var, widget in self.editable_vars.items():
            if sub_var in sensitive_keys:
                continue  # Skip sensitive variables

            if isinstance(widget, tk.BooleanVar):
                value = widget.get()  # Already a boolean
            elif isinstance(widget, ttk.Entry):
                value = widget.get()
                # Handle integer values
                if value.isdigit():
                    value = int(value)  # Convert to integer
                elif value.lower() in ["true", "false"]:
                    value = value.lower() == "true"  # Convert to boolean
                else:
                    pass  # Keep as string
            else:
                value = widget.get()  # Keep as string

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

        # Save to constants_last_path
        self.save_to_constants_last()

        # After saving, update constants.py with the loaded values
        self.save_to_constants()

        # Save sensitive settings separately
        self.save_sensitive_settings()

        # Attempt to reconnect to the server with the new credentials
        self.connect_to_server()

    def run_script(self, from_queue=False):
        """Run the main script with optional setting save, skipping save if from queue."""
        if not from_queue:  # Only save settings if not from the queue
            self.save_settings()
        self.current_task_start_time = time.time()

        # Reset termination trigger before running the script
        termination.termination_trigger = False

        # Clear console
        self.console_text.config(state='normal')
        self.console_text.delete('1.0', tk.END)
        self.console_text.config(state='disabled')

        # Execute script in a new thread
        self.script_process = threading.Thread(target=self.execute_script, daemon=True)
        self.script_process.start()

    def execute_script(self):
        """Execute the main script, capturing stdout and stderr, and handle any warnings."""

        def handle_warnings(message, _category, filename, lineno, _file=None, _line=None):
            self.append_to_console(f"Warning: {message} in {filename}, line {lineno}")

        # Capture warnings
        warnings.showwarning = handle_warnings

        try:
            if getattr(sys, 'frozen', False):
                main_path = os.path.join(sys._MEIPASS, 'main.py')
                with open(main_path, 'r') as f:
                    code = f.read()
                    exec(code, {'__name__': '__main__'})
            else:
                script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
                self.append_to_console(f"Executing script: {script_path}")

                # Run subprocess and capture output
                self.script_process = subprocess.Popen(
                    ["python", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Combine stdout and stderr
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                self.main_pid = self.script_process.pid
                self.append_to_console(f"Started process with PID: {self.main_pid}")

                # Thread to capture combined output
                output_thread = threading.Thread(target=self.capture_output, args=(self.script_process.stdout,))
                output_thread.start()

                # Start monitoring for vconf.exe
                # self.after(1000, self.check_for_vconf_process)

                # Wait for output to complete
                output_thread.join()
                self.script_process.wait()

                self.append_to_console("Script execution completed.")

        except Exception as exec_exception:
            self.append_to_console(f"An error occurred: {exec_exception}")

    @staticmethod
    def create_tooltip(widget, text):
        tool_tip = ToolTip(widget)

        def enter(_event):
            tool_tip.showtip(text)

        def leave(_event):
            tool_tip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def terminate_script(self):
        self.append_to_console("Attempting to terminate the script process...")

        # Terminate the subprocess, not the thread
        if self.script_process and self.script_process.poll() is None:
            try:
                self.script_process.terminate()
                self.script_process.wait(timeout=5)  # Wait up to 5 seconds for the process to terminate
                self.append_to_console("Successfully terminated the script process.")
            except subprocess.TimeoutExpired:
                self.script_process.kill()
                self.append_to_console("Forcefully killed the script process.")
            except Exception as e:
                self.append_to_console(f"Failed to terminate the script process: {e}")
        else:
            self.append_to_console("No running script process found to terminate.")

        # Set the termination trigger
        termination.termination_trigger = True

        # Additional logic to terminate any other Python processes if needed
        current_pid = os.getpid()
        self.append_to_console(f"Current process ID: {current_pid}")

        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
                if proc_info['pid'] != current_pid and 'python' in proc_info['name'].lower():
                    if getattr(sys, 'frozen', False):
                        if 'main' in ' '.join(proc_info.get('cmdline', [])):
                            self.terminate_process(proc)
                    else:
                        self.terminate_process(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Handle cases where the process has ended or access is denied
                continue

        # Terminate any VCONF processes if needed
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
                if 'vconf' in proc_info['name'].lower() or (
                        'vconf' in ' '.join(proc_info.get('cmdline', [])).lower() if proc_info.get(
                            'cmdline') else False):
                    self.terminate_process(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Handle cases where the process has ended or access is denied
                continue

        self.append_to_console("Script termination process completed.")

    def terminate_process(self, proc):
        """Helper function to terminate a process with error handling."""
        try:
            proc.terminate()
            proc.wait(timeout=5)  # Wait up to 5 seconds for the process to terminate
            self.append_to_console(f"Terminated process: {proc.info['pid']}")
        except psutil.NoSuchProcess:
            self.append_to_console(f"Process {proc.info['pid']} does not exist")
        except psutil.TimeoutExpired:
            proc.kill()  # Forcefully kill if terminate times out
            self.append_to_console(f"Forcefully killed process {proc.info['pid']}")
        except Exception as e:
            self.append_to_console(f"Failed to terminate process {proc.info['pid']}: {e}")

    def save_to_constants(self):
        self.save_to_python_file(self.constants_path if getattr(sys, 'frozen', False) else "constants.py")

    def save_to_constants_last(self):
        self.save_to_file(self.constants_last_path if getattr(sys, 'frozen', False) else "constants_last.txt")

    def save_to_file(self, filename):
        if not os.path.exists(filename) and not getattr(sys, 'frozen', False):
            print(f"File {filename} does not exist. Skipping save operation.")
            return

        sensitive_keys = ['server', 'username', 'password', 'remote_directory', 'remote_file_path']

        try:
            with open(filename, "w") as file:
                # Save script toggle variables, excluding sensitive ones
                for key, value in self.script_toggle_vars.items():
                    if key in sensitive_keys:
                        continue  # Skip sensitive variables
                    file.write(f"{key}={value.get()}\n")

                # Save editable variables, excluding sensitive ones
                for key, entry in self.editable_vars.items():
                    if key in sensitive_keys:
                        continue  # Skip sensitive variables

                    # Explicitly check if the key is one of the integer-storing fields
                    if key in ["geometry_optimize_lowest_energy_structures", "max_conformers"]:
                        file.write(f"{key}={self.format_value(int(entry.get()))}\n")  # Convert to int and format
                    elif isinstance(entry, tk.BooleanVar):
                        file.write(f"{key}={self.format_value(entry.get())}\n")  # Pass boolean to format_value
                    else:
                        file.write(f"{key}={self.format_value(entry.get())}\n")  # Pass string value to format_value

                # Save VConf settings
                for key, value in const_2.default_vconf_settings.items():
                    file.write(f"default_vconf_settings_{key}={self.format_value(value)}\n")
                for key, value in const_2.experimental_vconf_settings.items():
                    file.write(f"experimental_vconf_settings_{key}={self.format_value(value)}\n")

                # Save script contents
                for script_path, text_widget in self.script_texts.items():
                    content = text_widget.get("1.0", tk.END).strip()
                    content = content.replace('\n', '\\n')
                    file.write(f"{os.path.basename(script_path).replace('.', '_')}_content={content}\n")

                # Save gzip_and_unzip_script separately
                file.write(f"gzip_and_unzip_script={self.format_value(self.gzip_and_unzip_var.get())}\n")

            print(f"Settings saved to {filename}")  # Debug statement
        except Exception as e:
            print(f"Failed to save settings to {filename}: {e}")

    def save_to_python_file(self, filename):
        if not os.path.exists(filename) and not getattr(sys, 'frozen', False):
            print(f"File {filename} does not exist. Skipping save operation.")
            return

        try:
            with open(filename, "w") as file:
                file.write('"""\nAuto-generated constants file from GUI settings.\n"""\n\n')
                file.write("import gui as gui_prop\n\n")

                # Write variables to the file
                for section, variables in sections.items():
                    file.write(f"# {section}\n")
                    for attr in variables:
                        if attr in ['server', 'username', 'password', 'remote_directory', 'remote_file_path']:
                            continue  # Skip sensitive variables
                        value = getattr(const, attr, None)
                        if value is not None:
                            # Special handling for max_conformers and geometry_optimize_lowest_energy_structures
                            if attr in ["max_conformers", "geometry_optimize_lowest_energy_structures"]:
                                formatted_value = self.format_value(str(value))  # Convert these to strings
                            elif isinstance(value, str) and '\\' in value:
                                # Add 'r' prefix for strings with backslashes (for paths)
                                formatted_value = f'r"{value}"'
                            else:
                                formatted_value = self.format_value(value)
                            file.write(f"{attr} = {formatted_value}\n")
                    file.write("\n")

                # Save VConf settings
                file.write("# Default VConf Settings\n")
                file.write("default_vconf_settings = {\n")
                for key in vconf_variables:
                    value = const_2.default_vconf_settings.get(key, None)
                    formatted_value = self.format_vconf_value(value)
                    file.write(f"    '{key}': {formatted_value}, \n")
                file.write("}\n\n")

                file.write("# Experimental VConf Settings\n")
                file.write("experimental_vconf_settings = {\n")
                for key in vconf_variables:
                    value = const_2.experimental_vconf_settings.get(key, None)
                    formatted_value = self.format_vconf_value(value)
                    file.write(f"    '{key}': {formatted_value}, \n")
                file.write("}\n\n")

                # Save script contents with newline handling
                for script_path, text_widget in self.script_texts.items():
                    script_name = os.path.basename(script_path).replace('.', '_')
                    content = text_widget.get("1.0", tk.END).strip()
                    content = content.replace('"""', '\\"\\"\\"')
                    content = content.replace('\n', '\\n')
                    file.write(f'{script_name}_content = """{content}"""\n')

                file.write(dependencies_text.strip() + "\n")

            print(f"Settings saved to {filename}")
        except Exception as e:
            print(f"Failed to save settings to {filename}: {e}")

    @staticmethod
    def strip_quotes(value):
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value.startswith('fr"') and value.endswith('"'):
            return value[3:-1]
        return value

    @staticmethod
    def convert_value(value):
        if value.isdigit():
            return int(value)
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.lower() == "none":
            return None
        return value

    def load_settings(self, settings_file):
        current_script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script

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
                if key in ['server', 'username', 'password', 'remote_directory', 'remote_file_path']:
                    continue  # Skip sensitive variables
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
                    # Use convert_value to ensure correct type assignment
                    setattr(const, key, self.convert_value(value))
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
                    script_path = os.path.join(current_script_dir,
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

        # Load Sensitive Settings
        self.load_sensitive_settings()

    def save_remote_directory(self, _event=None):
        remote_directory = self.editable_vars["remote_directory"].get().rstrip('/')
        self.editable_vars["remote_directory"].delete(0, tk.END)
        self.editable_vars["remote_directory"].insert(0, remote_directory)
        self.save_to_constants_last()

    def handle_window_closing(self):
        self.save_to_constants_last()
        if hasattr(self, 'process') and self.script_process and self.script_process.poll() is None:
            try:
                self.script_process.terminate()
                self.script_process.wait(timeout=5)
                self.append_to_console("Successfully terminated the script process.")
            except subprocess.TimeoutExpired:
                self.script_process.kill()
                self.append_to_console("Forcefully killed the script process.")
            except Exception as e:
                self.append_to_console(f"Failed to terminate the script process: {e}")
        self.destroy()

    @staticmethod
    def load_file_content(filepath, text_widget):
        try:
            with open(filepath, "r") as file:
                content = file.read()
                text_widget.delete("1.0", tk.END)
                text_widget.insert(tk.END, content)
                print(f"Loaded content from {filepath}")  # Debug statement
        except Exception as e:
            print(f"Failed to load content from {filepath}: {e}")  # Debug statement

    # endregion

    # region ---- Server Connection Functions ----

    def connect_to_server(self):
        """Connect to the remote server using SSH with the provided credentials."""
        server = const.server
        username = const.username
        password = const.password

        if not server or not username or not password:
            self.append_to_console("Server credentials are missing. Please enter them in the settings.")
            return

        try:
            self.ssh_client.connect(server, username=username, password=password)
            self.ssh_connected = True
            self.append_to_console("Connected to the server successfully.")
        except Exception as e:
            self.ssh_connected = False
            self.append_to_console(f"Failed to connect to server: {e}")

    def browse_file(self, var_name):
        file_path = filedialog.askopenfilename(initialdir="/", title="Select File",
                                               filetypes=[("Executables", "*.exe")],
                                               parent=self)  # Set parent to self
        if file_path:
            file_path = file_path.replace('/', '\\')
            self.editable_vars[var_name].delete(0, tk.END)
            self.editable_vars[var_name].insert(0, file_path)

    def remote_directory_dialog(self, initial_dir, browse_files=False):
        current_dir = initial_dir
        selected = None

        def refresh_listbox():
            nonlocal current_dir
            stdin, stdout, stderr = self.ssh_client.exec_command(f'ls -p {current_dir}')
            dir_list = stdout.read().decode().splitlines()
            dir_listbox.delete(0, tk.END)
            dir_listbox.insert(0, '..')
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
            except tk.TclError as e:
                print(f"Selection error: {e}")
                selected = current_dir
            dialog.destroy()

        dialog = tk.Toplevel(self)
        dialog.title("Remote Directory Browser")

        # Position the dialog relative to the main window
        main_x = self.winfo_rootx()
        main_y = self.winfo_rooty()
        dialog.geometry(f"+{main_x + 50}+{main_y + 50}")

        current_dir_label = tk.Label(dialog, text=f"Current directory: {current_dir}", font=("TkDefaultFont", 12))
        current_dir_label.pack(side="top", fill="x", pady=5)

        dir_frame = ttk.Frame(dialog)
        dir_frame.pack(fill="both", expand=True, padx=10, pady=10)

        dir_listbox = tk.Listbox(dir_frame)
        dir_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(dir_frame, orient="vertical", command=dir_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        dir_listbox.config(yscrollcommand=scrollbar.set)

        refresh_listbox()

        dir_listbox.bind("<Double-Button-1>", lambda _event: go_into_folder())
        dir_listbox.bind("<Return>", lambda _event: go_into_folder())

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side="bottom", fill="x", pady=5)

        into_button = ttk.Button(button_frame, text="Go Into Folder", command=go_into_folder)
        into_button.pack(side="left", padx=5)

        up_button = ttk.Button(button_frame, text="Go Up Folder", command=go_up_folder)
        up_button.pack(side="left", padx=5)

        select_button = ttk.Button(button_frame, text="Select Folder", command=select_folder)
        select_button.pack(side="right", padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: dialog.destroy())
        cancel_button.pack(side="right", padx=5)

        # Update the dialog size after adding all widgets
        dialog.update_idletasks()
        width = dialog.winfo_reqwidth()
        height = dialog.winfo_reqheight()
        dialog.minsize(width, height)

        self.wait_window(dialog)

        return selected

    # def on_mouse_wheel_script_settings(self, event):
    #     current_tab = self.tabs.select()
    #     if current_tab == str(self.vconf_settings_tab):
    #         self.vconf_settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # endregion


def run_main_gui():
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    if getattr(sys, 'frozen', False):
        # Running in a bundle
        base_path = os.path.join(sys._MEIPASS)  # noqa: Access to protected member _MEIPASS is necessary for PyInstaller
        splash_img_path = os.path.join(base_path, 'icon.png')
    else:
        # Running in normal Python environment
        splash_img_path = 'icon.png'

    SplashScreen.show_splash_screen(root, splash_img_path)

    root.after(3000, lambda: [root.destroy(), run_main_gui()])

    root.mainloop()
