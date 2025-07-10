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

def resource_path(relative_path):
    #Get absolute path to resource, works for dev and for PyInstaller.
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, relative_path)

ffmpeg_binary_path = resource_path('ffmpeg/bin')

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
progress_bar = None
progress_label = None

def setup_app():
    customtkinter.set_appearance_mode(CONFIG['appearance_mode'])
    customtkinter.set_default_color_theme(CONFIG['color_theme'])

def show_progress_error(message):
    if progress_label:
        progress_label.configure(text=f"Error: {message}")

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
        except Exception:
            pass
    dynamic_widgets.clear()

def clear_url_entry():
    global url_entry
    if url_entry:
        url_entry.delete(0, tk.END)

def reset_app():
    clear_dynamic_elements()
    clear_url_entry()
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
            'ffmpeg_location': ffmpeg_binary_path,
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, "Audio downloaded successfully!"
    except Exception as e:
        return False, f"Error downloading audio: {e}"

def download_video(url: str, output_path: str):
    try:
        ydl_opts = {
            'ffmpeg_location': ffmpeg_binary_path,
            'format': 'best[height<=720]/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, "Video downloaded successfully!"
    except Exception as e:
        return False, f"Error downloading video: {e}"

def create_title_label(parent, title: str):
    """Create and display the video title label."""
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
    """Create and display the video thumbnail."""
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
        # Avoid duplicate error labels if thumbnail fails
        if not any(isinstance(w, customtkinter.CTkLabel) and "Could not load thumbnail" in str(w.cget("text")) for w in dynamic_widgets):
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
    """Display an error message label."""
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
    """Perform the download in a background thread and show result."""
    try:
        if download_type == 'mp3':
            success, msg = download_audio(url, output_path)
        else:
            success, msg = download_video(url, output_path)
        if success:
            messagebox.showinfo("Download Complete", msg)
        else:
            messagebox.showerror("Download Error", msg)
    except Exception as e:
        messagebox.showerror("Download Error", str(e))

def start_download(url: str, file_type: str):
    """Start the download in a new thread."""
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
    """Fetch video info and update UI (runs in thread)."""
    success, result = get_video_info(url)
    window.after(0, lambda: update_video_display(success, result))

def update_video_display(success: bool, result):
    """Update the UI with video info or error."""
    if success:
        create_title_label(window, result['title'])
        create_thumbnail_label(window, result['thumbnail_url'])
        create_download_buttons(window, current_url)
    else:
        show_error(result)

def search_video():
    """Handle search button click."""
    global current_url
    url = url_entry.get().strip()
    ok, msg = validate_youtube_url(url)
    if not ok:
        messagebox.showwarning("Invalid URL", msg)
        return
    clear_dynamic_elements()
    current_url = url
    thread = threading.Thread(
        target=fetch_and_display_video_info,
        args=(url,),
        daemon=True
    )
    thread.start()

def build_main_interface(parent):
    """Build the main UI interface."""
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
    """Check if ffmpeg and ffprobe binaries exist."""
    ffmpeg = os.path.join(ffmpeg_binary_path, 'ffmpeg.exe')
    ffprobe = os.path.join(ffmpeg_binary_path, 'ffprobe.exe')
    return os.path.isfile(ffmpeg) and os.path.isfile(ffprobe)

def main():
    """Main entry point."""
    setup_app()
    main_win = create_main_window()
    build_main_interface(main_win)
    main_win.mainloop()

if __name__ == "__main__":
    if not check_ffmpeg_exists():
        messagebox.showerror("FFmpeg Missing", "FFmpeg not found in expected path:\n" + ffmpeg_binary_path)
        sys.exit(1)
    main()