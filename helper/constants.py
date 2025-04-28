# Controller Constants
INPUT_MODE = "files"

# Model Constants
# sectionizer constants
SECTION_ID = "SEC_ID"
LITERAL = "literal"
CATEGORY = "category"
DOC_ID = "doc_name"
MAX_DOCS = 100
MAX_FILES_PER_PAGE = 25

# lexicon constants
LEXICON_COLS = ['CONCEPT_ID', 'CONCEPT_CATEGORY', 'TERM_OR_REGEX', 'CASE_SENSITIVITY', 'REGULAR_EXPRESSION']
REGEX_LETTERS = r'[^a-zA-Z]'

# main constants
INPUT_DIR = r"C:\Users\M314694\Desktop\Application\cheack\test_notes"
OUTPUT_DIR = r"C:\Users\M314694\Desktop\Application\cheack"
PROJECT_RESOURCES_DIR = r"C:\Users\M314694\Desktop\Application\cheack\resources"
PROJECT_PATH = r"C:\Users\M314694\Desktop\Application\cheack"

# Annotations
NOTES_DIR = r"C:\Users\M314694\Desktop\Python_Package\sample_notes\sample_notes"
OUTPUT_PATH = r"H:\Projects\Fred_MedSpacy\test8\Fred_MedSpacy_2024-04-19_11-20-51.xlsx"
COLOR_LIST = ['#E69F00',
              '#56B4E9',
              '#009E73',
              '#F0E442',
              '#0072B2',
              '#D55E00',
              '#CC79A7',
              '#F0A500',
              '#3CBB75',
              '#E41A1C'
              ]

OUTPUT_HEADERS = [
    "doc_name", "concept", "matched_text", "concept_start", "concept_end", 
    "sentence", "sentence_start", "sentence_end", "section_id", "matched_section_header", 
    "is_negated", "is_family", "is_uncertain", "is_historical", "is_hypothetical"
]

RESOURCE_SECTIONS_RULE = "section_rules.tsv"
RESOURCE_SENTENCE_RULE = "sentence_rules.tsv"
RESOURCE_CONCEPTS = "concepts.xlsx"
RESOURCE_CONTEXT_RULES = "context_rules.json"
RESOURCE_EXCLUDE_TERMS = "exclude_terms.txt"

DEBUG_LOG_FILE = "debug.log"