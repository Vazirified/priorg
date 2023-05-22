# priorg
PRIORG organizer, personal information manager and priority scheduler system

---

PRIORG core modules will create/sync a local collections of ICS files from a remote CalDAV server VTODO items, edits the files using a human readable method with MarkDown to store and read/parse the required additional data in VTODO items' descriptions and creates a couple of additional VCALENDAR entries to store data that are independent from the tasks/assignments but are required for the methods and algorithms to work and finally synchronizes them back to the server. The results of prioritizing tasks with PRIORG will be stored as the priority number of the VCALENDAR items, so that other applications can use the results with their priority sorted views, but core modules for creating/viewing/editing tasks/assignments are also included.

---

Other features, probable future modules of the PIM, future data-structures and the details of PRIORG method for prioritizing tasks will be discussed after the release of an initial working command-line/TUI version that includes synchronization, priority evaluation, editor and viewer modules.
Project progress until the initial release is tracked through the [issues](https://github.com/Vazirified/priorg/issues) section and this README file is updated in each step.
