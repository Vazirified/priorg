# TODO: Integrate this module with synchronizer.py if not used anywhere else.
import os
from configuration import *

def directory_check(path_to_check):
    if not os.path.exists(path_to_check):
        os.makedirs(path_to_check, exist_ok=True)

def file_check(path_to_check, file_to_check):
    if not os.path.exists(path_to_check + file_to_check):
        with open(path_to_check + file_to_check, 'x') as hashfile:
            hashfile.write("{}")

directory_check(local_files_path)
# file_check(local_files_path, "server_todo_hashes.json")
# file_check(local_files_path, "local_todo_hashes.json")
file_check(local_files_path, "synced_todo_hashes.json")
