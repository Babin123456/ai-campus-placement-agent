import tempfile
from pathlib import Path

import config
from utils.database import (
    create_interview_session,
    get_analysis,
    get_interview_session,
    init_db,
    save_analysis,
    update_interview_session,
)


def test_database_lifecycle(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_placement.db"
        monkeypatch.setattr(config, "DATABASE_PATH", test_db_path)

        init_db()
        assert test_db_path.exists()

        analysis_id = "test-uuid-1234"
        sample_results = {
            "resume_analysis": {"ats_score": 85},
            "job_match": {"match_percentage": 90},
        }
        save_analysis(
            analysis_id=analysis_id,
            resume_filename="resume.pdf",
            company_name="Google",
            job_description="Python SDE",
            results_dict=sample_results,
        )

        record = get_analysis(analysis_id)
        assert record is not None
        assert record["company_name"] == "Google"
        assert record["results"]["resume_analysis"]["ats_score"] == 85

        questions = [{"index": 0, "type": "HR", "question": "Tell me about yourself."}]
        create_interview_session(analysis_id, analysis_id, questions)

        session = get_interview_session(analysis_id)
        assert session is not None
        assert len(session["questions"]) == 1
        assert session["completed"] == 0

        update_interview_session(
            interview_id=analysis_id,
            current_question_index=1,
            answers_list=[{"question_index": 0, "answer": "Here is my background."}],
            completed=True,
        )

        updated_session = get_interview_session(analysis_id)
        assert updated_session["completed"] == 1
        assert len(updated_session["answers"]) == 1
