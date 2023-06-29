import vobject
import caldav
import os
import json
import hashlib
import keyring
import uuid
from datetime import datetime
# TODO: Write a setup utility to create/edit configuration.py file.
from configuration import *
from rich.console import Console

console = Console()


# TODO: Wrap applicable parts in callable function definitions so that we can call them from the main procedures in
#  the future. The functions that are used everywhere should naturally be taken out of this file, saved to a mutual
#  modules file and imported in every use case...

# TODO:
#  Write a setup utility for managing username and password of the CalDAV server in they OS keychain through
#  keyring.
#  The remote username/password are saved to
#  ("priorg-caldav", "username", "password") and the username can be accessed
#  from ("priorg-caldav", "priorg", "username").

# This 'if' statement will check if verbose_mode flag from configuration is set to true, in which case defined vprint
#  function as such that it works as print function (so that all the verbose messages which are passed to vprint are
#  actually printed), else, vprint function does nothing (as per definition) and the messages are not displayed.
def vprint(*args, **kwargs):
    return None


if verbose_mode:
    vprint = console.log


def calendar_selection(calendars_list: list) -> int:
    """Calendar Selector

    In the operations that write to the server, we need to know which calendar
    to write to...
    The calendar_selection function, when called with the list of calendars
    discovered on the server, will ask the user to choose a calendar and return
    the index number of that calendar for other operations to refer to and
    continue.

    Parameter:
    - calendars_list: A list of calendars as created with Python CalDAV library
        in a "Calendar(url)" format.

    Returns:
        The index number of the user's choice from calendars list as an
        integer.
    """
    if default_calendar == -1:
        vprint("A default calendar was not found. User input is required to continue...")
        index_counter = 0
        for discovered_calendar in calendars_list:
            print(index_counter, ":", discovered_calendar)
            index_counter += 1
        default_calendar_index = int(console.input("Please enter the index number of your calendar of choice for "
                                                   "current operation: "))
        if default_calendar_index < 0 or default_calendar_index > index_counter - 1:
            console.print("Your selection is not a valid item from the list. Defaulting to the first item")
            return 0
        return default_calendar_index
    else:
        vprint("A default calendar was found in configuration. Default calendar will be used to write to the server.")
        return default_calendar


def server_connect(url: str = server_url, usrname: str = keyring.get_password("priorg-caldav", "priorg"),
                   password: str = keyring.get_password("priorg-caldav", keyring.get_password("priorg-caldav", "priorg")
                                                        )) -> object:
    """Server Connection Starter

    This function connects to a remote CalDAV server and returns a Python CalDAV
    library class instance from the connection to be accessed by other modules.

    Mandatory arguments are:
        - url:  URL of the CalDAV server. If not provided, default to the value
                stored in configuration.py file.
        - usr:  Username to access the CalDAV server. If not provided, defaults
                to the value stored in the local keychain.
        - pas:  Password to access the CalDAV server. If not provided, defaults
                to the value stored in the local keychain.

    Returns:
        Server class object of the remote server.
    """
    # Credentials, if not provided as arguments, are retrieved from OS keychain and used to establish a
    #  connection/session with the remote CalDAV server.
    vprint("Establishing a connection to the remote server...")
    server_session = caldav.DAVClient(url=url, username=usrname, password=password)
    vprint("[bright_green]Connection to remote server established.")
    return server_session


def server_disconnect(server: object) -> None:
    """Server Connection Disconnector

    This function closes the connection to the CalDAV server passed to is as a
    Python CalDAV library server class instance.

    Parameters:
        - server: A Python CalDAV server class object

    Returns:
        None
    """
    # Connection/session with server is closed.
    vprint("Closing connection to server...")
    server.close()
    vprint("[bright_green]Connection to remote server was successfully closed.")


def calendar_discovery(server: object) -> list:
    """CalDAV Server Calendar Discovery

    This functions receives a server object in for of Python CalDAV server class
    instance and returns a list of calendars discovered on the server.

    Parameter:
        - server: Is an object, as an instance of Python CalDAV server class.

    Returns:
        A list containing all discovered calendars on the CalDAV server.
    """
    vprint("Getting a list of server calendars...")
    server_object = server.principal()
    server_calendars = server_object.calendars()
    vprint("[bright_green]List of calendars on the server was successfully obtained.")
    return server_calendars


def server_todos_lister(calendar_list: list) -> list:
    """Server Todos list Creator

    This functions receives a list of calendars and iterates them to extract all
    VTODO items and returns them as a list of URLs pointing to ICS files.

    Parameter:
        - calendar_list: A list of calendars in "Calendar(url)" format such as
        one generated by Python CalDAV library.

    Returns:
        A list in "T0D0(url)" format, containing URLs of the ICS files for the
        VTODO items on the server.
    """
    vprint("Creating a list of all VTODO items on the server...")
    server_todos = []
    for calendar in calendar_list:
        server_todos.extend(calendar.todos())
    vprint("[bright_green]Server VTODO items list was successfully created.")
    return server_todos


def server_todo_hasher(server_todos_list: list) -> dict:
    """Server VTODOs UID and Contents Hash Digest Dictionary Creator

    Server_todos_hasher function receives a list of VTODOs on a CalDAV server in
    T0D0(url) format, iterates them and reads their contents and outputs a
    dictionary containing UID/contents-hash-digest value-pairs.

    Parameter:
        - server_todos_list: List of VTODOs on a CalDAV server in T0D0(url)
        format

    Returns:
        Dictionary containing UID/contents-hash-digest value-pairs.
    """
    vprint("Creating a dictionary of all server VTODO UID and hash digests...")
    server_todo_hashes = {}
    for server_todo in server_todos_list:
        working_todo = str(server_todo.instance.vtodo.uid)
        server_todo_hashes[working_todo[working_todo.find("}") + 1: working_todo.find(">")]] = \
            hashlib.sha256(str(server_todo.instance).encode('utf-8')).hexdigest()
    vprint("[bright_green]Server VTODO items UID/hash digest dictionary was successfully created.")
    return server_todo_hashes


def ics_files_hasher(path: str) -> dict:
    """Local ICS-files/VTODOs UID and Contents Hash Digest Dictionary Creator

    Ics_files_hasher function receives a path to local files directory, iterates
    the files in that directory and looks for ICS files, and creates a
    dictionary of the VTODO UIDs and content hashes from each ICS file to
    return.

    Parameter:
        - path: A string containing the path to local files directory.
    Returns:
        Dictionary containing UID/contents-hash-digest value-pairs.
    """
    vprint("Reading ICS files and creating a dictionary of UID/hash digests...")
    ics_file_hashes = {}
    for file in os.listdir(path):
        if file.endswith('.ics'):
            with open(path + file, 'r') as todo_file:
                local_todo = vobject.base.readOne(todo_file)
                working_todo = str(local_todo.vtodo.uid)
                ics_file_hashes[working_todo[working_todo.find("}") + 1: working_todo.find(">")]] = \
                    hashlib.sha256(str(local_todo).encode('utf-8')).hexdigest()
    vprint("[bright_green]ICS files UID/hash digest dictionary was successfully created.")
    return ics_file_hashes


def json_file_reader(path: str, name: str) -> dict:
    """JSON File Reader/Importer

    Json_file_reader attempts to read a json file from the given path and file-
    name and returns the data within it as a dictionary.

    Parameters:
        - path: Path to the directory containing the file.
        - name: Filename of the JSON file (without the extension).

    Returns:
        Dictionary containing the data that was serialized in JSON format.
    """
    vprint("Reading previously saved JSON file...")
    with open(path + name + '.json', 'r') as working_file:
        working_dict = json.load(working_file)
    vprint("[bright_green]Previously saved JSON file was successfully imported.")
    return working_dict


def json_file_writer(path: str, name: str, data) -> None:
    """JSON File Writer/Exporter

    Json_file_writer accepts a path, a filename and some structured data such as
    a dictionary, serializes the data in JSON format and writes it to a JSON
    file.

    Parameters:
        - path: Path to the directory where the JSON file should be saved.
        - name: Filename without extension.
        - data: Structured data, such as a dictionary.

    Returns:
        None. But a file should be created/overwritten after the execution in
        the 'path' and with the 'name' filename and JSON extension.
    """
    vprint("Serializing and writing dictionary to JSON file...")
    with open(path + name + '.json', 'w') as working_file:
        json.dump(data, working_file, indent=4)
    vprint("[bright_green]Dictionary was successfully saved to JSON file.")


def dictionary_keys_lister(*args: dict) -> list:
    """Dictionary Keys Lister Without Duplicates

    Dictionary_keys_lister takes in infinite number of dictionaries and returns
    a list containing all of their keys without repeating the duplicates.

    Parameters:
        - infinite number of dictionaries
    Returns:
        List of input dictionaries keys, without duplicates.
    """
    keys = []
    for input_dict in args:
        keys += list(input_dict.keys())
    no_dup_keys = list(set(keys))
    return no_dup_keys


def file_vtodo_finder(path: str, uid: str) -> list:
    """ICS File VTODO Finder

    File_vtodo_finder gets a path to a collection of ICS files and a UID, reads
    and parses the ICS files and compares their UIDs against the UID provided to
    it when called and as soon as finding a VTODO ICS file with the same UID,
    returns a list containing the UID, the filename, VObject instance of the
    VTODO and the datetime object instance of its last modification date/time.

    Parameters:
        - path: A string containing the path to the directory containing the ICS
                files.
        - uid : A string containing the uid of the VTODO the function will
                search for.

    Returns:
        A list, defined and indexed as below:
        0: UID string of the VTODO;
        1: Filename string of the file containing the VTODO with the same UID;
        2: VObject instance of the VTODO with the same UID;
        3: Date/Time object of the last modification date/time of the VTODO;
    """
    for file in os.listdir(path):
        if file.endswith('.ics'):
            with open(path + file, 'r') as todo_file:
                todo = vobject.base.readOne(todo_file)
                todo_uid = str(todo.vtodo.uid)
                todo_uid_parsed = todo_uid[todo_uid.find("}") + 1: todo_uid.find(">")]
                if todo_uid_parsed == uid:
                    working_file = file
                    working_local_todo = todo
                    working_local_todo_uid_parsed = todo_uid_parsed
                    working_local_todo_modification = str(working_local_todo.vtodo.last_modified)
                    working_local_todo_modification_parsed = working_local_todo_modification[
                                                             working_local_todo_modification.find("}") + 1:
                                                             working_local_todo_modification.find(">")]
                    working_local_todo_modification_datetime = datetime.strptime(working_local_todo_modification_parsed,
                                                                                 "%Y-%m-%d %H:%M:%S")
    todo_attributes = [working_local_todo_uid_parsed,
                       working_file,
                       working_local_todo,
                       working_local_todo_modification_datetime]
    return todo_attributes


def server_vtodo_finder(server_todos: list, uid: str) -> list:
    """CalDAV Tasklist VTODO Finder

    Server_vtodo_finder gets a tasklist of a collection of VTODOs on a CalDAV
    server and a UID, reads and parses the VTODOs and compares their UIDs
    against the UID provided to it when called and as soon as finding a VTODO
    instance with the same UID, returns a list containing the UID, the CalDAV
    object instance (e.g. the address on the server), VObject instance of the
    VTODO and the datetime object instance of its last modification date/time.

    Parameters:
        - server_todos  : A list containing the VTODOs on a CalDAV servre in the
                          format similar to what the Python CalDAV library
                          generates.
        - uid           : A string containing the uid of the VTODO the function
                          will search for.

    Returns:
        A list, defined and indexed as below:
        0: UID string of the VTODO;
        1: CalDAV instance of the VTODO with the same UID;
        2: VObject instance of the VTODO with the same UID;
        3: Date/Time object of the last modification date/time of the VTODO;
    """
    for todo in server_todos:
        todo_uid = str(todo.instance.vtodo.uid)
        todo_uid_parsed = todo_uid[todo_uid.find("}") + 1: todo_uid.find(">")]
        if todo_uid_parsed == uid:
            working_server_todo_caldav = todo
            working_server_todo = todo.instance
            working_server_todo_uid_parsed = todo_uid_parsed
            working_server_todo_modification = str(working_server_todo.vtodo.last_modified)
            working_server_todo_modification_parsed = working_server_todo_modification[
                                                      working_server_todo_modification.find("}") + 1:
                                                      working_server_todo_modification.find(">")]
            working_server_todo_modification_datetime = datetime.strptime(working_server_todo_modification_parsed,
                                                                          "%Y-%m-%d %H:%M:%S")
    todo_attributes = [working_server_todo_uid_parsed,
                       working_server_todo_caldav,
                       working_server_todo,
                       working_server_todo_modification_datetime]
    return todo_attributes


def file_todo_writer(path: str, filename: str, data: object) -> None:
    """ICS File VTODO Updater/Creator

    File_todo_writer accepts a path and a filename (with extension) as target
    and overwrites/creates the target with the data provided as a VObject VTODO
    instance.

    Parameters:
        - path      :   A string, containing the path to the file that should be
                        created or overwritten.
        - filename  :   A string containing the name and extension of the target
                        file.
        - data      :   VObject instance, holding the VTODO data that should be
                        written to the target file.

    Returns:
        None.
    """
    vprint("Attempting to create/update the file with provided data...")
    with open(path + filename, 'w') as updating_local_file:
        updating_local_file.write(data.serialize())
    vprint("[bright_green]File was successfully overwritten with the source data.")


def server_todo_updater(caldav_item: object, data: object) -> None:
    """CalDAV Server VTODO Updater

    Server_todo_updater accepts an existing CalDAV VTODO item in Python CalDAV
    library VTODO object format, and overwrites it with the data provided as a
    VObject VTODO instance.

    Parameters:
        - caldav_item   :   A CalDAV library VTODO object, pointing to an
                            existing VTODO item on a CalDAV server.
        - data          :   VObject instance, holding the VTODO data that should
                            be written to the target VTODO on the server.

    Returns:
        None.
    """
    vprint("Attempting to update the existing server VTODO with provided data...")
    caldav_item.vobject_instance = data
    caldav_item.save()
    vprint("[bright_green]Server copy was successfully overwritten with the local copy.")


def server_todo_creator(calendar: list, data: object) -> None:
    """Server VTODO Item Creator

    Server_todo_creator receives a calendar from a list of calendars in Python
    CalDAV library and creates a VTODO entry on it using the data provided in
    VObject instance format.

    Parameters:
        - calendar  :   A list item from the list of calendars on a CalDAV
                        server in Python CalDAV library discovered calendars
                        format.
        - data      :   A VObject instance, containing icalendar data to be
                        created on the server.

    Returns:
        None.
    """
    vprint("Creating a VTODO item on the server, in the chosen calendar, using the provided data...")
    calendar.save_todo(ical_fragment=data.serialize())
    vprint("[bright_green]Server copy was successfully created using the provided icalendar data.")


def server_vtodo_eraser(item) -> None:
    """Server VTODO Eraser

    Server_vtodo_eraser receives a VTODO object in Python CalDAV VTODO objects
    format and deletes it from the CalDAV server.

    Arguments:
        item    :   A VTODO object instance in the format provided by Python
                    CalDAV library.
    Returns:
        None.
    """
    vprint("Attempting to delete the addressed VTODO item...")
    item.delete()
    vprint("[bright_green]Addressed VTODO item on the server was successfully deleted.")


def file_vtodo_eraser(path, filename) -> None:
    """File VTODO Eraser

    File_vtodo_eraser receives a path and a filename (which includes the
    extension) and deletes it from the filesystem.

    Arguments:
        path    :   Relative path to the directory that contains the file which
                    is to be deleted.
        filename:   Filename of the file which should be deleted, which should
                    contain the extension.

    Returns:
        None
    """
    vprint("Attempting to remove the addressed file...")
    os.remove(path + filename)
    vprint("[bright_green]Local copy was successfully deleted.")


# =====================================================================================================================
# ========= Main Procedures of The Synchronizer - Minimized for a Blackbox Approach ===================================
# =====================================================================================================================

vprint("[bright_blue]Synchronization module started.")

server_session = server_connect()
server_calendars = calendar_discovery(server_session)
server_todos = server_todos_lister(server_calendars)
server_todo_hashes = server_todo_hasher(server_todos)
local_todo_hashes = ics_files_hasher(local_files_path)
synced_todo_hashes = json_file_reader(local_files_path, 'synced_todo_hashes')

# =====================================================================================================================

no_dup_uids = dictionary_keys_lister(server_todo_hashes, local_todo_hashes, synced_todo_hashes)

# TODO: Find repeating operations in each condition below and try to modularize them in pre-defined functions.

# Now we compare the dictionaries to determine the required sync operations for each UID item...
for uid_item in no_dup_uids:
    # The condition below means the item exists in all dictionaries, and we now have to check the hashes to see if it
    #  was changed on any side...
    if uid_item in server_todo_hashes and uid_item in local_todo_hashes and uid_item in synced_todo_hashes:
        vprint("Item with UID", uid_item, "exists on both sides, we just need to check if the content are the same "
                                          "or there have been any changes.")
        if server_todo_hashes[uid_item] == synced_todo_hashes[uid_item] and \
                local_todo_hashes[uid_item] == synced_todo_hashes[uid_item]:
            vprint("The item is the same on both sides. No further action needed.")
        else:
            vprint("The item is changed at least on one side. The last modification dates will be checked and the "
                   "newer copy will be used as source for synchronization.")
            working_local_todo = file_vtodo_finder(local_files_path, uid_item)
            working_server_todo = server_vtodo_finder(server_todos, uid_item)

            if working_server_todo[3] > working_local_todo[3]:
                vprint("Server copy was modified later. Taking server copy as source and updating local copy...")
                file_todo_writer(local_files_path, working_local_todo[1], working_server_todo[2])

            elif working_server_todo[3] < working_local_todo[3]:
                vprint("Local copy was modified later. Taking local copy as source and updating the server copy...")
                server_todo_updater(working_server_todo[1], working_local_todo[2])

            else:
                vprint("Modification date/times are the same. Taking server copy as source and updating local copy...")
                file_todo_writer(local_files_path, working_local_todo[1], working_server_todo[2])

    elif uid_item in server_todo_hashes and uid_item not in local_todo_hashes and uid_item not in \
            synced_todo_hashes:
        # TODO: Thoroughly test and evaluate this condition as in the modularized version of the synchronizer we have
        #  tried to use the file_todo_writer function with uses .write() instead of .writelines() and this approach is
        #  not compatible with the initially working code.
        vprint("Item with UID", uid_item, "has been created on the server after the previous sync and is not "
                                          "present in the synchronized items list or local items. Server item will "
                                          "be used as source to create the item locally...")
        working_server_todo = server_vtodo_finder(server_todos, uid_item)
        file_todo_writer(local_files_path, str(uuid.uuid4()).upper() + ".ics", working_server_todo[1].serialize())

    elif uid_item not in server_todo_hashes and uid_item in local_todo_hashes and uid_item not in \
            synced_todo_hashes:
        vprint("Item with UID", uid_item,
               "has been created after the previous synchronization and is not present on "
               "The remote server. Local ICS file will be used as source to create the "
               "assignment on server.")
        working_local_todo = file_vtodo_finder(local_files_path, uid_item)
        server_todo_creator(server_calendars[calendar_selection(server_calendars)], working_local_todo[2])

    elif uid_item not in server_todo_hashes and uid_item not in local_todo_hashes and uid_item in \
            synced_todo_hashes:
        vprint("[bright_yellow]Item with UID", uid_item,
               "[bright_yellow]which was present after previous sync is now "
               "deleted both remotely and locally between this and previous "
               "synchronization (which is a bit strange)!")
        vprint("No further action required.")

    elif uid_item in server_todo_hashes and uid_item in local_todo_hashes and uid_item not in synced_todo_hashes:
        vprint("[bright_yellow]Item with UID", uid_item,
               "[bright_yellow]is created both remotely and locally between "
               "this and previous sync! This usually indicates a problem as "
               "UID collisions between separate items are nearly impossible!")
        if server_todo_hashes[uid_item] == local_todo_hashes[uid_item]:
            vprint("This item has equal contents on both sides. No further action required.")
        else:
            vprint("This item has different contents on different sides. Searching for the item with a newer "
                   "modification date/time to accept as synchronization source...")
            working_local_todo = file_vtodo_finder(local_files_path, uid_item)
            working_server_todo = server_vtodo_finder(server_todos, uid_item)

            if working_server_todo[3] > working_local_todo[3]:
                vprint("Server copy was modified later. Taking server copy as source and updating local copy...")
                file_todo_writer(local_files_path, working_local_todo[1], working_server_todo[2])

            elif working_server_todo[3] < working_local_todo[3]:
                vprint("Local copy was modified later. Taking local copy as source and updating the server copy...")
                server_todo_updater(working_server_todo[1], working_local_todo[2])
            else:
                vprint(
                    "[bright_yellow]Both modification date/times are the same.[/] Taking server copy as source and "
                    "updating local copy...")
                file_todo_writer(local_files_path, working_local_todo[1], working_server_todo[2])

    elif uid_item in server_todo_hashes and uid_item not in local_todo_hashes and uid_item in synced_todo_hashes:
        vprint("Item with UID", uid_item, "was deleted locally in the interval between this and the "
                                          "previous synchronization. This item will be deleted from the server...")
        working_server_todo = server_vtodo_finder(server_todos, uid_item)
        server_vtodo_eraser(working_server_todo[1])

    elif uid_item not in server_todo_hashes and uid_item in local_todo_hashes and uid_item in synced_todo_hashes:
        vprint("Item with UID", uid_item, "was deleted from the remote server in the interval between this and the "
                                          "previous synchronization. This item will be deleted from local files...")
        working_local_todo = file_vtodo_finder(local_files_path, uid_item)
        file_vtodo_eraser(local_files_path, working_local_todo[1])

    # The situation below means that something has gone wrong as it is impossible to happen!
    # This "else" statement should not really exist, but let's include it for now and raise some kind of error if
    #  this happens...
    else:
        vprint("[bright_red]There seems to be a problem with the PRIORG data.\n"
               "This can be an unknown problem with the server or the local filesystem, or the data is corrupted. "
               "You may need to investigate this error manually before changing/synchronizing anything.")

# Another dictionary is created from the local "synced" ICS file with their UID and the SHA256 digest of their
#  content
#  as local_todo_hashes.
vprint("[bright_green]Synchronization completed successfully.")

# =====================================================================================================================

synced_todo_hashes = ics_files_hasher(local_files_path)
json_file_writer(local_files_path, 'synced_todo_hashes', synced_todo_hashes)
server_disconnect(server_session)
vprint("[bright_blue]Synchronization module operations finished.")