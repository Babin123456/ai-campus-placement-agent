import pytest
from utils.pdf_reader import (
    validate_resume_text,
    MIN_RESUME_TEXT_CHARS,
    MIN_RESUME_WORD_COUNT,
    MAX_RESUME_TEXT_CHARS,
    MAX_PDF_PAGES,
)
from app import app


def test_validate_resume_text_empty():
    is_valid, msg = validate_resume_text("")
    assert not is_valid
    assert "empty" in msg.lower()

    is_valid, msg = validate_resume_text("   \n\t  ")
    assert not is_valid


def test_validate_resume_text_too_short():
    short_text = "I am a programmer."
    is_valid, msg = validate_resume_text(short_text)
    assert not is_valid
    assert f"minimum {MIN_RESUME_TEXT_CHARS}" in msg


def test_validate_resume_text_insufficient_words():
    # Length > 50 chars but only 4 words
    text_few_words = "Supercalifragilisticexpialidocious " * 3
    is_valid, msg = validate_resume_text(text_few_words)
    assert not is_valid
    assert f"at least {MIN_RESUME_WORD_COUNT} words" in msg


def test_validate_resume_text_valid():
    valid_resume = (
        "BTech Computer Science graduate with strong foundation in Python, Java, Data Structures, "
        "and SQL. Developed multiple full-stack web applications and REST APIs using Flask and Docker."
    )
    is_valid, msg = validate_resume_text(valid_resume)
    assert is_valid
    assert msg == ""


def test_analyze_route_rejects_empty_and_short_pasted_text():
    app.config["TESTING"] = True
    with app.test_client() as client:
        # No input
        res = client.post("/analyze", data={}, follow_redirects=True)
        assert res.status_code == 200
        assert b"Please upload a PDF resume or paste your resume text" in res.data

        # Too short pasted text
        res = client.post("/analyze", data={"resume_text": "Hi"}, follow_redirects=True)
        assert res.status_code == 200
        assert b"too short" in res.data
