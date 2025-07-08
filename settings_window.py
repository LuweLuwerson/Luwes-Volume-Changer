import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import keyboard
from PIL import Image, ImageTk
import sys
import subprocess
import psutil
import time

class SettingsWindow:
    def __init__(self):
        # Create a Toplevel window
        self.window = tk.Toplevel()
        self.window.title("Volume Changer Settings")
        self.window.geometry("600x400")
        self.window.resizable(False, False)
        
        # Initialize drag data
        self._drag_data = {"x": 0, "y": 0, "item": None}
        
        # Remove default title bar
        self.window.overrideredirect(True)
        
        # Set dark theme colors
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.entry_bg = "#3c3f41"
        self.button_bg = "#4c5052"
        self.button_fg = "#ffffff"
        self.selection_bg = "#4c5052"
        self.selection_fg = "#ffffff"
        self.disabled_bg = "#2b2b2b"
        self.focus_bg = "#4c5052"
        
        # Create custom title bar
        self.title_bar = tk.Frame(self.window, bg=self.bg_color, height=30)
        self.title_bar.pack(fill=tk.X)
        
        # Add title
        title_label = tk.Label(self.title_bar, 
                             text="Volume Changer Settings",
                             bg=self.bg_color,
                             fg=self.fg_color,
                             font=('Segoe UI', 10))
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Add close button
        close_button = tk.Button(self.title_bar,
                               text="×",
                               bg=self.bg_color,
                               fg=self.fg_color,
                               font=('Segoe UI', 13),
                               relief=tk.FLAT,
                               command=self.on_closing)
        close_button.pack(side=tk.RIGHT, padx=10)
        
        # Make window draggable only from title bar
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)
        
        # Ensure the window can receive focus and stays on top
        self.window.attributes('-topmost', True)
        self.window.focus_force()
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('default')  # Reset to default theme first
        
        # Configure custom styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TButton", 
                           background=self.button_bg, 
                           foreground=self.button_fg,
                           padding=5)
        
        # Configure messagebox style
        self.style.configure("Messagebox", 
                           background=self.bg_color,
                           foreground=self.fg_color)
        
        # Set window background
        self.window.configure(bg=self.bg_color)
        
        # Configure selection colors
        self.window.option_add('*TEntry.selectBackground', self.selection_bg)
        self.window.option_add('*TEntry.selectForeground', self.selection_fg)
        self.window.option_add('*TEntry.disabledBackground', self.disabled_bg)
        self.window.option_add('*TEntry.disabledForeground', self.fg_color)
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image.ico")
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        # Create the main frame
        main_frame = ttk.Frame(self.window, padding="10", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.columnconfigure(3, weight=1)
        
        # Load current settings
        self.settings_file = "settings.json"
        self.default_settings = {
            'brave': {'down': 'ctrl+alt+shift+!', 'up': 'ctrl+alt+shift+"', 'mute': 'ctrl+alt+shift+£', 'app_name': 'brave.exe'},
            'discord': {'down': 'ctrl+alt+shift+$', 'up': 'ctrl+alt+shift+%', 'mute': 'ctrl+alt+shift+^', 'app_name': 'discord.exe'},
            'focused': {'down': 'ctrl+alt+shift+&', 'up': 'ctrl+alt+shift+*', 'mute': 'ctrl+alt+shift+(', 'app_name': 'focused'}
        }
        self.current_settings = self.load_settings()
        
        # Create headers
        ttk.Label(main_frame, text="Application", style="TLabel").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(main_frame, text="Volume Down", style="TLabel").grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(main_frame, text="Volume Up", style="TLabel").grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(main_frame, text="Mute Toggle", style="TLabel").grid(row=0, column=3, padx=5, pady=5)
        
        # Create entries for each setting
        self.entries = {}
        row = 1
        for app, settings in self.current_settings.items():
            if app == 'overlay_enabled':
                continue
                
            # Application name
            app_var = tk.StringVar(value=settings['app_name'])
            app_entry = tk.Entry(main_frame, 
                               textvariable=app_var,
                               bg=self.entry_bg,
                               fg=self.fg_color,
                               insertbackground=self.fg_color,
                               relief=tk.FLAT,
                               selectbackground=self.selection_bg,
                               selectforeground=self.selection_fg,
                               disabledbackground=self.disabled_bg,
                               disabledforeground=self.fg_color)
            app_entry.grid(row=row, column=0, padx=5, pady=5, sticky='ew')
            
            # Make focused entry read-only
            if app == 'focused':
                app_entry.config(state='disabled')
            
            # Volume down hotkey
            down_var = tk.StringVar(value=settings['down'])
            down_entry = tk.Entry(main_frame, 
                                textvariable=down_var,
                                bg=self.entry_bg,
                                fg=self.fg_color,
                                insertbackground=self.fg_color,
                                relief=tk.FLAT,
                                selectbackground=self.selection_bg,
                                selectforeground=self.selection_fg)
            down_entry.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
            down_entry.bind('<Button-1>', lambda e, entry=down_entry: self.start_hotkey_capture(e, entry))
            
            # Volume up hotkey
            up_var = tk.StringVar(value=settings['up'])
            up_entry = tk.Entry(main_frame, 
                              textvariable=up_var,
                              bg=self.entry_bg,
                              fg=self.fg_color,
                              insertbackground=self.fg_color,
                              relief=tk.FLAT,
                              selectbackground=self.selection_bg,
                              selectforeground=self.selection_fg)
            up_entry.grid(row=row, column=2, padx=5, pady=5, sticky='ew')
            up_entry.bind('<Button-1>', lambda e, entry=up_entry: self.start_hotkey_capture(e, entry))
            
            # Mute toggle hotkey
            mute_var = tk.StringVar(value=settings['mute'])
            mute_entry = tk.Entry(main_frame, 
                                textvariable=mute_var,
                                bg=self.entry_bg,
                                fg=self.fg_color,
                                insertbackground=self.fg_color,
                                relief=tk.FLAT,
                                selectbackground=self.selection_bg,
                                selectforeground=self.selection_fg)
            mute_entry.grid(row=row, column=3, padx=5, pady=5, sticky='ew')
            mute_entry.bind('<Button-1>', lambda e, entry=mute_entry: self.start_hotkey_capture(e, entry))
            
            self.entries[app] = {'app': app_var, 'down': down_var, 'up': up_var, 'mute': mute_var}
            row += 1
        
        # Add overlay toggle
        self.overlay_var = tk.BooleanVar(value=self.current_settings.get('overlay_enabled', True))
        overlay_check = tk.Checkbutton(main_frame,
                                     text="Show Volume Overlay",
                                     variable=self.overlay_var,
                                     bg=self.bg_color,
                                     fg=self.fg_color,
                                     selectcolor=self.button_bg,
                                     activebackground=self.bg_color,
                                     activeforeground=self.fg_color)
        overlay_check.grid(row=row, column=0, columnspan=4, pady=10, sticky='w')
        row += 1
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.grid(row=row, column=0, columnspan=4, pady=20)
        
        # Create a container frame for buttons to center them
        button_container = ttk.Frame(button_frame, style="TFrame")
        button_container.pack(expand=True)
        
        # Create custom styled buttons
        save_btn = tk.Button(button_container, 
                           text="Save",
                           command=self.save_settings,
                           bg=self.button_bg,
                           fg=self.button_fg,
                           relief=tk.FLAT,
                           padx=10,
                           pady=5)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(button_container,
                            text="Reset to Defaults",
                            command=self.reset_to_defaults,
                            bg=self.button_bg,
                            fg=self.button_fg,
                            relief=tk.FLAT,
                            padx=10,
                            pady=5)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_container,
                             text="Cancel",
                             command=self.window.destroy,
                             bg=self.button_bg,
                             fg=self.button_fg,
                             relief=tk.FLAT,
                             padx=10,
                             pady=5)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Center the window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Initialize hotkey capture state
        self.capturing_hotkey = False
        self.current_hotkey_entry = None
        self.original_hotkey = None
        self.keyboard_hook = None
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure the window is properly initialized
        self.window.update()
    
    def start_move(self, event):
        # Only start moving if clicking on the title bar
        if event.widget == self.title_bar:
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y
            self._drag_data["item"] = event.widget
        else:
            self._drag_data["item"] = None
    
    def on_move(self, event):
        if self._drag_data["item"] is None:
            return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.window.winfo_x() + dx
        y = self.window.winfo_y() + dy
        self.window.geometry(f"+{x}+{y}")
    
    def start_hotkey_capture(self, event, entry):
        if self.capturing_hotkey:
            return
        
        self.capturing_hotkey = True
        self.current_hotkey_entry = entry
        self.original_hotkey = entry.get()  # Store original value
        entry.delete(0, tk.END)
        entry.insert(0, "Press keys...")
        entry.configure(
            state='readonly',
            bg=self.entry_bg,
            readonlybackground=self.entry_bg
        )
        
        # Start keyboard hook
        if self.keyboard_hook is None:
            self.keyboard_hook = keyboard.hook(self.on_keyboard_event)
        
        # Bind click-away event
        self.window.bind('<Button-1>', self.on_click_away)
    
    def on_click_away(self, event):
        if self.capturing_hotkey and self.current_hotkey_entry:
            # Check if click was outside the current entry
            x, y = event.x_root, event.y_root
            entry_x = self.current_hotkey_entry.winfo_rootx()
            entry_y = self.current_hotkey_entry.winfo_rooty()
            entry_width = self.current_hotkey_entry.winfo_width()
            entry_height = self.current_hotkey_entry.winfo_height()
            
            if not (entry_x <= x <= entry_x + entry_width and 
                   entry_y <= y <= entry_y + entry_height):
                # Only accept if we have a valid hotkey (not "Press keys...")
                if self.current_hotkey_entry.get() != "Press keys...":
                    self.current_hotkey_entry.configure(
                        state='normal',
                        bg=self.entry_bg,
                        readonlybackground=self.entry_bg
                    )
                    self.stop_hotkey_capture()
                else:
                    # If no valid hotkey was entered, restore the original
                    self.current_hotkey_entry.configure(
                        state='normal',
                        bg=self.entry_bg,
                        readonlybackground=self.entry_bg
                    )
                    self.current_hotkey_entry.delete(0, tk.END)
                    self.current_hotkey_entry.insert(0, self.original_hotkey)
                    self.current_hotkey_entry.configure(
                        state='readonly',
                        bg=self.entry_bg,
                        readonlybackground=self.entry_bg
                    )
                    self.stop_hotkey_capture()
    
    def on_keyboard_event(self, event):
        if not self.capturing_hotkey or not self.current_hotkey_entry:
            return
        
        if event.event_type == keyboard.KEY_DOWN:
            # Handle special keys
            if event.name == 'esc':
                self.current_hotkey_entry.configure(
                    state='normal',
                    bg=self.entry_bg,
                    readonlybackground=self.entry_bg
                )
                self.current_hotkey_entry.delete(0, tk.END)
                # Leave it blank instead of restoring original
                self.current_hotkey_entry.configure(
                    state='readonly',
                    bg=self.entry_bg,
                    readonlybackground=self.entry_bg
                )
                self.stop_hotkey_capture()
                return
            
            if event.name == 'enter':
                if self.current_hotkey_entry.get() != "Press keys...":
                    self.current_hotkey_entry.configure(
                        state='normal',
                        bg=self.entry_bg,
                        readonlybackground=self.entry_bg
                    )
                    self.stop_hotkey_capture()
                return
            
            # Get the key combination
            keys = []
            if keyboard.is_pressed('ctrl'):
                keys.append('ctrl')
            if keyboard.is_pressed('shift'):
                keys.append('shift')
            if keyboard.is_pressed('alt'):
                keys.append('alt')
            
            # Add the main key if it's not a modifier
            key = event.name.lower()
            if key not in ['ctrl', 'shift', 'alt', 'enter', 'esc']:
                keys.append(key)
            
            if keys:
                hotkey = '+'.join(keys)
                self.current_hotkey_entry.configure(
                    state='normal',
                    bg=self.entry_bg,
                    readonlybackground=self.entry_bg
                )
                self.current_hotkey_entry.delete(0, tk.END)
                self.current_hotkey_entry.insert(0, hotkey)
                self.current_hotkey_entry.configure(
                    state='readonly',
                    bg=self.entry_bg,
                    readonlybackground=self.entry_bg
                )
    
    def stop_hotkey_capture(self):
        if self.capturing_hotkey:
            self.capturing_hotkey = False
            self.current_hotkey_entry = None
            self.original_hotkey = None
            if self.keyboard_hook is not None:
                keyboard.unhook(self.keyboard_hook)
                self.keyboard_hook = None
            # Unbind click-away event
            self.window.unbind('<Button-1>')
    
    def on_closing(self):
        self.stop_hotkey_capture()
        self.window.grab_release()  # Release the grab before destroying
        self.window.destroy()
    
    def run(self):
        try:
            # Make the window modal
            self.window.grab_set()
            # Center the window
            self.window.update_idletasks()
            width = self.window.winfo_width()
            height = self.window.winfo_height()
            x = (self.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.window.winfo_screenheight() // 2) - (height // 2)
            self.window.geometry(f'{width}x{height}+{x}+{y}')
            
            # Ensure window is visible and focused
            self.window.deiconify()
            self.window.focus_force()
            
            # Start the window's event loop
            self.window.wait_window()
        except Exception as e:
            print(f"Error in window: {e}")
            self.window.destroy()
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Convert the loaded settings to match our expected format
                    settings = {}
                    for app in self.default_settings.keys():
                        settings[app] = {
                            'app_name': self.default_settings[app]['app_name'],
                            'down': self.default_settings[app]['down'],
                            'up': self.default_settings[app]['up'],
                            'mute': self.default_settings[app]['mute']
                        }
                    
                    # Update with any saved settings
                    for key, value in loaded_settings.items():
                        if key == 'overlay_enabled':
                            settings['overlay_enabled'] = value
                            continue
                            
                        # Extract app name from the key (e.g., 'brave_down' -> 'brave')
                        app = key.split('_')[0]
                        if app in settings:
                            # Set the appropriate hotkey based on the key suffix
                            if key.endswith('_down'):
                                settings[app]['down'] = value.get('hotkey', self.default_settings[app]['down'])
                            elif key.endswith('_up'):
                                settings[app]['up'] = value.get('hotkey', self.default_settings[app]['up'])
                            elif key.endswith('_mute'):
                                settings[app]['mute'] = value.get('hotkey', self.default_settings[app]['mute'])
                    
                    # Ensure overlay setting exists
                    if 'overlay_enabled' not in settings:
                        settings['overlay_enabled'] = True
                    return settings
            except Exception as e:
                print(f"Error loading settings: {e}")
                return self.default_settings.copy()
        return self.default_settings.copy()
    
    def save_settings(self):
        new_settings = {}
        for app, entry in self.entries.items():
            # Save volume down hotkey
            new_settings[f'{app}_down'] = {
                'hotkey': entry['down'].get(),
                'app_name': entry['app'].get()
            }
            # Save volume up hotkey
            new_settings[f'{app}_up'] = {
                'hotkey': entry['up'].get(),
                'app_name': entry['app'].get()
            }
            # Save mute toggle hotkey
            new_settings[f'{app}_mute'] = {
                'hotkey': entry['mute'].get(),
                'app_name': entry['app'].get()
            }
        
        # Save overlay setting
        new_settings['overlay_enabled'] = self.overlay_var.get()
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(new_settings, f, indent=4)
            # Close the window directly
            self.window.destroy()
        except Exception as e:
            # Create error messagebox
            msg_window = tk.Toplevel(self.window)
            msg_window.title("Error")
            msg_window.geometry("300x100")
            msg_window.configure(bg=self.bg_color)
            
            # Set icon
            try:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image.ico")
                if os.path.exists(icon_path):
                    msg_window.iconbitmap(icon_path)
            except Exception as e:
                print(f"Could not set messagebox icon: {e}")
            
            # Add message
            msg_label = tk.Label(msg_window, 
                               text=f"Failed to save settings: {str(e)}",
                               bg=self.bg_color,
                               fg=self.fg_color)
            msg_label.pack(pady=10)
            
            # Add OK button
            ok_button = tk.Button(msg_window,
                                text="OK",
                                command=msg_window.destroy,
                                bg=self.button_bg,
                                fg=self.button_fg,
                                relief=tk.FLAT,
                                padx=10,
                                pady=5)
            ok_button.pack(pady=10)
            
            # Center the messagebox
            msg_window.update_idletasks()
            width = msg_window.winfo_width()
            height = msg_window.winfo_height()
            x = (msg_window.winfo_screenwidth() // 2) - (width // 2)
            y = (msg_window.winfo_screenheight() // 2) - (height // 2)
            msg_window.geometry(f'{width}x{height}+{x}+{y}')
            
            # Make messagebox modal
            msg_window.transient(self.window)
            msg_window.grab_set()
    
    def reset_to_defaults(self):
        for app, entry in self.entries.items():
            entry['app'].set(self.default_settings[app]['app_name'])
            entry['down'].set(self.default_settings[app]['down'])
            entry['up'].set(self.default_settings[app]['up'])
            entry['mute'].set(self.default_settings[app]['mute'])
        self.overlay_var.set(True)
    
    def restart_application(self):
        self.window.destroy()
        
        # Start a new instance of the application
        python = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        subprocess.Popen([python, script_path])
        
        # Terminate the current process
        os._exit(0) 