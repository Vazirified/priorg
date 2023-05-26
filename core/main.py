# TODO: Imports should be optimized after we determine what components we are using from the libraries.
import vobject
import caldav
import os
import datetime
import hashlib
import keyring

import sys
from datetime import date
from datetime import datetime
from datetime import timedelta

# Configuration variables are imported/accessed.
# TODO: Change code to manage server url in a local configuration.py file.
from configuration import *

# Credentials are retrieved from OS keychain and used to establish a connection/session with the remote CalDAV server.
# Then a client object is formed by assigning all principle properties of the session to server_object and a list of
# calendars on the server is built as server_calendars.
# TODO: Write code to manage username and password of the CalDAV server in they OS keychain through keyring. The remote
#  username/password are saved to ("priorg-caldav", "username", "password") and the username can be accessed from
#  ("priorg-caldav", "priorg", "username").
server_session = caldav.DAVClient(url=server_url,
                                  username=keyring.get_password("priorg-caldav", "priorg"),
                                  password=keyring.get_password("priorg-caldav",
                                                                keyring.get_password("priorg-caldav", "priorg")))
server_object = server_session.principal()
server_calendars = server_object.calendars()

# Calendars are iterated and all VTODO items are fetched from user's birthday up to 100 years into the future!
server_todos = []
for calendar in server_calendars:
    server_todos.extend(calendar.search(start=datetime(user_birthday[0], user_birthday[1], user_birthday[2]),
                                        end=datetime(date.today().year + 100, 1, 1),
                                        todo=True, expand=True))
