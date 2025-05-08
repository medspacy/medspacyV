# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import sys
import logging
import base64
from PIL import Image, ImageTk
from io import BytesIO
import subprocess
import shutil
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from helper.annotations import AnnotationViewer
import helper.constants as CNST

# Setting up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class View(tk.Tk):
    """Creates and manages the main GUI window for the MedSpaCy application.

    This class is responsible for setting up and displaying the user interface, 
    including tabs for configuring the NLP pipeline, entering concepts, adjusting 
    advanced settings, and selecting directories for input/output. It also manages 
    events and actions related to the UI components.
    
    Args:
        tk (module): The tkinter module for creating GUI elements.
    """
    def __init__(self):
        """Initializes the View object and sets up the window and tabs.
        """
        super().__init__()
        self.title("MedSpaCy: A visual interface for the medspacy NLP pipeline")
        self.geometry("1200x600")

        tab_control = ttk.Notebook(self)
        self.tab1 = ttk.Frame(tab_control)
        self.tab3 = ttk.Frame(tab_control)
        tab_control.add(self.tab1, text="Configure and Run the Pipeline")
        tab_control.add(self.tab3, text="About")
        tab_control.pack(expand=1, fill="both")

        self.project_path = ""
        self.project_resources_dir = ""
        self.input_dir = ""
        self.output_dir = ""
        self.output_folder = ""
        self.output_dir_initial = ""
        self.log_file_path = ""

        self.initialize_logfile()
        self.use_existing_output = tk.BooleanVar()
        self.csv_file_check = tk.BooleanVar()
        self.create_tab1_contents()
        self.create_tab3()

        self.logger = logging.getLogger(__name__)

    def create_tab1_contents(self):
        """Creates the contents of the first tab (Configure and Run the Pipeline). 

        This method sets up all the UI elements on the first tab, including project 
        selection, concepts editing, advanced settings for sentence splitter, 
        section detector, and negation detector, as well as input directory selection.
        """
        # Adjust font size for labels and buttons
        font_size = 12
        
        # Add some margin space
        margin_x = 15
        margin_y = 5
        
        # one empty row
        label_empty_row = tk.Label(self.tab1, text="")
        label_empty_row.grid(row=0, column=0, columnspan=4, padx=margin_x, pady=margin_y)
        
        row1 = 1
    
        # Project Section
        label_create_project = tk.Label(self.tab1, text="Please select or create your project folder:", font=("Helvetica", font_size))
        label_create_project.grid(row=row1, column=0, columnspan=2, sticky="w", padx=margin_x, pady=margin_y)
        btn_create_project = tk.Button(self.tab1, text="Create or Open a Project", font=("Helvetica", font_size), command=self.create_or_open_project)
        btn_create_project.grid(row=row1, column=1, columnspan=1, sticky="ew", padx=margin_x, pady=margin_y)        
        self.label_project_path = tk.Label(self.tab1, text="Project Path: ", font=("Helvetica", font_size-2), width=80, anchor="w", justify="left", wraplength=500)
        self.label_project_path.grid(row=row1, column=2, columnspan=6, sticky="w", padx=margin_x, pady=margin_y)

        # Concepts Section
        label_enter_concepts = tk.Label(self.tab1, text="Enter or edit the concepts of your project: ", font=("Helvetica", font_size))
        label_enter_concepts.grid(row=row1+1, column=0, sticky="w", padx=margin_x, pady=margin_y)
        
        btn_enter_concepts = tk.Button(self.tab1, text="Create/Update Concepts", font=("Helvetica", font_size), command=self.enter_concepts)
        btn_enter_concepts.grid(row=row1+1, column=1, columnspan=1, sticky="ew", padx=margin_x, pady=margin_y)

        # Advanced Settings Section
        label_advanced_settings = tk.Label(self.tab1, text="Advanced Settings:", font=("Helvetica", font_size, "underline"))
        label_advanced_settings.grid(row=row1+2, column=0, columnspan=4, sticky="w", padx=margin_x, pady=margin_y)
        label_advanced_settings.bind("<Button-1>", lambda event: label_advanced_settings.focus_set())
        label_advanced_settings.bind("<FocusIn>", lambda event: label_advanced_settings.config(text="Advanced Settings:", font=("Helvetica", font_size, "underline")))
        label_advanced_settings.bind("<FocusOut>", lambda event: label_advanced_settings.config(text="Advanced Settings:", font=("Helvetica", font_size)))

        label_adjust_sent_tokenizer = tk.Label(self.tab1, text="Adjust the sentence splitter", font=("Helvetica", font_size))
        label_adjust_sent_tokenizer.grid(row=row1+3, column=0, sticky="e", padx=margin_x, pady=margin_y)
        btn_adjust_sent_tokenizer = tk.Button(self.tab1, text="Edit Sentence Rules", font=("Helvetica", font_size), command=self.adjust_sent_tokenizer)
        btn_adjust_sent_tokenizer.grid(row=row1+3, column=1, sticky="ew", padx=margin_x, pady=margin_y)

        label_adjust_sectionizer = tk.Label(self.tab1, text="Adjust the section detector", font=("Helvetica", font_size))
        label_adjust_sectionizer.grid(row=row1+4, column=0, sticky="e", padx=margin_x, pady=margin_y) 
        btn_adjust_sectionizer = tk.Button(self.tab1, text="Edit Section Rules", font=("Helvetica", font_size), command=self.adjust_sectionizer)
        btn_adjust_sectionizer.grid(row=row1+4, column=1, sticky="ew", padx=margin_x, pady=margin_y)

        label_negation_detector = tk.Label(self.tab1, text="Adjust the negation detector", font=("Helvetica", font_size))
        label_negation_detector.grid(row=row1+5, column=0, sticky="e", padx=margin_x, pady=margin_y) 
        btn_negation_detector = tk.Button(self.tab1, text="Edit Negation Rules", font=("Helvetica", font_size), command=self.adjust_negation_rules)
        btn_negation_detector.grid(row=row1+5, column=1, sticky="ew", padx=margin_x, pady=margin_y)
    
        # Directory Selection Section
        input_dir_label = tk.Label(self.tab1, text="Select the directory with your input documents:", font=("Helvetica", font_size), width=37)
        input_dir_label.grid(row=row1+6, column=0, sticky="w", padx=margin_x, pady=margin_y)
        
        self.input_dir_entry = tk.Entry(self.tab1)
        self.input_dir_entry.grid(row=row1+6, column=1, sticky="ew", columnspan=4, padx=margin_x, pady=margin_y)
        
        input_dir_browse_btn = tk.Button(self.tab1, text="Browse", font=("Helvetica", font_size), command=self.browse_input_directory)
        input_dir_browse_btn.grid(row=row1+6, column=5, sticky="w", padx=margin_x, pady=margin_y)

        self.checkbox_csv_file = tk.Checkbutton(self.tab1, text="Use CSV as input", variable=self.csv_file_check, font=("Helvetica", font_size - 2))
        self.checkbox_csv_file.grid(row=row1+7, column=1, sticky="w", padx=margin_x, pady=margin_y)

        icon_base64 = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAA6NJREFUSEuNll1sk2UUx3+nb7u5rYyxCgubCUzH6GBu0c1gYqLohRpDuBnykS0xQowooDbERBMTinKzLME5mcGPxAuCKDdzhMRoMBg+NpULA0HYQGcYA6ayuNUWun68xzwthW62fTmX5z3n/z9fzzmvkEuC6lpeTkXcwwIrzjMqrACWIPgUEGUCuCjKT7aLo26bsV/vY4q1kpwNJzMUqlK9k5J5XhbbFlsV1gK+nEHcUYYF9gGfeRIMn3lTItn2dwhUxd9LpcZYLcJbQH2uaNwWeFxgK0QTty0U5Sou3ku4OPDbaxLKfEkT3AKXKJvUYhfgyRV1sRtaqqH+XvgzDN9dhKSpWUaUKRW6rCI+OLdFwkadIqgOaumcctaJ8HE+cGNX5YXP22BRBVy4DlsOwdV//xfKPy4hyCR7zwUlJpiGevEnLfpylSXbvaYc+trBZGIy2HEEBi/n7NA1oG0oIIOyfLdW2sIuhVccmsmcYtjQBA9WwYUJ6D8Po5M5vW6i9CXcbJT6D9XvSnDCaVpEoMQNJR5SRNcjEI4VDOmawvPSsFtfV6G7kKklYMrz+GJ4qAbC0/DuUUjaBQlCCHvE/75+AWzIZ2rAH/DBjqegsQqKLLgSgvaD6T4UkLjCcUNwCmjNZ+grhXdWQmgamhbCEh+cHYf1Xzl1LDWjf4i/W0dQavOZm3qvWgonL8GBdeke9A/Bzu/vggBGZWm3jkgBAgNjyvLYIvhoNUxFoXsAvjxzlwROJTIwJouXH4FNrfB3BLYdhtNm0h1E4XfHJhuM+WXQswqaF6bnvm0/ROJO8MRRTjiOqdkltZXQ32FWFgxchs1fO4IbgxDKHtODJlFOAt5cbve44ek66HwWIjHYfxo+OQVGP3EjD5GgajPmctGRvSo2Z5ZftlupB9Y0wttPwGQUen8EjwWNC2D7N3kIlKgK/cMBWS8cVKvhCs2qHEKome3iLYIXW+DVFekMjl+Chvmw75d0NjnEvO8R4KWhgPyQWtdNXVoW89CBTSfC3GwnQ/DCw9DenD4y5vV2HoOfx/KCjyt0DQcktX5uX7S6Hi23kmwT2A7Mm12mlffDjRic/Su96PJEPg58OhSQYOb7jJu8rFe9xNloa+pkVgAljvMiKDbTCGMKvZnIcxIY5bKgFtlzaUHZivAkUHaLaPYZNS/hpipTCAMCe03NZwc0868i62tdjxZbSVpFeE6VR0WoRbGMiUJclFFgUFx8e/4NOZYv0/8AgMpGeaeHrRYAAAAASUVORK5CYII="
        icon_data = base64.b64decode(icon_base64)
        original_image = Image.open(BytesIO(icon_data))

        desired_size = (11, 11)
        resized_image = original_image.resize(desired_size, Image.LANCZOS)
        self.info_icon = ImageTk.PhotoImage(resized_image)

        self.tool_tip1 = tk.Label(self.tab1, image=self.info_icon, cursor="hand2")
        self.tool_tip1.grid(row=row1+7, column=1, sticky="nw", padx=(self.checkbox_csv_file.winfo_reqwidth() + 14, 0))

        self.create_tooltip(self.tool_tip1, "If checked, the program will process the CSV file present in the input folder. \nPlease make sure the CSV file contains two mandatory columns `doc_name` and `note_text`, \nwhich should have contents unique to each row. Additional columns are allowed and will be \ndirectly copied over in the output.")

        # self.csv_file_label = tk.Label(self.tab1, text="(Note: )", font=("Helvetica", font_size - 3), fg="gray")
        # self.csv_file_label.grid(row=row1+8, column=1, sticky="w", padx=margin_x, pady=margin_y)
    
        output_dir_label = tk.Label(self.tab1, text="Select the directory for your output results:", font=("Helvetica", font_size), width=32)
        output_dir_label.grid(row=row1+8, column=0, sticky="w", padx=margin_x, pady=margin_y)
        
        self.output_dir_entry = tk.Entry(self.tab1)
        self.output_dir_entry.grid(row=row1+8, column=1, sticky="ew", columnspan=4, padx=margin_x, pady=margin_y)
        
        output_dir_browse_btn = tk.Button(self.tab1, text="Browse", font=("Helvetica", font_size), command=self.browse_output_directory)
        output_dir_browse_btn.grid(row=row1+8, column=5, sticky="w", padx=margin_x, pady=margin_y)

        self.checkbox_use_existing_output = tk.Checkbutton(self.tab1, text="Use existing output", variable=self.use_existing_output, font=("Helvetica", font_size - 2))
        self.checkbox_use_existing_output.grid(row=row1+9, column=1, sticky="w", padx=margin_x+2, pady=margin_y)

        # Adding info tool tip
        self.tool_tip2 = tk.Label(self.tab1, image=self.info_icon, cursor="hand2")
        self.tool_tip2.grid(row=row1+9, column=1, sticky="nw",  padx=(self.checkbox_use_existing_output.winfo_reqwidth() + 14, 0))

        self.create_tooltip(self.tool_tip2, "If checked, the program will visualize the NLP results from the output path specified above. \nPlease also make sure the original source texts are present in the specified input folder, \nand with the box `Use CSV as input` checked accordingly if that was used instead of TXT files.")

        self.label_note_xlsx = tk.Label(self.tab1, text="(Note: Only .xlsx output files are accepted)", font=("Helvetica", font_size - 3), fg="gray")
        self.label_note_xlsx.grid(row=row1+10, column=1, sticky="w", padx=margin_x, pady=margin_y)
        # self.label_note_xlsx.grid_remove()

        # progress Bar
        self.progress = ttk.Progressbar(self.tab1, orient='horizontal', length=100, mode='determinate')
        self.progress.grid(row=row1+12, column=3, columnspan=2, sticky="ew", padx=margin_x, pady=margin_y)

        # progress Bar Label
        self.progress_label = tk.Label(self.tab1, text="0%", font=("Helvetica", font_size))
        self.progress_label.grid(row=row1+12, column=5, columnspan=2, sticky="ew", padx=margin_x, pady=margin_y)

        self.progress.grid_remove()
        self.progress_label.grid_remove()

        # Process Button
        self.btn_process_notes = tk.Button(self.tab1, text="Process Documents", font=("Helvetica", font_size,"bold"), command=self.process_notes, state=tk.NORMAL)
        self.btn_process_notes.grid(row=row1+12, column=1, columnspan=2, sticky="ew", padx=margin_x, pady=margin_y)
        
        # Review Annotated Documents
        self.btn_review_annotation_resuls = tk.Button(self.tab1, text="Review Annotated Documents", font=("Helvetica", font_size,"bold"), command=self.display_output_tab2, state=tk.DISABLED)
        self.btn_review_annotation_resuls.grid(row=row1+13, column=1, columnspan=2, sticky="ew", padx=margin_x, pady=margin_y)

        self.use_existing_output.trace_add("write", self.toggle_review_button)
        # self.csv_file_check.trace_add("write", self.toggle_csv_file_button)
        
        # Configure grid weights for equal distribution
        for i in range(60):  # Adjust based on the number of rows
            
            self.tab1.grid_rowconfigure(i, weight=1)
       
        for j in range(60):  # Adjust based on the number of columns
            self.tab1.grid_columnconfigure(j, weight=1)

        pass

    def initialize_logfile(self):
        """Initializes the log file for the application.

        This method checks if the log file exists, and if not, creates a new log file.
        It writes an initial log entry stating that the file is for error tracking.
        """
        open_directory = os.getcwd()
        initialdirectory = os.path.join(open_directory)
        initialdirectory=initialdirectory.replace('\\','/')
        self.log_file_path = os.path.join(initialdirectory, CNST.DEBUG_LOG_FILE)
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, "w") as f:
                f.write("Debug Log - Error Tracking - MedSpaCy\n\n")

    def log_error(self, error_type, error_message):
        """Logs an error message to the log file with a timestamp.

        Args:
            error_type (str): A brief description of the error type.
            error_message (str): Detailed message describing the error.
        """
        with open(self.log_file_path, "a") as f:
            timestamp = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
            f.write(f"[{timestamp}]\nError type: {error_type}\nError details: {error_message}\n\n")

    def create_tooltip(self, widget, text):
        """Creates a tooltip that appears when the user hovers over a widget.

        Args:
            widget (tk.Widget): The widget to attach the tooltip to.
            text (str): The text to display in the tooltip.
        """
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True) 
        label = tk.Label(tooltip, text=text, bg="#E3F2FD", relief="solid", borderwidth=1, font=("Helvetica", 10))
        label.pack(ipadx=5, ipady=2)

        def enter(event):
            """Displays the tooltip when the mouse enters the widget area.

            Args:
                event (tk.Event): The event that triggers the tooltip to appear.
            """
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def leave(event):
            """Hides the tooltip when the mouse leaves the widget area.

            Args:
                event (tk.Event): The event that triggers the tooltip to disappear.
            """
            tooltip.withdraw()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def toggle_review_button(self, *args):
        """Toggles the state of the review button based on the checkbox.

        Enables or disables the review button and the process notes button, 
        depending on whether the 'use existing output' checkbox is selected.
        """
        if self.use_existing_output.get():
            self.btn_review_annotation_resuls.config(state=tk.NORMAL)
            self.btn_process_notes.config(state=tk.DISABLED)
            # self.label_note_xlsx.grid()
        else:
            self.btn_review_annotation_resuls.config(state=tk.DISABLED)
            self.btn_process_notes.config(state=tk.NORMAL)
            # self.label_note_xlsx.grid_remove()
            if self.output_dir_initial:
                self.output_folder = ""
                self.output_dir_initial = ""
                self.output_dir_entry.delete(0, tk.END)

    def create_tab3(self):
        """Creates the 'About' tab in the user interface.

        This method sets up the content for the third tab, including displaying 
        information about the MedSpaCy application, its origin, and purpose.
        """
        # Create an empty row
        self.empty_row2 = tk.Label(self.tab3, text="      ")
        self.empty_row2.grid(column=0, row=0, sticky='w')
        
        label_font = ("Arial", 14, "bold")
        full_text = (
            "The MedSpaCy is a desktop application developed by the Mayo Clinic's "
            "Center for Clinical and Translational Science (CCaTS) Informatics Team. It "
            "offers a visual interface for the open-source medspacy natural language "
            "processing package (https://github.com/medspacy/medspacy)."
        )

        self.about_label = tk.Label(self.tab3, text=full_text, font=label_font, justify="left", wraplength=1000)
        self.about_label.grid(column=2, row=1, columnspan=5, sticky='n', padx=20, pady=20)


    # Tab1 Commands
    def create_or_open_project(self):
        """Opens a project directory or creates a new one.

        This method allows the user to either select an existing project directory 
        or create a new one. It also sets up necessary directories and files, 
        such as creating a "resources" folder if it doesn't exist.
        """
        # Get the directory where the main Python script is located
        script_directory = os.path.dirname(os.path.abspath(__file__))
        open_directory = os.getcwd()
        initialdirectory = os.path.join(open_directory)
        initialdirectory=initialdirectory.replace('\\','/')
        self.project_path = filedialog.askdirectory(title="Open an existing project directory or create a new folder for a new project", initialdir=initialdirectory, mustexist=True)

        if self.project_path:
            self.output_dir_initial = self.project_path

            self.update_project_path_label()
            # Check if the "resources" folder exists in the project directory
            self.project_resources_dir = os.path.join(self.project_path, "resources")
            if (not os.path.exists(self.project_resources_dir)) or (not os.listdir(self.project_resources_dir)):
                # Create the "resources" folder
                os.makedirs(self.project_resources_dir, exist_ok=True)
                try:
                    # Copy files from the source "resources" folder to the project "resources" folder
                    source_resources_dir = os.path.join(script_directory, "resources")

                    for file_name in os.listdir(source_resources_dir):
                        source_file = os.path.join(source_resources_dir, file_name)
                        if os.path.isfile(source_file):
                            shutil.copy(source_file, self.project_resources_dir)
                    #print("the resources were copied")        
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy resource files for your project: {e}") 
                    self.log_error("Issues with selecting directory", f"Failed to copy resource files for your project: {e}") 
        self.update_rule_file_paths()
        self.output_dir_entry.delete(0, tk.END)        
        self.output_dir_entry.insert(0, self.project_path)  # Set default value 

    def adjust_sent_tokenizer(self):
        """Allows the user to edit the sentence tokenizer rules.

        This method checks if the project resources directory exists, and if so, 
        opens the sentence rule file using Notepad for editing. It logs an error 
        if the project directory is not selected.
        """
        if self.project_resources_dir == "":
            messagebox.showerror("Error", "Project directory not selected!")
            self.log_error("Issues with selecting directory", "Project directory not selected!")
            return
        
        sent_rules_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_SENTENCE_RULE)
        if os.path.exists(sent_rules_file):
            subprocess.Popen(['notepad.exe', sent_rules_file], creationflags=subprocess.CREATE_NO_WINDOW)

    def adjust_sectionizer(self):
        """Allows the user to edit the sectionizer rules.

        This method checks if the project resources directory exists, and if so, 
        opens the section rule file using Notepad for editing. If the file is not 
        found, it logs the error and shows an error message.
        """
        if not self.project_resources_dir:
            messagebox.showerror("Error", "Project directory not selected!")
            self.log_error("Issues with selecting directory", "Project directory not selected!")
            return

        sections_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_SECTIONS_RULE)
        if os.path.exists(sections_file):
            subprocess.Popen(['notepad.exe', sections_file], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            messagebox.showerror("Error", f"I can't find {CNST.RESOURCE_SECTIONS_RULE} file in the project resources")
            self.log_error("Issues with resource files", f"I can't find {CNST.RESOURCE_CONTEXT_RULES} file in the project resources")

    def adjust_negation_rules(self):
        """Allows the user to edit the negation detection rules.

        This method checks if the project resources directory exists, and if so, 
        opens the negation rule file using Notepad for editing. If the file is not 
        found, it logs the error and shows an error message.
        """
        if not self.project_resources_dir:
            messagebox.showerror("Error", "Project directory not selected!")
            self.log_error("Issues with selecting directory", "Project directory not selected!")
            return

        negation_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_CONTEXT_RULES)
        if os.path.exists(negation_file):
            subprocess.Popen(['notepad.exe', negation_file], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            messagebox.showerror("Error", f"I can't find {CNST.RESOURCE_CONTEXT_RULES} file in the project resources")
            self.log_error("Issues with resource files", f"I can't find {CNST.RESOURCE_CONTEXT_RULES} file in the project resources")

    def enter_concepts(self):
        """Allows the user to enter or edit the concepts file.

        This method opens the concepts file in Excel. If the file doesn't exist, 
        it creates a new one with the appropriate headers and opens it in Excel.
        """
        if not self.project_resources_dir:
            messagebox.showerror("Error", "Project directory not selected!")
            self.log_error("Issues with selecting directory", "Project directory not selected!")
            return
        
        concepts_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_CONCEPTS)
        concepts_file=concepts_file.replace('\\','/')
        if os.path.exists(concepts_file):
            subprocess.Popen(['start', 'excel.exe', concepts_file], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            messagebox.showinfo("Info", f"Creating {CNST.RESOURCE_CONCEPTS} file...")
            df = pd.DataFrame(columns=["CONCEPT_ID", "CONCEPT", "TERM", "IS_REGULAR_EXPRESSION", "IS_CASE_SENSITIVE"])
            df.to_excel(concepts_file, index=False)
            subprocess.Popen(['start', 'excel.exe', concepts_file], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        self.update_concept_label(concepts_file)
        
    def update_concept_label(self, concepts_file):
        """Updates the label to display the path of the concepts file.

        Args:
            concepts_file (str): The path of the concepts file to display.
        """
        # Remove the label if it already exists
        if hasattr(self, 'concept_label'):
            self.concept_label.destroy()
    
        # Create the label to display the path
        self.concept_label = tk.Label(self.tab1, text=concepts_file, width=80, anchor="w")
        self.concept_label.grid(row=2, column=2, columnspan=6, sticky="w", padx=15, pady=5)    

    def update_rule_file_paths(self):
        """Updates the labels to display the paths of various rule files.

        This method checks if the required rule files exist in the project resources 
        directory. It then updates the displayed paths, indicating whether the 
        files are found or not.
        """
        if not self.project_resources_dir:
            return

        sent_rules_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_SENTENCE_RULE)
        section_rules_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_SECTIONS_RULE)
        negation_rules_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_CONTEXT_RULES)
        concepts_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_CONCEPTS)

        concepts_file=concepts_file.replace('\\','/')
        sent_rules_file = sent_rules_file.replace('\\', '/')
        section_rules_file = section_rules_file.replace('\\', '/')
        negation_rules_file = negation_rules_file.replace('\\', '/')

        if hasattr(self, 'concept_label'):
            self.concept_label.destroy()
        file_status = concepts_file if os.path.exists(concepts_file) else 'File not found'
        self.concept_label = tk.Label(self.tab1, text=file_status, width=90, anchor="w", justify="left", wraplength=500)
        self.concept_label.grid(row=2, column=2, columnspan=6, sticky="w", padx=15, pady=5)

        if hasattr(self, 'label_sent_rules_path'):
            self.label_sent_rules_path.destroy()
        file_status = sent_rules_file if os.path.exists(sent_rules_file) else 'File not found'
        self.label_sent_rules_path = tk.Label(self.tab1, text=f"{file_status}", width=90, anchor="w", justify="left", wraplength=500)
        self.label_sent_rules_path.grid(row=4, column=2, columnspan=6, sticky="w", padx=15, pady=5)

        if hasattr(self, 'label_section_rules_path'):
            self.label_section_rules_path.destroy()
        file_status = section_rules_file if os.path.exists(section_rules_file) else 'File not found'
        self.label_section_rules_path = tk.Label(self.tab1, text=f"{file_status}", width=90, anchor="w", justify="left", wraplength=500)
        self.label_section_rules_path.grid(row=5, column=2, columnspan=6, sticky="w", padx=15, pady=5)

        if hasattr(self, 'label_negation_rules_path'):
            self.label_negation_rules_path.destroy()
        file_status = negation_rules_file if os.path.exists(negation_rules_file) else 'File not found'
        self.label_negation_rules_path = tk.Label(self.tab1, text=f"{file_status}", width=90, anchor="w", justify="left", wraplength=500)
        self.label_negation_rules_path.grid(row=6, column=2, columnspan=6, sticky="w", padx=15, pady=5)
                  
    def browse_input_directory(self):
        """Allows the user to browse and select the input directory.

        This method opens a directory selection dialog and updates the input directory entry with the selected directory.
        """
        directory = filedialog.askdirectory()
        if directory:
            self.input_dir_entry.delete(0, tk.END)
            self.input_dir_entry.insert(tk.END, directory)
            self.input_dir = directory

    def browse_output_directory(self):
        """Allows the user to browse and select the output directory.

        This method opens a directory selection dialog and updates the output directory entry with the selected directory.
        """
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(tk.END, directory)
            self.output_dir = directory
            self.output_dir_initial = directory
            self.output_folder = ""

    def set_controller(self, controller):
        """Sets the controller for the View.

        Args:
            controller (Controller): The controller object that handles interactions between the view and the model.
        """
        self.controller = controller     
            
           
    def update_project_path_label(self):
        """Updates the project path label with the selected project path.

        This method updates the label that displays the current project path. It ensures that the project path is displayed in a formatted manner within the UI.
        """
        # Update project_path_label with the selected project path
        if self.project_path:
            max_length = 90  # Define maximum length for displayed path
            project_path_text = f"Project Path: {self.project_path}"
            formatted_text = project_path_text.ljust(90)
            self.label_project_path.config(text=formatted_text)
            

    def process_notes(self):    
        """Processes the clinical notes based on the selected project and resources.

        This method performs the following tasks:
        - Verifies the existence of necessary directories and files (input, output, project resources).
        - Reads and processes the concepts file.
        - Validates the input files (CSV or TXT) based on the user's settings.
        - Calls the processing function in the controller.
        - Displays messages and logs errors based on the processing results.

        It also handles the creation and management of output directories and reports.
        """
        if self.output_dir_initial:
            self.output_folder = ""
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, self.output_dir_initial)

        self.progress.grid()
        self.progress_label.grid()

        if not self.project_path:
            messagebox.showerror("Error", "Project directory not selected!")
            self.log_error("Issues with selecting directory", "Project directory not selected!")
            return

        concepts_file = os.path.join(self.project_resources_dir, CNST.RESOURCE_CONCEPTS)
        if not os.path.exists(concepts_file):
            messagebox.showerror("Error", f"Concepts file ({CNST.RESOURCE_CONCEPTS}) not found!")
            self.log_error("Issues with the resources file", f"Concepts file ({CNST.RESOURCE_CONCEPTS}) not found!")
            return

        df = pd.read_excel(concepts_file)
        df.columns = df.columns.str.strip()
        df = df.iloc[:, :5]
        df.columns=['CONCEPT_ID', 	'CONCEPT_CATEGORY',	'TERM_OR_REGEX','CASE_SENSITIVITY',"REGULAR_EXPRESSION"]
        
        df = df.dropna(subset=['CONCEPT_ID', 'CONCEPT_CATEGORY']).drop_duplicates()

        if df.empty:
            messagebox.showerror("Error", f"Concepts file ({CNST.RESOURCE_CONCEPTS}) is empty!")
            self.log_error("Issues with the resources file", f"Concepts file ({CNST.RESOURCE_CONCEPTS}) is empty!")
            return

        self.input_dir = self.input_dir_entry.get().replace('\\', '/')
        self.output_dir = self.output_dir_entry.get().replace('\\', '/')

        if not self.input_dir or not self.output_dir:
            messagebox.showerror("Error", "Input and Output directories are required!")
            self.log_error("Issues with selecting the directory","Input and Output directories are required!")
            return
        
        
        if self.csv_file_check.get():
            csv_files = [f for f in os.listdir(self.input_dir) if f.endswith('.csv')]
            if not csv_files:
                messagebox.showerror(
                    "Error",
                    "No CSV files found in the input folder, but 'Use CSV as input' is checked. "
                    "Please ensure that your input folder contains the necessary CSV files."
                )

                self.log_error("There are no CSV file in the given input folder, since you checked the 'Use CSV as input' CSV files must be present in the input folder.",
                            "Please double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                return
        else:
            txt_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.txt')]
            if not txt_files:
                messagebox.showerror(
                    "Error",
                    "No TXT files found in the input folder, but 'Use CSV as input' is not checked. "
                    "If your input files are CSVs, please check the 'Use CSV as input' box."
                )
                self.log_error(
                            "There are no TXT file in the given input folder, since you unchecked the 'Use CSV as input' TXT files must be present in the input folder.",
                            "Please double-check your input path contains the exact CSV or TXT files used for generating the output XLSX."
                )
                return
                

        self.project_resources_dir = self.project_resources_dir.replace('\\', '/')
        self.output_folder = ""
        self.controller.process_notes(self.input_dir, self.output_dir, self.project_resources_dir, self.project_path, self.csv_file_check.get())

        if self.output_folder == "EMPTY":
            self.output_folder = ""
            messagebox.showinfo("Info", "No concepts has been matched with the clinical notes!")
            return
        elif not self.output_folder:
            messagebox.showerror("Error", "Failed to process notes!")
            self.log_error("Issues with processing the document","Failed to process notes!")
            return
        
        self.btn_review_annotation_resuls.config(state="normal")
        messagebox.showinfo("Info", "Processing complete. Annotation is ready!")
        self.output_dir_entry.delete(0, tk.END)
        self.output_dir_entry.insert(tk.END, self.output_folder)

    def display_output_tab2(self):
        """Displays the output results in a new window.

        This method performs the following tasks:
        - Verifies if input and output directories contain the required files.
        - If the "Use existing output" option is selected, it validates the output files in the specified folder.
        - Checks for missing input-output file correspondences and reports errors.
        - Displays the processed results in a new window using the `AnnotationViewer` class.
        """
        try:
            new_window = None

            if not self.input_dir:
                self.logger.info(self.input_dir)
                messagebox.showerror("Error", "Please select an input directory first.")
                self.log_error("Issues with selecting the directory","Please select an input directory first.")
                return
            
            if not os.listdir(self.input_dir):
                messagebox.showerror("Error", "Input directory does not contain processed results.")
                self.log_error("Issues with selecting the directory","Input directory does not contain processed results.")
                return
            
            if not self.output_dir:
                self.logger.info(self.output_dir)
                messagebox.showerror("Error", "Please select an output directory first.")
                self.log_error("Issues with selecting the directory","Please select an output directory first.")
                return
            
            if not os.listdir(self.output_dir):
                messagebox.showerror("Error", "Output directory does not contain processed results.")
                self.log_error("Issues with selecting the directory","Output directory does not contain processed results.")
                return

            input_filenames = {os.path.splitext(f)[0] for f in os.listdir(self.input_dir)}
            output_doc_ids = set()

            if self.use_existing_output.get():
                if self.output_folder:
                    self.output_dir = self.output_folder
                
                output_file = []
                xlsx_files = [file for file in os.listdir(self.output_dir) if file.endswith(".xlsx")]
                if not xlsx_files:
                    messagebox.showerror("Error", "Output Folder doesn't contain output files. Please see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause.")
                    self.log_error("Output Folder doesn't contain output files.","Missing .xlsx ouput files in the output, please provide the output folder with .xlsx output files in it.")
                    return
                for file in xlsx_files:
                    file_path = os.path.normpath(os.path.join(self.output_dir, file))
                    df = pd.read_excel(file_path)
                    missing_columns = [col for col in CNST.OUTPUT_HEADERS if col not in df.columns]
                    if len(missing_columns) > 0:
                        messagebox.showerror("Error", "The columns in the output XLSX don't look right, or there is no record in it. Please see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause.")
                        self.log_error("The columns in the output XLSX don't look right, or there is no record in it.", f"The headers of the output file doesn't match the original columns which are: \n{', '.join(CNST.OUTPUT_HEADERS)}")
                        return
                    
                    if df["doc_name"].dropna().astype(str).str.strip().empty:
                        messagebox.showerror("Error", "The columns in the output XLSX don't look right, or there is no record in it. Please see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause.")
                        self.log_error("The columns in the output XLSX don't look right, or there is no record in it.","The output file is empty because no matches were found for the given concepts in the input notes. \nPlease review the concepts and input data or verify that you have selected the correct output folder.")
                        return
                        

                    for doc_id in df["doc_name"].astype(str).unique():
                        output_doc_ids.add(doc_id)
                    output_file.append(file)

                if self.csv_file_check.get():
                    if "csv" not in output_file[0].split(".")[0]:
                        messagebox.showerror("Error", "The input and output files do not correspond correctly to each other. Please double-check if the 'Use CSV as input' box is correctly (un)checked. \nPlease see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause.")
                        self.log_error("The input and output files do not correspond correctly to each other.","You have selected 'Use CSV as input', but the specified output folder corresponds to processed .TXT file inputs. \nPlease double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                        return

                    csv_files = [f for f in os.listdir(self.input_dir) if f.endswith('.csv')]
                    if not csv_files:
                        messagebox.showerror(
                            "Error",
                            "The input and output files do not correspond correctly to each other. Please double-check if the 'Use CSV as input' box is correctly (un)checked. \nPlease see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause."
                        )
                        self.log_error("The input and output files do not correspond correctly to each other.",
                                    "There are no CSV file in the given input folder, since you checked the 'Use CSV as input' CSV files must be present in the input folder." +
                                    "\nPlease double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                        return
                    
                    input_doc_ids = set()
                    for csv_file in csv_files:
                        input_csv_path = os.path.normpath(os.path.join(self.input_dir, csv_file))
                        input_df = pd.read_csv(input_csv_path, usecols=["doc_name"])
                        for doc_id in input_df["doc_name"].astype(str).unique():
                            input_doc_ids.add(doc_id)

                    missing_files = output_doc_ids - input_doc_ids

                    if missing_files:
                        missing_list = list(missing_files)[:3]
                        truncated_message = "\n... [truncated at top 3]" if len(missing_files) > 3 else ""
                        messagebox.showerror(
                            "Error",
                            "The input and output files do not correspond correctly to each other. Please double-check if the 'Use CSV as input' box is correctly (un)checked. \nPlease see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause."
                        )
                        self.log_error("The input and output files do not correspond correctly to each other.",
                                    "Mismatch: Some input files do not have corresponding processed results in the output folder.\n" + 
                                    f"The following are not present in the input:\n\n" +
                                    "\n".join(missing_list) + truncated_message +
                                    "\nPlease double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                        return
                    
                else:
                    if "text" not in output_file[0].split(".")[0]:
                        messagebox.showerror("Error", "The input and output files do not correspond correctly to each other. 'Use CSV as input' box is correctly (un)checked. \nPlease see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause.")
                        self.log_error("The input and output files do not correspond correctly to each other.",
                                    "You have not selected 'Use CSV as input' to process the .TXT files, but the specified output folder corresponds to processed .CSV file inputs." +
                                    "\nPlease double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                        return
                    
                    txt_files = [f for f in os.listdir(self.input_dir) if f.endswith('.txt')]
                    if not txt_files:
                        messagebox.showerror(
                            "Error",
                            "The input and output files do not correspond correctly to each other. Please see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause."
                        )
                        self.log_error("The input and output files do not correspond correctly to each other.",
                                    "There are no TXT file in the given input folder, since you unchecked the 'Use CSV as input' CSV files must be present in the input folder." +
                                    "\nPlease double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                        return
                    
                    input_filenames = {os.path.splitext(f)[0]+os.path.splitext(f)[1] for f in os.listdir(self.input_dir)}
                    missing_files =  output_doc_ids - input_filenames

                    if missing_files:
                        missing_list = list(missing_files)[:3]
                        truncated_message = "\n... [truncated at top 3]" if len(missing_files) > 3 else ""

                        messagebox.showerror(
                            "Error",
                            "The input and output files do not correspond correctly to each other. Please see the debug.log file in the same folder as your Controller.exe of MedSpaCyV for possible cause."
                        )
                        self.log_error("The input and output files do not correspond correctly to each other.",
                                    "Mismatch: Some input files do not have corresponding processed results in the output folder.\n" + 
                                    f"The following are not present in the input:\n\n" +
                                    "\n".join(missing_list) + truncated_message +
                                    "\nPlease double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                        return
                
                new_window = tk.Toplevel(self)
                annotation_viewer = AnnotationViewer(new_window, self.output_dir, self.input_dir, self.csv_file_check.get())
            else:
                if not self.output_folder:
                    messagebox.showerror("Error", "Please select an output directory first.")
                    return

                if self.csv_file_check.get():
                    csv_files = [f for f in os.listdir(self.input_dir) if f.endswith('.csv')]
                    if not csv_files:
                        messagebox.showerror(
                            "Error",
                            "No CSV files found in the input folder, but 'Use CSV as input' is checked. "
                            "Please ensure that your input folder contains the necessary CSV files."
                        )

                        self.log_error("There are no CSV file in the given input folder, since you checked the 'Use CSV as input' CSV files must be present in the input folder.",
                                    "Please double-check your input path contains the exact CSV or TXT files used for generating the output XLSX.")
                        return
                else:
                    txt_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.txt')]
                    if not txt_files:
                        messagebox.showerror(
                            "Error",
                            "No TXT files found in the input folder, but 'Use CSV as input' is not checked. "
                            "If your input files are CSVs, please check the 'Use CSV as input' box."
                        )
                        self.log_error(
                                    "There are no TXT file in the given input folder, since you unchecked the 'Use CSV as input' TXT files must be present in the input folder.",
                                    "Please double-check your input path contains the exact CSV or TXT files used for generating the output XLSX."
                        )
                        return
                
                new_window = tk.Toplevel(self)
                annotation_viewer = AnnotationViewer(new_window, self.output_folder, self.input_dir, self.csv_file_check.get())
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while displaying the output: {str(e)}")

    def reset_progress(self):
        """Resets the progress bar to 0 and updates the progress label.

        This method is typically used to reset the progress bar and label 
        to their initial state before starting a new operation or process.
        """
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.update_idletasks()
    
    def update_progress(self, value, prog):
        """Updates the progress bar and label with the current progress.

        Args:
            value (float): The current value of the progress (0 to 100).
            prog (str): A description or label to be displayed alongside the progress percentage.
        
        This method is typically used to update the progress bar and the associated 
        label as the process progresses, showing the current value and progress description.
        """
        self.progress['value'] = value
        self.progress_label.config(text=f"{prog} : {int(value)}%")
        self.update()
        self.update_idletasks()

# Example usage of the Model class
if __name__ == "__main__":
    view = View()
    view.mainloop()
