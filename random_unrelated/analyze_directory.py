import os
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd

def analyze_directory(directory):
    file_summary = defaultdict(lambda: {'count': 0, 'size': 0})
    file_sizes = []

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_extension = os.path.splitext(file)[1].lower()
                file_size = os.path.getsize(file_path)
                file_sizes.append(file_size)

                file_summary[file_extension]['count'] += 1
                file_summary[file_extension]['size'] += file_size
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    # convert summary into a DataFrame
    df_summary = pd.DataFrame([
        {"File Type": ext, "Count": info['count'], "Total Size (MB)": info['size'] / 1_000_000}
        for ext, info in file_summary.items()
    ])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # histogram of file sizes
    ax1.hist([size / 1_000_000 for size in file_sizes], bins=30, color='skyblue', edgecolor='black')
    ax1.set_title('Histogram of File Sizes')
    ax1.set_xlabel('File Size (MB)')
    ax1.set_ylabel('Frequency')
    ax1.grid(axis='y')

    # table for file types
    ax2.axis('tight')
    ax2.axis('off')
    table_data = df_summary.values
    columns = df_summary.columns.tolist()
    table = ax2.table(cellText=table_data, colLabels=columns, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)

    plt.suptitle('File Analysis Summary', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

    return df_summary

# Example usage
directory_path = r"C:\Users\me\Downloads"
file_types_summary = analyze_directory(directory_path)

#print(file_types_summary)
