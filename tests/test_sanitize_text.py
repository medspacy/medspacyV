"""
Unit tests for Model.sanitize_text — no GUI, no NLP pipeline, no disk I/O.
"""
import pytest

from model import Model


@pytest.fixture
def model():
    return Model()


@pytest.mark.unit
class TestSanitizeText:
    def test_none_returns_empty_string(self, model):
        assert model.sanitize_text(None) == ""

    def test_normal_string_unchanged(self, model):
        assert model.sanitize_text("Hello world") == "Hello world"

    def test_null_byte_replaced_with_space(self, model):
        assert model.sanitize_text("abc\x00def") == "abc def"

    def test_non_breaking_space_replaced(self, model):
        assert model.sanitize_text("abc\xa0def") == "abc def"

    def test_newline_preserved(self, model):
        assert model.sanitize_text("line1\nline2") == "line1\nline2"

    def test_tab_preserved(self, model):
        assert model.sanitize_text("col1\tcol2") == "col1\tcol2"

    def test_carriage_return_preserved(self, model):
        assert model.sanitize_text("line1\r\nline2") == "line1\r\nline2"

    def test_control_char_replaced(self, model):
        # \x01 is a control char that should be replaced
        assert model.sanitize_text("abc\x01def") == "abc def"

    def test_non_string_converted(self, model):
        assert model.sanitize_text(12345) == "12345"

    def test_empty_string_unchanged(self, model):
        assert model.sanitize_text("") == ""

    def test_multiple_bad_chars(self, model):
        result = model.sanitize_text("a\x00b\xa0c\x01d")
        assert result == "a b c d"

    def test_length_preserved_after_replacement(self, model):
        original = "abc\x00def"
        result = model.sanitize_text(original)
        assert len(result) == len(original)
