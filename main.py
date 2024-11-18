import os
import sys
import time
import threading
from pynput import mouse
from constants import (
    clean_up_molecule_list_script,
    generate_conformers_using_vconf_script,
    prepare_TMoleX_files_script,
    submit_TMoleX_files_to_cluster_script,
    check_cluster_queue_script,
    gzip_and_unzip_script,
    grab_files_from_cluster_script,
    write_new_inp_file_script,
    check_remote_directory_script
)

# Import termination trigger
import termination

def check_termination():
    return termination.termination_trigger

print(3)
time.sleep(0.5)
print(2)
time.sleep(0.5)
print(1)
time.sleep(0.5)
print("Launching QueueTY!\n")
time.sleep(1)

# Get the base path for the scripts
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    print(fr"{base_path} for EXE")
else:
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    print(fr"{base_path} for PYTHON")

terminate_file_path = os.path.join(base_path, 'terminate.txt')

# Define the script paths and activation flags
scripts = [
    ("gzip_and_unzip.py", gzip_and_unzip_script),
    ("check_remote_directory.py", check_remote_directory_script),
    ("clean_up_molecule_list.py", clean_up_molecule_list_script),
    ("generate_conformers_vconf.py", generate_conformers_using_vconf_script),
    ("cmdline_TMoleX_process.py", prepare_TMoleX_files_script),
    ("submit_remote_jobs_to_cluster.py", submit_TMoleX_files_to_cluster_script),
    ("check_cluster_queue.py", check_cluster_queue_script),
    ("grab_files_from_cluster.py", grab_files_from_cluster_script),
    ("write_new_inp_file.py", write_new_inp_file_script)
]

# Flag to control the kill-switch
terminate_script = False

# Store running processes to ensure they are terminated properly
running_processes = []

def on_click(x, y, button, pressed):
    global terminate_script
    if button == mouse.Button.middle and pressed:
        terminate_script = True
        termination.termination_trigger = True
        return False  # Stop listener and terminate the script

def run_script(script_name, is_active):
    global terminate_script
    if terminate_script or check_termination():
        print(f"\nExecution of {script_name} was terminated.\n")
        sys.stdout.flush()  # Ensure the message is flushed to stdout immediately
        return False

    if not is_active:
        print(f"\n{script_name} is disabled\n")
        sys.stdout.flush()  # Ensure the message is flushed to stdout immediately
        return True

    script_path = os.path.join(base_path, script_name)
    print(f"Running script: {script_path}")  # Debug statement
    try:
        with open(script_path, 'r') as script_file:
            script_content = script_file.read()

        # Execute the script content
        exec(script_content, globals())

        print(r"////////////////////////////////////")
        sys.stdout.flush()  # Ensure the message is flushed to stdout immediately
        print(f"{script_name} passed!")
        sys.stdout.flush()  # Ensure the message is flushed to stdout immediately
        print(r"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"f"\n\n\n")
        sys.stdout.flush()  # Ensure the message is flushed to stdout immediately
        time.sleep(2)
        return True
    except Exception as e:
        print(f"\nError occurred while running {script_name}: {e}\n")
        sys.stdout.flush()  # Ensure the message is flushed to stdout immediately
        return False

def monitor_mouse():
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

def main():
    global terminate_script

    # Start the mouse listener in a separate thread
    listener_thread = threading.Thread(target=monitor_mouse)
    listener_thread.start()

    try:
        for script, is_active in scripts:
            print(f"Processing script: {script}, Active: {is_active}")  # Debug statement
            if not run_script(script, is_active) or terminate_script or check_termination():
                print("\nMaster script terminated early.\n")
                sys.stdout.flush()  # Ensure the message is flushed to stdout immediately
                break

        if not terminate_script:
            print("\nAll active scripts passed!\n")
            sys.stdout.flush()  # Ensure the message is flushed to stdout immediately

    finally:
        terminate_script = True  # Ensure the script terminates
        listener_thread.join()  # Ensure the listener thread is properly joined
        termination.termination_trigger = False  # Reset termination trigger
        # Explicitly terminate the script in the same way as the middle mouse button click
        os._exit(0)

if __name__ == "__main__":
    main()
