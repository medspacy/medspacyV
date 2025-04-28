# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 21:03:33 2024

@author: m199589
"""

import os
import sys
import pandas as pd
import time
import re
import json
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

import helper.constants as CNST

class Model:
    
    def load_sections(self,sec_file, the_sectionizer):
        with open(sec_file, 'r') as fh:
            for line in fh:
                columns = line.strip().split('\t')
                sec_id, synonym, source = columns[:3] # MDE (Mayo Data Explorer), JWF (Fred added) - ource

                if sec_id == CNST.SECTION_ID:
                    continue 
                entry = {CNST.LITERAL : synonym,
                         CNST.CATEGORY : sec_id}
                the_sectionizer.add(SectionRule.from_dict(entry)) # load one rule in a dictionary format

    def load_lexicon(self,lex_file):
        result = dict()
        inclusion_lexicon = pd.read_excel(lex_file)
        print("I read the the concept")
                
        inclusion_lexicon = inclusion_lexicon.iloc[:, :5]
        inclusion_lexicon.columns = CNST.LEXICON_COLS
        # TO DO HECK FOR EMPTY FIELDS
        #cleen concep file
        inclusion_lexicon = inclusion_lexicon[~inclusion_lexicon[CNST.LEXICON_COLS[1]].isnull()]
        inclusion_lexicon = inclusion_lexicon[~inclusion_lexicon[CNST.LEXICON_COLS[2]].isnull()]

        print(f"concepts number is {len(inclusion_lexicon)}")
        

        inclusion_lexicon = inclusion_lexicon.drop_duplicates()
        # # Iterate over the rows of the DataFrame
        # for index, row in inclusion_lexicon.iterrows():
        #     # Construct the key using concept_category, concept_id, and case_sensitivity
        #     key = (row['CONCEPT_CATEGORY'], row['CONCEPT_ID'], row['CASE_SENSITIVITY'])
        #     # Assign the value to the key
        #     result[key] = row['TERM_OR_REGEX']

        # # Print the resulting dictionary
        # print(result)
        return inclusion_lexicon

    def load_excl_terms(self,excl_file):
        result = set()
        with open(excl_file, 'r') as fh:
            for line in fh:
                if line.startswith('!'):
                    trimmed = line[1:]
                    result.add(trimmed.strip().lower())
        return result

    def load_concept_rules(self, incl_lexicon, excl_lexicon=None):
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

            if excl_lexicon and term.lower() in excl_lexicon:
                continue

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
        # for (concept_category, concept_id, case_sensitive) in incl_lexicon.keys():
        #     for term in incl_lexicon[(concept_category, concept_id, case_sensitive)]:
        #         term = term.replace('\t', ' ') # the TAB thing is OHNLP format
        #         if term.lower() in excl_lexicon:
        #             continue # skip if in the exclusion list
        #         term = '\\b(?:' + term + ')\\b'
        #         regex_pattern = fr'(?i){term}' # defaul to insensitive
        #         if case_sensitive == 'CaseSen':
        #             regex_pattern = fr'{term}'
        #         id_attr = {'concept_id': concept_id}
        #         rule = TargetRule(literal=term, category=concept_category, pattern=regex_pattern, attributes=id_attr)
        #         #tokens = term.split(' ')
        #         #token_patterns = [{"LOWER": token} for token in tokens]
        #         #rule = TargetRule(literal=term, category=concept_category, pattern=token_patterns, attributes=id_attr)
        #         the_rules.append(rule)
        # return the_rules
        # print(type(incl_lexicon))
        # for index , row in incl_lexicon.iterrows():
        #     # Prepend each character in term with case-insensitivity flag if term is a regex
        #     #pattern_str = 
        #     #print(pattern_str)
        #     #print(row)
        #     norm = row[CNST.LEXICON_COLS[1]]
        #     term = row[CNST.LEXICON_COLS[2]]
        #     id_attr = {'concept_id': row[CNST.LEXICON_COLS[0]]}
        #     regex = row[CNST.LEXICON_COLS[4]]
        #     case_sensitive = row[CNST.LEXICON_COLS[3]]
            
        #     # Use a regular expression to keep only letters becasue the logic wont work if user put somethin like Flu_diagnosis
        #     norm = re.sub(CNST.REGEX_LETTERS, '', norm)
            
        #     case_sensitive = True if case_sensitive == "YES" else False
                
        #     regex = True if regex == "YES" else False  
                        
                                
        #     if excl_lexicon and term.lower() in excl_lexicon:
        #         continue # skip if in the exclusion list   
        
        #     rule = self.generate_target_rules(norm, term, id_attr, regex, case_sensitive)
            
        #     the_rules.append(rule)
        # return(the_rules)

    def generate_target_rules(self, norm, term, id_attr, regex, case_sensitive):
        if case_sensitive:
            if regex: 
                    #tokens =  term
                # tokens =  term.split(' ')
                regex_pattern = [{"TEXT":{"REGEX": term}}]
                rule=TargetRule(literal=term, category=norm,pattern=regex_pattern, attributes=id_attr)
            else:    
                tokens =  term.split(' ')
                token_patterns = [{"TEXT": token} for token in tokens]
                rule = TargetRule(literal=term, category=norm, pattern=token_patterns, attributes=id_attr)                    
        else:
            if regex:
                # tokens =  term.split(' ')
                regex_pattern = [{"TEXT":{"REGEX": term}}] # defaul to insensitive 
                rule = TargetRule(literal=term, category=norm, pattern=regex_pattern, attributes=id_attr)
            else:
                tokens =  term.split(' ')
                token_patterns = [{"LOWER": token.lower()} for token in tokens]
                rule = TargetRule(literal=term, category=norm, pattern=token_patterns, attributes=id_attr)
        return rule

    def process_notes_on_disk(self,the_pipeline, the_input_path, tho_output_path,project_path_resources, inclusion_concepts, project_path, csv_file_chk, progress_callback=None):
        print(" I am in process notes on disk")
        print(f"the_input_path, tho_output_path,project_path_resources,  inclusion_concepts, project_path, {the_input_path}, {tho_output_path},{project_path_resources},  {inclusion_concepts}, {project_path}\n")

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
            print(f"Processing the CSV file input...")

            total_texts = sum(len(pd.read_csv(os.path.join(the_input_path, file))) for file in csv_files)
            
            for csv_file in csv_files:
                csv_path = os.path.join(the_input_path, csv_file)
                csv_path = os.path.normpath(csv_path)
                print(f"Processing the file: {csv_path}")
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
                        # print(result_entry)
                        results.append(result_entry)

                    files_processed += 1
                    if total_texts > 0:
                        divisor = max(1, total_texts // 10)

                        if (files_processed % divisor == 0 or files_processed == total_texts) and progress_callback:
                            progress_percent = (files_processed / total_texts) * 100
                            progress_callback(progress_percent, f"{files_processed}/{total_texts}")
                        else:
                            print(f"Processed : {(files_processed / total_texts) * 100}% of files")
                    else:
                        print("No files to process.")
        else:
            file_flag = "text"
            print(f"Processing the Text files input...")
            files = os.listdir(the_input_path)

            total_files = 0
            for f in files:
                if f.endswith('.txt'):
                    total_files = total_files + 1
        
            for f in files:
                if not f.endswith('.txt'):
                    continue
                note_txt = None
                print("  I read the files\n")
                with open(os.path.join(the_input_path, f),  'r', encoding='utf-8') as fh:
                    try:
                        note_txt = fh.read()
                    except Exception as e:
                        print(f"The program was not able to process the following file:{f} with errror: {e}")
                        continue
                
                if not note_txt:
                    #print(f + ' has empty text!')
                    continue
                doc = the_pipeline(note_txt)
                for ent in doc.ents:
                    #print("************ent")
                    #print(dir(ent))
                    # if ent.label_ not in inclusion_concepts:
                    #     continue
                    #sent_obj = ent.sent
                    #sent_str_newline_replaced = str(sent_obj).replace('\n', ' ')
                    #print(f + '\t' + str(ent.label_) + '\t' + str(ent._.concept_id) + '\t' + str(ent.start)+'-'+str(ent.end) + '\t' + str(ent) + '\t' + str(sent_obj.start)+'-'+str(sent_obj.end) + '\t' + sent_str_newline_replaced + '\t' + str(ent._.section_category) + '\t' + str(ent._.section_title) + '\t' + str(ent._.is_negated) + '\t' + str(ent._.is_uncertain) + '\t' + str(ent._.is_historical) + '\t' + str(ent._.is_hypothetical) + '\t' + str(ent._.is_family))
                                    # Add information to results
                    results.append({
                                        "doc_name": f,
                                        "concept":ent.label_,
                                    #  "context_id":ent._.concept_id,
                                        #"concept": norm,
                                        "matched_text": ent.text,
                #                        "start1": ent.start,
                                        "concept_start": ent.start_char,  # is prefered
                #                        "end1:": ent.end,
                                        # "ent": ent,
                                        "concept_end": ent.end_char,
                                        "sentence": ent.sent.text,
                                        "sentence_start": ent.sent.start_char,
                                        "sentence_end" : ent.sent.end_char,
                #                        "sentence_number":ent.sentence_number,
                                        "section_id": "" if pd.isna(ent._.section_category) else ent._.section_category,
                                        "matched_section_header" : ent._.section_title,
                                        "is_negated": ent._.is_negated,
                                        "is_family": ent._.is_family,
                                        "is_uncertain": ent._.is_uncertain,
            #                           "section_pattern": ent._.section_patterns,
                                        "is_historical": ent._.is_historical,
                                        "is_hypothetical": ent._.is_hypothetical,
                                        #"is_POSSIBLE_EXISTENCE": is_POSSIBLE_EXISTENCE
                                    #  "Experiencer": experiencer
        
                                    
                                    })
                files_processed += 1

                if total_files > 0:
                    divisor = max(1, total_files // 10)

                    if (files_processed % divisor == 0 or files_processed == total_files) and progress_callback:
                        progress_percent = (files_processed / total_files) * 100
                        progress_callback(progress_percent, f"{files_processed}/{total_files}")
                    else:
                        print(f"Processed : {(files_processed / total_files) * 100}% of files")
                else:
                    print("No files to process.")

                
                
        df = pd.DataFrame(results)
        if df.empty:
            return "EMPTY"
        else:
            #project_path=os.path.dirname(os.path.dirname(project_path_resources))
            # Split the path and get the second-to-last component
            project_name = os.path.basename(project_path)
            print(f" results is ready {len(df)}")
            # print("project_name {project_name}")
            
            #Get the current date and time
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
        # Redirect stdout to a log file
        # log_file = "debug.log"
    
        old_stdout = sys.stdout  # Save the original stdout
        # log_file= open("debug.log", "w")  # Open the log file in append mode            
        #logging.basicConfig(level=logging.ERROR)
        #sys.stdout = log_file
        print(f"input_dir, output_dir,project_path_resources, project_path, input_mode,{input_dir}, {output_dir},{project_path_resources}, {project_path}, {input_mode}\n")

        #config_json=project_path_resources+'/'+config_json
        # configuration = None
        # with open(config_json, 'r') as fh:
        #     configuration = json.load(fh)
        #     #print(configuration['resources'])
        # resources = configuration['resources'] # loaded the config info

        nlp, inclusion_lexicon = self.init_nlp_pipeline(project_path_resources)
        
        if input_mode == 'files':
            try:
                print("I'm going to files on dist\d")
                entity_types_to_print = ['RARE_DZ'] # customize for use case!
                output_file=self.process_notes_on_disk(nlp, input_dir,output_dir, project_path_resources, inclusion_lexicon, project_path, csv_file_chk, progress_callback)  
            
                print("NLP process finished.\n")
                print(f"outputfile {output_file}")
                #sys.stdout=old_stdout
                # log_file.close()
                return(output_file)
            except Exception as e:
                print(f"Error procesing files on disk", {e})
                #sys.stdout=old_stdout
                # log_file.close()
        else: 
            print(f"input_file is not file {input_mode}")
            #sys.stdout=old_stdout
            # log_file.close()
    
    def init_nlp_pipeline(self, project_path_resources):
        # Create Pipeline
        nlp = medspacy.load(medspacy_enable=['medspacy_tokenizer']) # add the tokenizer first; should be just symbolic as it's loaded by default.
        print(" I loaded medspacy tokenizer\n")

        # ADD Sentenizer
        #if 'medspacy_pyrush' in resources and 'split_rules' in resources['medspacy_pyrush']:
        try:
            #path_of_resource = resources['medspacy_pyrush']['split_rules']
            path_of_resource=f"{project_path_resources}/{CNST.RESOURCE_SENTENCE_RULE}"
            sentencizer = nlp.add_pipe('medspacy_pyrush', config={'rules_path': path_of_resource})
            #print(sentencizer.rules_path)
        except Exception as e:
            print(f"Exception adding custom sentencizer: {e}")
            sentencizer = nlp.add_pipe('medspacy_pyrush') # load the default
        
            # ADD Sectionizer
        #if 'medspacy_sectionizer' in resources and 'header_terms' in resources['medspacy_sectionizer']:
        try:    
            #path_of_resource = resources['medspacy_sectionizer']['header_terms']
            path_of_resource=f"{project_path_resources}/{CNST.RESOURCE_SECTIONS_RULE}"
            
            sectionizer = nlp.add_pipe('medspacy_sectionizer',
                            config={'rules': None, # init with empty section rules
                                    'require_start_line': True}
                                    , # require the header to be at begin of a line
                                #   'phrase_matcher_attr': 'TEXT'} # require exact match of header text
                    )
            self.load_sections(path_of_resource, sectionizer)
        except Exception as e:
            print(f"Exception adding custom sectionizer: {e}")
            sectionizer = nlp.add_pipe('medspacy_sectionizer') # load the default           
    
        concept_matcher = nlp.add_pipe('medspacy_target_matcher') # add an empty matcher
        concept_rules = list()
        
        # Load concepts and exclusion terms
        try: #if 'medspacy_target_matcher' in resources:
            
            #matcher_resources = resources['medspacy_target_matcher']
            inclusion_lexicon = None
            exclusion_lexicon = None
            #if 'concept_terms' in matcher_resources:
            path_of_resource = f"{project_path_resources}/{CNST.RESOURCE_CONCEPTS}"
                #path_of_resource =matcher_resources['concept_terms']
                #
            inclusion_lexicon = self.load_lexicon(path_of_resource)
            #if 'exclusion_terms' in matcher_resources:
                #path_of_resource = matcher_resources['exclusion_terms']
            # path_of_resource =  f"{project_path_resources}/exclude_terms.txt"     
            # exclusion_lexicon = self.load_excl_terms(path_of_resource)
            concept_rules = self.load_concept_rules(inclusion_lexicon, exclusion_lexicon)
        except Exception as e:
            print(f"Exception loading concept matcher rules: {e}")

        concept_matcher.add(concept_rules) # fill attach the rules to the matcher

        #Load general context       
        
        context_classifier = nlp.add_pipe('medspacy_context', config={"rules": None})  # load the default context component
        try:
            # Attempting to use a custom path for context rules
            path_of_resource = f"{project_path_resources}/{CNST.RESOURCE_CONTEXT_RULES}"
            #print(f"Loading custom context rules from: {path_of_resource}")
            
            # Loading custom rules from the JSON file
            rules = ConTextRule.from_json(path_of_resource)
            # Adding the custom rules to the context classifier
            context_classifier.add(rules)
            
        except Exception as e:
            print(f"Exception loading custom context rules: {e}")
            # Fallback to default context rules
            context_classifier = ConText(nlp, rules='default')

        return nlp, inclusion_lexicon

# Example usage of the Model class
if __name__ == "__main__":
    model = Model()
    # config_json = "H:/Projects/Fred_Spacy/medspacyV_config_V3.json"
    # input_mode = "files" # "files" or "bigquery"
    # input_dir = "C:/CNPA2/sample_notes" # the input path or a query for the notes
    # output_dir="C:/CNPA2/test7"
    # #config_json = "H:/Projects/Fred_Spacy/medspacyV_config_V3.json"
    
    # project_resources_dir="C:/CNPA2/test7/resources"
    # project_path="C:/CNPA2/test7"'

    
    output_file=model.perform_nlp(CNST.INPUT_DIR,
                                  CNST.OUTPUT_DIR, 
                                  CNST.PROJECT_RESOURCES_DIR, 
                                  CNST.PROJECT_PATH, CNST.INPUT_MODE, True)
    print(output_file)
    