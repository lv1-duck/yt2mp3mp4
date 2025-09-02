"""
Simplified GUI: restored to your original structure but cleaned up a little and pinned to `pytubefix`.
- Uses pytubefix.YouTube as you requested (no pytube fallback)
- Keeps the same global-style UI state and functions (restart, check, download_to_mp3)
- No threading, no ffmpeg conversion — downloads the audio stream file that pytubefix returns
- Keeps thumbnail display and prevents the image from being garbage-collected

Dependencies:
    pip install customtkinter pytubefix requests pillow

"""

import tkinter
from tkinter import messagebox
import customtkinter

# Using pytubefix as requested
from pytubefix import YouTube
import requests
from PIL import Image, ImageTk
from io import BytesIO

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")
window = customtkinter.CTk()

current_title_label = None
current_thumbnail_label = None
download_mp4 = None
error_label = None
thumbnail_image_ref = None


def restart():
    global current_title_label, current_thumbnail_label, download_mp4, error_label, thumbnail_image_ref
    if current_title_label:
        try:
            current_title_label.destroy()
        except Exception:
            pass
        current_title_label = None
    if current_thumbnail_label:
        try:
            current_thumbnail_label.destroy()
        except Exception:
            pass
        current_thumbnail_label = None
    if download_mp4:
        try:
            download_mp4.destroy()
        except Exception:
            pass
        download_mp4 = None
    if error_label:
        try:
            error_label.destroy()
        except Exception:
            pass
        error_label = None
    thumbnail_image_ref = None


def download_to_mp3(link):
    """Download the audio-only stream. This keeps behavior similar to your original code and uses pytubefix.
    Note: pytubefix typically downloads the audio in its original container (eg .webm). If you need a true
    .mp3 conversion we can add ffmpeg later.
    """
    try:
        if not link:
            messagebox.showinfo(title="Download failed", message="No URL provided.")
            return

        yt = YouTube(link)
        # get_audio_only api mirrors
        ys = yt.streams.get_audio_only()
        # download returns path to the downloaded file
        out_path = ys.download() # type: ignore
        messagebox.showinfo(title="Download complete", message=f"Downloaded: {out_path}")
    except Exception as e:
        messagebox.showinfo(title="Download failed", message=f"Error in downloading: {e}")


def check(entry_val):
    global current_title_label, current_thumbnail_label, download_mp4, error_label, thumbnail_image_ref

    url = entry_val.get().strip()
    restart()
    try:
        if not url:
            raise ValueError("Please enter a YouTube URL.")

        yt = YouTube(url)
        title = getattr(yt, 'title', '(no title)')
        thumbnail_url = getattr(yt, 'thumbnail_url', None)

        current_title_label = customtkinter.CTkLabel(window, text=f"Title: {title}",
                                                     font=("helvetica", 20),
                                                     fg_color="#1e2c42",
                                                     corner_radius=20,
                                                     wraplength=500)
        current_title_label.pack(pady=8)

        # Fetch and display thumbnail
        if thumbnail_url:
            try:
                response = requests.get(thumbnail_url, timeout=5)
                response.raise_for_status()
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
                img = img.resize((320, 180))
                tkimg = ImageTk.PhotoImage(img)

                current_thumbnail_label = tkinter.Label(window, image=tkimg)
                current_thumbnail_label.image = tkimg  # pyright: ignore[reportAttributeAccessIssue]
                thumbnail_image_ref = tkimg
                current_thumbnail_label.pack(pady=10)
            except Exception as img_err:
                # thumbnail fetch failed; continue without it
                print("Thumbnail fetch error:", img_err)

        # Add download button (keeps original naming)
        download_mp4 = customtkinter.CTkButton(window, text="Download as mp3", command=lambda: download_to_mp3(url))
        download_mp4.pack(pady=10)

    except Exception as e:
        error_label = customtkinter.CTkLabel(window, text=f"Error: {e}",
                                             font=("helvetica", 16),
                                             fg_color="#ff4c4c",
                                             corner_radius=20)
        error_label.pack(pady=10)


def main():
    window.geometry("720x480")
    window.title("YT to Mp3")

    prompt_link = customtkinter.CTkLabel(window, text="Convert YouTube video to Mp3 file.",
                                         font=("helvetica", 20),
                                         fg_color="#1e2c42",
                                         corner_radius=20)

    url = tkinter.StringVar()
    entry = customtkinter.CTkEntry(window, placeholder_text="Input URL of the YouTube video",
                                   width=500,
                                   textvariable=url)

    button_frame = customtkinter.CTkFrame(window)
    check_button = customtkinter.CTkButton(button_frame, text="Search", command=lambda: check(url))
    another_button = customtkinter.CTkButton(button_frame, text="Refresh", command=restart)

    prompt_link.pack(pady=10, padx=10)
    entry.pack()
    button_frame.pack(pady=10)
    check_button.pack(side="left", padx=5)
    another_button.pack(side="left", padx=5)
    window.mainloop()


if __name__ == "__main__":
    main()
