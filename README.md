# YouTube to MP3 Downloader

#### Video Demo: [https://youtu.be/pIa2eOqbX6U]

#### Description:

The Youtube to MP3 downloader is a graphical user interface (GUI) application made with python that is designed to convert YouTube videos into MP3 audio files. This project uses the `customtkinter` library because i think it looks cool.

To Download the MP3 files, we use `pytubefix` and `requests` library for video processing and downloading functionalities.

### Files and Their Functions

- **`project.py`**: This is the main file of the project. It contains:
The `main()` function, which initializes the GUI and sets up the application's window.
The `check()` function, which processes the YouTube URL, fetches video details, and updates the GUI with the video title and thumbnail.
The `restart()` function, which resets the GUI to its initial state, clearing previously displayed information.
The `download_to_mp3()` function, which handles the conversion of the YouTube video to an MP3 file using the `pytubefix`(just mentioning that i used this instead of pytube since pytube sadly doesn't work) library and notifies the user upon completion.
- **`test_project.py`**: We dont talk about this one, forget about this.
- **`requirements.txt`**: This file lists all the Python packages required to run the project. It includes `customtkinter`, `pytubefix`, `requests`, and `Pillow`.
- **Error Handling**: The application provides feedback to the user through dialog boxes in case of errors,I used f-strings to display the exact error given in the terminal so that the user is informed of any issues during the download process.

**Now lets tackle how this program works exactly**
The `main()` function activates or initializes our GUI which in our case is `Tkinter` and `Customtkniter`.
Our GUI elements consist of buttons, labels, a button frame, and an entrybox.Upon execution ,we would see an entrybox where we would should add the Youtube video URL and a search button which when clicked calls for the `check()` function.
In this function is where `pytubefix` and `requests` libraries does their purpose with help of the other to search for the Youtube video to confirm if the link is indeed valid.
In the event that the link it is invalid, the app packs a label, colored red, that states the link is indeed invalid.
When a valid link is provided, the `check()`function fetches the title and thumbnail of the video to then display it as their respective label areas. As i mentioned above ,the purpose of this is to have a way to confirm if the link provided is the URL to the expexted YouTube video.
At the same time the title and thumbnail are displayed, the app packs a new button.
This is the `download_to_mp3()` button which starts the downloading process, again using the `pytubefix` library.
If the download is successful, a message box pops up to inform the user that the file is sucessfully downloaded.
inversely, a message box also pops up if the download is unsucessful, the difference is it shows an error message.
Which in order to show an accurate source of the error,I used an f-string to show the exact error message printed in the terminal.

Now lets mention the `restart()` function, this function when activated uses the  `CTkinter.destroy` method to destroy existing labels below the entry and search,refresh widgets.
There are two ways this is activated, the first is when you click the `refresh` button beside search button.
The second instance this is activated is when there is a new input in entry box that is searched.
Technically, it also activates whenever you click the search button.

Now that i mention that, in order to fix this problem when the labels just accumulates when you click search button. In order to fix that, I just implemented the `refresh()` function so it deletes the existing labels and since clicking search button packs the title and thumbnail image display, so yeah that solved this problem.
