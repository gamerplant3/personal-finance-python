# given a file directory, python script parses all files in that location and outputs a list (.txt file)
# of each file's path. Optional rebasing, optional specify text file save location

import os

def list_file_paths(
        original_directory,
        new_directory=None, # optional, use to rewrite paths to a new base directory
        txt_output_directory=None, # optional, use to save .txt file in a different location. else, saves in original_directory
        txt_filename="file_paths.txt"
):

    original_directory = os.path.abspath(original_directory)
    paths = []

    # If different folder specified for saving the .txt file
    if txt_output_directory:
        txt_output_directory = os.path.abspath(txt_output_directory)
    else:
        txt_output_directory = original_directory  # default

    os.makedirs(txt_output_directory, exist_ok=True)
    txt_output_path = os.path.join(txt_output_directory, txt_filename)

    # If changing base directories
    for root, _, files in os.walk(original_directory):
        for file in files:
            original_path = os.path.join(root, file)

            if new_directory:
                rel_path = os.path.relpath(original_path, original_directory)
                rewritten_path = os.path.join(new_directory, rel_path)
                paths.append(rewritten_path)
            else:
                paths.append(original_path)

    # Write paths to text file
    with open(txt_output_path, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(p + "\n")

    return paths, txt_output_path


# Example usage
directory_path = r"C:\Users\me\Desktop"
rewrite_dir = r"C:\Users\me\Documents"
paths, saved_file = list_file_paths(directory_path,new_directory=rewrite_dir)

#print("Saved to:", saved_file)
