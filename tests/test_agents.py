import pytest

from agents.interview_agent import InterviewAgent
from agents.job_match_agent import JobMatchAgent
from agents.resume_agent import ResumeAgent
from agents.roadmap_agent import RoadmapAgent
from agents.skill_gap_agent import SkillGapAgent


def test_resume_agent_processing():
    agent = ResumeAgent()
    raw = {
        "ats_score": "82",
        "summary": "Experienced python developer",
        "strengths": ["Python", "Flask"],
        "weaknesses": ["Docker"],
        "grammar_suggestions": ["Improve action verbs"],
        "formatting_suggestions": ["Use 10pt font"],
        "project_feedback": "Projects demonstrate good API design",
        "experience_feedback": "Bullet points are strong",
        "missing_skills": ["Kubernetes"],
        "overall_recommendation": "Ready for backend interviews",
    }
    processed = agent.process(raw)
    assert processed["ats_score"] == 82
    assert processed["strengths"] == ["Python", "Flask"]
    assert "Kubernetes" in processed["missing_skills"]


def test_resume_agent_handles_invalid_data():
    agent = ResumeAgent()
    processed = agent.process(None)
    assert processed["ats_score"] == 0
    assert isinstance(processed["strengths"], list)
    assert isinstance(processed["summary"], str)


def test_job_match_agent_processing():
    agent = JobMatchAgent()
    raw = {
        "match_percentage": 75,
        "matched_skills": ["Python", "SQL"],
        "missing_skills": ["AWS"],
        "required_certifications": ["AWS Certified"],
        "recommended_improvements": ["Add cloud project"],
        "top_5_resume_changes": ["Update header", "List SQL first"],
    }
    processed = agent.process(raw)
    assert processed["match_percentage"] == 75
    assert len(processed["top_5_resume_changes"]) <= 5
    assert "Python" in processed["matched_skills"]


def test_skill_gap_agent_processing():
    agent = SkillGapAgent()
    raw = [
        {
            "skill": "Docker",
            "importance": "high",
            "difficulty": "medium",
            "learning_time": "1 week",
            "learning_resource": "Docker Docs",
            "project_suggestion": "Containerize Flask app",
            "priority": "high",
        }
    ]
    processed = agent.process(raw)
    assert len(processed) == 1
    assert processed[0]["skill"] == "Docker"
    assert processed[0]["importance"] == "High"
    assert processed[0]["difficulty"] == "Medium"


def test_roadmap_agent_enforces_six_weeks():
    agent = RoadmapAgent()
    processed = agent.process([])
    assert len(processed) == 6
    for idx, week in enumerate(processed, 1):
        assert week["week"] == f"Week {idx}"
        assert week["estimated_hours"] >= 1


def test_interview_agent_enforces_five_questions_per_category():
    agent = InterviewAgent()
    raw = {
        "hr": ["Q1", "Q2"],
        "technical": ["Tech 1"],
        "behavioral": [],
    }
    processed = agent.process(raw)
    assert len(processed["hr"]) == 5
    assert len(processed["technical"]) == 5
    assert len(processed["behavioral"]) == 5
