import json
from utils.gemini import _extract_json_string


def test_extract_clean_json():
    raw = '{"name": "test", "ats_score": 85}'
    extracted = _extract_json_string(raw)
    assert json.loads(extracted) == {"name": "test", "ats_score": 85}


def test_extract_with_markdown_fences():
    raw = '```json\n{"name": "test", "ats_score": 85}\n```'
    extracted = _extract_json_string(raw)
    assert json.loads(extracted) == {"name": "test", "ats_score": 85}


def test_extract_with_conversational_preamble_and_fence():
    raw = (
        "Here is the evaluation report:\n"
        "```json\n"
        '{"name": "test", "ats_score": 85}\n'
        "```\n"
        "Hope this helps!"
    )
    extracted = _extract_json_string(raw)
    assert json.loads(extracted) == {"name": "test", "ats_score": 85}


def test_extract_embedded_without_code_fences():
    raw = 'Sure! The output is {"name": "test", "ats_score": 85}. Let me know.'
    extracted = _extract_json_string(raw)
    assert json.loads(extracted) == {"name": "test", "ats_score": 85}


def test_extract_json_array():
    raw = '```\n[{"name": "Python"}, {"name": "SQL"}]\n```'
    extracted = _extract_json_string(raw)
    data = json.loads(extracted)
    assert len(data) == 2
    assert data[0]["name"] == "Python"


def test_extract_utf8_bom():
    raw = '\ufeff{"name": "test", "ats_score": 85}'
    extracted = _extract_json_string(raw)
    assert json.loads(extracted) == {"name": "test", "ats_score": 85}


def test_extract_empty_string():
    assert _extract_json_string("") == ""
    assert _extract_json_string(None) == ""
