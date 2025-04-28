import sys
import logging
from model import Model
from view import View
from tkinter import messagebox
import helper.constants as CNST

if getattr(sys, 'frozen', False):
    import pyi_splash # type: ignore

class Controller:
    """_summary_
    """
    def __init__(self, view, model):
        """_summary_

        Args:
            view (_type_): _description_
            model (_type_): _description_
        """
        self.view = view
        self.model = model
        self.view.set_controller(self)

    def process_notes(self, input_dir, output_dir, project_resources_dir, project_path, csv_file_chk):
        """_summary_

        Args:
            input_dir (_type_): _description_
            output_dir (_type_): _description_
            project_resources_dir (_type_): _description_
            project_path (_type_): _description_
        """
        if not project_path:
            self.view.show_error("Project directory not selected!")
            return
        
        if not input_dir or not output_dir:
            self.view.show_error("Input and Output directories are required!")
            return
        
        try:
            self.view.reset_progress()
            # print(f"input: {input_dir}, output: {output_dir}, project_resource: {project_resources_dir}, project :{project_path}")
            output_folder = self.model.perform_nlp(input_dir, 
                                                 output_dir, 
                                                 project_resources_dir, 
                                                 project_path, 
                                                 CNST.INPUT_MODE,
                                                 csv_file_chk,
                                                 self.view.update_progress)

            # print("the output file is ready")
            # Call a method in the view to display the output (annotation) in tab2
            self.view.output_folder = output_folder
            # self.view.display_output_tab2()  
            # self.view.update_output("Processing completed successfully.")
            # self.view.enable_done_button()  # Enable the Done button after processing
        except Exception as e:
            messagebox.showinfo("Error2", f"{e}")

# Main function to run the application
def main():
    """_summary_
    """
    app = View()
    model = Model()
    Controller(app, model)

    # loading should be done before this point. The following lines of code are for creating pause while running exe package
    if getattr(sys, 'frozen', False):
        pyi_splash.close()

    app.mainloop()


if __name__ == "__main__":
    main()