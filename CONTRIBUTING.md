# Contributing to medspacyV

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Table of Contents
- [Dev Environment Setup](#dev-environment-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Submitting a PR](#submitting-a-pr)
- [What Not to Change](#what-not-to-change)

---

## Dev Environment Setup

**Requirements:** Python 3.8+, Windows recommended for full GUI testing.

```bash
git clone https://github.com/medspacy/medspacyV
cd medspacyV

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install runtime + dev dependencies
pip install -e ".[dev]"

# Download spacy language model
python -m spacy download en_core_web_sm
```

---

## Running Tests

```bash
# Unit tests only (fast, no disk I/O)
pytest -m unit

# Integration tests (reads from notes/)
pytest -m integration

# All tests with coverage report
pytest --cov=. --cov-report=term-missing
```

Tests live in `tests/` and are split into:
- `test_sanitize_text.py` — pure unit tests for text cleaning logic
- `test_find_sentence_number.py` — pure unit tests for sentence indexing
- `test_csv_loading.py` — integration tests using sample data in `notes/`

---

## Code Style

This project uses **ruff** for linting:

```bash
# Check for issues
ruff check .

# Auto-fix what's possible
ruff check . --fix
```

Please ensure `ruff check .` passes before opening a PR. CI will enforce this.

---

## Submitting a PR

1. Fork the repo and create a branch from `main`
2. Make your changes — **do not modify core NLP/GUI logic** (see below)
3. Add or update tests if applicable
4. Ensure `ruff check .` and `pytest -m unit` pass locally
5. Open a PR against `main` with a clear description of what and why

---

## What Not to Change

The following files contain core logic that should only be modified with explicit discussion:

| File | Why |
|---|---|
| `model.py` | Core NLP pipeline and CSV/text processing |
| `view.py` | Tkinter GUI layout and interactions |
| `controller.py` | MVC wiring between view and model |
| `helper/annotations.py` | Annotation viewer logic |
| `helper/constants.py` | Shared configuration — changes affect the whole app |
| `resources/` | NLP rule files — changes affect extraction results |

For changes to any of the above, please open an issue first to discuss.

---

## Building the EXE Locally

```bash
python assets/create_splash_image.py
pyinstaller controller.spec --noconfirm
# Output: dist/Controller.exe
```

> Note: The EXE is not committed to the repo. Download the latest release from the
> [Releases page](https://github.com/medspacy/medspacyV/releases).
