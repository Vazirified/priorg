import os
from configuration import *

def directory_check(path_to_check):
    if not os.path.exists(path_to_check):
        os.makedirs(path_to_check, exist_ok=True)

# This function checks for existence of the given file at the given path and creates it with default contents if not.
def file_check(path_to_check, file_to_check, contents):
    if not os.path.exists(path_to_check + file_to_check):
        with open(path_to_check + file_to_check, "w") as hashfile:
            hashfile.write(contents)

directory_check(local_files_path)
# file_check(local_files_path, "server_todo_hashes.json", "{}")
# file_check(local_files_path, "local_todo_hashes.json", "{}")
file_check(local_files_path, "synced_todo_hashes.json", "{}")
