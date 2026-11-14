"""
Unit and Integration Tests for Input-Hash Placement Analysis Caching (#296)
===========================================================================
Validates acceptance criteria:
1. Identical input does not call the AI a second time within the expiry window.
2. Changing any of the three inputs (resume text, job description, target company)
   creates a fresh analysis.
3. The "Re-run" button forces a new analysis, bypassing the cache.
4. Tests cover cache hit, cache miss, expiration, and forced re-run.
5. The cache persists only cryptographic hashes and timestamps without storing
   duplicate resume text or personal details.
"""

import io
import time
import json
import sqlite3
from unittest.mock import MagicMock, patch
import pytest

import config
from app import app
from utils.database import init_db, get_db_connection, save_analysis, get_analysis
from utils.analysis_cache import (
    normalize_text,
    compute_analysis_hash,
    get_cached_analysis_id,
    get_cached_analysis,
    set_cached_analysis,
    invalidate_cache_entry,
    clear_expired_cache,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Ensure a fresh SQLite database and clean cache for each test."""
    test_db_path = str(tmp_path / "test_cache.db")
    monkeypatch.setattr(config, "DATABASE_PATH", test_db_path)
    monkeypatch.setattr(config, "ANALYSIS_CACHE_ENABLED", True)
    monkeypatch.setattr(config, "ANALYSIS_CACHE_EXPIRY_SECONDS", 86400)
    init_db()
    yield test_db_path


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


SAMPLE_RESUME_1 = """
Alex Mercer
Email: alex.mercer@example.com | Phone: +1-555-0199
Education: B.S. in Computer Science, Tech University
Skills: Python, Django, PostgreSQL, Docker, Redis
Experience: Software Developer Intern at CloudCorp
- Implemented high-throughput REST APIs handling 10k RPM
- Automated deployment scripts reducing build times by 40%
"""

SAMPLE_RESUME_2 = """
Jordan Lee
Email: jordan.lee@example.com
Education: B.Tech Information Technology
Skills: Java, Spring Boot, MySQL, AWS
Experience: Backend Engineering Intern at DevBase
"""

SAMPLE_JD_1 = "Looking for a Backend Software Engineer proficient in Python, SQL, and Docker."
SAMPLE_JD_2 = "Frontend Developer needed with React, TypeScript, and Tailwind experience."

MOCK_ANALYSIS_PAYLOAD = {
    "resume_analysis": {
        "ats_score": 85,
        "strengths": ["Clear technical stack", "Quantifiable impact"],
        "weaknesses": ["Add more cloud metrics"],
        "formatting_suggestions": ["Standardize date formats"],
        "grammar_suggestions": []
    },
    "job_match": {
        "match_percentage": 82,
        "matched_skills": ["Python", "Docker", "SQL"],
        "missing_skills": ["Kubernetes"],
        "top_5_resume_changes": ["Highlight container experience"]
    },
    "skill_gap": [
        {
            "skill": "Kubernetes",
            "importance": "High",
            "learning_resource": "https://kubernetes.io/docs/",
            "learning_time": "2 weeks"
        }
    ],
    "learning_roadmap": [
        {
            "week": "Week 1",
            "topics": ["Container Orchestration"],
            "coding_practice": ["Minikube setup"]
        }
    ],
    "interview_questions": {
        "technical": ["Explain Docker container lifecycles."],
        "hr": ["Why do you want to join our engineering team?"],
        "behavioral": ["Tell me about a time you optimized a slow database query."]
    },
    "overall_recommendation_summary": "Strong candidate with solid backend engineering background."
}


# ==============================================================================
# 1. Normalization & SHA-256 Hashing Unit Tests
# ==============================================================================

class TestAnalysisCacheHashing:
    """Verifies deterministic SHA-256 hashing and whitespace normalization."""

    def test_normalize_text_whitespace_and_crlf(self):
        raw = "   Line 1 with   multiple   spaces  \r\n\r\n  Line 2   \twith tab  \r\n"
        normalized = normalize_text(raw)
        assert "\r" not in normalized
        assert normalized == "Line 1 with multiple spaces\n\nLine 2 with tab"

    def test_compute_analysis_hash_deterministic(self):
        hash1 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        hash2 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        assert len(hash1) == 64
        assert hash1 == hash2

    def test_compute_analysis_hash_case_and_spacing_insensitivity_for_company(self):
        hash1 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        hash2 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "  google  ")
        hash3 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "GOOGLE")
        assert hash1 == hash2 == hash3

    def test_compute_analysis_hash_changes_when_resume_changes(self):
        hash1 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        hash2 = compute_analysis_hash(SAMPLE_RESUME_2, SAMPLE_JD_1, "Google")
        assert hash1 != hash2

    def test_compute_analysis_hash_changes_when_jd_changes(self):
        hash1 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        hash2 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_2, "Google")
        assert hash1 != hash2

    def test_compute_analysis_hash_changes_when_company_changes(self):
        hash1 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        hash2 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Amazon")
        assert hash1 != hash2

    def test_cache_stores_only_hash_no_extra_personal_data(self):
        """Verifies that the cache table stores only hash, IDs and timestamps."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(analysis_cache)")
        cols = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected_cols = {"input_hash", "student_id", "analysis_id", "created_at", "expires_at"}
        assert cols == expected_cols, f"Unexpected columns found in analysis_cache: {cols}"
        assert "resume_text" not in cols
        assert "email" not in cols
        assert "phone" not in cols


# ==============================================================================
# 2. Database Cache Expiry, Invalidation & Retrieval Tests
# ==============================================================================

class TestAnalysisCacheStorageAndExpiry:
    """Verifies SQLite storage, TTL expiration checks, and invalidation."""

    def test_set_and_get_cached_analysis_happy_path(self):
        analysis_id = "test-uuid-101"
        save_analysis(
            analysis_id=analysis_id,
            resume_filename="resume.pdf",
            company_name="Google",
            job_description=SAMPLE_JD_1,
            results_dict=MOCK_ANALYSIS_PAYLOAD,
            student_id="student_1"
        )

        input_hash = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        set_cached_analysis(input_hash, analysis_id, student_id="student_1", ttl_seconds=3600)

        # Lookup
        found_id = get_cached_analysis_id(input_hash, student_id="student_1")
        assert found_id == analysis_id

        cached_rec = get_cached_analysis(input_hash, student_id="student_1")
        assert cached_rec is not None
        assert cached_rec["id"] == analysis_id
        assert cached_rec["from_cache"] is True
        assert cached_rec["is_cached"] is True

    def test_cache_miss_on_unknown_hash(self):
        unknown_hash = "0" * 64
        assert get_cached_analysis_id(unknown_hash, student_id="student_1") is None
        assert get_cached_analysis(unknown_hash, student_id="student_1") is None

    def test_cache_miss_on_expired_entry(self):
        analysis_id = "test-uuid-expired"
        save_analysis(
            analysis_id=analysis_id,
            resume_filename="resume.pdf",
            company_name="Google",
            job_description=SAMPLE_JD_1,
            results_dict=MOCK_ANALYSIS_PAYLOAD,
            student_id="student_1"
        )

        input_hash = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        # Created 25 hours ago with 24 hours TTL
        now = time.time()
        past_created = now - (25 * 3600)
        set_cached_analysis(
            input_hash,
            analysis_id,
            student_id="student_1",
            ttl_seconds=86400,
            created_at=past_created
        )

        # Querying now should identify it as expired, purge it, and return None
        found_id = get_cached_analysis_id(input_hash, student_id="student_1", current_time=now)
        assert found_id is None
        assert get_cached_analysis(input_hash, student_id="student_1", current_time=now) is None

    def test_clear_expired_cache_cleans_only_expired_records(self):
        analysis_id_1 = "test-active"
        analysis_id_2 = "test-expired"

        save_analysis(
            analysis_id=analysis_id_1,
            resume_filename="resume.pdf",
            company_name="Google",
            job_description=SAMPLE_JD_1,
            results_dict=MOCK_ANALYSIS_PAYLOAD,
            student_id="student_1"
        )
        save_analysis(
            analysis_id=analysis_id_2,
            resume_filename="resume.pdf",
            company_name="Amazon",
            job_description=SAMPLE_JD_1,
            results_dict=MOCK_ANALYSIS_PAYLOAD,
            student_id="student_1"
        )

        now = time.time()
        hash1 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        hash2 = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Amazon")

        # Active entry: valid for next 2 hours
        set_cached_analysis(hash1, analysis_id_1, student_id="student_1", ttl_seconds=7200, created_at=now)
        # Expired entry: created 10 hours ago with 1 hour TTL
        set_cached_analysis(hash2, analysis_id_2, student_id="student_1", ttl_seconds=3600, created_at=now - 36000)

        purged_count = clear_expired_cache(current_time=now)
        assert purged_count == 1

        assert get_cached_analysis_id(hash1, student_id="student_1", current_time=now) == analysis_id_1
        assert get_cached_analysis_id(hash2, student_id="student_1", current_time=now) is None

    def test_invalidate_cache_entry_by_hash_and_analysis_id(self):
        analysis_id = "test-inv"
        save_analysis(
            analysis_id=analysis_id,
            resume_filename="resume.pdf",
            company_name="Google",
            job_description=SAMPLE_JD_1,
            results_dict=MOCK_ANALYSIS_PAYLOAD,
            student_id="student_1"
        )
        input_hash = compute_analysis_hash(SAMPLE_RESUME_1, SAMPLE_JD_1, "Google")
        set_cached_analysis(input_hash, analysis_id, student_id="student_1")

        assert get_cached_analysis_id(input_hash, student_id="student_1") == analysis_id
        invalidate_cache_entry(analysis_id=analysis_id)
        assert get_cached_analysis_id(input_hash, student_id="student_1") is None


# ==============================================================================
# 3. Acceptance Criteria Integration Tests (/analyze, /api/analysis/start, rerun)
# ==============================================================================

class TestAnalysisCacheIntegration:
    """Verifies end-to-end cache hit, miss, re-run, and dashboard rendering."""

    @patch("agents.coordinator.CoordinatorAgent.analyze")
    def test_identical_input_does_not_call_ai_a_second_time(self, mock_analyze, client):
        """Criterion 1: Identical input within expiry window does not call Gemini AI."""
        mock_analyze.return_value = MOCK_ANALYSIS_PAYLOAD

        with client.session_transaction() as sess:
            sess["user_id"] = "student_cache_test"

        # 1. First submission (Cache Miss)
        resp1 = client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        }, follow_redirects=False)

        assert resp1.status_code == 302
        first_location = resp1.headers["Location"]
        assert "/dashboard/" in first_location
        assert mock_analyze.call_count == 1

        # 2. Second submission with identical inputs (Cache Hit)
        resp2 = client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        }, follow_redirects=False)

        assert resp2.status_code == 302
        second_location = resp2.headers["Location"]
        assert "/dashboard/" in second_location
        assert "from_cache=1" in second_location
        # AI coordinator MUST NOT have been called a second time
        assert mock_analyze.call_count == 1

    @patch("agents.coordinator.CoordinatorAgent.analyze")
    def test_changing_any_input_creates_fresh_analysis(self, mock_analyze, client):
        """Criterion 2: Modifying resume, JD, or company results in a cache miss and new AI call."""
        mock_analyze.return_value = MOCK_ANALYSIS_PAYLOAD

        with client.session_transaction() as sess:
            sess["user_id"] = "student_cache_test"

        # Base submission
        client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        })
        assert mock_analyze.call_count == 1

        # Change resume text -> Fresh call
        client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_2,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        })
        assert mock_analyze.call_count == 2

        # Change company name -> Fresh call
        client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Microsoft",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        })
        assert mock_analyze.call_count == 3

        # Change job description -> Fresh call
        client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_2,
            "privacy_consent": "true"
        })
        assert mock_analyze.call_count == 4

    @patch("agents.coordinator.CoordinatorAgent.analyze")
    def test_rerun_button_forces_new_analysis(self, mock_analyze, client):
        """Criterion 3: The 'Re-run' button or rerun flag forces a new analysis bypassing cache."""
        mock_analyze.return_value = MOCK_ANALYSIS_PAYLOAD

        with client.session_transaction() as sess:
            sess["user_id"] = "student_cache_test"

        # 1. Initial submission
        resp1 = client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        }, follow_redirects=False)
        analysis_id = resp1.headers["Location"].split("/dashboard/")[1].split("?")[0]
        assert mock_analyze.call_count == 1

        # 2. Trigger re-run via /analyze/rerun/<analysis_id>
        rerun_resp = client.post(f"/analyze/rerun/{analysis_id}", follow_redirects=False)
        assert rerun_resp.status_code == 302
        new_location = rerun_resp.headers["Location"]
        assert "/dashboard/" in new_location
        assert "from_cache=1" not in new_location
        # Coordinator was invoked again
        assert mock_analyze.call_count == 2

        # 3. Submitting via /analyze with rerun=true query or form param also forces fresh call
        client.post("/analyze?rerun=true", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        })
        assert mock_analyze.call_count == 3

    @patch("agents.coordinator.CoordinatorAgent.analyze")
    def test_dashboard_renders_loaded_from_previous_analysis_note_and_rerun_button(self, mock_analyze, client):
        """Criterion 4: Dashboard displays 'Loaded from previous analysis' note and 'Re-run' button on hit."""
        mock_analyze.return_value = MOCK_ANALYSIS_PAYLOAD

        with client.session_transaction() as sess:
            sess["user_id"] = "student_cache_test"

        # First run to populate analysis in database
        resp = client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        }, follow_redirects=False)
        analysis_id = resp.headers["Location"].split("/dashboard/")[1].split("?")[0]

        # View dashboard as cached hit (?from_cache=1)
        dash_cached = client.get(f"/dashboard/{analysis_id}?from_cache=1")
        assert dash_cached.status_code == 200
        html = dash_cached.data.decode("utf-8")

        assert "Loaded from previous analysis" in html
        assert "cachedAnalysisBanner" in html
        assert "btnRerunAnalysis" in html
        assert "Re-run Analysis" in html
        assert f"/analyze/rerun/{analysis_id}" in html

        # View normal dashboard without from_cache: banner should NOT appear
        dash_fresh = client.get(f"/dashboard/{analysis_id}")
        assert dash_fresh.status_code == 200
        html_fresh = dash_fresh.data.decode("utf-8")
        assert "cachedAnalysisBanner" not in html_fresh
        assert "Loaded from previous analysis" not in html_fresh

    @patch("agents.coordinator.CoordinatorAgent.analyze")
    def test_api_async_start_endpoint_returns_cached_status(self, mock_analyze, client):
        """API /api/analysis/start endpoint leverages hash caching."""
        mock_analyze.return_value = MOCK_ANALYSIS_PAYLOAD

        with client.session_transaction() as sess:
            sess["user_id"] = "student_cache_test"

        # Pre-seed cache
        client.post("/analyze", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        })
        assert mock_analyze.call_count == 1

        # Request via REST API
        api_resp = client.post("/api/analysis/start", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        })
        assert api_resp.status_code == 200
        data = api_resp.get_json()
        assert data["success"] is True
        assert data["cached"] is True
        assert data["status"] == "cached"
        assert "from_cache=1" in data["redirect_url"]
        # No extra AI call was made
        assert mock_analyze.call_count == 1

        # Request via REST API with force_rerun=true
        rerun_resp = client.post("/api/analysis/start?force_rerun=true", data={
            "resume_text": SAMPLE_RESUME_1,
            "company": "Google",
            "job_description": SAMPLE_JD_1,
            "privacy_consent": "true"
        })
        assert rerun_resp.status_code == 202
        rerun_data = rerun_resp.get_json()
        assert rerun_data["status"] == "started"
        assert "task_id" in rerun_data
