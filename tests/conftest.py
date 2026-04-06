import os

import pytest


@pytest.fixture
def notes_csv_dir():
    """Path to the sample CSV test input directory."""
    return os.path.join(os.path.dirname(__file__), "..", "notes", "test_input_csv")


@pytest.fixture
def notes_txt_dir():
    """Path to the sample TXT test input directory."""
    return os.path.join(os.path.dirname(__file__), "..", "notes", "test_input_txt")


@pytest.fixture
def resources_dir():
    """Path to the NLP resource files."""
    return os.path.join(os.path.dirname(__file__), "..", "resources")
