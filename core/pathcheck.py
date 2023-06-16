import os
from configuration import *

print("Checking for existence of required files and directories...")

def directory_check(path_to_check):
    if not os.path.exists(path_to_check):
        print("Path", path_to_check, "does not exist. Attempting to create it...")
        os.makedirs(path_to_check, exist_ok=True)
        print("Done.")
    else:
        print(path_to_check, "already exists.")

# This function checks for existence of the given file at the given path and creates it with default contents if not.
def file_check(path_to_check, file_to_check, contents):
    if not os.path.exists(path_to_check + file_to_check):
        print(file_to_check, "does not exist in filesystem. Attempting to create it...")
        with open(path_to_check + file_to_check, "w") as hashfile:
            hashfile.write(contents)
        print("Done.")
    else:
        print(file_to_check, "already exists.")

directory_check(local_files_path)
file_check(local_files_path, "synced_todo_hashes.json", "{}")
