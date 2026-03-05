# given a directory, generates a csv with a list of duplicate files

import os
import hashlib
import csv
from collections import defaultdict

def get_file_hash(file_path, block_size=65536):
    """Generates a SHA-256 hash for a file using memory-efficient chunks."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
    except (PermissionError, OSError) as e:
        return None


def find_and_export_duplicates(target_dir):
    size_map = defaultdict(list)
    output_file = os.path.join(target_dir, "duplicate_report.csv")

    print(f"Scanning: {target_dir}")

    # Step 1: Group by size
    for root, _, files in os.walk(target_dir):
        for filename in files:
            # Skip the report file itself if it already exists
            if filename == "duplicate_report.csv":
                continue
            path = os.path.join(root, filename)
            try:
                size_map[os.path.getsize(path)].append(path)
            except OSError:
                continue

    # Step 2: Hash only size-collisions
    hash_map = defaultdict(list)
    potential_dup_sizes = {s: p for s, p in size_map.items() if len(p) > 1}

    for size, paths in potential_dup_sizes.items():
        for path in paths:
            f_hash = get_file_hash(path)
            if f_hash:
                hash_map[f_hash].append(path)

    # Step 3: Filter for actual duplicates and write to CSV
    duplicates = {h: p for h, p in hash_map.items() if len(p) > 1}

    if not duplicates:
        print("No duplicates found. CSV will not be created.")
        return

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header Row
            writer.writerow(['Hash Group', 'File Name', 'File Size (Bytes)', 'Full Path'])

            for hash_val, paths in duplicates.items():
                for path in paths:
                    writer.writerow([
                        hash_val[:12],  # Shortened hash for readability
                        os.path.basename(path),
                        os.path.getsize(path),
                        os.path.dirname(path)
                    ])
                # Add an empty row between groups for visual clarity in Excel/Sheets
                writer.writerow([])

        print(f"Success! Report generated: {output_file}")
    except PermissionError:
        print(f"Error: Could not write to {output_file}. Is it open in another program?")


# running

folder_to_scan = r'C:\Users\rwend\OneDrive\Documents Onedrive\Learning French'

if os.path.exists(folder_to_scan):
    find_and_export_duplicates(folder_to_scan)
else:
    print("Directory path not found.")