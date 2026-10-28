import os
import tempfile
from pathlib import Path
import pytest

from utils.report_generator import generate_pdf_report, escape_xml


def test_escape_xml_utility():
    assert escape_xml("C++ & Python") == "C++ &amp; Python"
    assert escape_xml("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert escape_xml(None) == ""
    assert escape_xml(100) == "100"


def test_generate_pdf_report_basic():
    sample_data = {
        "company_name": "Google",
        "results": {
            "resume_analysis": {
                "ats_score": 85,
                "summary": "Candidate has strong CS background.",
                "overall_recommendation": "Focus on high-level system design.",
                "strengths": ["Fast learner", "Python & SQL"],
                "weaknesses": ["Lack of cloud certifications"],
                "grammar_suggestions": ["Use active voice"],
                "formatting_suggestions": ["Standardize date formatting"]
            },
            "job_match": {
                "match_percentage": 78,
                "top_5_resume_changes": ["Highlight distributed systems", "Detail backend scalability"]
            },
            "skill_gap": [
                {
                    "skill": "Docker & Kubernetes",
                    "importance": "High",
                    "learning_time": "3 weeks",
                    "learning_resource": "Official Documentation",
                    "project_suggestion": "Containerize microservices app",
                    "priority": "High"
                }
            ],
            "learning_roadmap": [
                {
                    "week": "Week 1",
                    "estimated_hours": 12,
                    "topics": ["Data Structures", "Algorithms <O(N)>"],
                    "coding_practice": ["LeetCode 1 & 2"],
                    "mini_projects": ["Cache implementation"],
                    "interview_questions": ["Explain hash collision & resolution."],
                    "revision_tasks": ["Review time complexities"]
                }
            ],
            "conflicts": []
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "placement_report.pdf"
        result_path = generate_pdf_report(sample_data, str(output_file))

        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 1000  # Generated valid PDF with content


def test_generate_pdf_report_with_special_characters_and_conflicts():
    sample_data_special = {
        "company_name": "AT&T <Global>",
        "results": {
            "overall_recommendation_summary": "Prepare for DSA & System Design with O(N < M) runtime.",
            "resume_analysis": {
                "ats_score": "90",
                "summary": "Proficient in C++ & C# <OOP patterns> & Python 3.11.",
                "strengths": ["C++ & STL", "Complexity < O(N^2)"],
                "weaknesses": ["None & N/A"],
                "grammar_suggestions": ["Avoid 'etc.' & slang"],
                "formatting_suggestions": ["Keep font < 12pt"]
            },
            "job_match": {
                "match_percentage": 88,
                "top_5_resume_changes": ["Replace 'C++' with 'Modern C++ & STL'"]
            },
            "skill_gap": [
                {
                    "skill": "HTML & CSS <Frontend>",
                    "importance": "Medium",
                    "learning_time": "1 week",
                    "learning_resource": "MDN Web Docs & Tutorials",
                    "project_suggestion": "Build responsive page with <canvas> & CSS",
                    "priority": "Medium"
                }
            ],
            "learning_roadmap": [
                {
                    "week": "Week 1",
                    "estimated_hours": 10,
                    "topics": ["Trees & Graphs", "Depth < 100"],
                    "coding_practice": ["Practice BFS & DFS"],
                    "mini_projects": ["Routing & Graph visualizer"],
                    "interview_questions": ["Explain pointers & references in C++."],
                    "revision_tasks": ["Review graph edge cases & cycles"]
                }
            ],
            "conflicts": [
                {
                    "conflict_type": "matched_skill_in_skill_gap",
                    "skill": "C++ & Python",
                    "rule_description": "Skill identified as both matched and missing."
                }
            ]
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "special_char_report.pdf"
        result_path = generate_pdf_report(sample_data_special, str(output_file))

        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 1000


def test_generate_pdf_report_empty_fallback():
    empty_data = {
        "company_name": "",
        "results": {}
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "empty_report.pdf"
        result_path = generate_pdf_report(empty_data, str(output_file))

        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 1000
