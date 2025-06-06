import customtkinter

# Simple variables to track progress UI
progress_bar = None
progress_label = None
is_cancelled = False

def create_progress_bar(parent):
    #Create a progress bar and label
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

def update_progress(percentage):
    #Update the progress bar
    global progress_bar, progress_label
    
    if progress_bar and progress_label:
        # Update bar (needs 0-1, not 0-100)
        progress_bar.set(percentage / 100)
        
        # Update text
        if percentage < 100:
            progress_label.configure(text=f"Downloading... {percentage:.1f}%")
        else:
            progress_label.configure(text="Download complete!")

def hide_progress_bar():
    #Remove the progress bar
    global progress_bar, progress_label
    
    if progress_bar:
        progress_bar.destroy()
        progress_bar = None
    
    if progress_label:
        progress_label.destroy()
        progress_label = None

def show_error(message):
    #Show error message on progress label
    global progress_label
    
    if progress_label:
        progress_label.configure(text=f"Error: {message}")

def make_progress_callback(window):
    #Create a callback function for pytubefix
    
    def progress_callback(stream, chunk, bytes_remaining):
        # Calculate percentage
        total_size = stream.filesize
        downloaded = total_size - bytes_remaining
        percentage = (downloaded / total_size) * 100
        
        # Update UI safely (must use window.after for threading)
        window.after(0, update_progress, percentage)
    
    return progress_callback

def auto_hide_after_seconds(window, seconds=3):
    #Hide progress bar after some seconds
    window.after(seconds * 1000, hide_progress_bar)