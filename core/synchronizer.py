# TODO: Imports should be optimized after we determine what components we are using from the libraries.
import vobject
import caldav
import os
import json
import hashlib
import keyring
import sys
# TODO: Write a setup utility to create/edit configuration.py file.
from configuration import *

# Credentials are retrieved from OS keychain and used to establish a connection/session with the remote CalDAV server.
# Then a client object is formed by assigning all principle properties of the session to server_object and a list of
# calendars on the server is built as server_calendars.
# TODO: Write a setup utility to manage username and password of the CalDAV server in they OS keychain through keyring.
#  The remote username/password are saved to ("priorg-caldav", "username", "password") and the username can be accessed
#  from ("priorg-caldav", "priorg", "username").
server_session = caldav.DAVClient(url=server_url,
                                  username=keyring.get_password("priorg-caldav", "priorg"),
                                  password=keyring.get_password("priorg-caldav",
                                                                keyring.get_password("priorg-caldav", "priorg")))
server_object = server_session.principal()
server_calendars = server_object.calendars()

# Calendars are iterated and all VTODO items are fetched.
# VTODOs are stored in server_todos list.
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
# intentionally chosen so that the hashes dictionary stays human-readable.
# with open(local_files_path + 'server_todo_hashes.json', 'w') as working_file:
#     json.dump(server_todo_hashes, working_file, indent=4)

# TODO: Write an ICS files UID/SHA256hash generator function and call it twice instead of writing the code below twice!

# Another dictionary is created from the local ICS file with their UID and the SHA256 digest of their content as
# local_todo_hashes.
local_todo_hashes = {}
for file in os.listdir(local_files_path):
    if file.endswith('.ics'):
        with open(local_files_path + file, 'r') as todo_file:
            local_todo = vobject.base.readOne(todo_file)
            working_todo = str(local_todo.vtodo.uid)
            local_todo_hashes[working_todo[working_todo.find("}") + 1: working_todo.find(">")]] = \
                hashlib.sha256(str(local_todo).encode('utf-8')).hexdigest()

# "local_todo_hashes" is written to a file in the "local_files_path" with local_todo_hashes.json filename. JSON is
# intentionally chosen so that the hashes dictionary stays human-readable.
# with open(local_files_path + 'local_todo_hashes.json', 'w') as working_file:
#     json.dump(local_todo_hashes, working_file, indent=4)

# Previously saved UID/hashes from the last synchronization are read back in from the JSON file. This file will be
# updated after synchronization.
with open(local_files_path + 'synced_todo_hashes.json', 'r') as working_file:
    synced_todo_hashes = json.load(working_file)

# We now have three dictionaries containing UID/hash pairs. By comparing these, we should be able to understand what
# needs to be synced and in which way.

# "no_dup_uids" is a list of all keys from the three dictionaries with duplicates removed. We will use this to iterate
# on all dictionaries and check for existence of keys...
uids = list(server_todo_hashes.keys()) + list(local_todo_hashes.keys()) + list(synced_todo_hashes.keys())
no_dup_uids = list(set(uids))

for uid_item in no_dup_uids:
    if uid_item in server_todo_hashes and uid_item in local_todo_hashes and uid_item in synced_todo_hashes:
        # This means the item exists in all dictionaries. We now have to check the hash and see if it is changed on
        # any side...
        pass
    elif uid_item in server_todo_hashes and uid_item not in local_todo_hashes and uid_item not in synced_todo_hashes:
        # This item is only stored on the sever. It must have been created on the server in the interval between current
        # synchronization and the previous one. Such items must be created in the local copies.
        pass
    elif uid_item not in server_todo_hashes and uid_item in local_todo_hashes and uid_item not in synced_todo_hashes:
        # This item only exists locally. It must have been created locally between this synchronization and the previous
        # one. Such items must be created on the server.
        pass
    elif uid_item not in server_todo_hashes and uid_item not in local_todo_hashes and uid_item in synced_todo_hashes:
        # This item only exists in the synced list. This means that it was present everywhere during the last
        # synchronization but was deleted from both sides in the interval (which is a bit strange but can happen).
        # Such an item does not require any action. It will be deleted from the synced items dictionary at the end of
        # current synchronization automatically. We also need to issue a warning.
        pass
    elif uid_item in server_todo_hashes and uid_item in local_todo_hashes and uid_item not in synced_todo_hashes:
        # Item exists on server and locally, but it was not present in previous synchronization. This means that the
        # is miraculously created on both sides with the same UID between this sync and the last one.
        # We have to check the hashed on both sides and if not equal, the one with newer modification date must be
        # copied to the other side. We also need to issue a warning for this.
        pass
    elif uid_item in server_todo_hashes and uid_item not in local_todo_hashes and uid_item in synced_todo_hashes:
        # Item is on the server and was present after the previous synchronization, but does not exist locally. Such an
        # item must have been deleted locally between the two synchronizations and must be deleted from the server too.
        pass
    elif uid_item not in server_todo_hashes and uid_item in local_todo_hashes and uid_item in synced_todo_hashes:
        # Item exists locally and was present after the previous synchronization, but is not on the server. Such an
        # item must have been deleted from the server between the two synchronizations and must be deleted locally too.
        pass
    else:
        # This situation means that something has gone wrong as it is impossible to happen! This "else" statement should
        # not really exist! But let's include it for now and raise some kind of error if this happens...
        pass

# =====================================================================================================================
# Make sure that local files are in sync before creating the UID/hashes dictionary and dumping it to the JSON file.
# This means that synchronization must happen above this comment.
# =====================================================================================================================

# Another dictionary is created from the local "synced" ICS file with their UID and the SHA256 digest of their content
# as local_todo_hashes.
synced_todo_hashes = {}
for file in os.listdir(local_files_path):
    if file.endswith('.ics'):
        with open(local_files_path + file, 'r') as todo_file:
            synced_todo = vobject.base.readOne(todo_file)
            working_todo = str(synced_todo.vtodo.uid)
            synced_todo_hashes[working_todo[working_todo.find("}") + 1: working_todo.find(">")]] = \
                hashlib.sha256(str(synced_todo).encode('utf-8')).hexdigest()

# "synced_todo_hashes" is written to a file in the "local_files_path" with synced_todo_hashes.json filename. JSON is
# intentionally chosen so that the hashes dictionary stays human-readable.

with open(local_files_path + 'synced_todo_hashes.json', 'w') as working_file:
    json.dump(synced_todo_hashes, working_file, indent=4)

# Connection/session with server is closed.
server_session.close()
