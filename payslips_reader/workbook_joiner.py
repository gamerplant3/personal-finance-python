import os
import pandas as pd

# Configuration
search_dir = r"C:\Users\[   ]\TT Pay Slips"  # Change this to the folder you want to search
target_filename = "pay_summary.xlsx"  # Name of the workbooks to find
output_filename = "combined.xlsx"  # Name of the output workbook

# List to hold all dataframes
all_data = []

# Walk through directory recursively
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file == target_filename:
            file_path = os.path.join(root, file)
            print(f"Reading {file_path}")
            df = pd.read_excel(file_path)
            all_data.append(df)

# Combine all dataframes
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)

    # Save to parent folder
    output_path = os.path.join(search_dir, output_filename)
    combined_df.to_excel(output_path, index=False)
    print(f"Combined workbook saved to {output_path}")
else:
    print("No matching workbooks found.")
