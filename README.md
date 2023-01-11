# Time Tracker

This is a simple launchd- / launchctl-based focus tracker.

It creates a job which logs the "current focus" from macOS / iOS every 5 minutes, writing this to a file in iCloud.

## Installation

- Install the `Log Current Focus.shortcut` to the app "Shortcuts".
- Install and activate the job using `./install.sh`

## Removal

- Deactivate and delete the job using `.uninstall.sh`.
- Delete the `Log Current Focus.shortcut` shortcut in the app "Shortcuts".