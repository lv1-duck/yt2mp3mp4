import customtkinter
import tkinter as tk
from tkinter import messagebox, filedialog
from io import BytesIO
from pytubefix import YouTube
from PIL import Image, ImageTk
import requests
import threading
from pathlib import Path

# Import our progress manager
import progress_manager

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


def create_main_window():
    global window
    window = customtkinter.CTk()
    window.geometry(CONFIG['window_size'])
    window.title(CONFIG['title'])
    return window


def clear_dynamic_elements():
    """Destroy all widgets we listed in dynamic_widgets, then empty the list."""
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
    """Clear everything on screen + hide any progress bar + reset URL."""
    clear_dynamic_elements()
    clear_url_entry()
    progress_manager.hide_progress_bar()
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
    """Return (success, info_or_error). info is a dict with title/thumbnail_url/author/length."""
    try:
        yt = YouTube(url)
        return True, {
            'title': yt.title,
            'thumbnail_url': yt.thumbnail_url,
            'author': yt.author,
            'length': yt.length
        }
    except Exception as e:
        return False, str(e)


def download_audio(url: str, output_path: str, progress_callback=None):
    """Download audio only, with optional progress callback."""
    try:
        yt = YouTube(url, on_progress_callback=progress_callback) if progress_callback else YouTube(url)
        stream = yt.streams.get_audio_only()
        if not stream:
            return False, "No audio stream available"
        stream.download(output_path=output_path)
        return True, "Audio downloaded successfully!"
    except Exception as e:
        return False, f"Error downloading audio: {e}"


def download_video(url: str, output_path: str, progress_callback=None):
    """Download highest‐res video, with optional progress callback."""
    try:
        yt = YouTube(url, on_progress_callback=progress_callback) if progress_callback else YouTube(url)
        stream = yt.streams.get_highest_resolution()
        if not stream:
            return False, "No video stream available"
        stream.download(output_path=output_path)
        return True, "Video downloaded successfully!"
    except Exception as e:
        return False, f"Error downloading video: {e}"


def create_title_label(parent, title: str):
    """Show “Title: …” on the screen, and remember to destroy later."""
    lbl = customtkinter.CTkLabel(
        master=parent,
        text=f"Title: {title}",
        font=("Helvetica", 16),
        fg_color="#1e2c42",
        corner_radius=20,
        wraplength=500
    )
    lbl.pack(pady=10)
    dynamic_widgets.append(lbl)


def create_thumbnail_label(parent, thumbnail_url: str):
    """Fetch the thumbnail over HTTP, resize it, and show it. Append to dynamic_widgets."""
    try:
        resp = requests.get(thumbnail_url, timeout=10)
        img_data = BytesIO(resp.content)
        img = Image.open(img_data).resize(CONFIG['thumbnail_size'], Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        lbl = tk.Label(master=parent, image=img_tk, background="#1e2c42")
        lbl.image = img_tk
        lbl.pack(pady=10)
        dynamic_widgets.append(lbl)
    except Exception as e:
        show_error(f"Could not load thumbnail: {e}")


def create_download_buttons(parent, url: str):
    """
    Show two buttons: “Download as MP3” and “Download as MP4”.
    When clicked, they start a background thread.
    """
    frame = customtkinter.CTkFrame(master=parent)
    frame.pack(pady=10)

    btn_mp3 = customtkinter.CTkButton(
        master=frame,
        text="Download as MP3",
        command=lambda: start_download(url, 'mp3')
    )
    btn_mp4 = customtkinter.CTkButton(
        master=frame,
        text="Download as MP4",
        command=lambda: start_download(url, 'mp4')
    )

    btn_mp3.pack(side="left", padx=5)
    btn_mp4.pack(side="left", padx=5)
    dynamic_widgets.append(frame)


def show_error(msg: str):
    """Display a red error box at the top, and remember to destroy it later."""
    lbl = customtkinter.CTkLabel(
        master=window,
        text=f"Error: {msg}",
        font=("Helvetica", 14),
        fg_color="#ff4c4c",
        corner_radius=20
    )
    lbl.pack(pady=10)
    dynamic_widgets.append(lbl)


def choose_download_path(file_type: str) -> str:
    """
    Ask the user for a folder. If they cancel, return the default.
    file_type is either 'mp3' or 'mp4'.
    """
    default = CONFIG['default_mp3_path'] if file_type == 'mp3' else CONFIG['default_mp4_path']
    chosen = filedialog.askdirectory(
        title=f"Choose folder to save {file_type.upper()} file",
        initialdir=default
    )
    return chosen if chosen else default


def perform_download_task(url: str, output_path: str, download_type: str):
    """
    Runs in a background thread. Creates a progress bar, downloads,
    then calls show_download_result_and_cleanup on the main thread.
    """
    progress_manager.create_progress_bar(window)
    callback = progress_manager.make_progress_callback(window)

    if download_type == 'mp3':
        success, msg = download_audio(url, output_path, callback)
    else:
        success, msg = download_video(url, output_path, callback)

    # Schedule GUI update on the main thread
    window.after(0, show_download_result_and_cleanup, success, msg)


def show_download_result_and_cleanup(success: bool, message: str):
    """After download finishes (or fails), show a messagebox and hide the progress bar."""
    if success:
        messagebox.showinfo("Download Complete", message)
        progress_manager.auto_hide_after_seconds(window, 3)
    else:
        messagebox.showerror("Download Failed", message)
        progress_manager.show_error(message)
        progress_manager.auto_hide_after_seconds(window, 5)


def start_download(url: str, file_type: str):
    """Called when user clicks “Download as MP3/MP4”."""
    path = choose_download_path(file_type)
    thread = threading.Thread(
        target=perform_download_task,
        args=(url, path, file_type),
        daemon=True
    )
    thread.start()


def fetch_and_display_video_info(url: str):
    """
    Runs in a background thread: fetches title/thumbnail.
    Then schedules update_video_display(...) on the main thread.
    """
    success, result = get_video_info(url)
    window.after(0, update_video_display, success, result)


def update_video_display(success: bool, result):
    """
    If fetching was successful, show title + thumbnail + download buttons.
    Otherwise show an error box.
    """
    if success:
        # result is a dict with 'title' and 'thumbnail_url'
        create_title_label(window, result['title'])
        create_thumbnail_label(window, result['thumbnail_url'])
        create_download_buttons(window, current_url)
    else:
        show_error(result)


def search_video():
    """Called when user clicks “Search”. Validate URL, then clear old UI + fetch info."""
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
    """Place header, URL entry, and Search/Clear buttons."""
    header = customtkinter.CTkLabel(
        master=parent,
        text="Convert YouTube videos to MP3/MP4 files",
        font=("Helvetica", 20),
        fg_color="#1e2c42",
        corner_radius=20
    )
    header.pack(pady=10)
    dynamic_widgets.append(header)

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
    dynamic_widgets.extend([btn_frame, search_btn, clear_btn])


def main():
    setup_app()
    main_win = create_main_window()
    build_main_interface(main_win)
    main_win.mainloop()


if __name__ == "__main__":
    main()
