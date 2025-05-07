# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import time
import re
import json
import logging
import argparse
#import spacy
import medspacy
from medspacy.sentence_splitting import PyRuSHSentencizer
from medspacy.section_detection import SectionRule
from medspacy.section_detection import Sectionizer
#from clinical_sectionizer import TextSectionizer
from medspacy.ner import TargetRule
from medspacy.context import ConText, ConTextRule
#from medspacy.visualization import visualize_ent
#from spacy import displacy
from spacy.tokens import Span
#from google.cloud import bigquery

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import helper.constants as CNST

# Setting up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Model:
    """Handles loading and processing various data files such as sections, lexicons, and exclusion terms.
    """

    def __init__(self):
        """setting logging
        """
        self.logger = logging.getLogger(__name__)
    
    def load_sections(self,sec_file, the_sectionizer):
        """Load sections from the provided file and add them to the sectionizer.

        Args:
            sec_file (str): Path to the section file that contains section information.
            the_sectionizer (object): The sectionizer object where the section rules will be added.
        """
        with open(sec_file, 'r') as fh:
            for line in fh:
                columns = line.strip().split('\t')
                sec_id, synonym, source = columns[:3]

                if sec_id == CNST.SECTION_ID:
                    continue 
                entry = {CNST.LITERAL : synonym,
                         CNST.CATEGORY : sec_id}
                the_sectionizer.add(SectionRule.from_dict(entry)) # load one rule in a dictionary format

    def load_lexicon(self,lex_file):
        """Load the inclusion lexicon from the provided file and return it as a pandas DataFrame.

        Args:
            lex_file (str): Path to the lexicon file (Excel format).

        Returns:
            pandas.DataFrame: A cleaned lexicon containing the concepts and their respective categories.
        """
        result = dict()
        inclusion_lexicon = pd.read_excel(lex_file)
        self.logger.info("Read the concept")
                
        inclusion_lexicon = inclusion_lexicon.iloc[:, :5]
        inclusion_lexicon.columns = CNST.LEXICON_COLS

        inclusion_lexicon = inclusion_lexicon[~inclusion_lexicon[CNST.LEXICON_COLS[1]].isnull()]
        inclusion_lexicon = inclusion_lexicon[~inclusion_lexicon[CNST.LEXICON_COLS[2]].isnull()]

        self.logger.info(f"concepts number is {len(inclusion_lexicon)}")
        

        inclusion_lexicon = inclusion_lexicon.drop_duplicates()
        return inclusion_lexicon

    def load_concept_rules(self, incl_lexicon):
        """Generate a list of concept rules from the inclusion lexicon and optional exclusion lexicon.

        Args:
            incl_lexicon (pandas.DataFrame): The inclusion lexicon containing terms and categories.

        Returns:
            list: A list of concept rules generated from the lexicons.
        """
        ''' ref. https://github.com/medspacy/target_matcher '''
        the_rules = list()
        # Register a new custom attribute to store the rare disease IDs
        Span.set_extension('concept_id', default='', force=True)
        for _, row in incl_lexicon.iterrows():
            concept_id = row[CNST.LEXICON_COLS[0]]
            concept_category = row[CNST.LEXICON_COLS[1]]
            term = row[CNST.LEXICON_COLS[2]]
            case_sensitive = row[CNST.LEXICON_COLS[3]]
            regex = row[CNST.LEXICON_COLS[4]]

            term = "\\b(?:" + term + ")\\b"
            regex_pattern = fr"(?i){term}"

            if case_sensitive == "YES":
                regex_pattern = [{"TEXT" : {"REGEX" : term}}]

            id_attr = {"concept_id" : concept_id}

            rule = TargetRule(literal = term,
                                category = concept_category,
                                pattern = regex_pattern,
                                attributes = id_attr)
            the_rules.append(rule)

        return (the_rules)

    def generate_target_rules(self, norm, term, id_attr, regex, case_sensitive):
        """Generate target rules for NLP processing based on provided parameters.

        Args:
            norm (str): The normalized concept or category.
            term (str): The term or phrase to match in the text.
            id_attr (dict): Dictionary containing concept ID attributes.
            regex (bool): Whether to use regular expressions for pattern matching.
            case_sensitive (bool): Whether the matching should be case-sensitive.

        Returns:
            TargetRule: A constructed target rule for use in the NLP pipeline.
        """
        if case_sensitive:
            if regex: 
                regex_pattern = [{"TEXT":{"REGEX": term}}]
                rule=TargetRule(literal=term, category=norm,pattern=regex_pattern, attributes=id_attr)
            else:    
                tokens =  term.split(' ')
                token_patterns = [{"TEXT": token} for token in tokens]
                rule = TargetRule(literal=term, category=norm, pattern=token_patterns, attributes=id_attr)                    
        else:
            if regex:
                regex_pattern = [{"TEXT":{"REGEX": term}}] # default to insensitive 
                rule = TargetRule(literal=term, category=norm, pattern=regex_pattern, attributes=id_attr)
            else:
                tokens =  term.split(' ')
                token_patterns = [{"LOWER": token.lower()} for token in tokens]
                rule = TargetRule(literal=term, category=norm, pattern=token_patterns, attributes=id_attr)
        return rule

    def process_notes_on_disk(self,the_pipeline, the_input_path, tho_output_path,project_path_resources, inclusion_concepts, project_path, csv_file_chk, progress_callback=None):
        """Process notes stored on disk, either in CSV or text files, and extract entities using the NLP pipeline.

        Args:
            the_pipeline (object): The NLP pipeline used to process the notes.
            the_input_path (str): Path to the input directory containing the notes.
            tho_output_path (str): Path to the output directory where results will be saved.
            project_path_resources (str): Path to the project resources.
            inclusion_concepts (pandas.DataFrame): DataFrame containing the inclusion concepts for entity extraction.
            project_path (str): Path to the project.
            csv_file_chk (bool): Flag to indicate whether CSV files are being processed.
            progress_callback (function, optional): Callback function to update the progress. Defaults to None.

        Raises:
            ValueError: If no CSV files are found in the directory.
        
        Returns:
            str: The path to the folder containing the output files.
        """
        self.logger.info("In process notes on disk")
        self.logger.info(f"the_input_path, tho_output_path,project_path_resources,  inclusion_concepts, project_path, {the_input_path}, {tho_output_path},{project_path_resources},  {inclusion_concepts}, {project_path}\n")

        the_input_path = the_input_path.replace("\\", "/")
        tho_output_path = tho_output_path.replace("\\", "/")
        project_path_resources = project_path_resources.replace("\\", "/")

        results=[]
        file_flag = ""
        files_processed = 0
        if csv_file_chk:
            file_flag = "csv"
            csv_files = [f for f in os.listdir(the_input_path) if f.endswith('.csv')]
            if not csv_files:
                raise ValueError("No CSV files found in the directory.")
            self.logger.info(f"Processing the CSV file input...")

            total_texts = sum(len(pd.read_csv(os.path.join(the_input_path, file))) for file in csv_files)
            
            for csv_file in csv_files:
                csv_path = os.path.join(the_input_path, csv_file)
                csv_path = os.path.normpath(csv_path)
                self.logger.info(f"Processing the file: {csv_path}")
                input_csv_file = pd.read_csv(csv_path)

                # making sure that the required columns exist
                if 'doc_name' not in input_csv_file.columns or 'note_text' not in input_csv_file.columns:
                    raise ValueError("CSV file must contain 'doc_name' and 'note_text' columns.")

                # getting the last remaining columns
                end_columns = input_csv_file.loc[:, input_csv_file.columns[input_csv_file.columns.get_loc("note_text") + 1:]].columns.tolist()

                for idx, row in input_csv_file.iterrows():
                    doc_id = row["doc_name"]
                    note_text = row["note_text"]

                    # skipping the empty notes
                    if not isinstance(note_text, str) or note_text.strip() == "":
                        continue
                    
                    # Initiating the text processing through the NLP pipeline
                    doc = the_pipeline(note_text)

                    # extracting the processed annotations
                    for ent in doc.ents:
                        result_entry = {
                            "doc_name": doc_id,
                            "concept": ent.label_,
                            "matched_text": ent.text,
                            "concept_start": ent.start_char,  # is prefered
                            "concept_end": ent.end_char,
                            "sentence": ent.sent.text,
                            "sentence_start": ent.sent.start_char,
                            "sentence_end" : ent.sent.end_char,
                            "section_id": "" if pd.isna(ent._.section_category) else ent._.section_category,
                            "matched_section_header" : ent._.section_title,
                            "is_negated": ent._.is_negated,
                            "is_family": ent._.is_family,
                            "is_uncertain": ent._.is_uncertain,
                            "is_historical": ent._.is_historical,
                            "is_hypothetical": ent._.is_hypothetical
                        }

                        for el in end_columns:
                            result_entry.update({el: row[el]})

                        results.append(result_entry)

                    files_processed += 1
                    if total_texts > 0:
                        divisor = max(1, total_texts // 10)

                        if (files_processed % divisor == 0 or files_processed == total_texts) and progress_callback:
                            progress_percent = (files_processed / total_texts) * 100
                            progress_callback(progress_percent, f"{files_processed}/{total_texts}")
                        else:
                            self.logger.info(f"Processed : {(files_processed / total_texts) * 100}% of files")
                    else:
                        self.logger.info("No files to process.")
        else:
            file_flag = "text"
            self.logger.info(f"Processing the Text files input...")
            files = os.listdir(the_input_path)

            total_files = 0
            for f in files:
                if f.endswith('.txt'):
                    total_files = total_files + 1
        
            for f in files:
                if not f.endswith('.txt'):
                    continue
                note_txt = None

                with open(os.path.join(the_input_path, f),  'r', encoding='utf-8') as fh:
                    try:
                        note_txt = fh.read()
                    except Exception as e:
                        self.logger.error(f"The program was not able to process the following file:{f} with errror: {e}")
                        continue
                
                if not note_txt:
                    #print(f + ' has empty text!')
                    continue
                doc = the_pipeline(note_txt)
                for ent in doc.ents:
                    
                    results.append({"doc_name": f,
                                    "concept":ent.label_,
                                    "matched_text": ent.text,
                                    "concept_start": ent.start_char,
                                    "concept_end": ent.end_char,
                                    "sentence": ent.sent.text,
                                    "sentence_start": ent.sent.start_char,
                                    "sentence_end" : ent.sent.end_char,
                                    "section_id": "" if pd.isna(ent._.section_category) else ent._.section_category,
                                    "matched_section_header" : ent._.section_title,
                                    "is_negated": ent._.is_negated,
                                    "is_family": ent._.is_family,
                                    "is_uncertain": ent._.is_uncertain,
                                    "is_historical": ent._.is_historical,
                                    "is_hypothetical": ent._.is_hypothetical})
                files_processed += 1

                if total_files > 0:
                    divisor = max(1, total_files // 10)

                    if (files_processed % divisor == 0 or files_processed == total_files) and progress_callback:
                        progress_percent = (files_processed / total_files) * 100
                        progress_callback(progress_percent, f"{files_processed}/{total_files}")
                    else:
                        self.logger.info(f"Processed : {(files_processed / total_files) * 100}% of files")
                else:
                    self.logger.info("No files to process.")

                
                
        df = pd.DataFrame(results)
        if df.empty:
            return "EMPTY"
        else:

            project_name = os.path.basename(project_path)
            
            # Get the current date and time
            current_datetime = time.localtime()
            
            # Format the current date and time as desired
            formatted_datetime = time.strftime("%Y-%m-%d_%H-%M-%S", current_datetime)
            timestamped_output_folder = f"{tho_output_path}/{formatted_datetime}"
            csv_folder = os.path.join(timestamped_output_folder, 'csv').replace("\\", "/")
            xlsx_folder = os.path.join(timestamped_output_folder, 'xlsx').replace("\\", "/")
            os.makedirs(csv_folder, exist_ok=True)
            os.makedirs(xlsx_folder, exist_ok=True)

            output_files = []
            unique_doc_ids = df[CNST.DOC_ID].unique()
            
            for i in range(0, len(unique_doc_ids), CNST.MAX_DOCS):
                doc_id_chunk = unique_doc_ids[i:i + CNST.MAX_DOCS]
                chunk_df = df[df[CNST.DOC_ID].isin(doc_id_chunk)]
                
                output_file_name_csv = f"{project_name}_{formatted_datetime}_{file_flag}_part{i//CNST.MAX_DOCS+1}.csv"
                output_file_name_excel = f"{project_name}_{formatted_datetime}_{file_flag}_part{i//CNST.MAX_DOCS+1}.xlsx"
                
                chunk_df.to_csv(f"{csv_folder}/{output_file_name_csv}", index=False, sep='|')
                chunk_df.to_excel(f"{xlsx_folder}/{output_file_name_excel}", index=False)
                output_files.append(os.path.join(xlsx_folder, output_file_name_excel))
            
            return xlsx_folder

    def perform_nlp(self,input_dir, output_dir, project_path_resources, project_path, input_mode, csv_file_chk, progress_callback=None):
        """Performs the NLP pipeline on the input files or directories.

        Args:
            input_dir (str): The directory containing the input files.
            output_dir (str): The directory to save the output files.
            project_path_resources (str): Path to the project resources.
            project_path (str): Path to the project.
            input_mode (str): The mode of input ('files' for processing files).
            csv_file_chk (bool): Flag to check if CSV files should be processed.
            progress_callback (function, optional): Callback function to update the progress. Defaults to None.

        Returns:
            str: The path to the output folder containing processed files.
        """
    
        old_stdout = sys.stdout
        self.logger.info(f"input_dir, output_dir,project_path_resources, project_path, input_mode,{input_dir}, {output_dir},{project_path_resources}, {project_path}, {input_mode}\n")

        nlp, inclusion_lexicon = self.init_nlp_pipeline(project_path_resources)
        
        if input_mode == 'files':
            try:
                self.logger.info("I'm going to files on dist\d")
                entity_types_to_print = ['RARE_DZ'] # customize for use case!
                output_file=self.process_notes_on_disk(nlp, input_dir,output_dir, project_path_resources, inclusion_lexicon, project_path, csv_file_chk, progress_callback)  
            
                self.logger.info("NLP process finished.\n")
                self.logger.info(f"outputfile {output_file}")

                return(output_file)
            except Exception as e:
                self.logger.error(f"Error procesing files on disk", {e})
        else: 
            self.logger.error(f"input_file is not file {input_mode}")
    
    def init_nlp_pipeline(self, project_path_resources):
        """Initializes the NLP pipeline by adding components like tokenizers, sentence splitters, and sectionizers.

        Args:
            project_path_resources (str): Path to the project resources containing custom configuration files.

        Returns:
            tuple: A tuple containing the initialized NLP pipeline and the inclusion lexicon.
        """
        # Create Pipeline
        nlp = medspacy.load(medspacy_enable=['medspacy_tokenizer']) # add the tokenizer first; should be just symbolic as it's loaded by default.
        self.logger.info("Loaded medspacy tokenizer\n")

        # ADD Sentenizer
        try:
            # path_of_resource = resources['medspacy_pyrush']['split_rules']
            path_of_resource=f"{project_path_resources}/{CNST.RESOURCE_SENTENCE_RULE}"
            sentencizer = nlp.add_pipe('medspacy_pyrush', config={'rules_path': path_of_resource})
        except Exception as e:
            self.logger.error(f"Exception adding custom sentencizer: {e}")
            sentencizer = nlp.add_pipe('medspacy_pyrush') 

        # ADD Sectionizer
        try:    
            path_of_resource=f"{project_path_resources}/{CNST.RESOURCE_SECTIONS_RULE}"
            
            sectionizer = nlp.add_pipe('medspacy_sectionizer', config={'rules': None,
                                                                        'require_start_line': True})
            self.load_sections(path_of_resource, sectionizer)
        except Exception as e:
            self.logger.error(f"Exception adding custom sectionizer: {e}")
            sectionizer = nlp.add_pipe('medspacy_sectionizer') # load the default           
    
        concept_matcher = nlp.add_pipe('medspacy_target_matcher') # add an empty matcher
        concept_rules = list()
        
        # Load concepts
        try:
            
            inclusion_lexicon = None
            path_of_resource = f"{project_path_resources}/{CNST.RESOURCE_CONCEPTS}"

            inclusion_lexicon = self.load_lexicon(path_of_resource)

            concept_rules = self.load_concept_rules(inclusion_lexicon)
        except Exception as e:
            self.logger.error(f"Exception loading concept matcher rules: {e}")

        concept_matcher.add(concept_rules) # fill attach the rules to the matcher

        #Load general context       
        
        context_classifier = nlp.add_pipe('medspacy_context', config={"rules": None})  # load the default context component
        try:
            # Attempting to use a custom path for context rules
            path_of_resource = f"{project_path_resources}/{CNST.RESOURCE_CONTEXT_RULES}"
            
            # Loading custom rules from the JSON file
            rules = ConTextRule.from_json(path_of_resource)
            # Adding the custom rules to the context classifier
            context_classifier.add(rules)
            
        except Exception as e:
            self.logger.error(f"Exception loading custom context rules: {e}")
            # Fallback to default context rules
            context_classifier = ConText(nlp, rules='default')

        return nlp, inclusion_lexicon

# Example usage of the Model class
if __name__ == "__main__":

    # argparse to accept command-line arguments
    parser = argparse.ArgumentParser(description="Run the NLP processing with specified directories and project settings.")
    
    # command-line arguments
    parser.add_argument('--input_dir', type=str, help="Directory containing input files (default from CNST).")
    parser.add_argument('--output_dir', type=str, help="Directory to save output files (default from CNST).")
    parser.add_argument('--project_resources_dir', type=str, default=CNST.PROJECT_RESOURCES_DIR, help="Path to the project resources directory (default from CNST).")
    parser.add_argument('--project_path', type=str, help="Path to the project directory (default from CNST).")
    parser.add_argument('--input_mode', type=str, default=CNST.INPUT_MODE, choices=['files', 'csv'], help="Input mode (either 'files' or 'csv').")
    parser.add_argument('--csv_file_chk', type=bool, default=True, help="Flag to check for CSV files in input.")
    
    args = parser.parse_args()

    model = Model()
    
    output_file = model.perform_nlp(args.input_dir,
                                     args.output_dir, 
                                     args.project_resources_dir, 
                                     args.project_path, 
                                     args.input_mode, 
                                     args.csv_file_chk)
    print(output_file)

if __name__ == "__main__":
    main()