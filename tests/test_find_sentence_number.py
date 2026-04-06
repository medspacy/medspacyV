"""
Unit tests for the find_sentence_number logic — no GUI, no Tkinter, no disk I/O.

We copy the pure algorithm here rather than importing AnnotationViewer (which
pulls in Tkinter and requires a display, causing failures on headless CI runners).
"""
import pytest


def find_sentence_number(text: str, char_index: int):
    """
    Exact copy of AnnotationViewer.find_sentence_number for headless testing.
    Returns (sentence_number, chars_before_sentence) or (-1, -1) if out of bounds.
    """
    sentences = text.split("\n")
    current_index = 0
    sentence_number = 0
    chars_until_previous_sentence = 0

    for sentence in sentences:
        current_index += len(sentence) + 1
        if char_index < current_index:
            return sentence_number + 1, chars_until_previous_sentence
        chars_until_previous_sentence = current_index
        sentence_number += 1

    return -1, -1


@pytest.mark.unit
class TestFindSentenceNumber:
    def test_first_sentence_first_char(self):
        sent_num, chars_before = find_sentence_number("Hello\nWorld", 0)
        assert sent_num == 1
        assert chars_before == 0

    def test_first_sentence_last_char(self):
        sent_num, chars_before = find_sentence_number("Hello\nWorld", 4)
        assert sent_num == 1
        assert chars_before == 0

    def test_second_sentence_first_char(self):
        # "Hello\n" = 6 chars, index 6 is start of "World"
        sent_num, chars_before = find_sentence_number("Hello\nWorld", 6)
        assert sent_num == 2
        assert chars_before == 6

    def test_second_sentence_mid_char(self):
        sent_num, chars_before = find_sentence_number("Hello\nWorld", 8)
        assert sent_num == 2
        assert chars_before == 6

    def test_out_of_bounds_returns_minus_one(self):
        sent_num, chars_before = find_sentence_number("Hello\nWorld", 999)
        assert sent_num == -1
        assert chars_before == -1

    def test_single_line_no_newline(self):
        sent_num, chars_before = find_sentence_number("OneLine", 3)
        assert sent_num == 1
        assert chars_before == 0

    def test_three_sentences(self):
        text = "First\nSecond\nThird"
        # "First\n"=6, "Second\n"=7 → index 13 is start of "Third"
        sent_num, chars_before = find_sentence_number(text, 13)
        assert sent_num == 3
        assert chars_before == 13

    def test_empty_text_out_of_bounds(self):
        sent_num, chars_before = find_sentence_number("", 0)
        assert sent_num == -1
        assert chars_before == -1

    def test_index_at_newline_boundary(self):
        # "Hello" = 5 chars, newline at index 5 → belongs to sentence 1
        sent_num, chars_before = find_sentence_number("Hello\nWorld", 5)
        assert sent_num == 1
        assert chars_before == 0
