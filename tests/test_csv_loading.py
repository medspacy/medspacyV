"""
Integration tests for Model CSV loading and text processing helpers.
Reads from notes/test_input_csv/ — no GUI, no NLP pipeline.
"""
import io
import os

import pandas as pd
import pytest

from model import Model


@pytest.fixture
def model():
    return Model()


@pytest.mark.integration
class TestCsvLoading:
    def test_sample_csv_has_required_columns(self, notes_csv_dir):
        csv_files = [f for f in os.listdir(notes_csv_dir) if f.endswith(".csv")]
        assert csv_files, "No CSV files found in test_input_csv/"

        for csv_file in csv_files:
            path = os.path.join(notes_csv_dir, csv_file)
            df = pd.read_csv(path)
            assert "doc_name" in df.columns, f"Missing doc_name in {csv_file}"
            assert "note_text" in df.columns, f"Missing note_text in {csv_file}"

    def test_sample_csv_has_rows(self, notes_csv_dir):
        csv_files = [f for f in os.listdir(notes_csv_dir) if f.endswith(".csv")]
        for csv_file in csv_files:
            path = os.path.join(notes_csv_dir, csv_file)
            df = pd.read_csv(path)
            assert len(df) > 0, f"{csv_file} is empty"

    def test_sanitize_survives_csv_content(self, model, notes_csv_dir):
        """sanitize_text should not raise on any cell in the sample CSV."""
        csv_files = [f for f in os.listdir(notes_csv_dir) if f.endswith(".csv")]
        for csv_file in csv_files:
            path = os.path.join(notes_csv_dir, csv_file)
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            for val in df["note_text"]:
                result = model.sanitize_text(val)
                assert isinstance(result, str)

    def test_robust_csv_parsing_with_null_bytes(self, model):
        """Simulate a CSV with null bytes — should parse without error."""
        raw_csv = b"doc_name,note_text\ndoc1,hello\x00world\ndoc2,normal text\n"
        clean = raw_csv.decode("cp1252", errors="replace").replace("\x00", " ")
        df = pd.read_csv(
            io.StringIO(clean),
            engine="python",
            on_bad_lines="warn",
            dtype=str,
            keep_default_na=False,
        )
        assert len(df) == 2
        assert "doc_name" in df.columns
        assert "note_text" in df.columns

    def test_robust_csv_parsing_with_nbsp(self, model):
        """Non-breaking spaces in CSV should be sanitized cleanly."""
        raw = "doc_name,note_text\ndoc1,hello\xa0world\n"
        df = pd.read_csv(
            io.StringIO(raw),
            engine="python",
            on_bad_lines="warn",
            dtype=str,
            keep_default_na=False,
        )
        sanitized = model.sanitize_text(df.loc[0, "note_text"])
        assert "\xa0" not in sanitized
        assert sanitized == "hello world"


@pytest.mark.integration
class TestTxtLoading:
    def test_sample_txt_files_exist(self, notes_txt_dir):
        txt_files = [f for f in os.listdir(notes_txt_dir) if f.endswith(".txt")]
        assert txt_files, "No TXT files found in test_input_txt/"

    def test_sample_txt_files_readable(self, model, notes_txt_dir):
        """All sample txt files should be readable and sanitizable."""
        txt_files = [f for f in os.listdir(notes_txt_dir) if f.endswith(".txt")]
        for txt_file in txt_files:
            path = os.path.join(notes_txt_dir, txt_file)
            with open(path, "rb") as fh:
                raw = fh.read()
            text = model.sanitize_text(raw.decode("cp1252", errors="replace"))
            assert isinstance(text, str)
            assert len(text) > 0
