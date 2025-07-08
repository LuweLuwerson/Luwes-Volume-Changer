## Overview
Luwe's Volume Changer is a Windows utility that allows you to control the volume and mute state of specific applications (such as Brave and Discord) or the currently focused application using customizable global hotkeys. It features a settings window and an on-screen overlay to display volume changes.

## Features
- **Per-application volume control:** Adjust volume or mute/unmute for 2 apps of your choosing (defaults to Brave and Discord), or any focused app.
- **Customizable hotkeys:** Set your own global hotkeys for volume up, down, and mute actions per app.
- **On-screen overlay:** Visual feedback for volume changes, including app icons and mute status.
- **System tray integration:** Access settings or quit the app from the tray icon.

## Default Hotkeys
| Action                | Brave                | Discord              | Focused App           |
|-----------------------|----------------------|----------------------|-----------------------|
| Volume Down           | Ctrl+Alt+Shift+!     | Ctrl+Alt+Shift+$     | Ctrl+Alt+Shift+&      |
| Volume Up             | Ctrl+Alt+Shift+"     | Ctrl+Alt+Shift+%     | Ctrl+Alt+Shift+*      |
| Mute/Unmute           | Ctrl+Alt+Shift+£     | Ctrl+Alt+Shift+^     | Ctrl+Alt+Shift+(      |

You can change these hotkeys in the settings window.

## Settings Window
- Open the settings from the system tray icon.
- Configure each app by changing the app name + '.exe'.
- Configure hotkeys for each app and action.
- Enable or disable the on-screen overlay.
- Restore default settings.

## Overlay
- Shows the app icon, volume percentage, and a progress bar when you change volume or mute/unmute.
- Can be toggled on/off in settings.

## Installation
1. Install dependencies:
   pip install -r requirements.txt

2. Run the app:
   python main.py

## Building the EXE yourself
To build a standalone executable (Windows):
1. Make sure you have [PyInstaller](https://pyinstaller.org/) installed:
   pip install pyinstaller
   
2. Run the following command in CMD:
   pyinstaller --onefile --windowed --icon=image.ico --add-data "image.ico;." --add-data "disabled.ico;." main.py
   
(The EXE will be created in the 'dist/' folder)

## Dependencies
- keyboard
- pycaw
- pywin32
- psutil
- Pillow
- pystray
- tkinter
