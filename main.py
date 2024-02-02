"""DDLC Mod Installer"""
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, scrolledtext
import os
import zipfile
import shutil
import winreg
import errno
import subprocess

LEFT_PADDING = 10
def calculate_directory_size(path):
    """Calculate the total size of all files in the directory."""
    total_size = 0
    for root, dirs, files in os.walk(path):
        total_size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
    return total_size

def delete_directory_with_progress(path, total_size, deleted_size=None):
    """Delete a directory and its contents, updating the progress bar."""
    if deleted_size is None:
        deleted_size=[0]
    if not os.path.exists(path):
        return

    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            file_size = os.path.getsize(file_path)
            os.remove(file_path)
            deleted_size[0] += file_size
            progress_bar['value'] = (deleted_size[0] / total_size) * 100
            app.update_idletasks()

        for name in dirs:
            os.rmdir(os.path.join(root, name))

    os.rmdir(path)  # Finally, remove the root directory itself
    progress_bar['value'] = 100  # Ensure it reaches 100% at the end
    app.update_idletasks()

def delete_ddlc():
    "Delete the DDLC Folder for a Clean Install"
    game_path = game_path_entry.get().strip()

    # Check if the path is empty
    if not game_path:
        messagebox.showerror("Error", "Game directory is empty. Please specify a valid path.")
        return

    # Safeguard checks to ensure the directory is indeed for DDLC
    valid_names = ["Doki Doki Literature Club"]
    if not any(name in game_path for name in valid_names):
        messagebox.showerror(
            "Error", 
            "The specified directory does not appear to be a valid DDLC installation."
            )
        append_to_console("Error: Attempted to delete a non-DDLC directory.")
        return

    # Check for existence of expected game files as an extra precaution
    expected_files = ["DDLC.exe", "DDLC.sh", "game"]
    if not any(
        os.path.exists(
            os.path.join(game_path, expected_file)
        ) for expected_file in expected_files):
        messagebox.showerror(
            "Error",
            "The specified directory does not contain expected DDLC files.")
        append_to_console("Error: The specified directory lacks expected DDLC files.")
        return

    # Confirmation dialog
    confirm = messagebox.askyesno(
        "Confirm Uninstall",
        "Are you sure you want to Uninstall DDLC? This action cannot be undone!", icon='warning')
    if confirm:
        try:
            total_size = calculate_directory_size(game_path)
            show_progressbar()  # Initialize progress bar
            delete_directory_with_progress(game_path, total_size)
            append_to_console(f"DDLC has been uninstalled successfully from: {game_path}")
            messagebox.showinfo("Uninstall Complete", "DDLC has been successfully uninstalled.")
            game_path_entry.delete(0, tk.END)  # Clear the path entry after deletion
        except Exception as e:
            append_to_console(f"Error during uninstallation: {e}")
            messagebox.showerror("Error", f"Failed to uninstall DDLC. {e}")
    else:
        append_to_console("Uninstallation cancelled.")


def get_steam_path():
    """Find Steam on the System"""
    try:
        key_path = r"SOFTWARE\Valve\Steam"
        if os.environ["PROCESSOR_ARCHITECTURE"].endswith('64'):
            key_path = r"SOFTWARE\Wow6432Node\Valve\Steam"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "InstallPath")
        append_to_console(f"Steam Path Value: {value}")
        return value
    except Exception as e:
        append_to_console(f"Error accessing registry: {e}")
        return None

def parse_vdf_for_paths(vdf_path, game_ids=None):
    """Find the Game Path in the steam library"""
    if game_ids is None:
        game_ids=['698780']
    paths = []
    try:
        with open(vdf_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        current_path = ""
        in_apps_block = False
        for line in lines:
            # Strip line of whitespace for cleaner processing
            stripped_line = line.strip()
            if '"path"' in stripped_line:
                # Extract path value
                current_path = stripped_line.split('"')[3].replace('\\\\', '\\')
            if '"apps"' in stripped_line:
                in_apps_block = True
            elif in_apps_block:
                if any(game_id in stripped_line for game_id in game_ids):
                    # Found a game ID, add the current path if it's not already added
                    if current_path and current_path not in paths and os.path.exists(current_path):
                        paths.append(current_path)
                        append_to_console(f"Found Steam library with game: {current_path}")
                        # Reset for next library
                        current_path = ""
                        in_apps_block = False
                elif '}' in stripped_line:
                    # Exiting the apps block
                    in_apps_block = False
                    current_path = ""  # Reset current path after exiting an apps block

    except Exception as e:
        append_to_console(f"Error parsing VDF: {e}")
    append_to_console(f"VDF Paths: {paths}")
    return paths


def calculate_total_size(zip_path):
    """Get total size of zip"""
    total_size = 0
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            total_size += file_info.file_size
    return total_size

def show_progressbar():
    """Display the progressbar"""
    progress_bar.grid_forget()
    progress_bar.config(mode='determinate', maximum=100, value=0)
    progress_bar.grid(
        row=6,
        column=0,
        columnspan=4,
        sticky=tk.EW,
        padx=(LEFT_PADDING, 0),
        pady=(LEFT_PADDING, 0)
        )

def append_to_console(message):
    """Append a message to the console and prevent user input."""
    console.config(state=tk.NORMAL)  # Temporarily enable the widget for editing
    console.insert(tk.END, str(message) + "\n")
    console.see(tk.END)  # Scroll to the end
    console.config(state=tk.DISABLED)  # Disable the widget to prevent user input

def browse_path(entry, is_folder=False):
    """Open a dialog to update the entry with the selected path,
    either file or folder, and log to console."""
    if is_folder:
        filename = filedialog.askdirectory()
        action = "Directory selected: "
    else:
        filename = filedialog.askopenfilename()
        action = "File selected: "
    entry.delete(0, tk.END)
    if filename:  # Ensure a path was selected
        entry.insert(0, filename)
        append_to_console(action + filename)

def auto_toggle(entry):
    """Toggle the entry field for automatic game location detection and log to console."""
    game_path = find_game_directory()
    if entry.get().lower() == game_path:
        entry.delete(0, tk.END)
        append_to_console("Auto detection disabled.")
    else:
        entry.delete(0, tk.END)
        entry.insert(0, game_path)
        append_to_console("Auto detection enabled.")

def find_game_directory():
    """Find the Directory of DDLC"""
    steam_path = get_steam_path()
    if steam_path:
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        library_paths = parse_vdf_for_paths(vdf_path)
        library_paths.insert(0, steam_path)  # Include the default path
        for path in library_paths:
            for game_folder in ["Doki Doki Literature Club"]:
                game_path = os.path.join(path, "steamapps", "common", game_folder)
                append_to_console(f"Game Path: {game_path}")
                if os.path.exists(game_path):
                    return game_path
    # Return an informative string or empty if not found
    return "Game directory not found automatically."

def merge_directories(src, dst):
    """Merge directories from src to dst, overwriting conflicts."""
    for root, dirs, files in os.walk(src):
        # Calculate relative path to the source directory
        rel_path = os.path.relpath(root, src)
        dst_path = os.path.join(dst, rel_path)

        # Ensure the destination directory exists
        os.makedirs(dst_path, exist_ok=True)

        # Copy and overwrite files
        for file in files:
            src_file_path = os.path.join(root, file)
            dst_file_path = os.path.join(dst_path, file)
            if os.path.exists(dst_file_path):
                append_to_console(f"Overwriting file: {dst_file_path}")
            else:
                append_to_console(f"Copying file: {dst_file_path}")
            shutil.copy2(src_file_path, dst_file_path)

def overwrite_file(src, dst, processed_size):
    """Overwrite the file at dst with src."""
    file_size = os.path.getsize(src)
    if os.path.exists(dst):
        os.remove(dst)
        append_to_console(f"Removed existing file: {dst}")
    shutil.copy2(src, dst)
    append_to_console(f"Copied {src} to {dst}")
    processed_size[0] += file_size
    progress_bar['value'] = processed_size[0]
    app.update_idletasks()  # Update the GUI to reflect progress change

def process_files(zip_path, game_path):
    """Process files and directories with explicit handling for overwriting."""
    open_dir = False
    append_to_console(f"Processing files from: {zip_path} to {game_path}")
    if not zip_path.lower().endswith('.zip'):
        append_to_console("Error: The provided path does not point to a zip file.")
        return

    try:
        total_size = calculate_total_size(zip_path)
        processed_size = [0]  # Use a list for a mutable integer

        # Update progress bar setup
        progress_bar['value'] = 0
        progress_bar['maximum'] = total_size

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            extract_path = os.path.splitext(zip_path)[0]
            # Attempt to extract and catch PermissionError
            try:
                zip_ref.extractall(extract_path)
                append_to_console(f"Extracted zip to: {extract_path}")
            except PermissionError as e:
                if e.errno == errno.EACCES:
                    append_to_console(
                        (
                        "Warning: Permission denied during extraction.",
                        "The ZIP file might have been already extracted."
                        )
                        )
                else:
                    raise  # Re-raise if a different error

        open_dir = process_extracted_files(extract_path, game_path, processed_size)

    except Exception as e:
        append_to_console(f"Error during processing: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")

    progress_bar['value'] = progress_bar['maximum']  # Ensure progress bar reaches 100% at the end
    messagebox.showinfo("Process Completed", "All files have been processed successfully.")
    if open_dir:
        game_path = game_path_entry.get().strip()
    if os.path.exists(game_path):  # Make sure the path exists before trying to open it
        # Open the file explorer to the given path
        subprocess.run(['explorer', game_path], check=True)
    else:
        messagebox.showerror("Error", "The specified path does not exist.")
    app.config(cursor="")
    enable_ui_elements()

def process_extracted_files(extract_path, game_path, processed_size):
    """Process Game files after zip extraction."""
    open_dir=False
    target_files = ['audio.rpa', 'fonts.rpa', 'images.rpa', 'scripts.rpa']
    target_dirs = ['game', 'characters', 'lib', 'renpy']
    executable_extensions = ['.exe', '.bat', '.sh', '.py']

    # Find the directory that contains any of the target directories
    for root, dirs, files in os.walk(extract_path):
        # Check if any of the target directories are present in the current 'root'
        if any(t_dir in dirs for t_dir in target_dirs):
            base_dir = root  # This directory contains at least one of the target directories
            break
    else:
        append_to_console("None of the target directories found in the extracted path.")
        return open_dir

    # Process files and directories from the found base directory
    for root, dirs, files in os.walk(base_dir, topdown=True):
        # Files processing
        for name in files:
            src_path = os.path.join(root, name)
            # Check if the file is an executable or script and move accordingly
            if any(name.lower().endswith(ext) for ext in executable_extensions):
                dst_path = os.path.join(game_path, name)  # Executables go directly to game_path
                append_to_console(f"Moving executable/script: {name} to {dst_path}")
                overwrite_file(src_path, dst_path, processed_size)
                if name.lower().endswith('.exe'):  # Create desktop shortcut for executables
                    open_dir = True
            elif name in target_files:
                dst_path = os.path.join(game_path, 'game', name)  # Target files go to game_path/game
                append_to_console(f"Moving target file: {name} to {dst_path}")
                overwrite_file(src_path, dst_path, processed_size)

        # Directories processing
        for name in dirs:
            src_path = os.path.join(root, name)
            if name in target_dirs or name.endswith('.app'):
                dst_path = os.path.join(game_path, name)  # Target directories are copied as is
                append_to_console(f"Copying directory: {name}")
                merge_directories(src_path, dst_path)

        # Modify dirs list to exclude the target directories since they are already processed
        dirs[:] = [d for d in dirs if d not in target_dirs and not d.endswith('.app')]

    return open_dir



def disable_ui_elements():
    """Disable all UI"""
    zip_browse.config(state="disabled")
    game_path_browse.config(state="disabled")
    auto_button.config(state="disabled")
    process_button.config(state="disabled")
    delete_button.config(state="disabled")

def enable_ui_elements():
    """Enable all UI"""
    zip_browse.config(state="normal")
    game_path_browse.config(state="normal")
    auto_button.config(state="normal")
    process_button.config(state="normal")
    delete_button.config(state="normal")

def on_button_click():
    """When the process button is clicked"""
    try:
        app.config(cursor="watch")  # Set cursor to 'watch' indicating a process is running
        zip_path = zip_entry.get().strip()
        game_path = game_path_entry.get().strip()

        if not zip_path or not game_path:
            messagebox.showerror(
                "Error",
                "Please specify both the ZIP file and the game directory.")
            return

        # Assuming show_progressbar() and process_files() are defined to handle their tasks
        show_progressbar()
        app.update_idletasks()  # Update UI immediately to reflect cursor change
        disable_ui_elements()
        # Run the processing in a separate thread or after a short delay to ensure UI updates
        app.after(100, lambda: process_files(zip_path, game_path))
    except Exception as e:
        append_to_console(f"Error: {e}")
    finally:
        app.config(cursor="")  # Revert cursor to default after operation



app = tk.Tk()
app.geometry("680x355")
app.resizable(width=False, height=False)
app.title("DDLC Mod Installer")
zip_label = tk.Label(app, text="Zip File:")
zip_label.grid(row=0, column=0, pady=(LEFT_PADDING, 0))
zip_entry = tk.Entry(app, width=50)
zip_entry.grid(row=0, column=1, pady=(LEFT_PADDING, 0))
zip_browse = tk.Button(app, text="Browse", command=lambda: browse_path(zip_entry, is_folder=False))
zip_browse.grid(row=0, column=2, pady=(LEFT_PADDING, 0))

game_path_label = tk.Label(app, text="Game Directory:")
game_path_label.grid(row=1, column=0)
game_path_entry = tk.Entry(app, width=50)
game_path_entry.grid(row=1, column=1)
game_path_browse = tk.Button(
    app,
    text="Browse",
    command=lambda: browse_path(
        game_path_entry, is_folder=True))
game_path_browse.grid(row=1, column=2)
auto_button = tk.Button(app, text="Auto", command=lambda: auto_toggle(game_path_entry))
auto_button.grid(row=1, column=3, pady=(LEFT_PADDING, 0))

process_button = tk.Button(
    app,
    text="Install Mod",
    command=on_button_click)
process_button.grid(row=2, column=0, columnspan=3, pady=(LEFT_PADDING, 0))
delete_button = tk.Button(app, text="Delete DDLC", command=delete_ddlc)
delete_button.grid(row=2, column=3, pady=(LEFT_PADDING, 0))

console_label = tk.Label(app, text="Console Output:")
console_label.grid(row=3, column=0, columnspan=3,padx=(LEFT_PADDING, 0))
console = scrolledtext.ScrolledText(app, height=10, width=70, state=tk.DISABLED)
console.grid(row=4, column=0, columnspan=3,padx=(LEFT_PADDING, 0))
progress_bar = ttk.Progressbar(app, orient=tk.HORIZONTAL, length=400, mode='determinate')
reminder_label = tk.Label(
    app, text="Remember to install on a fresh copy of Doki Doki Literature Club!"
    )
reminder_label.grid(row=5, column=0, columnspan=3)
append_to_console("Select a ZIP file to Install")
app.mainloop()
