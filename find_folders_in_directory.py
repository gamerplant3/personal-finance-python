import os
import csv

def report_embedded_parents(target_directory):
    # Standardize the path and create the full path for the CSV
    target_directory = os.path.abspath(target_directory)
    output_csv = os.path.join(target_directory, "found_parents.csv")

    if not os.path.exists(target_directory):
        print(f"Error: The directory '{target_directory}' does not exist.")
        return

    parent_folders = set()
    suffix = "_embedded_files"

    print(f"Scanning: {target_directory}...")

    for root, dirs, files in os.walk(target_directory):
        for dir_name in dirs:
            if dir_name.endswith(suffix):
                full_path = os.path.join(root, dir_name)
                parent_dir = os.path.dirname(full_path)
                parent_folders.add(parent_dir)

    if parent_folders:
        try:
            with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Parent Directory Path"])
                for path in sorted(parent_folders):
                    writer.writerow([path])

            print("-" * 30)
            print(f"Success! {len(parent_folders)} unique paths found.")
            print(f"Report saved to: {output_csv}")
        except PermissionError:
            print(f"Error: Could not write to {output_csv}. Is the file open in Excel?")
    else:
        print("No matching folders found. No CSV created.")


folder_to_scan = r'C:\Users\rwend\OneDrive\Documents Onedrive\Zvinhu from basa laptop'

if os.path.exists(folder_to_scan):
    report_embedded_parents(folder_to_scan)
else:
    print(f"Directory path not found: {folder_to_scan}")