import sys
import logging
from model import Model
from view import View
from tkinter import messagebox
import helper.constants as CNST

if getattr(sys, 'frozen', False):
    import pyi_splash  # type: ignore

# Setting up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Controller:
    """Handles the control logic between View and Model"""
    
    def __init__(self, view, model):
        """Initializes the controller with view and model.

        Args:
            view (View): The view object.
            model (Model): The model object.
        """
        self.view = view
        self.model = model
        self.view.set_controller(self)
        self.logger = logging.getLogger(__name__)  # Logger for Controller class

    def process_notes(self, input_dir, output_dir, project_resources_dir, project_path, csv_file_chk):
        """Process the notes based on input directories and project paths.

        Args:
            input_dir (str): The input directory containing notes.
            output_dir (str): The directory where output is saved.
            project_resources_dir (str): Directory containing project resources.
            project_path (str): Path of the project.
            csv_file_chk (bool): Flag to check CSV input.

        """
        if not project_path:
            self.view.show_error("Project directory not selected!")
            self.logger.error("Project directory not selected.")
            return
        
        if not input_dir or not output_dir:
            self.view.show_error("Input and Output directories are required!")
            self.logger.error("Input and Output directories are required.")
            return
        
        try:
            self.view.reset_progress()
            self.logger.info(f"Starting NLP processing with input: {input_dir}, output: {output_dir}, project_resources: {project_resources_dir}, project: {project_path}")
            
            output_folder = self.model.perform_nlp(input_dir, 
                                                 output_dir, 
                                                 project_resources_dir, 
                                                 project_path, 
                                                 CNST.INPUT_MODE,
                                                 csv_file_chk,
                                                 self.view.update_progress)
            
            self.logger.info(f"NLP processing completed. Output folder: {output_folder}")
            self.view.output_folder = output_folder
        except Exception as e:
            self.logger.error(f"Error processing notes: {e}")
            messagebox.showinfo("Error", f"An error occurred: {e}")
            

# Main function to run the application
def main():
    """Initialize and start the application."""
    app = View()
    model = Model()
    Controller(app, model)

    # loading should be done before this point. The following lines of code are for creating pause while running exe package
    if getattr(sys, 'frozen', False):
        pyi_splash.close()

    app.mainloop()


if __name__ == "__main__":
    main()