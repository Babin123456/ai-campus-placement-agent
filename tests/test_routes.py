import tempfile
from pathlib import Path
import pytest

import config
from app import app
from utils.database import init_db, save_analysis, get_interview_session


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"AI Campus" in response.data


def test_dashboard_not_found(client):
    response = client.get("/dashboard/non-existent-id")
    # Redirects to index when not found
    assert response.status_code == 302


def test_interview_not_found(client):
    response = client.get("/interview/non-existent-id")
    # Redirects to index when not found
    assert response.status_code == 302


def test_interview_round_filtering(client, monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_placement.db"
        monkeypatch.setattr(config, "DATABASE_PATH", test_db_path)
        init_db()

        aid = "analysis-round-test-123"
        sample_results = {
            "resume_analysis": {"ats_score": 80},
            "job_match": {"match_percentage": 75},
            "interview_questions": {
                "hr": [f"HR Q{i}" for i in range(1, 6)],
                "technical": [f"Tech Q{i}" for i in range(1, 6)],
                "behavioral": [f"Beh Q{i}" for i in range(1, 6)],
            },
        }
        save_analysis(aid, "resume.pdf", "Google", "SWE", sample_results)

        # Test Technical round session creation
        res_tech = client.get(f"/interview/{aid}?round=Technical")
        assert res_tech.status_code == 200
        session_tech = get_interview_session(f"{aid}_technical")
        assert session_tech is not None
        assert len(session_tech["questions"]) == 5
        assert session_tech["questions"][0]["type"] == "Technical"

        # Test All round session creation
        res_all = client.get(f"/interview/{aid}")
        assert res_all.status_code == 200
        session_all = get_interview_session(aid)
        assert session_all is not None
        assert len(session_all["questions"]) == 15
