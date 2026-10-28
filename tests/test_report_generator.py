from pathlib import Path

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from utils.report_generator import _escape_pdf_text, generate_pdf_report


def test_escape_pdf_text_preserves_markup_like_text_literally():
    source = "Experience with std::vector<T> & I know <img>"

    paragraph = Paragraph(_escape_pdf_text(source), getSampleStyleSheet()["Normal"])

    assert paragraph.getPlainText() == source


def test_escape_pdf_text_handles_xml_special_characters_and_none():
    assert _escape_pdf_text("R&D <Campus> \"AI\"") == "R&amp;D &lt;Campus&gt; \"AI\""
    assert _escape_pdf_text(None) == ""


def test_pdf_generation_succeeds_with_markup_like_dynamic_text(tmp_path: Path):
    output_path = tmp_path / "placement-report.pdf"
    analysis_data = {
        "company_name": "R&D <Campus>",
        "results": {
            "resume_analysis": {
                "ats_score": 82,
                "summary": "I know <img> and use std::vector<T> & modern C++.",
                "overall_recommendation": "Keep <tags> as literal text & validate output.",
                "strengths": ["C++ templates: std::vector<T> & iterators"],
                "weaknesses": ["Avoid literal <img> markup in generated text"],
                "grammar_suggestions": ["Use A & B correctly"],
                "formatting_suggestions": ["Keep <code> examples readable"],
            },
            "job_match": {
                "match_percentage": 75,
                "top_5_resume_changes": ["Mention std::vector<T> & C++ skills"],
            },
            "skill_gap": [
                {
                    "skill": "std::vector<T>",
                    "importance": "High",
                    "learning_time": "2 weeks",
                    "learning_resource": "Guide <Tutorial> & Docs",
                    "project_suggestion": "Build a parser for <img> text & tags",
                    "priority": "High",
                }
            ],
            "learning_roadmap": [
                {
                    "week": "Week 1 <Basics>",
                    "estimated_hours": 5,
                    "topics": ["C++ <Templates> & generics"],
                    "coding_practice": ["Parse <img> safely"],
                    "mini_projects": ["Build std::vector<T> demo & tests"],
                    "interview_questions": ["Explain <T> & templates"],
                    "revision_tasks": ["Review A & B"],
                }
            ],
        },
    }

    returned_path = generate_pdf_report(analysis_data, str(output_path))

    assert returned_path == str(output_path)
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF-")
    assert output_path.stat().st_size > 0
