# TODO: Imports should be optimized after we determine what components we are using from the libraries.
import vobject
import caldav
import os
import json
import hashlib
import keyring
from datetime import datetime
# TODO: Write a setup utility to create/edit configuration.py file.
from configuration import *

# TODO: Write more verbose alerts in code and decide on a way to determine how much (if any) of them are displayed,
#   e.g. how the user choses the verbosity of the running application in terminal mode...

# Credentials are retrieved from OS keychain and used to establish a connection/session with the remote CalDAV server.
#   Then a client object is formed by assigning all principle properties of the session to server_object and a list of
#   calendars on the server is built as server_calendars.

# TODO: Write a setup utility to manage username and password of the CalDAV server in they OS keychain through keyring.
#  The remote username/password are saved to ("priorg-caldav", "username", "password") and the username can be accessed
#  from ("priorg-caldav", "priorg", "username").
server_session = caldav.DAVClient(url=server_url,
                                  username=keyring.get_password("priorg-caldav", "priorg"),
                                  password=keyring.get_password("priorg-caldav",
                                                                keyring.get_password("priorg-caldav", "priorg")))
server_object = server_session.principal()
server_calendars = server_object.calendars()

# Calendars are iterated and all VTODO items are fetched. VTODOs are stored in server_todos list.
server_todos = []
for calendar in server_calendars:
    server_todos.extend(calendar.todos())

# A dictionary is created from the server tasks UIDs and the SHA256 digest of their contents as server_todo_hashes.
server_todo_hashes = {}
for server_todo in server_todos:
    working_todo = str(server_todo.instance.vtodo.uid)
    server_todo_hashes[working_todo[working_todo.find("}") + 1: working_todo.find(">")]] = \
        hashlib.sha256(str(server_todo.instance).encode('utf-8')).hexdigest()

# "server_todo_hashes" is written to a file in the "local_files_path" with server_todo_hashes.json filename. JSON is
#   intentionally chosen so that the hashes dictionary stays human-readable.
#   with open(local_files_path + 'server_todo_hashes.json', 'w') as working_file:
#       json.dump(server_todo_hashes, working_file, indent=4)

# TODO: Write an ICS files UID/SHA256hash generator function and call it twice instead of writing the code below twice!

# Another dictionary is created from the local ICS file with their UID and the SHA256 digest of their content as
#   local_todo_hashes.
local_todo_hashes = {}
for file in os.listdir(local_files_path):
    if file.endswith('.ics'):
        with open(local_files_path + file, 'r') as todo_file:
            local_todo = vobject.base.readOne(todo_file)
            working_todo = str(local_todo.vtodo.uid)
            local_todo_hashes[working_todo[working_todo.find("}") + 1: working_todo.find(">")]] = \
                hashlib.sha256(str(local_todo).encode('utf-8')).hexdigest()

# "local_todo_hashes" is written to a file in the "local_files_path" with local_todo_hashes.json filename. JSON is
#   intentionally chosen so that the hashes dictionary stays human-readable.
#   with open(local_files_path + 'local_todo_hashes.json', 'w') as working_file:
#       json.dump(local_todo_hashes, working_file, indent=4)

# Previously saved UID/hashes from the last synchronization are read back in from the JSON file. This file will be
#   updated after synchronization.
with open(local_files_path + 'synced_todo_hashes.json', 'r') as working_file:
    synced_todo_hashes = json.load(working_file)

# We now have three dictionaries containing UID/hash pairs. By comparing these, we should be able to understand what
#   needs to be synced and in which way.

# In the operations that write something to the server, we need to know which calendar to write to...
#   The calendar_selection function, when called, will ask the user to choose a calendar and returnes the index number
#   of that calendar for the operation to continue.
def calendar_selection():
    if default_calendar == -1:
        index_counter = 0
        for discovered_calendar in server_calendars:
            print(index_counter, ":", discovered_calendar)
            index_counter += 1
        default_calendar_index = int(input("Please enter the index number of your calendar of choice for current operation: "))
        if default_calendar_index < 0 or default_calendar_index > index_counter - 1:
            print("Your selection is not a valid item from the list. Defaulting to the first item")
            return 0
        return default_calendar_index
    else:
        return default_calendar

# "no_dup_uids" is a list of all keys from the three dictionaries with duplicates removed. We will use this to iterate
#   on all dictionaries and check for existence of keys...
uids = list(server_todo_hashes.keys()) + list(local_todo_hashes.keys()) + list(synced_todo_hashes.keys())
no_dup_uids = list(set(uids))

# TODO: Find repeating operations in each condition below and try to modularize them in pre-defined functions.

# Now we compare the dictionaries to determine the required sync operations for each UID item...
for uid_item in no_dup_uids:
# Condition below means the item exists in all dictionaries. We now have to check the hash and see if it is changed on
#   any side...
    if uid_item in server_todo_hashes and uid_item in local_todo_hashes and uid_item in synced_todo_hashes:
        pass

# The item below is only stored on the sever. It must have been created on the server in the interval between current
#   synchronization and the previous one. Such items must be created in the local copies.
    elif uid_item in server_todo_hashes and uid_item not in local_todo_hashes and uid_item not in synced_todo_hashes:
        pass

# The item below only exists locally. It must have been created locally between this synchronization and the previous
#   one. Such items must be created on the server.
    elif uid_item not in server_todo_hashes and uid_item in local_todo_hashes and uid_item not in synced_todo_hashes:
        pass

# The item below only exists in the synced list. This means that it was present everywhere during the last
#   synchronization but was deleted from both sides in the interval (which is a bit strange but can happen).
#   Such an item does not require any action. It will be deleted from the synced items dictionary at the end of
#   current synchronization automatically. We also need to issue a warning.
    elif uid_item not in server_todo_hashes and uid_item not in local_todo_hashes and uid_item in synced_todo_hashes:
        print("Item with UID", uid_item, "which was present after previous sync is now deleted both remotely and "
                                         "locally between this and previous sync!")
        print("No further action required.")

# Below item exists on server and locally, but it was not present in previous synchronization. This means that the
#   is miraculously created on both sides with the same UID between this sync and the last one.
#   We have to check the hashed on both sides and if not equal, the one with newer modification date must be
#   copied to the other side. We also need to issue a warning for this.
    elif uid_item in server_todo_hashes and uid_item in local_todo_hashes and uid_item not in synced_todo_hashes:
        print("Item with UID", uid_item, "is created both remotely and locally between this and previous sync!")
        print("This usually indicates a problem as UID collisions between separate items are very rare!")
        if server_todo_hashes[uid_item] == local_todo_hashes[uid_item]:
            print("This item has equal contents on both sides. No further action required.")
        else:
            print("This item has different contents on different sides. Searching for the item with a newer "
                  "modification date/time to accept as synchronization source...")
            for file in os.listdir(local_files_path):
                if file.endswith('.ics'):
                    with open(local_files_path + file, 'r') as todo_file:
                        todo = vobject.base.readOne(todo_file)
                        todo_uid = str(todo.vtodo.uid)
                        todo_uid_parsed = todo_uid[todo_uid.find("}") + 1: todo_uid.find(">")]
                        if todo_uid_parsed == uid_item:
                            working_file = file
                            working_local_todo = todo
                            working_local_todo_uid_parsed = todo_uid_parsed
                            working_local_todo_modification = str(working_local_todo.vtodo.last_modified)
                            working_local_todo_modification_parsed = working_local_todo_modification[
                                                      working_local_todo_modification.find("}") + 1:
                                                      working_local_todo_modification.find(">")]
            for todo in server_todos:
                todo_uid = str(todo.instance.vtodo.uid)
                todo_uid_parsed = todo_uid[todo_uid.find("}") + 1: todo_uid.find(">")]
                if todo_uid_parsed == uid_item:
                    working_server_todo_caldav = todo
                    working_server_todo = todo.instance
                    working_server_todo_uid_parsed = todo_uid_parsed
                    working_server_todo_modification = str(working_server_todo.vtodo.last_modified)
                    working_server_todo_modification_parsed = working_server_todo_modification[
                                                      working_server_todo_modification.find("}") + 1:
                                                      working_server_todo_modification.find(">")]
            working_local_todo_modification_datetime = datetime.strptime(working_local_todo_modification_parsed,
                                                                         "%Y-%m-%d %H:%M:%S")
            working_server_todo_modification_datetime = datetime.strptime(working_server_todo_modification_parsed,
                                                                         "%Y-%m-%d %H:%M:%S")
            if working_server_todo_modification_datetime > working_local_todo_modification_datetime:
                print("Server copy was modified later. Taking server copy as source and updating local copy...")
                working_local_todo = working_server_todo
                with open(local_files_path + working_file, 'w') as updating_local_file:
                    updating_local_file.write(working_local_todo.serialize())
                print("Local file was overwritten with remote data.")
            elif working_server_todo_modification_datetime < working_local_todo_modification_datetime:
                print("Local copy was modified later. Taking local copy as source and updating the server copy...")
                working_server_todo_caldav.vobject_instance = working_local_todo
                working_server_todo_caldav.save()
                print("Server copy was overwritten with local data.")
            else:
                print("Both modification date/times are the same. Taking server copy as source and updating local "
                      "copy...")
                working_local_todo = working_server_todo
                with open(local_files_path + working_file, 'w') as updating_local_file:
                    updating_local_file.write(working_local_todo.serialize())
                print("Local file was overwritten with remote data.")


# Item below is on the server and was present after the previous synchronization, but does not exist locally. Such an
#   item must have been deleted locally between the two synchronizations and must be deleted from the server too.
    elif uid_item in server_todo_hashes and uid_item not in local_todo_hashes and uid_item in synced_todo_hashes:
        print("Item with UID", uid_item, "was deleted locally in the interval between this and the "
                                         "previous synchronization. This item will be deleted from the server...")
        for todo in server_todos:
            working_server_todo_uid = str(todo.instance.vtodo.uid)
            working_server_todo_uid_parsed = working_server_todo_uid[working_server_todo_uid.find("}") + 1:
                                                                     working_server_todo_uid.find(">")]
            if working_server_todo_uid_parsed == uid_item:
                todo.delete()
                print("The item was deleted from the server.")

# Item below exists locally and was present after the previous synchronization, but is not on the server. Such an
#   item must have been deleted from the server between the two synchronizations and must be deleted locally too.
    elif uid_item not in server_todo_hashes and uid_item in local_todo_hashes and uid_item in synced_todo_hashes:
        print("Item with UID", uid_item, "was deleted from the remote server in the interval between this and the "
                                         "previous synchronization. This item will be deleted from local files...")
        for file in os.listdir(local_files_path):
            if file.endswith('.ics'):
                with open(local_files_path + file, 'r') as todo_file:
                    working_todo = vobject.base.readOne(todo_file)
                    working_todo_uid = str(working_todo.vtodo.uid)
                    working_todo_uid_parsed = working_todo_uid[
                                              working_todo_uid.find("}") + 1: working_todo_uid.find(">")]
                    if working_todo_uid_parsed == uid_item:
                        os.remove(local_files_path + file)
                        print("The item was deleted from the local files.")

# Situation below means that something has gone wrong as it is impossible to happen! This "else" statement should
#   not really exist! But let's include it for now and raise some kind of error if this happens...
    else:
        print("There seems to be a problem with the PRIORG data.",
              "This can be an unknown problem with the server or the local filesystem, or the data is corrupted.",
              "You may need to investigate this error manually before changing/synchronizing anything.")

# =====================================================================================================================
# Make sure that local files are in sync before creating the UID/hashes dictionary and dumping it to the JSON file.
#   This means that synchronization must happen above this comment.
# =====================================================================================================================

# Another dictionary is created from the local "synced" ICS file with their UID and the SHA256 digest of their content
#   as local_todo_hashes.
synced_todo_hashes = {}
for file in os.listdir(local_files_path):
    if file.endswith('.ics'):
        with open(local_files_path + file, 'r') as todo_file:
            synced_todo = vobject.base.readOne(todo_file)
            working_todo = str(synced_todo.vtodo.uid)
            synced_todo_hashes[working_todo[working_todo.find("}") + 1: working_todo.find(">")]] = \
                hashlib.sha256(str(synced_todo).encode('utf-8')).hexdigest()

# "synced_todo_hashes" is written to a file in the "local_files_path" with synced_todo_hashes.json filename. JSON is
#   intentionally chosen so that the hashes dictionary stays human-readable.

with open(local_files_path + 'synced_todo_hashes.json', 'w') as working_file:
    json.dump(synced_todo_hashes, working_file, indent=4)

# Connection/session with server is closed.
server_session.close()
