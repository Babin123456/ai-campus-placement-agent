import os
import uuid
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename

import config
from utils.database import (
    init_db,
    save_analysis,
    get_analysis,
    create_interview_session,
    get_interview_session,
    update_interview_session
)
from utils.pdf_reader import extract_text_from_pdf
from utils.report_generator import generate_pdf_report
from agents.coordinator import CoordinatorAgent
from agents.interview_agent import InterviewAgent

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# Ensure directories exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.REPORT_FOLDER, exist_ok=True)

# Run database schema migrations/initializations
try:
    init_db()
except Exception as db_err:
    logger.critical(f"Critical: Database initialization failed: {str(db_err)}")

# Instantiate coordination and specialized interview agents
coordinator_agent = CoordinatorAgent()
live_interview_agent = InterviewAgent()

@app.route("/")
def index() -> str:
    """
    Renders the placement landing page containing the configuration forms.
    """
    companies_list = ["Google", "Microsoft", "Amazon", "TCS", "Infosys", "Accenture", "Capgemini", "Wipro"]
    return render_template("index.html", companies=companies_list)


@app.route("/api/company/<company_name>")
def get_company_profile(company_name: str):
    """
    Returns company hiring details from data/companies.json for the preview explorer modal.
    """
    companies_file = config.BASE_DIR / "data" / "companies.json"
    try:
        if companies_file.exists():
            with open(companies_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if company_name in data:
                    return jsonify({"success": True, "company": company_name, "details": data[company_name]})
    except Exception as e:
        logger.error(f"Error fetching company details for {company_name}: {e}")
    return jsonify({"success": False, "error": f"Profile for '{company_name}' not found."}), 404

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Handles PDF resume uploads, processes files, calls coordinator,
    persists result states, and redirects to candidate dashboards.
    """
    try:
        # Validate file upload presence
        if "resume" not in request.files:
            flash("No file key detected in upload form.", "error")
            return redirect(url_for("index"))

        uploaded_file = request.files["resume"]
        if uploaded_file.filename == "":
            flash("No resume file was selected. Please choose a PDF file.", "error")
            return redirect(url_for("index"))

        # Verify it's a PDF extension
        if not uploaded_file.filename.lower().endswith('.pdf'):
            flash("Invalid file format. Only PDF resumes are supported.", "error")
            return redirect(url_for("index"))

        selected_company = request.form.get("company", "General").strip()
        job_description = request.form.get("job_description", "").strip()

        # Save the file to local upload folders
        file_uuid = str(uuid.uuid4())
        safe_name = secure_filename(f"{file_uuid}_{uploaded_file.filename}")
        saved_file_path = os.path.join(config.UPLOAD_FOLDER, safe_name)
        uploaded_file.save(saved_file_path)
        logger.info(f"Uploaded resume saved locally at: {saved_file_path}")

        # Parse text content from the PDF
        extracted_resume_text = extract_text_from_pdf(saved_file_path)

        # Execute coordinated multi-agent analysis via single Gemini call
        analysis_payload = coordinator_agent.analyze(
            resume_text=extracted_resume_text,
            job_description=job_description,
            company_name=selected_company
        )

        # Store analysis result in SQLite database
        save_analysis(
            analysis_id=file_uuid,
            resume_filename=uploaded_file.filename,
            company_name=selected_company,
            job_description=job_description,
            results_dict=analysis_payload
        )

        # Redirect user directly to their new placement analysis dashboard
        return redirect(url_for("dashboard", analysis_id=file_uuid))

    except Exception as e:
        logger.error(f"Analysis workflow crashed: {str(e)}")
        flash(f"Analysis Failed: {str(e)}", "error")
        return redirect(url_for("index"))

@app.route("/dashboard/<analysis_id>")
def dashboard(analysis_id: str) -> str:
    """
    Loads and renders the candidate evaluation dashboard.
    """
    analysis_record = get_analysis(analysis_id)
    if not analysis_record:
        flash("The requested placement analysis report could not be found.", "error")
        return redirect(url_for("index"))

    return render_template(
        "dashboard.html",
        analysis=analysis_record,
        analysis_id=analysis_id
    )

@app.route("/interview/<analysis_id>")
def interview(analysis_id: str) -> str:
    """
    Bootstraps or loads an existing interactive mock interview session.
    """
    analysis_record = get_analysis(analysis_id)
    if not analysis_record:
        flash("Cannot initialize mock interview. Parent analysis not found.", "error")
        return redirect(url_for("index"))

    # Load or initialize the interview session from DB
    interview_session = get_interview_session(analysis_id)

    if not interview_session:
        # Extract questions generated by Coordinator Agent
        coordinator_questions = analysis_record["results"].get("interview_questions", {})
        
        flat_questions_list = []
        q_idx = 0
        
        # Flatten the questions and categorize them
        for question_text in coordinator_questions.get("hr", []):
            flat_questions_list.append({"index": q_idx, "type": "HR", "question": question_text})
            q_idx += 1
            
        for question_text in coordinator_questions.get("technical", []):
            flat_questions_list.append({"index": q_idx, "type": "Technical", "question": question_text})
            q_idx += 1
            
        for question_text in coordinator_questions.get("behavioral", []):
            flat_questions_list.append({"index": q_idx, "type": "Behavioral", "question": question_text})
            q_idx += 1

        # Save new session into SQLite DB
        create_interview_session(
            interview_id=analysis_id,
            analysis_id=analysis_id,
            questions_list=flat_questions_list
        )
        interview_session = get_interview_session(analysis_id)

    return render_template(
        "interview.html",
        interview=interview_session,
        analysis_id=analysis_id
    )

@app.route("/interview/<analysis_id>/submit", methods=["POST"])
def submit_interview_answer(analysis_id: str):
    """
    Endpoint that evaluates a candidate response dynamically and updates session progress.
    """
    try:
        session = get_interview_session(analysis_id)
        if not session:
            return jsonify({"error": "Mock interview session was not found."}), 404

        # Read JSON POST payloads
        post_data = request.get_json() or {}
        candidate_response = post_data.get("answer", "").strip()
        question_index = int(post_data.get("question_index", 0))

        questions_list = session["questions"]
        answers_list = session["answers"]

        if question_index < 0 or question_index >= len(questions_list):
            return jsonify({"error": "The requested question index is out of bounds."}), 400

        target_question = questions_list[question_index]

        # Call InterviewAgent to dynamically evaluate response accuracy, metrics, and suggestions
        evaluation_results = live_interview_agent.evaluate_answer(
            question_type=target_question["type"],
            question=target_question["question"],
            answer=candidate_response
        )

        # Structure response details
        response_record = {
            "question_index": question_index,
            "type": target_question["type"],
            "question": target_question["question"],
            "answer": candidate_response,
            "evaluation": evaluation_results
        }

        # Protection against duplicate submission attempts
        is_replaced = False
        for idx, past_ans in enumerate(answers_list):
            if past_ans["question_index"] == question_index:
                answers_list[idx] = response_record
                is_replaced = True
                break
        if not is_replaced:
            answers_list.append(response_record)

        # Calculate progress parameters
        next_question_index = question_index + 1
        is_completed = next_question_index >= len(questions_list)

        # Update session logs in database
        update_interview_session(
            interview_id=analysis_id,
            current_question_index=next_question_index if not is_completed else question_index,
            answers_list=answers_list,
            completed=is_completed
        )

        result_payload = {
            "evaluation": evaluation_results,
            "next_index": next_question_index,
            "completed": is_completed
        }

        if not is_completed:
            result_payload["next_question"] = questions_list[next_question_index]

        return jsonify(result_payload)

    except Exception as e:
        logger.error(f"Failed to process answer submission: {str(e)}")
        return jsonify({"error": f"Internal process error evaluating response: {str(e)}"}), 500

@app.route("/download/<analysis_id>")
def download_pdf_report(analysis_id: str):
    """
    Compiles placement metrics into a ReportLab PDF and downloads the file.
    """
    try:
        analysis_record = get_analysis(analysis_id)
        if not analysis_record:
            flash("Cannot generate PDF. Placement record not found.", "error")
            return redirect(url_for("index"))

        # Check if file has already been generated
        pdf_output_name = f"Placement_Report_{analysis_id}.pdf"
        pdf_full_path = os.path.join(config.REPORT_FOLDER, pdf_output_name)

        if not os.path.exists(pdf_full_path):
            generate_pdf_report(
                analysis_data=analysis_record,
                output_path=pdf_full_path
            )

        return send_file(
            pdf_full_path,
            as_attachment=True,
            download_name=f"Placement_Readiness_Report_{analysis_record['company_name']}.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        logger.error(f"Failed to generate and serve PDF report: {str(e)}")
        flash(f"Error compiling report file: {str(e)}", "error")
        return redirect(url_for("dashboard", analysis_id=analysis_id))

if __name__ == "__main__":
    # Boot Flask server locally on default port 5000
    app.run(debug=True, port=5000)
