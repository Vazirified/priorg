# TODO: Imports should be optimized after we determine what components we are using from the libraries.
import vobject
import caldav
import os
import hashlib
import keyring

# Configuration variables are imported/accessed.
# TODO: Change code to manage server url in a local configuration.py file.
from configuration import *

# Credentials are retrieved from OS keychain and used to establish a connection/session with the remote CalDAV server.
# TODO: Write code to manage username and password of the CalDAV server in they OS keychain through keyring. The remote
#  username/password are saved to ("priorg-caldav", "username", "password") and the username can be accessed from
#  ("priorg-caldav", "priorg", "username").
client_session = caldav.DAVClient(url=server_url,
                                  username=keyring.get_password("priorg-caldav", "priorg"),
                                  password=keyring.get_password("priorg-caldav", keyring.get_password("priorg-caldav",
                                                                                                      "priorg")))
