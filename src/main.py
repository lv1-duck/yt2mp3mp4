import customtkinter
import tkinter as tk
from tkinter import messagebox, filedialog
from io import BytesIO
import yt_dlp
from PIL import Image, ImageTk
import requests
import threading
from pathlib import Path
import os
import sys

venv_base = os.path.dirname(sys.executable)  # Points to venv\Scripts\python.exe

# Path to your extracted ffmpeg\bin
ffmpeg_bin_path = os.path.join(venv_base, '..', 'ffmpeg', 'bin')
ffmpeg_bin_path = os.path.abspath(ffmpeg_bin_path)

# Prepend to PATH
os.environ['PATH'] = ffmpeg_bin_path + os.pathsep + os.environ['PATH']

# Configuration
CONFIG = {
    'window_size': "720x640",
    'title': "YouTube to MP3/MP4",
    'thumbnail_size': (500, 360),
    'default_mp3_path': str(Path.home() / "Music"),
    'default_mp4_path': str(Path.home() / "Videos"),
    'appearance_mode': "dark",
    'color_theme': "blue"
}

window = None
url_entry = None
current_url = ""
dynamic_widgets = [] 

def setup_app():
    customtkinter.set_appearance_mode(CONFIG['appearance_mode'])
    customtkinter.set_default_color_theme(CONFIG['color_theme'])

#just some state variables to track progress UI
progress_bar = None
progress_label = None
is_cancelled = False

def create_progress_bar(parent):
    global progress_bar, progress_label, is_cancelled
   
    is_cancelled = False
   
    #Create progress bar
    progress_bar = customtkinter.CTkProgressBar(parent, width=400)
    progress_bar.set(0)
    progress_bar.pack(pady=10)
   
    #Create label
    progress_label = customtkinter.CTkLabel(parent, text="Starting download...")
    progress_label.pack(pady=5)

def update_progress(percentage, status_text=None):
    global progress_bar, progress_label
   
    if progress_bar and progress_label:
        #Update bar (needs 0-1, not 0-100)
        progress_bar.set(percentage / 100)
       
        #Update status
        if status_text:
            progress_label.configure(text=status_text)
        elif percentage < 100:
            progress_label.configure(text=f"Downloading... {percentage:.1f}%")
        else:
            progress_label.configure(text="Download complete!")

def hide_progress_bar():
    global progress_bar, progress_label
   
    if progress_bar:
        progress_bar.destroy()
        progress_bar = None
   
    if progress_label:
        progress_label.destroy()
        progress_label = None

def show_progress_error(message):
    global progress_label
   
    if progress_label:
        progress_label.configure(text=f"Error: {message}")

def make_ytdlp_progress_hook(window):
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            #Calculate percentage
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
                #No total size available
                downloaded_mb = d.get('downloaded_bytes', 0) / (1024 * 1024)
                percent = 0
                status_text = f"Downloading... {downloaded_mb:.1f} MB"
            
            #if available
            if 'speed' in d and d['speed']:
                speed_mb = d['speed'] / (1024 * 1024)
                status_text += f" ({speed_mb:.1f} MB/s)"
            
            #Update UI
            window.after(0, update_progress, percent, status_text)
            
        elif d['status'] == 'finished':
            filename = d.get('filename', 'file')
            window.after(0, update_progress, 100, f"Finished downloading: {filename}")
            
        elif d['status'] == 'error':
            error_msg = str(d.get('error', 'Unknown error'))
            window.after(0, lambda: show_progress_error(error_msg))
    
    return progress_hook

def auto_hide_after_seconds(window, seconds=3):
    window.after(seconds * 1000, hide_progress_bar)

def create_main_window():
    global window
    window = customtkinter.CTk()
    window.geometry(CONFIG['window_size'])
    window.title(CONFIG['title'])
    return window

def clear_dynamic_elements():
    global dynamic_widgets
    for w in dynamic_widgets:
        try:
            w.destroy()
        except:
            pass
    dynamic_widgets.clear()

def clear_url_entry():
    global url_entry
    if url_entry:
        url_entry.delete(0, tk.END)

def reset_app():
    clear_dynamic_elements()
    clear_url_entry()
    hide_progress_bar()
    global current_url
    current_url = ""

def validate_youtube_url(url: str):
    if not url or not url.strip():
        return False, "Please enter a URL"
    lower = url.strip().lower()
    if 'youtube.com' not in lower and 'youtu.be' not in lower:
        return False, "Please enter a valid YouTube URL"
    return True, ""

def get_video_info(url: str):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return True, {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail_url': info.get('thumbnail', ''),
                'author': info.get('uploader', 'Unknown Author'),
                'length': info.get('duration', 0)
            }
    except Exception as e:
        return False, str(e)

def download_audio(url: str, output_path: str, hook_func=None):
    try:
        ydl_opts = {
            'ffmpeg_location': ffmpeg_bin_path,
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [hook_func] if hook_func else [],
            'noplaylist': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return True, "Audio downloaded successfully!"
    except Exception as e:
        return False, f"Error downloading audio: {e}"

def download_video(url: str, output_path: str, hook_func=None):
    try:
        ydl_opts = {
            'ffmpeg_location': ffmpeg_bin_path,
            'format': 'best[height<=720]/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [hook_func] if hook_func else [],
            'noplaylist': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return True, "Video downloaded successfully!"
    except Exception as e:
        return False, f"Error downloading video: {e}"

def create_title_label(parent, title: str):
    label = customtkinter.CTkLabel(
        master=parent,
        text=f"Title: {title}",
        font=("Helvetica", 16),
        fg_color="#1e2c42",
        corner_radius=20,
        wraplength=500
    )
    label.pack(pady=10)
    dynamic_widgets.append(label)

def create_thumbnail_label(parent, thumbnail_url: str):
    try:
        resp = requests.get(thumbnail_url, timeout=10)
        img_data = BytesIO(resp.content)
        img = Image.open(img_data).resize(CONFIG['thumbnail_size'], Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        label = tk.Label(master=parent, image=img_tk, background="#1e2c42")
        label.image = img_tk
        label.pack(pady=10)
        dynamic_widgets.append(label)
    except Exception as e:
        show_error(f"Could not load thumbnail: {e}")

def create_download_buttons(parent, url: str):
    frame = customtkinter.CTkFrame(master=parent)
    frame.pack(pady=10)

    button_mp3 = customtkinter.CTkButton(
        master=frame,
        text="Download as MP3",
        command=lambda: start_download(url, 'mp3')
    )
    button_mp4 = customtkinter.CTkButton(
        master=frame,
        text="Download as MP4",
        command=lambda: start_download(url, 'mp4')
    )

    button_mp3.pack(side="left", padx=5)
    button_mp4.pack(side="left", padx=5)
    dynamic_widgets.append(frame)

def show_error(msg: str):
    label = customtkinter.CTkLabel(
        master=window,
        text=f"Error: {msg}",
        font=("Helvetica", 14),
        fg_color="#ff4c4c",
        corner_radius=20
    )
    label.pack(pady=10)
    dynamic_widgets.append(label)

def choose_download_path(file_type: str) -> str:
    default = CONFIG['default_mp3_path'] if file_type == 'mp3' else CONFIG['default_mp4_path']
    chosen = filedialog.askdirectory(
        title=f"Choose folder to save {file_type.upper()} file",
        initialdir=default
    )
    return chosen if chosen else default

def perform_download_task(url: str, output_path: str, download_type: str):
    window.after(0, create_progress_bar, window)
    
    #Create progress hook
    hook_function = make_ytdlp_progress_hook(window)

    if download_type == 'mp3':
        success, msg = download_audio(url, output_path, hook_function)
    else:
        success, msg = download_video(url, output_path, hook_function)

    #Schedule GUI update on main thread
    window.after(0, lambda: show_download_result_and_cleanup(success, msg))

def show_download_result_and_cleanup(success: bool, message: str):
    if success:
        messagebox.showinfo("Download Complete", message)
        auto_hide_after_seconds(window, 3)
    else:
        messagebox.showerror("Download Failed", message)
        window.after(0, lambda: show_progress_error(message))
        auto_hide_after_seconds(window, 5)

def start_download(url: str, file_type: str):
    path = choose_download_path(file_type)
    thread = threading.Thread(
        target=perform_download_task,
        args=(url, path, file_type),
        daemon=True
    )
    thread.start()

def fetch_and_display_video_info(url: str):
    success, result = get_video_info(url)
    window.after(0, lambda: update_video_display(success, result))

def update_video_display(success: bool, result):
    if success:
        create_title_label(window, result['title'])
        create_thumbnail_label(window, result['thumbnail_url'])
        create_download_buttons(window, current_url)
    else:
        show_error(result)

def search_video():
    url = url_entry.get().strip()
    ok, msg = validate_youtube_url(url)
    if not ok:
        messagebox.showwarning("Invalid URL", msg)
        return

    clear_dynamic_elements()
    global current_url
    current_url = url

    thread = threading.Thread(
        target=fetch_and_display_video_info,
        args=(url,),
        daemon=True
    )
    thread.start()

def build_main_interface(parent):
    header = customtkinter.CTkLabel(
        master=parent,
        text="Convert YouTube videos to MP3/MP4 files",
        font=("Helvetica", 20),
        fg_color="#1e2c42",
        corner_radius=20
    )
    header.pack(pady=10)

    global url_entry
    url_entry = customtkinter.CTkEntry(
        master=parent,
        placeholder_text="Enter YouTube URL here...",
        width=500
    )
    url_entry.pack(pady=10)

    btn_frame = customtkinter.CTkFrame(master=parent)
    btn_frame.pack(pady=10)

    search_btn = customtkinter.CTkButton(
        master=btn_frame, text="Search", command=search_video
    )
    clear_btn = customtkinter.CTkButton(
        master=btn_frame, text="Clear", command=reset_app
    )
    search_btn.pack(side="left", padx=5)
    clear_btn.pack(side="left", padx=5)

def check_ffmpeg_exists():
    ffmpeg = os.path.join(ffmpeg_bin_path, 'ffmpeg.exe')
    ffprobe = os.path.join(ffmpeg_bin_path, 'ffprobe.exe')
    return os.path.isfile(ffmpeg) and os.path.isfile(ffprobe)

def main():
    setup_app()
    main_win = create_main_window()
    build_main_interface(main_win)
    main_win.mainloop()

if __name__ == "__main__":
    if not check_ffmpeg_exists():
        messagebox.showerror("FFmpeg Missing", "FFmpeg binaries not found in expected path:\n" + ffmpeg_bin_path)
        sys.exit(1)
    main()