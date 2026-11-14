"""
Test suite for Resume Revision Comparison (#297):
- Comparing a revised resume with a previous analysis for the same target role or company.
- Side-by-side view: ATS score before and after, score difference, skills added/removed, weaknesses fixed/present.
- Purely deterministic code calculation without AI / Gemini calls.
- Small trend chart of ATS score across versions.
- First analysis for a role shows no comparison banner and no error.
- Strict student authorization enforcement.
- Improved, worse, and unchanged resumes.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from flask import json

import config
from app import app
from utils.database import (
    init_db,
    save_analysis,
    get_analysis,
    get_previous_analysis_for_target,
    get_student_versions_for_target
)
from utils.progress_tracker import (
    compare_analysis_versions,
    extract_skills_list,
    extract_weaknesses_list
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_comparison.db"
        monkeypatch.setattr(config, "DATABASE_PATH", db_path)
        init_db()
        yield db_path


# ==============================================================================
# 1. First Analysis for Role: Baseline State (No Error, No Comparison)
# ==============================================================================

def test_first_analysis_for_role_shows_no_comparison_and_no_error(client, test_db):
    """The first analysis for a role shows no comparison banner and no error (Acceptance Criteria)."""
    student_id = "student_first_timer"
    analysis_id = "aid-first-01"

    save_analysis(
        analysis_id=analysis_id,
        resume_filename="first_resume.pdf",
        company_name="Google",
        job_description="Backend Engineer",
        results_dict={
            "resume_analysis": {
                "ats_score": 70,
                "skills": ["Python", "Flask", "SQL"],
                "weaknesses": ["No cloud architecture experience"]
            },
            "job_match": {
                "target_role": "Backend Engineer",
                "match_percentage": 65,
                "matched_skills": ["Python", "SQL"]
            }
        },
        student_id=student_id,
        target_role="Backend Engineer"
    )

    # 1. Dashboard view: renders cleanly without revision comparison banner
    res_dash = client.get(f"/dashboard/{analysis_id}")
    assert res_dash.status_code == 200
    html_dash = res_dash.data.decode("utf-8")
    assert "comparePreviousBanner" not in html_dash

    # 2. Compare view: shows clean baseline state with NO error
    res_compare = client.get(f"/dashboard/{analysis_id}/compare-previous")
    assert res_compare.status_code == 200
    html_compare = res_compare.data.decode("utf-8")
    assert "firstAnalysisNotice" in html_compare
    assert "Initial Baseline Analysis Established" in html_compare
    assert "scoreComparisonRow" not in html_compare

    # 3. API endpoint: returns success with has_previous: False
    res_api = client.get(f"/api/analysis/{analysis_id}/compare-previous")
    assert res_api.status_code == 200
    data = json.loads(res_api.data.decode("utf-8"))
    assert data["status"] == "success"
    assert data["has_previous"] is False


# ==============================================================================
# 2. Improved Resume Comparison
# ==============================================================================

def test_improved_resume_comparison(client, test_db):
    """Upload revised resume with higher ATS score, added skills, and resolved weaknesses."""
    student_id = "student_improver"

    # Version 1 (Baseline)
    save_analysis(
        analysis_id="aid-imp-v1",
        resume_filename="resume_v1.pdf",
        company_name="Amazon",
        job_description="Software Development Engineer",
        results_dict={
            "resume_analysis": {
                "ats_score": 65,
                "skills": ["Java", "SQL"],
                "weaknesses": ["Lacks Docker containerization", "No unit test metrics mentioned"]
            },
            "job_match": {
                "target_role": "Software Development Engineer",
                "match_percentage": 60,
                "matched_skills": ["Java", "SQL"],
                "missing_skills": ["Docker", "Kubernetes", "AWS"]
            }
        },
        student_id=student_id,
        target_role="Software Development Engineer"
    )

    # Version 2 (Revised after feedback)
    save_analysis(
        analysis_id="aid-imp-v2",
        resume_filename="resume_v2.pdf",
        company_name="Amazon",
        job_description="Software Development Engineer",
        results_dict={
            "resume_analysis": {
                "ats_score": 82,
                "skills": ["Java", "SQL", "Docker", "Kubernetes", "AWS", "JUnit"],
                "weaknesses": ["No unit test metrics mentioned"]
            },
            "job_match": {
                "target_role": "Software Development Engineer",
                "match_percentage": 85,
                "matched_skills": ["Java", "SQL", "Docker", "Kubernetes", "AWS"],
                "missing_skills": []
            }
        },
        student_id=student_id,
        target_role="Software Development Engineer"
    )

    # 1. Dashboard offers 'Compare with my previous analysis'
    res_dash = client.get("/dashboard/aid-imp-v2")
    assert res_dash.status_code == 200
    html_dash = res_dash.data.decode("utf-8")
    assert "comparePreviousBanner" in html_dash
    assert "Compare with my previous analysis" in html_dash
    assert "+17 pts Improved" in html_dash

    # 2. Side-by-side comparison view
    res_compare = client.get("/dashboard/aid-imp-v2/compare-previous")
    assert res_compare.status_code == 200
    html_compare = res_compare.data.decode("utf-8")

    assert "65" in html_compare  # ATS before
    assert "82" in html_compare  # ATS after
    assert "+17" in html_compare  # Score difference
    assert "Skills Added" in html_compare
    assert "Docker" in html_compare
    assert "Kubernetes" in html_compare
    assert "Weaknesses Fixed" in html_compare
    assert "Lacks Docker containerization" in html_compare
    assert "Weaknesses Still Present" in html_compare
    assert "No unit test metrics mentioned" in html_compare

    # 3. JSON API
    res_api = client.get("/api/analysis/aid-imp-v2/compare-previous")
    assert res_api.status_code == 200
    data = json.loads(res_api.data.decode("utf-8"))
    assert data["has_previous"] is True
    assert data["score_difference"] == 17
    assert data["comparison"]["status"] == "improved"
    assert "Docker" in data["skills_added"]
    assert "Kubernetes" in data["skills_added"]
    assert "Lacks Docker containerization" in data["weaknesses_fixed"]
    assert "No unit test metrics mentioned" in data["weaknesses_still_present"]


# ==============================================================================
# 3. Worse Resume Comparison (Score Dip)
# ==============================================================================

def test_worse_resume_comparison(client, test_db):
    """Upload revised resume where score decreased and skills were accidentally removed."""
    student_id = "student_dip"

    # Version 1
    save_analysis(
        analysis_id="aid-dip-v1",
        resume_filename="resume_v1.pdf",
        company_name="Microsoft",
        job_description="Cloud Solutions Architect",
        results_dict={
            "resume_analysis": {
                "ats_score": 85,
                "skills": ["Azure", "Terraform", "Python", "Kubernetes"],
                "weaknesses": ["Vague project metrics"]
            },
            "job_match": {
                "target_role": "Cloud Solutions Architect",
                "matched_skills": ["Azure", "Terraform", "Python", "Kubernetes"]
            }
        },
        student_id=student_id,
        target_role="Cloud Solutions Architect"
    )

    # Version 2 (Removed key cloud keywords)
    save_analysis(
        analysis_id="aid-dip-v2",
        resume_filename="resume_v2.pdf",
        company_name="Microsoft",
        job_description="Cloud Solutions Architect",
        results_dict={
            "resume_analysis": {
                "ats_score": 71,
                "skills": ["Python"],
                "weaknesses": ["Vague project metrics", "Missing cloud orchestration experience"]
            },
            "job_match": {
                "target_role": "Cloud Solutions Architect",
                "matched_skills": ["Python"]
            }
        },
        student_id=student_id,
        target_role="Cloud Solutions Architect"
    )

    res_api = client.get("/api/analysis/aid-dip-v2/compare-previous")
    assert res_api.status_code == 200
    data = json.loads(res_api.data.decode("utf-8"))
    assert data["has_previous"] is True
    assert data["score_difference"] == -14
    assert data["comparison"]["status"] == "worse"
    assert data["comparison"]["badge_class"] == "danger"
    assert "Azure" in data["skills_removed"]
    assert "Terraform" in data["skills_removed"]
    assert "Kubernetes" in data["skills_removed"]

    # View route renders score dip
    res_view = client.get("/dashboard/aid-dip-v2/compare-previous")
    assert res_view.status_code == 200
    html = res_view.data.decode("utf-8")
    assert "-14" in html
    assert "Score Dip" in html


# ==============================================================================
# 4. Unchanged Resume Comparison
# ==============================================================================

def test_unchanged_resume_comparison(client, test_db):
    """Upload revised resume with identical score and skills."""
    student_id = "student_same"

    save_analysis(
        analysis_id="aid-same-v1",
        resume_filename="resume_v1.pdf",
        company_name="Google",
        job_description="Site Reliability Engineer",
        results_dict={
            "resume_analysis": {
                "ats_score": 78,
                "skills": ["Linux", "Go", "Prometheus"],
                "weaknesses": ["Lacks incident management examples"]
            },
            "job_match": {
                "target_role": "Site Reliability Engineer",
                "matched_skills": ["Linux", "Go"]
            }
        },
        student_id=student_id,
        target_role="Site Reliability Engineer"
    )

    save_analysis(
        analysis_id="aid-same-v2",
        resume_filename="resume_v2.pdf",
        company_name="Google",
        job_description="Site Reliability Engineer",
        results_dict={
            "resume_analysis": {
                "ats_score": 78,
                "skills": ["Linux", "Go", "Prometheus"],
                "weaknesses": ["Lacks incident management examples"]
            },
            "job_match": {
                "target_role": "Site Reliability Engineer",
                "matched_skills": ["Linux", "Go"]
            }
        },
        student_id=student_id,
        target_role="Site Reliability Engineer"
    )

    res_api = client.get("/api/analysis/aid-same-v2/compare-previous")
    assert res_api.status_code == 200
    data = json.loads(res_api.data.decode("utf-8"))
    assert data["has_previous"] is True
    assert data["score_difference"] == 0
    assert data["comparison"]["status"] == "unchanged"
    assert "Maintained" in data["comparison"]["badge_text"]


# ==============================================================================
# 5. User Data Isolation & Authorization
# ==============================================================================

def test_user_data_isolation_enforcement(client, test_db):
    """It works only with analyses owned by the current user (Acceptance Criteria)."""
    # Create analyses for user_alice
    save_analysis(
        analysis_id="aid-alice-v1",
        resume_filename="alice_v1.pdf",
        company_name="Netflix",
        job_description="Data Engineer",
        results_dict={"resume_analysis": {"ats_score": 70}},
        student_id="user_alice",
        target_role="Data Engineer"
    )
    save_analysis(
        analysis_id="aid-alice-v2",
        resume_filename="alice_v2.pdf",
        company_name="Netflix",
        job_description="Data Engineer",
        results_dict={"resume_analysis": {"ats_score": 85}},
        student_id="user_alice",
        target_role="Data Engineer"
    )

    app.config["ENFORCE_LOGIN_IN_TESTS"] = True
    app.config["ENFORCE_STUDENT_ISOLATION"] = True
    try:
        # Simulate unauthorized visitor or user_bob trying to access alice's comparison
        with client.session_transaction() as sess:
            sess["user_id"] = "user_bob"
            sess["student_id"] = "user_bob"

        # API attempt -> 403 Forbidden
        res_api = client.get("/api/analysis/aid-alice-v2/compare-previous")
        assert res_api.status_code == 403

        # HTML view attempt -> redirect or 403
        res_view = client.get("/dashboard/aid-alice-v2/compare-previous")
        assert res_view.status_code in [302, 403]

        # Authorized user_alice accesses own comparison
        with client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = "user_alice"
            sess["student_id"] = "user_alice"

        res_auth_api = client.get("/api/analysis/aid-alice-v2/compare-previous")
        assert res_auth_api.status_code == 200
        auth_data = json.loads(res_auth_api.data.decode("utf-8"))
        assert auth_data["has_previous"] is True
        assert auth_data["score_difference"] == 15
    finally:
        app.config["ENFORCE_STUDENT_ISOLATION"] = False
        app.config["ENFORCE_LOGIN_IN_TESTS"] = False


# ==============================================================================
# 6. Zero AI Calls During Comparison
# ==============================================================================

def test_zero_ai_calls_during_comparison(client, test_db):
    """Comparison itself must be computed in code, not by another AI call."""
    student_id = "student_code_only"

    save_analysis(
        analysis_id="aid-noai-v1",
        resume_filename="v1.pdf",
        company_name="Oracle",
        job_description="Database Specialist",
        results_dict={"resume_analysis": {"ats_score": 60, "skills": ["SQL"]}},
        student_id=student_id,
        target_role="Database Specialist"
    )

    save_analysis(
        analysis_id="aid-noai-v2",
        resume_filename="v2.pdf",
        company_name="Oracle",
        job_description="Database Specialist",
        results_dict={"resume_analysis": {"ats_score": 75, "skills": ["SQL", "PL/SQL"]}},
        student_id=student_id,
        target_role="Database Specialist"
    )

    # Patch coordinator_agent and genai to fail if called
    with patch("agents.coordinator.CoordinatorAgent.analyze", side_effect=AssertionError("AI Coordinator must NOT be called")), \
         patch("utils.gemini.generate_json_response", side_effect=AssertionError("Gemini generate_json_response must NOT be called")):
        # Call view
        res_view = client.get("/dashboard/aid-noai-v2/compare-previous")
        assert res_view.status_code == 200

        # Call API
        res_api = client.get("/api/analysis/aid-noai-v2/compare-previous")
        assert res_api.status_code == 200
        data = json.loads(res_api.data.decode("utf-8"))
        assert data["score_difference"] == 15


# ==============================================================================
# 7. Trend Chart Across Versions
# ==============================================================================

def test_trend_chart_trajectory(client, test_db):
    """Small trend chart of ATS score across multiple versions for the target."""
    student_id = "student_trend"
    role = "Frontend Developer"
    company = "Airbnb"

    # Save 3 versions
    for v_num, score in [(1, 55), (2, 70), (3, 88)]:
        save_analysis(
            analysis_id=f"aid-trend-v{v_num}",
            resume_filename=f"cv_v{v_num}.pdf",
            company_name=company,
            job_description="Frontend Role",
            results_dict={
                "resume_analysis": {"ats_score": score, "skills": ["React"]},
                "job_match": {"target_role": role, "matched_skills": ["React"]}
            },
            student_id=student_id,
            version_number=v_num,
            target_role=role
        )

    res_api = client.get("/api/analysis/aid-trend-v3/compare-previous")
    assert res_api.status_code == 200
    data = json.loads(res_api.data.decode("utf-8"))
    trend = data["trend_chart"]

    assert len(trend) == 3
    assert [pt["ats_score"] for pt in trend] == [55, 70, 88]

    res_view = client.get("/dashboard/aid-trend-v3/compare-previous")
    assert res_view.status_code == 200
    html = res_view.data.decode("utf-8")
    assert "atsTrendCanvas" in html
    assert "Longitudinal Trajectory" in html
    assert "v3" in html


# ==============================================================================
# 8. Distinct Roles Are Not Falsely Paired
# ==============================================================================

def test_distinct_target_roles_are_not_falsely_paired(client, test_db):
    """Uploading for a new role does not compare with an unrelated previous role."""
    student_id = "student_multi_track"

    # First analysis is for DevOps Engineer
    save_analysis(
        analysis_id="aid-track-devops",
        resume_filename="devops.pdf",
        company_name="AWS",
        job_description="DevOps Engineer",
        results_dict={"resume_analysis": {"ats_score": 80, "skills": ["Terraform", "CI/CD"]}},
        student_id=student_id,
        target_role="DevOps Engineer"
    )

    # Second analysis is for Product Manager
    save_analysis(
        analysis_id="aid-track-pm",
        resume_filename="pm.pdf",
        company_name="Google",
        job_description="Product Manager",
        results_dict={"resume_analysis": {"ats_score": 68, "skills": ["Roadmapping", "Scrum"]}},
        student_id=student_id,
        target_role="Product Manager"
    )

    # Product Manager is the first analysis for that role/company
    res_pm = client.get("/api/analysis/aid-track-pm/compare-previous")
    assert res_pm.status_code == 200
    data_pm = json.loads(res_pm.data.decode("utf-8"))
    assert data_pm["has_previous"] is False
