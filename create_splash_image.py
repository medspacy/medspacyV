import tkinter as tk
from tkinter import ttk

def center_window(window, width, height):
    """Centers the window on the screen.

    Args:
        window (tk.Tk): The Tkinter window to be centered.
        width (int): The width of the window.
        height (int): The height of the window.
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_coordinate = (screen_width / 2) - (width / 2)
    y_coordinate = (screen_height / 2) - (height / 2)
    window.geometry("%dx%d+%d+%d" % (width, height, x_coordinate, y_coordinate))

def create_main_window():
    """Creates and displays the main window of the application with a label.

    The main window has a title, and a label is displayed with information 
    about the application. The window size is set to 600x300, and the window 
    is centered on the screen.
    """
    main_window = tk.Tk()
    main_window.title("medspacyV: A visual interface for the medspacy NLP pipeline")
    
    # Set larger window size
    window_width = 600
    window_height = 300
    center_window(main_window, window_width, window_height)
    
    label_font = ("Arial", 14, "bold")  # Bold and larger font for the label
    
    label = ttk.Label(main_window, 
                      text="\n\nmedspacyV:                                   \n\nA visual interface for the medspacy NLP pipeline                                   \n\nPlease wait while the application is loading ...                                   ", 
                      font=label_font,
                      anchor="center",
                      justify="center",)
    label.pack(padx=20, pady=20)
    
    main_window.mainloop()

if __name__ == "__main__":
    create_main_window()
