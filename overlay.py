import tkinter as tk
from PIL import Image, ImageTk
import win32gui
import win32process
import psutil
import os
import sys
import win32ui
import win32con
import win32api
from functools import lru_cache

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class VolumeOverlay:
    def __init__(self):
        # Create main volume change window
        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg='#2b2b2b')
        self.window.wm_attributes('-toolwindow', True)
        
        # Set fixed width for the window
        self.window.geometry("165x65")
        
        # Create main frame
        self.frame = tk.Frame(self.window, bg='#2b2b2b', padx=10, pady=0)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Left frame for icon
        self.left_frame = tk.Frame(self.frame, bg='#2b2b2b')
        self.left_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # App icon label
        self.icon_label = tk.Label(self.left_frame, bg='#2b2b2b')
        self.icon_label.pack()
        
        # Right frame for percentage and progress bar
        self.right_frame = tk.Frame(self.frame, bg='#2b2b2b')
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a spacer at the top
        tk.Frame(self.right_frame, height=2, bg='#2b2b2b').pack(fill=tk.X)
        
        # Container for percentage and progress bar
        self.content_frame = tk.Frame(self.right_frame, bg='#2b2b2b')
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 2))
        
        # Create a container for the label and progress bar
        self.text_container = tk.Frame(self.content_frame, bg='#2b2b2b')
        self.text_container.pack(fill=tk.BOTH, expand=True)
        
        # Volume percentage label
        self.volume_label = tk.Label(self.text_container, 
                                   text="0%", 
                                   font=('Segoe UI', 20, 'bold'),
                                   fg='#ffffff',
                                   bg='#2b2b2b',
                                   width=13,
                                   anchor='w')
        self.volume_label.pack(fill=tk.X)
        
        # Progress bar
        self.progress_bar = tk.Canvas(self.text_container, 
                                    height=4,
                                    bg='#2b2b2b',
                                    highlightthickness=0)
        self.progress_bar.pack(fill=tk.X)
        
        # Hide initially
        self.window.withdraw()
        
        # Fade animation variables
        self.fade_timer = None
        self.alpha = 1.0
        self.fade_duration = 300  # Duration in milliseconds
        self.fade_steps = 30  # Number of steps for smoother fade
        
        # Icon cache with size limit
        self.icon_cache = {}
        self.max_cache_size = 20  # Limit cache to 20 icons
        
        # Load disabled icon once
        try:
            self.disabled_icon = Image.open(resource_path("disabled.ico"))
        except Exception as e:
            print(f"Error loading disabled icon: {e}")
            self.disabled_icon = None
            
        # Create muted apps window
        self.muted_window = tk.Toplevel()
        self.muted_window.overrideredirect(True)
        self.muted_window.attributes('-topmost', True)
        self.muted_window.configure(bg='#000000')
        self.muted_window.wm_attributes('-toolwindow', True)
        self.muted_window.wm_attributes('-transparentcolor', '#000000')
        
        # Create frame for muted apps
        self.muted_frame = tk.Frame(self.muted_window, bg='#000000', padx=10, pady=5)
        self.muted_frame.pack(fill=tk.BOTH, expand=True)
        
        # Dictionary to store muted app icons
        self.muted_apps = {}
        
        # Position muted window
        self.muted_window.geometry("+5+20")
    
        # Pre-calculate common values
        self.ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        self.ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
        self.icon_scale = 1.5
        self.new_size = (int(self.ico_x * self.icon_scale), int(self.ico_y * self.icon_scale))

    def overlay_disabled_icon(self, base_img):
        """Overlay the disabled icon on the base image"""
        if self.disabled_icon is None:
            return base_img
            
        # Resize disabled icon to 50% of base image size
        disabled_size = (int(base_img.size[0] * 0.5), int(base_img.size[1] * 0.5))
        disabled_icon = self.disabled_icon.resize(disabled_size, Image.Resampling.LANCZOS)
        if disabled_icon.mode != 'RGBA':
            disabled_icon = disabled_icon.convert('RGBA')
            
        # Create a new image with alpha channel
        result = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
        
        # Paste the base image
        result.paste(base_img, (0, 0))
        
        # Calculate position for bottom right
        offset_x = int(base_img.size[0] * 0.5)
        offset_y = int(base_img.size[1] * 0.5)
        position = (offset_x, offset_y)
        
        # Overlay the disabled icon
        result.paste(disabled_icon, position, disabled_icon)
        
        return result
    
    @lru_cache(maxsize=32)
    def get_process_exe(self, app_name):
        """Get executable path for a process name with caching"""
        for proc in psutil.process_iter(['name', 'exe']):
            if proc.info['name'].lower() == app_name.lower():
                return proc.info['exe']
        return None

    def get_app_icon(self, app_name, is_muted=False):
        """Get the app icon with disabled overlay if needed"""
        # Check cache first
        cache_key = f"{app_name}_{'muted' if is_muted else 'normal'}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key], app_name
            
        try:
            if app_name == 'focused':
                hwnd = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                app_name = proc.name()
            
            # Get executable path using cached function
            exe_path = self.get_process_exe(app_name)
            if not exe_path:
                return None, app_name
            
            # Get icon
            large, small = win32gui.ExtractIconEx(exe_path, 0, 1)
            win32gui.DestroyIcon(small[0])
            
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, self.ico_x, self.ico_y)
            hdc = hdc.CreateCompatibleDC()
            
            hdc.SelectObject(hbmp)
            hdc.DrawIcon((0, 0), large[0])
            
            win32gui.DestroyIcon(large[0])
            
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGBA',
                (self.ico_x, self.ico_y),
                bmpstr, 'raw', 'BGRA', 0, 1
            )
            
            # Scale the image using pre-calculated size
            img = img.resize(self.new_size, Image.Resampling.LANCZOS)
            
            # If this is a muted icon, darken it
            if is_muted:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Use numpy for faster pixel manipulation if available
                try:
                    import numpy as np
                    data = np.array(img)
                    data[:, :, :3] = (data[:, :, :3] * 0.66).astype(np.uint8)
                    img = Image.fromarray(data)
                except ImportError:
                    # Fallback to slower method if numpy is not available
                    data = img.getdata()
                    new_data = [(int(r * 0.66), int(g * 0.66), int(b * 0.66), a) for r, g, b, a in data]
                    img.putdata(new_data)
                
            # Cache the icon with size limit
            if len(self.icon_cache) >= self.max_cache_size:
                # Remove oldest item
                self.icon_cache.pop(next(iter(self.icon_cache)))
            self.icon_cache[cache_key] = img
            
            return img, app_name
        except Exception as e:
            print(f"Error getting icon: {e}")
        return None, app_name
    
    def update_muted_apps(self, app_name, volume_percent):
        """Update the muted apps display"""
        if volume_percent == 0:
            if app_name not in self.muted_apps:
                img, _ = self.get_app_icon(app_name, is_muted=True)
                if img:
                    img = self.overlay_disabled_icon(img)
                    photo = ImageTk.PhotoImage(img)
                    label = tk.Label(self.muted_frame, image=photo, bg='#000000')
                    label.image = photo
                    label.pack(side=tk.LEFT, padx=5)
                    self.muted_apps[app_name] = label
                    self.muted_window.deiconify()
        else:
            if app_name in self.muted_apps:
                self.muted_apps[app_name].destroy()
                del self.muted_apps[app_name]
                if not self.muted_apps:
                    self.muted_window.withdraw()
    
    def update_progress_bar(self, volume_percent):
        """Update the progress bar to show current volume level"""
        if volume_percent >= 0:
            width = self.progress_bar.winfo_width()
            if width <= 1:
                self.progress_bar.update_idletasks()
                width = self.progress_bar.winfo_width()
            
            fill_width = int(width * volume_percent)
            
            # Draw background track (darker color)
            self.progress_bar.delete('all')
            self.progress_bar.create_rectangle(0, 0, width, 4, fill='#0f0f0f', outline='')
            
            # Draw current volume level (brighter color)
            self.progress_bar.create_rectangle(0, 0, fill_width, 4, fill='#ffffff', outline='')
        else:
            self.progress_bar.delete('all')

    def show(self, app_name, volume_percent):
        # Update muted apps display
        if volume_percent >= 0:
            self.update_muted_apps(app_name, volume_percent)
        
        # Get app icon and name
        img, app_name = self.get_app_icon(app_name, is_muted=False)
        
        # Position in top-left corner
        self.window.geometry("+10+80")
        
        # Cancel any existing fade timer
        if self.fade_timer:
            self.window.after_cancel(self.fade_timer)
        
        if volume_percent == -1:
            # Calculate required width based on text first
            temp_text = f"No audio source detected for {app_name}"
            self.volume_label.configure(
                text=temp_text,
                font=('Segoe UI', 16, 'bold'),
                width=0,
                anchor='w',
                pady=15
            )
            self.volume_label.update_idletasks()
            text_width = self.volume_label.winfo_reqwidth()
            window_width = max(300, text_width + 40)
            
            # Set window size before any other updates
            self.window.geometry(f"{window_width}x65")
            self.window.update_idletasks()
            
            # Update the content
            self.icon_label.configure(image='')
            self.volume_label.configure(
                text=temp_text,
                font=('Segoe UI', 16, 'bold'),
                width=0,
                anchor='w',
                pady=15
            )
            self.progress_bar.delete('all')
            
        elif img:
            # Reset to normal size for volume display
            self.window.geometry("165x65")
            self.window.update_idletasks()
            
            # Update the label
            photo = ImageTk.PhotoImage(img)
            self.icon_label.configure(image=photo)
            self.icon_label.image = photo
            
            self.volume_label.configure(
                text=f"{int(volume_percent * 100)}%",
                font=('Segoe UI', 20, 'bold'),
                width=13,
                anchor='w',
                pady=0
            )
            
            # Update progress bar
            self.update_progress_bar(volume_percent)
            
        else:
            # Calculate required width based on text first
            temp_text = f"No audio source detected for {app_name}"
            self.volume_label.configure(
                text=temp_text,
                font=('Segoe UI', 16, 'bold'),
                width=0,
                anchor='w',
                pady=15
            )
            self.volume_label.update_idletasks()
            text_width = self.volume_label.winfo_reqwidth()
            window_width = max(300, text_width + 40)
            
            # Set window size before any other updates
            self.window.geometry(f"{window_width}x65")
            self.window.update_idletasks()
            
            # Update the content
            self.icon_label.configure(image='')
            self.volume_label.configure(
                text=temp_text,
                font=('Segoe UI', 16, 'bold'),
                width=0,
                anchor='w',
                pady=15
            )
            self.progress_bar.delete('all')
        
        # Show window and set initial opacity
        self.alpha = 1.0
        self.window.attributes('-alpha', self.alpha)
        self.window.deiconify()
        
        # Start fade out timer
        self.fade_timer = self.window.after(1000, self.fade_out)
    
    def fade_out(self):
        """Fade out the window"""
        if self.fade_timer:
            self.window.after_cancel(self.fade_timer)
        
        def update_opacity():
            self.alpha -= 1.0 / self.fade_steps
            if self.alpha > 0:
                self.window.attributes('-alpha', self.alpha)
                self.fade_timer = self.window.after(self.fade_duration // self.fade_steps, update_opacity)
            else:
                self.window.withdraw()
                self.fade_timer = None
        
        self.fade_timer = self.window.after(self.fade_duration // self.fade_steps, update_opacity) 