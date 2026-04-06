[![CI](https://github.com/medspacy/medspacyV/actions/workflows/ci.yml/badge.svg)](https://github.com/medspacy/medspacyV/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8.20](https://img.shields.io/badge/python-3.8.20-blue.svg)](https://www.python.org/downloads/release/python-3820/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078d4.svg)](https://github.com/medspacy/medspacyV/releases)

# medspacyV: A Visual Interface for the medspacy NLP Pipeline

`medspacyV` is a desktop application specifically for Windows OS that provides a visual interface to interact with the medspacy NLP pipeline. Developed by the Mayo Clinic's Center for Clinical and Translational Science (CCaTS) Informatics Team, it allows users to configure and run medspacy's clinical text processing models without needing to write code.

This application helps in annotating clinical texts, detecting various concepts, and processing notes with a user-friendly graphical interface.

## Project Structure

- **assets/** — Splash screen image and generator script
- **helper/** — Annotation viewer and shared constants
- **resources/** — NLP rule and configuration files (`concepts.xlsx`, `context_rules.json`, `section_rules.tsv`, `sentence_rules.tsv`)
- **tests/** — Unit and integration tests (sample data in `tests/data/`)
- **docs/** — Architecture and reference documentation
- `controller.py` — Entry point, MVC wiring
- `model.py` — Core NLP pipeline and file processing
- `view.py` — Tkinter GUI
- `controller.spec` — PyInstaller build configuration
- `requirements.txt` — Runtime dependencies
- `requirements-dev.txt` — Dev dependencies (includes requirements.txt)
- `setup.cfg` — Tool configuration (pytest, mypy)
- `ruff.toml` — Ruff linter configuration

## Application Preview

<p align="center">
  <img src="./img/home_page.PNG" alt="home"/>
</p>

<p align="center">
  <img src="./img/annote.png" alt="annotation"/>
</p>

## Installation and Setup

> **Just want to run the app?** Download `Controller.exe` from the [Releases page](https://github.com/medspacy/medspacyV/releases) — no Python required.

### Prerequisites (developers only)

- Python 3.8.20

### Clone the Repository

```bash
git clone https://github.com/medspacy/medspacyV
cd medspacyV
```

### Create Virtual Environment and Install Dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt  # includes ruff, pytest, mypy
python -m spacy download en_core_web_sm
```

### Get Started

To launch the application:

```bash
python controller.py
```

### Building the EXE

The EXE is built automatically via GitHub Actions on every release tag (`v*.*.*`). To build locally on Windows:

```bash
pyinstaller controller.spec --noconfirm
# Output: dist/Controller.exe
```
