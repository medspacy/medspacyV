import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkfont  # Import the Font module
import pandas as pd
import os
import numpy as np
import helper.constants as CNST

class AnnotationViewer:
    def __init__(self, master, output_data, notes_dir, csv_file_chk):
        self.master = master
        self.master.title(f"Annotation Viewer - {output_data}")
        
        self.notes_dir = notes_dir
        self.csv_file_chk = csv_file_chk
        
        # Get screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        # Set default window size
        default_width = int(screen_width * 0.8)  # 80% of screen width
        default_height = int(screen_height * 0.8)  # 80% of screen height
        
        # Set window geometry
        self.master.geometry(f"{default_width}x{default_height}+{screen_width // 10}+{screen_height // 10}")

        # Create a PanedWindow to hold left and right panels, allowing them to be resized
        self.paned_window = tk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Adjusting left panel width to occupy one-fourth of the window
        left_panel_width = self.master.winfo_screenwidth() // 4.5

        # Left Panel: List of files
        self.left_frame = tk.Frame(self.paned_window, width=left_panel_width)
        self.paned_window.add(self.left_frame, minsize=200)
        # self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.columnconfigure(0, weight=1)
        self.left_frame.rowconfigure(1, weight=1)

        # Creating a font with larger size and bold style
        label_font = tkfont.Font(family="Arial", size=12, weight="bold")

        self.file_list_label = tk.Label(self.left_frame, text="Annotated Files:", font=label_font)
        self.file_list_label.grid(row=0, column=0, sticky="w")

        self.file_listbox = tk.Listbox(self.left_frame)
        self.file_listbox.grid(row=1, column=0, sticky="nsew")
        self.file_listbox.bind("<<ListboxSelect>>", self.load_annotation)
        
        # Adding scrollbar to the listbox
        scrollbar = tk.Scrollbar(self.left_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar_x = tk.Scrollbar(self.left_frame, orient="horizontal", command=self.file_listbox.xview)
        scrollbar_x.grid(row=2, column=0, sticky="we")
        self.file_listbox.config(xscrollcommand=scrollbar_x.set)

        self.back_button = tk.Button(self.left_frame, text="Back", command=self.load_previous_file)
        self.back_button.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.next_button = tk.Button(self.left_frame, text="Next", command=self.load_next_file)
        self.next_button.grid(row=2, column=0, sticky="e", padx=5, pady=5)

        self.right_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, minsize=200)
        # self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(0, weight=1)

        # Add a Text widget and a Scrollbar widget to the right frame        
        self.annotation_text = tk.Text(self.right_frame, wrap="word")
        self.annotation_text.grid(row=0, column=0, sticky="nsew")
        self.annotation_text.config(state="disabled")
        
        # Add a scrollbar to the right frame
        scrollbar = tk.Scrollbar(self.right_frame, orient="vertical", command=self.annotation_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        # Configure the scrollbar to scroll the annotation_text widget
        self.annotation_text.config(yscrollcommand=scrollbar.set)
        
        scrollbar_x = tk.Scrollbar(self.right_frame, orient="horizontal")
        scrollbar_x.grid(row=1, column=0, sticky="we")
        self.annotation_text.config(xscrollcommand=lambda *args: scrollbar_x.set(*args))

        scrollbar_x.config(command=self.annotation_text.xview)

        self.folder_path = output_data
        self.current_page = 0
        self.files_per_page = CNST.MAX_FILES_PER_PAGE
        self.file_paths = []
        # Load data from Excel file
        #self.annotation_data = pd.read_excel(r"H:\Projects\Fred_MedSpacy\test7\Fred_MedSpacy_2024-03-12_10-16-53.xlsx")
        self.load_data_in_folder(output_data)

        # Configure main grid row and column to expand with window
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=3)
        self.master.rowconfigure(0, weight=1)

        # Configure file_list_label to occupy exactly one row and one column
        self.left_frame.grid_propagate(False)
        
        # Additional Info Box
        self.additional_info_label = tk.Label(self.right_frame, text="", wraplength=200, justify="left")
        # self.additional_info_label.config(bg="yellow")  # Set background color
        self.additional_info_label.place_forget()  # Initially hide the label
        self.additional_info_label.bind("<Leave>", self.hide_additional_info)  # Bind leave event
        self.annotation_text.bind("<Motion>", self.show_additional_info)  # Bind motion event
        
        # self.unique_concepts = sorted(self.annotation_data['concept'].unique().tolist())
        self.concept_dict = self.create_concept_dict(self.annotation_data)
        print(f"Getting Concepts: {self.concept_dict}")
        self.concept_colors = self.assign_colors(self.concept_dict)
        # Save some information to display them later
        self.annotation_row=pd.DataFrame()
        self.current_page = 0

    def load_data_in_folder(self, output_data):

        output_data = output_data.replace('\\','/')

        self.file_paths = [os.path.join(output_data, f) for f in os.listdir(output_data) if f.endswith('.xlsx')]
        self.current_file_index = 0

        if self.file_paths:
            self.load_current_file()
        else:
            messagebox.showerror("Error", "No Excel files found in the specified folder.")

    def load_current_file(self):
        if not self.file_paths:
            return
        
        df = pd.read_excel(self.file_paths[self.current_file_index])
        doc_ids = df['doc_name'].unique()
        self.annotation_data = df[df['doc_name'].isin(doc_ids[:100])]
        self.file_list = self.annotation_data['doc_name'].unique().tolist()
        self.update_file_list_display()
        # Reset the annotation text display
        self.annotation_text.config(state="normal")
        self.annotation_text.delete(1.0, tk.END)
        self.annotation_text.config(state="disabled")
        
        self.update_navigation_buttons()

    def update_file_list_display(self):
        self.file_listbox.delete(0, tk.END)
        start_index = self.current_page * self.files_per_page
        end_index = start_index + self.files_per_page
        for file_name in self.file_list[start_index:end_index]:
            self.file_listbox.insert(tk.END, file_name)
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        total_pages = len(self.file_list) // self.files_per_page + (1 if len(self.file_list) % self.files_per_page != 0 else 0)
        if self.current_page == 0:
            self.back_button.config(state="disabled")
        else:
            self.back_button.config(state="normal")
        
        if self.current_page == total_pages - 1:
            self.next_button.config(state="disabled")
        else:
            self.next_button.config(state="normal")
    
    def load_next_file(self):
        if self.current_page < (len(self.file_list) // self.files_per_page):
            self.current_page += 1
            self.update_file_list_display()

    def load_previous_file(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_file_list_display()

    def create_concept_dict(self, df):
        concept_dict = df.groupby('concept')['matched_text'].apply(lambda x: x.unique().tolist()).to_dict()
        return concept_dict

    def assign_colors(self, concept_dict):
        colors = {}
        for i, (concept, matched_texts) in enumerate(concept_dict.items()):
            base_color = CNST.COLOR_LIST[i % len(CNST.COLOR_LIST)]
            for text in matched_texts:
                colors[text] = base_color
        return colors
        
    def show_additional_info(self, event):
        index = self.annotation_text.index(f"@{event.x},{event.y}")
        tags = self.annotation_text.tag_names(index)

        # Look for tags that start with 'highlight_'
        highlight_tags = [tag for tag in tags if tag.startswith("highlight_")]

        if highlight_tags:
            tag = highlight_tags[0]
            range_result = self.annotation_text.tag_nextrange(tag, index)
            
            if range_result and range_result[0] <= index <= range_result[1]:
                matched_text = tag[len("highlight_"):]
            else:
                range_result = self.annotation_text.tag_prevrange(tag, index)
                if range_result and range_result[0] <= index <= range_result[1]:
                    matched_text = tag[len("highlight_"):]
                else:
                    matched_text = highlight_tags[0][len("highlight_"):]
            
            if range_result:
                start, end = range_result
                additional_info = self.fetch_additional_info(matched_text, start, end)
                self.additional_info_label.config(text=additional_info, bg=self.concept_colors[matched_text])
                
                try:
                    x, y, _, _ = self.annotation_text.bbox(start)  # Use start instead of index
                    self.additional_info_label.place(x=x, y=y + 20, anchor="nw")
                except Exception as e:
                    print("Error displaying additional info:", e)

                self.annotation_text.bind("<Leave>", self.hide_additional_info)


    def hide_additional_info(self, event):
        # Unbind the show_additional_info function from the text widget
        self.annotation_text.unbind("<Motion>")
        # Hide the additional info label
        self.additional_info_label.place_forget()
        
    def fetch_additional_info(self, highlighted_text, start,end):
        # You can implement your logic here to fetch additional info based on highlighted text
        # Extracted startline and start values
        start_sentenct, start_in_sent = map(int, start.split('.'))
        end_sentence,end_in_sent=map(int, end.split('.'))
        
      
        # Filter rows based on the conditions
        result = self.annotation_row[  (self.annotation_row['start_sentenct'] == start_sentenct) & (self.annotation_row['start_in_sent'] == start_in_sent)
                                     & (self.annotation_row['end_sentence'] == end_sentence) & (self.annotation_row['end_in_sent'] == end_in_sent)]
        
        #print(f"Hi Elham result: {len(result)}")
        result=result.reset_index(drop=True)
        # Prepare the extra information to show
        try:
            negated='Yes' if result.loc[0,'is_negated']  else 'No'
            family='Yes' if result.loc[0,'is_family']  else 'No'
            certainty='Yes' if result.loc[0,'is_uncertain']  else 'No'
            historical='Yes' if result.loc[0,'is_historical']  else 'No'
            hypothetical='Yes' if result.loc[0,'is_hypothetical']  else 'No'
            section_id = '' if pd.isna(result.loc[0,'section_id']) else result.loc[0,'section_id']
            concept_label = '' if pd.isna(result.loc[0, 'concept']) else result.loc[0, 'concept']
        except Exception as e:
            #print("Error")
            #print(result)
            print(e)

        # For now, let's assume a simple implementation
        additional_info = (f"{'<'+concept_label+'>'}".center(20) + "\n" + 
        f"Negation: {negated}\n"
        f"Family: {family}\n"
        f"Uncertain: {certainty}\n"
        f"Historical: {historical}\n"
        f"Hypothetical: {hypothetical}\n"
        f"Section Id: {section_id}")
        return additional_info

    def bind_highlight_event(self):
        for tag in self.annotation_text.tag_names():
            if tag.startswith("highlight_"):
                self.annotation_text.tag_bind(tag, "<Enter>", self.show_additional_info)

    # Find the sentence number of the given Index and character counts until the one sentence before the containing sentence 
    def find_sentence_number(self, text, char_index):
        # Split the text into sentences based on newline characters (\n)
        sentences = text.split("\n")
        
        # Initialize variables to track the current character index, sentence number, 
        # and the number of characters until the last sentence before the target sentence
        current_index = 0
        sentence_number = 0
        chars_until_previous_sentence = 0
        
        # Iterate through each sentence
        for sentence in sentences:
            # Update the current character index
            current_index += len(sentence) + 1  # Add 1 for the newline character
            
            # Check if the character index falls within the current sentence
            if char_index < current_index:
                # Return the sentence number (0-based indexing) and the number of characters until the last sentence before the target sentence
                return sentence_number+1, chars_until_previous_sentence
            
            # Update the number of characters until the last sentence before the target sentence
            chars_until_previous_sentence = current_index
            
            # Increment the sentence number for the next iteration
            sentence_number += 1
        
        # If the character index exceeds the total length of the text, return -1
        return -1, -1  # Indicates that the character index is out of bounds
    
    def load_csv_files(self, notes_dir):
        csv_files = [f for f in os.listdir(notes_dir) if f.endswith('.csv')]
        if not csv_files:
            raise ValueError("No CSV files found in the directory.")

        all_dataframes = []
        for csv_file in csv_files:
            csv_path = os.path.join(notes_dir, csv_file)
            csv_path = os.path.normpath(csv_path)
            print(f"Annotating the file: {csv_path}")

            input_csv_file = pd.read_csv(csv_path)

            # making sure that the required columns exist
            if 'doc_name' not in input_csv_file.columns or 'note_text' not in input_csv_file.columns:
                raise ValueError("CSV file must contain 'doc_name' and 'note_text' columns.")

            all_dataframes.append(input_csv_file[["doc_name", "note_text"]])

        final_df = pd.concat(all_dataframes, ignore_index=True)

        return final_df


    def load_annotation(self, event):
        selected_file_index = self.file_listbox.curselection()

        if selected_file_index:
            selected_file_index = int(selected_file_index[0])
            selected_file = self.file_list[selected_file_index]
            #print("Selected File:", selected_file)
            self.annotation_row = self.annotation_data[self.annotation_data["doc_name"] == selected_file]
            
            # Save some inforamtion for later extraction
            self.annotation_row['start_in_sent']=np.nan
            self.annotation_row['start_sentenct']=np.nan
            self.annotation_row['end_in_sent']=np.nan
            self.annotation_row['end_sentence']=np.nan

            if self.csv_file_chk:
                file_data = self.load_csv_files(self.notes_dir)
                content = file_data.loc[file_data["doc_name"] == selected_file, "note_text"].values
                if content.size > 0:
                    file_content = content[0]
                else:
                    file_content = ""
            else:
                # Load content of the .txt file
                with open(os.path.join(self.notes_dir, selected_file), 'r', encoding='utf-8') as file:
                    file_content = file.read()
            
            file_content=file_content+"\n\n\n\n"
    
            # Display content of the file in the text widget
            self.annotation_text.config(state="normal")
            self.annotation_text.delete(1.0, tk.END)
            self.annotation_text.insert(tk.END, file_content)
    
            # Print the length of the file content (last possible character index)
            max_end_index = len(file_content)
            #print("Maximum End Index:", max_end_index)

            # Highlight annotations in a file
            for index, row in self.annotation_row.iterrows():    
                start_index = row["concept_start"]  # Adjust for line numbering starting from 1
                end_index = row["concept_end"]  # Adjust for line numbering starting from 1 and to include the character
                #print("Start Index:", start_index)
                #print("End Index:", end_index)
                
                # Find the sentence number and character count before, for the given span
                start_sent_number, char_num_before_start = self.find_sentence_number(file_content, start_index)
                end_sent_number, char_num_before_end = self.find_sentence_number(file_content, end_index)
                
                start_index_in_sent = start_index - char_num_before_start
                end_index_in_sent = end_index - char_num_before_end
                
                self.annotation_row.at[index,'start_in_sent']=start_index_in_sent
                self.annotation_row.at[index,'start_sentenct']=start_sent_number
                self.annotation_row.at[index,'end_in_sent']=end_index_in_sent
                self.annotation_row.at[index,'end_sentence']=end_sent_number
                #self.annotation_row.at[index, 'section_id']=section_id

                # Highlight annotation in the text widget
                self.annotation_text.tag_add(f"highlight_{row['matched_text']}", f"{start_sent_number}.{start_index_in_sent}", f"{end_sent_number}.{end_index_in_sent}")  # Format indices as line.column
                self.annotation_text.tag_config(f"highlight_{row['matched_text']}", background=self.concept_colors[row['matched_text']])
                
                # Bind event for showing additional info on highlight hover
                self.bind_highlight_event()
                
                # Print the length of the file content (last possible character index)
                max_end_index = len(file_content)
                #print("Maximum End Index:", max_end_index)
        
            self.annotation_text.config(state="disabled")

def main():
    root = tk.Tk()
    #output_data=r"H:\Projects\Fred_MedSpacy\test8\Fred_MedSpacy_2024-04-19_11-20-51.xlsx"
    app = AnnotationViewer(root, 
                            r"C:/Users/M314694/Desktop/Application/cheack/2025-02-11_13-36-22/xlsx",
                            CNST.INPUT_DIR,
                            True)
    root.mainloop()

if __name__ == "__main__":
    main()
