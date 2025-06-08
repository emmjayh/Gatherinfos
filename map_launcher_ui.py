import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys

# Assuming interactive_map.py is in the same directory
INTERACTIVE_MAP_SCRIPT = "interactive_map.py"
# Assuming parse_xml.py is in the same directory and should be run
PARSE_XML_SCRIPT = "parse_xml.py"

class MapLauncherApp:
    def __init__(self, master):
        self.master = master
        master.title("Interactive Map Launcher")

        self.data_file_path = tk.StringVar()
        self.data_file_path.set("spawn_data.json") # Default value

        self.stretch_factor = tk.DoubleVar()
        self.stretch_factor.set(1.0) # Default value, 1.0 means no stretch

        # --- UI Elements ---
        # File Selection
        tk.Label(master, text="Input Data File (JSON):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.file_entry = tk.Entry(master, textvariable=self.data_file_path, width=50)
        self.file_entry.grid(row=0, column=1, padx=5, pady=5)
        self.browse_button = tk.Button(master, text="Browse...", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        # Stretch Factor
        tk.Label(master, text="Vertical Stretch Factor:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.stretch_entry = tk.Entry(master, textvariable=self.stretch_factor, width=10)
        self.stretch_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        tk.Label(master, text="(e.g., 1.0 = default, >1 = taller, <1 = wider view)").grid(row=1, column=1, sticky="e", columnspan=2, padx=5)


        # Action Buttons
        self.run_parser_button = tk.Button(master, text="Run XML Parser", command=self.run_parser)
        self.run_parser_button.grid(row=2, column=0, pady=10, padx=5, sticky="ew")

        self.launch_button = tk.Button(master, text="Launch Map", command=self.launch_map)
        self.launch_button.grid(row=2, column=1, columnspan=2, pady=10, padx=5, sticky="ew")

        master.grid_columnconfigure(1, weight=1) # Allow file entry to expand

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.getcwd(),  # Start in current directory
            title="Select Spawn Data JSON File"
        )
        if file_path:
            # Update the StringVar with the absolute path of the selected file
            self.data_file_path.set(os.path.abspath(file_path))

    def run_parser(self):
        python_executable = sys.executable
        command = [python_executable, PARSE_XML_SCRIPT]

        try:
            # It's good practice to specify the current working directory if the script expects to find files relative to its own location
            # or if it generates output files in its directory.
            # For parse_xml.py, it might be looking for "spawn_data.xml" in CWD.
            # Let's assume PARSE_XML_SCRIPT is in the same directory as map_launcher_ui.py and that's our intended CWD for it.
            script_dir = os.path.dirname(os.path.abspath(__file__))

            result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=script_dir) # check=False to handle errors manually

            if result.returncode == 0:
                messagebox.showinfo("Parser Success", "XML Parser completed successfully.\n" + result.stdout)
            else:
                error_message = f"XML Parser failed (return code {result.returncode}).\n"
                if result.stdout:
                    error_message += f"\nOutput:\n{result.stdout}\n"
                if result.stderr:
                    error_message += f"\nError Output:\n{result.stderr}\n"
                messagebox.showerror("Parser Error", error_message)
                print("Parser STDOUT:", result.stdout)
                print("Parser STDERR:", result.stderr)
        except FileNotFoundError:
            messagebox.showerror("Parser Error", f"Error: The script '{PARSE_XML_SCRIPT}' was not found. Make sure it is in the same directory as the launcher.")
        except Exception as e:
            messagebox.showerror("Parser Error", f"An unexpected error occurred while running the parser: {e}")
            print(f"Unexpected error running parser: {e}")

    def launch_map(self):
        python_executable = sys.executable
        data_file = self.data_file_path.get()
        stretch = self.stretch_factor.get()

        if not data_file:
            messagebox.showerror("Error", "Input Data File cannot be empty.")
            return

        if not os.path.exists(data_file):
            messagebox.showerror("Error", f"The specified data file was not found:\n{data_file}\nPlease check the path or run the XML Parser if it generates this file.")
            return

        # The output file is currently hardcoded in interactive_map.py as "spawn_locations_map.html"
        # We don't need to pass it as an argument unless interactive_map.py is changed to accept it.
        # Let's assume the default output file name from interactive_map.py
        output_map_file = "spawn_locations_map.html"

        command = [
            python_executable,
            INTERACTIVE_MAP_SCRIPT,
            "--data_file", data_file,
            "--stretch_factor", str(stretch)
            # If interactive_map.py is modified to take an output file argument:
            # "--output_file", "some_output_name.html"
        ]

        try:
            # Similar to the parser, run interactive_map.py from its directory (or the app's root)
            # This helps if interactive_map.py reads/writes files relative to its location
            script_dir = os.path.dirname(os.path.abspath(__file__))

            result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=script_dir)

            if result.returncode == 0:
                success_message = f"Map generation script executed.\n"
                success_message += f"Output should be in '{os.path.join(script_dir, output_map_file)}'.\n"
                if result.stdout:
                     success_message += f"\nScript output:\n{result.stdout}"
                messagebox.showinfo("Map Generation Success", success_message)
                # Optionally, try to open the map file:
                # import webbrowser
                # webbrowser.open(os.path.join(script_dir, output_map_file))
            else:
                error_message = f"Map generation failed (return code {result.returncode}).\n"
                if result.stdout:
                    error_message += f"\nOutput:\n{result.stdout}\n"
                if result.stderr:
                    error_message += f"\nError Output:\n{result.stderr}\n"
                messagebox.showerror("Map Generation Error", error_message)
                print("Map Gen STDOUT:", result.stdout)
                print("Map Gen STDERR:", result.stderr)
        except FileNotFoundError:
            messagebox.showerror("Map Generation Error", f"Error: The script '{INTERACTIVE_MAP_SCRIPT}' was not found. Make sure it is in the same directory as the launcher.")
        except Exception as e:
            messagebox.showerror("Map Generation Error", f"An unexpected error occurred: {e}")
            print(f"Unexpected error launching map: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MapLauncherApp(root)
    root.mainloop()
