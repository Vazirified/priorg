# PRIORG
PRIORG organizer, personal information manager and priority scheduler system  

---

**Please note that PRIORG is currently considered to be in Pre-Alpha phase and will stay this way until all core features are implemented.**  

**As of January 2024, all development is stopped on this repository as I am trying to decide implementing the PRIORG idea using Emacs ORG mode as I have achieved promising results in my personal implementation and I need to sort out some issue in my personal affairs. I will shift development in the new direction (using ORG) or continue on the current path (using Python and ICS) as soon as my life gets back on track!**  

---

PRIORG core modules create/sync a local collection of ICS files from/to a remote CalDAV server VTODO items, edit the files using a human-readable method with MarkDown to store and read/parse the required additional data for prioritizing tasks in VTODO items' descriptions and create a couple of additional VCALENDAR entries to store data that are independent of the tasks/assignments but are required for the methods and algorithms to work, and finally synchronize them back to the server.  
The results of prioritizing tasks with PRIORG will be stored as the priority number of the VCALENDAR items, so that other applications can use the results with their priority sorted views, but core modules for creating/viewing/editing tasks/assignments are also included so that PRIORG can be used as a standalone application.  

---

Other features, probable future modules of the PIM, future data-structures and the details of PRIORG method for prioritizing tasks will be discussed after the release of an initial working command-line/TUI version that includes synchronization, priority evaluation, editor and viewer modules. Project progress until the initial release is tracked through the [issues](https://github.com/Vazirified/priorg/issues) section and this README file is updated in each step.  
Any feature other than core modules and basic functionalities will be initiated, tracked and brainstormed in [discussions](https://github.com/Vazirified/priorg/discussions) section.  