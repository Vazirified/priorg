# TODO: Imports should be optimized after we determine what components we are using from the libraries.
import vobject
import caldav
import os
import json
import hashlib
import keyring
import sys

# Configuration variables are imported/accessed.
# TODO: Write a setup utility to create/edit configuration.py file.
from configuration import *

# Credentials are retrieved from OS keychain and used to establish a connection/session with the remote CalDAV server.
# Then a client object is formed by assigning all principle properties of the session to server_object and a list of
# calendars on the server is built as server_calendars.
# TODO: Remember to close the established session to server in the end.
# TODO: Write code to manage username and password of the CalDAV server in they OS keychain through keyring. The remote
#  username/password are saved to ("priorg-caldav", "username", "password") and the username can be accessed from
#  ("priorg-caldav", "priorg", "username").
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
    server_todo_hashes[working_todo[working_todo.find("}") + 1 : working_todo.find(">")]] = \
        hashlib.sha256(str(server_todo.instance).encode('utf-8')).hexdigest()

# "server_todo_hashes" is written to a file in the "local_files_path" with server_todo_hashes.json filename. JSON in
# intentionally chosen so that the hashes dictionary stays human-readable.
# While staying human-readable, the dictionary can easily be read back with:
# with open(local_files_path + 'server_todo_hashes.json', 'r') as working_file:
#     data = json.load(working_file)
with open(local_files_path + 'server_todo_hashes.json', 'w') as working_file:
    json.dump(server_todo_hashes, working_file, indent=4)
