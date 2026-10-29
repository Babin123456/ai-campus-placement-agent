import sqlite3
import json
import logging
import config

logger = logging.getLogger(__name__)

def get_db_connection() -> sqlite3.Connection:
    """
    Establishes and returns a connection to the SQLite database.
    Sets row_factory to sqlite3.Row for dictionary-like access.
    Configures WAL mode and busy timeout to avoid database lock errors.
    """
    conn = sqlite3.connect(config.DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None:
    """
    Initializes the database tables (analyses, interviews) if they do not exist.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Table 1: Store placement analysis findings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                resume_filename TEXT NOT NULL,
                company_name TEXT NOT NULL,
                job_description TEXT,
                results_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: Store mock interview progress & evaluations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                current_question_index INTEGER NOT NULL DEFAULT 0,
                questions_json TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (analysis_id) REFERENCES analyses (id)
            )
        """)
        
        # Indexes for query and sorting performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses (created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_analysis_id ON interviews (analysis_id)")
        
        conn.commit()
        logger.info("Database schema checked and initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database: {str(e)}")
        raise e
    finally:
        conn.close()

def save_analysis(analysis_id: str, resume_filename: str, company_name: str, job_description: str, results_dict: dict) -> None:
    """
    Inserts a newly generated coordinator analysis into the database.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analyses (id, resume_filename, company_name, job_description, results_json)
            VALUES (?, ?, ?, ?, ?)
        """, (analysis_id, resume_filename, company_name, job_description, json.dumps(results_dict)))
        conn.commit()
        logger.info(f"Analysis saved to database with ID: {analysis_id}")
    except Exception as e:
        logger.error(f"Error saving analysis {analysis_id} to database: {str(e)}")
        raise e
    finally:
        conn.close()

def get_analysis(analysis_id: str) -> dict:
    """
    Retrieves and returns an analysis record by ID.
    Loads and injects the deserialized JSON results.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        row = cursor.fetchone()
        if row:
            record = dict(row)
            record["results"] = json.loads(record["results_json"])
            return record
        return None
    except Exception as e:
        logger.error(f"Error fetching analysis {analysis_id}: {str(e)}")
        raise e
    finally:
        conn.close()

def create_interview_session(interview_id: str, analysis_id: str, questions_list: list) -> None:
    """
    Creates a new mock interview session referencing an analysis.
    Stores the list of 15 generated questions (HR, Technical, Behavioral).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interviews (id, analysis_id, current_question_index, questions_json, answers_json, completed)
            VALUES (?, ?, 0, ?, ?, 0)
        """, (interview_id, analysis_id, json.dumps(questions_list), json.dumps([])))
        conn.commit()
        logger.info(f"Interview session initialized with ID: {interview_id}")
    except Exception as e:
        logger.error(f"Error initializing interview session {interview_id}: {str(e)}")
        raise e
    finally:
        conn.close()

def get_interview_session(interview_id: str) -> dict:
    """
    Retrieves and returns an interview session record by ID.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
        row = cursor.fetchone()
        if row:
            record = dict(row)
            record["questions"] = json.loads(record["questions_json"])
            record["answers"] = json.loads(record["answers_json"])
            return record
        return None
    except Exception as e:
        logger.error(f"Error fetching interview session {interview_id}: {str(e)}")
        raise e
    finally:
        conn.close()

def update_interview_session(interview_id: str, current_question_index: int, answers_list: list, completed: bool) -> None:
    """
    Updates the progress, answer list, and completion status of an active interview session.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE interviews
            SET current_question_index = ?, answers_json = ?, completed = ?
            WHERE id = ?
        """, (current_question_index, json.dumps(answers_list), 1 if completed else 0, interview_id))
        conn.commit()
        logger.info(f"Interview session {interview_id} updated. Current index: {current_question_index}. Completed: {completed}")
    except Exception as e:
        logger.error(f"Error updating interview session {interview_id}: {str(e)}")
        raise e
    finally:
        conn.close()

def get_recent_analyses(limit: int = 10) -> list:
    """
    Retrieves the most recent analysis sessions ordered by created_at DESC.
    Includes parsed resume ATS score and company match percentage for quick display.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, resume_filename, company_name, job_description, results_json, created_at
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?
        """, (max(1, min(limit, 50)),))
        rows = cursor.fetchall()
        recent = []
        for row in rows:
            record = dict(row)
            try:
                parsed_results = json.loads(record.pop("results_json", "{}"))
                resume_analysis = parsed_results.get("resume_analysis", {})
                job_match = parsed_results.get("job_match", {})
                record["ats_score"] = resume_analysis.get("ats_score", 0)
                record["match_percentage"] = job_match.get("match_percentage", 0)
            except Exception:
                record["ats_score"] = 0
                record["match_percentage"] = 0
            recent.append(record)
        return recent
    except Exception as e:
        logger.error(f"Error fetching recent analyses: {str(e)}")
        raise e
    finally:
        conn.close()

def delete_analysis(analysis_id: str) -> bool:
    """
    Deletes an analysis record and its corresponding interview sessions.
    Returns True if an analysis was deleted, False if not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM interviews WHERE analysis_id = ?", (analysis_id,))
        cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted analysis {analysis_id} and associated interview data.")
        return deleted
    except Exception as e:
        logger.error(f"Error deleting analysis {analysis_id}: {str(e)}")
        raise e
    finally:
        conn.close()
