# Architecture

## Overview

medspacyV is a Windows desktop application that wraps the [medspacy](https://github.com/medspacy/medspacy) clinical NLP pipeline in a graphical interface. It follows a classic **MVC (Model-View-Controller)** pattern.

```
┌─────────────────────────────────────────────────────────────┐
│                        User (GUI)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ clicks / events
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     view.py  (View)                         │
│  Tkinter GUI — tabs, buttons, directory pickers,            │
│  progress bar, annotation viewer launcher                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  controller.py  (Controller)                │
│  Wires View ↔ Model, manages splash screen,                 │
│  handles threading for long-running NLP jobs                │
└──────────┬──────────────────────────────────────────────────┘
           │ calls
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    model.py  (Model)                        │
│  Initialises medspacy pipeline, reads input files,          │
│  runs NLP, writes Excel + CSV output                        │
└──────────┬──────────────────────────────────────────────────┘
           │ reads
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    resources/  (Config)                     │
│  concepts.xlsx · context_rules.json                         │
│  section_rules.tsv · sentence_rules.tsv                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### `controller.py`
- Entry point — `python controller.py` starts the app
- Instantiates `View` and `Model`
- Passes a `progress_callback` into `model.perform_nlp()` so the GUI progress bar stays live during processing
- Manages the PyInstaller splash screen on startup

### `view.py`
- Pure Tkinter, no business logic
- Two tabs:
  - **Tab 1 — Process Pipeline**: directory pickers, CSV toggle, run button, progress bar, log output
  - **Tab 3 — About**: project info
- Calls into `controller.py` on button press; never calls `model.py` directly
- Launches `AnnotationViewer` (from `helper/annotations.py`) in a new window after processing

### `model.py`
- `init_nlp_pipeline()` — builds the medspacy pipeline:
  1. Tokenizer (`medspacy_tokenizer`)
  2. Sentence splitter (`medspacy_pyrush`) from `sentence_rules.tsv`
  3. Sectionizer (`medspacy_sectionizer`) from `section_rules.tsv`
  4. Target matcher (`medspacy_target_matcher`) from `concepts.xlsx`
  5. Context classifier (`medspacy_context`) from `context_rules.json`
- `process_notes_on_disk()` — iterates over input files (CSV or TXT), runs each note through the pipeline, collects entities, writes chunked Excel + CSV output
- `sanitize_text()` — normalises encoding issues (null bytes, control chars, non-breaking spaces) before text enters the pipeline

### `helper/annotations.py`
- Standalone Tkinter window opened after a run completes
- Reads the Excel output produced by `model.py`
- Displays original note text with colour-coded entity highlights
- Hover tooltip shows entity metadata (negation, family, certainty, section, etc.)
- Supports pagination for large document sets

### `helper/constants.py`
- Single source of truth for column names, file names, colour palette, and pagination limits
- No logic — import-safe from any module

---

## Data Flow

```
Input (CSV or TXT files)
        │
        ▼
model.sanitize_text()        ← encoding normalisation
        │
        ▼
medspacy pipeline             ← tokenise → sentence split → sectionise
        │                          → match concepts → apply context
        ▼
List of entity dicts          ← doc_name, concept, matched_text,
        │                          start/end offsets, section, flags
        ▼
pd.DataFrame → Excel + CSV   ← chunked by MAX_DOCS (100) per file
        │
        ▼
AnnotationViewer              ← reads Excel, highlights text
```

---

## Resource Files

| File | Format | Purpose |
|---|---|---|
| `concepts.xlsx` | Excel | Inclusion lexicon: concept ID, category, term/regex, case sensitivity |
| `context_rules.json` | JSON | ConText rules: negation, family, uncertainty, historical, hypothetical |
| `section_rules.tsv` | TSV | Section headers and their canonical IDs |
| `sentence_rules.tsv` | TSV | PyRuSH sentence splitting rules |

All resource files are loaded at pipeline initialisation time. They can be customised per project via the GUI's "Advanced Settings" dialogs.

---

## Output Structure

Each run creates a timestamped folder:

```
output_dir/
└── 2025-01-15_10-30-00/
    ├── csv/
    │   ├── projectname_2025-01-15_10-30-00_csv_part1.csv
    │   └── ...
    └── xlsx/
        ├── projectname_2025-01-15_10-30-00_csv_part1.xlsx
        └── ...
```

The annotation viewer reads from the `xlsx/` folder.

---

## Building the EXE

The app is distributed as a standalone Windows executable built with PyInstaller:

```
controller.py  ──► PyInstaller (controller.spec) ──► dist/Controller.exe
```

`controller.spec` bundles:
- All Python source files
- The `resources/` folder (copied into the exe)
- The splash screen image

Releases are built automatically via `.github/workflows/release.yml` on `git tag v*.*.*`.
