# ================ progress_manager.py ================
import customtkinter

# Simple variables to track progress UI
progress_bar = None
progress_label = None
is_cancelled = False

def create_progress_bar(parent):
    """Create a progress bar and label"""
    global progress_bar, progress_label, is_cancelled
   
    # Reset cancel flag
    is_cancelled = False
   
    # Create progress bar
    progress_bar = customtkinter.CTkProgressBar(parent, width=400)
    progress_bar.set(0)
    progress_bar.pack(pady=10)
   
    # Create label
    progress_label = customtkinter.CTkLabel(parent, text="Starting download...")
    progress_label.pack(pady=5)

def update_progress(percentage, status_text=None):
    """Update the progress bar"""
    global progress_bar, progress_label
   
    if progress_bar and progress_label:
        # Update bar (needs 0-1, not 0-100)
        progress_bar.set(percentage / 100)
       
        # Update text
        if status_text:
            progress_label.configure(text=status_text)
        elif percentage < 100:
            progress_label.configure(text=f"Downloading... {percentage:.1f}%")
        else:
            progress_label.configure(text="Download complete!")

def hide_progress_bar():
    """Remove the progress bar"""
    global progress_bar, progress_label
   
    if progress_bar:
        progress_bar.destroy()
        progress_bar = None
   
    if progress_label:
        progress_label.destroy()
        progress_label = None

def show_error(message):
    """Show error message on progress label"""
    global progress_label
   
    if progress_label:
        progress_label.configure(text=f"Error: {message}")

def make_ytdlp_progress_hook(window):
    """Create a progress hook function for yt-dlp"""
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            # Calculate percentage
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                total_mb = d['total_bytes'] / (1024 * 1024)
                downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                status_text = f"Downloading... {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)"
            elif 'total_bytes_estimate' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                status_text = f"Downloading... {percent:.1f}% (~{downloaded_mb:.1f} MB)"
            else:
                # No total size available
                downloaded_mb = d.get('downloaded_bytes', 0) / (1024 * 1024)
                percent = 0
                status_text = f"Downloading... {downloaded_mb:.1f} MB"
            
            # Add speed info if available
            if 'speed' in d and d['speed']:
                speed_mb = d['speed'] / (1024 * 1024)
                status_text += f" ({speed_mb:.1f} MB/s)"
            
            # Update UI safely
            window.after(0, update_progress, percent, status_text)
            
        elif d['status'] == 'finished':
            filename = d.get('filename', 'file')
            window.after(0, update_progress, 100, f"Finished downloading: {filename}")
            
        elif d['status'] == 'error':
            error_msg = str(d.get('error', 'Unknown error'))
            window.after(0, lambda: show_error(error_msg))
    
    return progress_hook

def auto_hide_after_seconds(window, seconds=3):
    """Hide progress bar after some seconds"""
    window.after(seconds * 1000, hide_progress_bar)