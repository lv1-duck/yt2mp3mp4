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
import queue

# Thread-safe communication queue
progress_queue = queue.Queue()

#Helper function to locate bundled files in both dev and PyInstaller modes
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    return os.path.join(base_path, relative_path)

ffmpeg_bin_path = resource_path('ffmpeg/bin')

# Dict for configuration
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
progress_bar = None
progress_label = None
is_cancelled = False

def setup_app():
    customtkinter.set_appearance_mode(CONFIG['appearance_mode'])
    customtkinter.set_default_color_theme(CONFIG['color_theme'])

def create_progress_bar(parent):
    global progress_bar, progress_label
    progress_bar = customtkinter.CTkProgressBar(parent, width=400)
    progress_bar.set(0)
    progress_bar.pack(pady=10)
   
    progress_label = customtkinter.CTkLabel(parent, text="Starting download...")
    progress_label.pack(pady=5)

def update_progress(percentage, status_text=None):
    if progress_bar and progress_label:
        progress_bar.set(percentage / 100)
        if status_text:
            progress_label.configure(text=status_text)
        else:
            progress_label.configure(text=f"Downloading... {percentage:.1f}%")

def hide_progress_bar():
    global progress_bar, progress_label
    if progress_bar:
        progress_bar.destroy()
        progress_bar = None
    if progress_label:
        progress_label.destroy()
        progress_label = None

def show_progress_error(message):
    if progress_label:
        progress_label.configure(text=f"Error: {message}")

# This runs in the main thread to process queue messages
def process_queue():
    try:
        while True:
            msg = progress_queue.get_nowait()
            if msg['type'] == 'progress':
                update_progress(msg['percentage'], msg.get('status'))
            elif msg['type'] == 'create':
                create_progress_bar(window)
            elif msg['type'] == 'hide':
                hide_progress_bar()
            elif msg['type'] == 'error':
                show_progress_error(msg['message'])
            elif msg['type'] == 'complete':
                messagebox.showinfo("Download Complete", msg['message'])
                hide_progress_bar()
    except queue.Empty:
        pass
    
    # Check queue again every 100ms
    window.after(100, process_queue)

def make_ytdlp_progress_hook():
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
                downloaded_mb = d.get('downloaded_bytes', 0) / (1024 * 1024)
                percent = 0
                status_text = f"Downloading... {downloaded_mb:.1f} MB"
            
            if 'speed' in d and d['speed']:
                speed_mb = d['speed'] / (1024 * 1024)
                status_text += f" ({speed_mb:.1f} MB/s)"
            
            progress_queue.put({
                'type': 'progress',
                'percentage': percent,
                'status': status_text
            })
            
        elif d['status'] == 'finished':
            filename = os.path.basename(d.get('filename', 'file'))
            progress_queue.put({
                'type': 'progress',
                'percentage': 100,
                'status': f"Finished: {filename}"
            })
            
        elif d['status'] == 'error':
            error_msg = str(d.get('error', 'Unknown error'))
            progress_queue.put({
                'type': 'error',
                'message': error_msg
            })
    
    return progress_hook

def create_main_window():
    global window
    window = customtkinter.CTk()
    window.geometry(CONFIG['window_size'])
    window.title(CONFIG['title'])
    
    # Start the queue processing loop
    window.after(100, process_queue)
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
    progress_queue.put({'type': 'hide'})
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
        ydl_opts = {'quiet': True, 'no_warnings': True}
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

def download_audio(url: str, output_path: str):
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
            'noplaylist': True,
            'progress_hooks': [make_ytdlp_progress_hook()]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return True, "Audio downloaded successfully!"
    except Exception as e:
        return False, f"Error downloading audio: {e}"

def download_video(url: str, output_path: str):
    try:
        ydl_opts = {
            'ffmpeg_location': ffmpeg_bin_path,
            'format': 'best[height<=720]/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'progress_hooks': [make_ytdlp_progress_hook()]
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
    try:
        # Notify main thread to create progress bar
        progress_queue.put({'type': 'create'})
        
        if download_type == 'mp3':
            success, msg = download_audio(url, output_path)
        else:
            success, msg = download_video(url, output_path)
        
        if success:
            progress_queue.put({'type': 'complete', 'message': msg})
        else:
            progress_queue.put({'type': 'error', 'message': msg})
    except Exception as e:
        progress_queue.put({'type': 'error', 'message': str(e)})

def start_download(url: str, file_type: str):
    path = choose_download_path(file_type)
    if not path:
        return
        
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