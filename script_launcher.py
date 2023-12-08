import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import os
import json
from datetime import datetime
import getpass
import socket
import threading

def save_session():
    session_data = {
        "script_files": script_files_text.get("1.0", "end-1c"),
        "target_dirs": target_dirs_text.get("1.0", "end-1c"),
        "script_dirs": script_dirs_text.get("1.0", "end-1c")
    }
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'w') as file:
            json.dump(session_data, file, indent=4)

def load_session():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            session_data = json.load(file)
            script_files_text.delete("1.0", "end")
            script_files_text.insert("1.0", session_data["script_files"])
            target_dirs_text.delete("1.0", "end")
            target_dirs_text.insert("1.0", session_data["target_dirs"])
            script_dirs_text.delete("1.0", "end")
            script_dirs_text.insert("1.0", session_data["script_dirs"])

def load_target_directories():
    # Open a directory selection dialog
    folder_path = filedialog.askdirectory()
    if folder_path:
        # List all subdirectories in the selected folder
        subdirs = [os.path.join(folder_path, d) for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]

        # Clear the existing text and add the new directories
        target_dirs_text.delete("1.0", "end")
        for subdir in subdirs:
            target_dirs_text.insert("end", subdir + "\n")

def update_log_display(log_filename, text_widget, last_position=[0]):
    try:
        with open(log_filename, "r") as log_file:
            # Move to the last read position
            log_file.seek(last_position[0])

            # Read new content from the file
            new_content = log_file.read()

            # Update the display if there is new content
            if new_content:
                text_widget.insert(tk.END, new_content)
                text_widget.see(tk.END)

            # Update the last read position
            last_position[0] = log_file.tell()

    except Exception as e:
        text_widget.insert(tk.END, f"Error reading log file: {e}\n")

    # Schedule the next update
    text_widget.after(1000, update_log_display, log_filename, text_widget, last_position)

def launch_scripts():
    # Open a log file
    log_filename = f"script_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_filename, "w") as log_file:
        log_file.write(f"Log created on: {datetime.now()}\n")
        log_file.write(f"User: {getpass.getuser()}\n")
        log_file.write(f"Host: {socket.gethostname()}\n\n")

    # Launch scripts in a separate thread
    threading.Thread(target=launch_scripts_thread, args=(log_filename,)).start()

    # Start updating the log display
    update_log_display(log_filename, log_display_text)
def launch_scripts_thread(log_filename):
    with open(log_filename, "a") as log_file:
        # Gather script information from text fields
        script_files = script_files_text.get("1.0", "end-1c").splitlines()
        target_dirs = target_dirs_text.get("1.0", "end-1c").splitlines()
        script_dirs = script_dirs_text.get("1.0", "end-1c").splitlines()

        for dir_path in target_dirs:
            for script in script_files:
                for script_dir in script_dirs:
                    script_path = os.path.join(script_dir, script)
                    if os.path.exists(script_path):
                        start_time = datetime.now()
                        try:
                            # Determine the command based on the file extension
                            if script.endswith('.py'):
                                command = ['python', script_path]
                            elif script.endswith('.pl'):
                                command = ['perl', script_path]
                            elif script.endswith('.bat'):
                                command = [script_path]
                            else:
                                # Default for executable scripts or other extensions
                                command = [script_path]

                            # Run the script
                            process = subprocess.Popen(
                                command, cwd=dir_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                            output, errors = process.communicate()
                            end_time = datetime.now()

                            log_file.write(f"Script: {script}\nDirectory: {dir_path}\n")
                            log_file.write(f"Start Time: {start_time}\n")
                            log_file.write("Output:\n")
                            log_file.write(output.decode() + "\n")
                            if errors:
                                log_file.write("Errors:\n")
                                log_file.write(errors.decode() + "\n")
                            log_file.write(f"End Time: {end_time}\n")
                            log_file.write(f"Status: {'Success' if process.returncode == 0 else 'Failed'}\n")
                            log_file.write("-" * 40 + "\n")

                        except Exception as e:
                            end_time = datetime.now()
                            log_file.write(f"Failed to run script: {script} at {start_time}\n")
                            log_file.write(f"Error: {str(e)}\n")
                            log_file.write(f"End Time: {end_time}\n")
                            log_file.write("-" * 40 + "\n")


# Create the main window
root = tk.Tk()
root.title("Script Launcher")

# Configure grid layout for resizing
for i in range(9):  # Assuming you have 9 rows
    root.grid_rowconfigure(i, weight=1)
root.grid_columnconfigure(0, weight=1)  # Assuming a single column layout

# Create a menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Add 'File' menu
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
# Modify the File menu in the menu bar to include the new function
file_menu.add_command(label="Load Target Directories From Folder", command=load_target_directories)
file_menu.add_command(label="Load JSON Session", command=load_session)
file_menu.add_command(label="Save Session", command=save_session)

# Add separator and Exit option in the File menu
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.destroy)

# Ctrl+O = load_session()
root.bind('<Control-o>', lambda event: load_session())

# Ctrl+Enter = launch_scripts()
root.bind('<Control-Return>', lambda event: launch_scripts())

# Configure grid layout for resizing
# Set weight to 0 for label rows and 1 for text box rows
root.grid_rowconfigure(0, weight=0)  # Label row
root.grid_rowconfigure(1, weight=1)  # Text box row
root.grid_rowconfigure(2, weight=0)  # Label row
root.grid_rowconfigure(3, weight=1)  # Text box row
root.grid_rowconfigure(4, weight=0)  # Label row
root.grid_rowconfigure(5, weight=1)  # Text box row
root.grid_rowconfigure(6, weight=0)  # Button row
root.grid_rowconfigure(7, weight=0)  # Label row
root.grid_rowconfigure(8, weight=1)  # ScrolledText row
root.grid_columnconfigure(0, weight=1)

# Modify the placement and configuration of text widgets and labels
# Adjust 'sticky' for labels to prevent stretching
label1 = tk.Label(root, text="Enter script filenames (one per line):")
label1.grid(row=0, column=0, sticky="w")

script_files_text = tk.Text(root, height=5)
script_files_text.grid(row=1, column=0, sticky="nsew")

label2 = tk.Label(root, text="Enter target directories (one per line):")
label2.grid(row=2, column=0, sticky="ew")

target_dirs_text = tk.Text(root, height=5)
target_dirs_text.grid(row=3, column=0, sticky="nsew")

label3 = tk.Label(root, text="Enter script directories (one per line):")
label3.grid(row=4, column=0, sticky="ew")

script_dirs_text = tk.Text(root, height=5)
script_dirs_text.grid(row=5, column=0, sticky="nsew")

# Create and place the launch button
launch_button = tk.Button(root, text="Launch", command=launch_scripts)
launch_button.grid(row=6, column=0, sticky="nsew")

# Create and place a log display
log_display_label = tk.Label(root, text="Log Output:")
log_display_label.grid(row=7, column=0, sticky="nw")

log_display_text = scrolledtext.ScrolledText(root, height=10, width=50)
# Ensure scrolled text box expands in all directions
log_display_text.grid(row=8, column=0, sticky="nsew")

# Start the Tkinter event loop
root.mainloop()