import os
from configuration import *

# This 'if' statement will check if verbose_mode flag from configuration is set to true, in which case defined vprint
#  function as such that it works as print function (so that all the verbose messages which are passed to vprint are
#  actually printed), else, vprint function does nothing and the messages are not displayed.
if verbose_mode:
    vprint = print
else:
    vprint = lambda string: None

vprint("Checking for existence of required files and directories...")

def directory_check(path_to_check):
    if not os.path.exists(path_to_check):
        vprint("Path", path_to_check, "does not exist. Attempting to create it...")
        os.makedirs(path_to_check, exist_ok=True)
        vprint("Done.")
    else:
        vprint(path_to_check, "already exists.")

# This function checks for existence of the given file at the given path and creates it with default contents if not.
def file_check(path_to_check, file_to_check, contents):
    if not os.path.exists(path_to_check + file_to_check):
        vprint(file_to_check, "does not exist in filesystem. Attempting to create it...")
        with open(path_to_check + file_to_check, "w") as working_file:
            working_file.write(contents)
        vprint("Done.")
    else:
        vprint(file_to_check, "already exists.")

directory_check(local_files_path)
file_check(local_files_path, "synced_todo_hashes.json", "{}")
