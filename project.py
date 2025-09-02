import tkinter
from tkinter import messagebox
import customtkinter

#Using these to download the mp3
from pytubefix import YouTube
import requests

#These are for displaying the thumbnail
from PIL import Image, ImageTk
from io import BytesIO


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")
window = customtkinter.CTk()

current_title_label = None
current_thumbnail_label = None
download_mp4 = None
error_label = None

def restart():
    global current_title_label, current_thumbnail_label, download_mp4, error_label
    if current_title_label:
        current_title_label.destroy()
        current_title_label = None
    if current_thumbnail_label:
        current_thumbnail_label.destroy()
        current_thumbnail_label = None
    if download_mp4:
        download_mp4.destroy()
        download_mp4 = None
    if error_label:
        error_label.destroy()
        error_label = None


def download_to_mp3(link):
    try:
        # Implement the actual download logic here
        yt = YouTube(link)
        ys = yt.streams.get_audio_only()
        ys.download(mp3=False)
        messagebox.showinfo(title="Download complete", message="Video downloaded successfully!")
    except Exception as e:
        messagebox.showinfo(title="Download failed", message=f"Error in downloading: {e}")

def check(entry_val):
    global current_title_label, current_thumbnail_label, download_mp4, error_label
    
    url = entry_val.get()
    restart()
    try:
        yt = YouTube(url)
        title = yt.title
        thumbnail_url = yt.thumbnail_url
        
        current_title_label = customtkinter.CTkLabel(window, text=f"Title: {title}",
                                                     font=("helvetica", 20),
                                                     fg_color="#1e2c42",
                                                     corner_radius=20,
                                                     wraplength=500)
        current_title_label.pack()

        # Fetch and display thumbnail
        response = requests.get(thumbnail_url)
        img_data = BytesIO(response.content)
        img = Image.open(img_data)
        img = img.resize((320, 180))
        img = ImageTk.PhotoImage(img)
        
        current_thumbnail_label = tkinter.Label(window, image=img)
        current_thumbnail_label.image = img
        current_thumbnail_label.pack(pady=10)

        # Add download button
        download_mp4 = customtkinter.CTkButton(window, text="Download as mp3", command=lambda: download_to_mp3(url))
        download_mp4.pack(pady=10)
    except Exception as e:
        error_label = customtkinter.CTkLabel(window, text=f"Error: {e}",
                                             font=("helvetica", 16),
                                             fg_color="#ff4c4c",
                                             corner_radius=20)
        error_label.pack(pady=10)

def main():
    dummy_function()
    dummy_function2()
    dummy_function3()
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

def dummy_function():
    return 1+1
def dummy_function2():
    return 1+2
def dummy_function3():
    return 1+3



    


if __name__ == "__main__":
    main()

