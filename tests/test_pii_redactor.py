"""
Unit & Integration Tests for Resume PII Redactor (#295)
======================================================
Tests:
1. Email detection and redaction (single, multiple, subdomains, special characters)
2. Indian phone number formats (+91, 91, 0 prefix, 10-digit mobile, separators, landlines)
3. International phone numbers (US, UK, Europe, Australia)
4. Non-PII text preservation (dates, years, GPA, percentages, version numbers, technical skills)
5. Address detection and redaction (labeled, street indicators, PIN codes, US ZIP)
6. Personal links / URL redaction (LinkedIn, GitHub, portfolio)
7. Configuration toggle (ENABLE_PII_REDACTION True vs False)
8. Coordinator integration (verifying model prompt contains placeholders, no raw PII)
9. Section detection and ATS score compatibility with placeholders
10. Detection helpers (has_pii, get_pii_counts, detect_pii)
"""

import pytest
from unittest.mock import patch
import config
from utils.pii_redactor import (
    redact_pii,
    detect_pii,
    has_pii,
    get_pii_counts,
    PLACEHOLDER_EMAIL,
    PLACEHOLDER_PHONE,
    PLACEHOLDER_ADDRESS,
    PLACEHOLDER_LINK,
)
from utils.pdf_reader import standardize_resume_sections, format_standardized_resume
from agents.resume_agent import ResumeAgent
from agents.coordinator import CoordinatorAgent


SAMPLE_CLEAN_RESUME = """
Jane Doe
PROFESSIONAL SUMMARY
Senior Backend Engineer with 5 years of experience in distributed systems, Python, and PostgreSQL.

SKILLS
Python, Go, PostgreSQL, Docker, Kubernetes, AWS, Redis, GraphQL, CI/CD, Git

WORK EXPERIENCE
Software Engineer | Acme Cloud Corp (2020 - Present)
- Architected asynchronous event pipeline processing 15M records daily.
- Improved database indexing, dropping p99 response latency by 45%.
- Maintained 99.99% service uptime across Kubernetes clusters.

EDUCATION
B.S. in Computer Science | University of California (2016 - 2020)
GPA: 3.85/4.0
"""

SAMPLE_PII_RESUME = """
Aarav Patel
Email: aarav.patel99@gmail.com
Alternate: a.patel@alumni.iitb.ac.in
Phone: +91 98765 43210, Alternate Mobile: 09876543210
US Office: +1 (555) 234-5678
Address: Flat 402, Sunshine Apartments, MG Road, Indiranagar, Bangalore - 560038
LinkedIn: linkedin.com/in/aaravpatel | GitHub: https://github.com/aarav-dev

PROFESSIONAL SUMMARY
Full-Stack Engineer with strong expertise in Python 3.11, React, and AWS microservices.

EXPERIENCE
Software Engineer - CloudTech Labs (2021-2024)
- Designed real-time websocket microservices handling 50,000 active connections.
- Achieved 95% automated test coverage with PyTest and GitHub Actions.

EDUCATION
B.Tech in Computer Science - IIT Bombay (2017 - 2021)
CGPA: 8.8/10.0
"""


# ---------------------------------------------------------------------------
# 1. Email Redaction Tests
# ---------------------------------------------------------------------------

class TestEmailRedaction:
    def test_single_standard_email(self):
        text = "Contact me at candidate@example.com for opportunities."
        redacted = redact_pii(text)
        assert "candidate@example.com" not in redacted
        assert PLACEHOLDER_EMAIL in redacted

    def test_multiple_and_complex_subdomain_emails(self):
        text = (
            "Primary: john.doe+career@engineering.stanford.edu\n"
            "Secondary: j_doe99@mail.co.in\n"
            "Personal: john-personal@my-domain.org"
        )
        redacted = redact_pii(text)
        assert "john.doe+career@engineering.stanford.edu" not in redacted
        assert "j_doe99@mail.co.in" not in redacted
        assert "john-personal@my-domain.org" not in redacted
        assert redacted.count(PLACEHOLDER_EMAIL) == 3


# ---------------------------------------------------------------------------
# 2. Indian Phone Number Redaction Tests
# ---------------------------------------------------------------------------

class TestIndianPhoneRedaction:
    @pytest.mark.parametrize("phone_str", [
        "9876543210",
        "98765 43210",
        "98765-43210",
        "98765.43210",
        "+91 98765 43210",
        "+91-9876543210",
        "+919876543210",
        "91 98765 43210",
        "91-9876543210",
        "09876543210",
        "0-98765-43210",
        "+91 (987) 654-3210",
        "88888 77777",
        "7012345678",
        "6123456789",
    ])
    def test_indian_mobile_formats(self, phone_str):
        text = f"Candidate phone number is {phone_str}."
        redacted = redact_pii(text)
        assert phone_str not in redacted
        assert PLACEHOLDER_PHONE in redacted

    @pytest.mark.parametrize("landline_str", [
        "011-23456789",
        "+91 11 2345 6789",
        "080 23456789",
    ])
    def test_indian_landline_formats(self, landline_str):
        text = f"Landline: {landline_str}."
        redacted = redact_pii(text)
        assert landline_str not in redacted
        assert PLACEHOLDER_PHONE in redacted


# ---------------------------------------------------------------------------
# 3. International Phone Number Redaction Tests
# ---------------------------------------------------------------------------

class TestInternationalPhoneRedaction:
    @pytest.mark.parametrize("intl_phone", [
        "+1 (555) 123-4567",
        "+1 555-123-4567",
        "(555) 123-4567",
        "555-123-4567",
        "+44 20 7946 0958",
        "+44-20-7946-0958",
        "+33 1 42 68 55 55",
        "+61 2 9876 5432",
    ])
    def test_international_phone_formats(self, intl_phone):
        text = f"Please reach out to me via phone: {intl_phone}."
        redacted = redact_pii(text)
        assert intl_phone not in redacted
        assert PLACEHOLDER_PHONE in redacted


# ---------------------------------------------------------------------------
# 4. Non-Personal Data Preservation Tests
# ---------------------------------------------------------------------------

class TestNonPersonalDataPreservation:
    def test_clean_text_remains_unchanged(self):
        redacted = redact_pii(SAMPLE_CLEAN_RESUME)
        assert redacted == SAMPLE_CLEAN_RESUME
        assert PLACEHOLDER_EMAIL not in redacted
        assert PLACEHOLDER_PHONE not in redacted
        assert PLACEHOLDER_ADDRESS not in redacted

    def test_year_ranges_and_dates_preserved(self):
        text = (
            "Experience:\n"
            "- Senior Developer (2018 - 2022)\n"
            "- Lead Engineer (2022-Present)\n"
            "- Certified Kubernetes Administrator (2023)\n"
        )
        redacted = redact_pii(text)
        assert "(2018 - 2022)" in redacted
        assert "(2022-Present)" in redacted
        assert "(2023)" in redacted
        assert PLACEHOLDER_PHONE not in redacted

    def test_gpa_percentages_and_tech_metrics_preserved(self):
        text = (
            "CGPA: 3.85/4.0, Aggregate: 8.9/10.0, Score: 95%\n"
            "Scaled microservices handling 10,000,000 daily requests.\n"
            "Reduced latency by 45% using Python 3.10 and PostgreSQL 14."
        )
        redacted = redact_pii(text)
        assert "3.85/4.0" in redacted
        assert "8.9/10.0" in redacted
        assert "95%" in redacted
        assert "10,000,000" in redacted
        assert "Python 3.10" in redacted
        assert "PostgreSQL 14" in redacted
        assert PLACEHOLDER_PHONE not in redacted


# ---------------------------------------------------------------------------
# 5. Street Address and PIN Code Redaction Tests
# ---------------------------------------------------------------------------

class TestAddressRedaction:
    def test_labeled_address_lines(self):
        text = (
            "Address: 123 Main Street, Suite 500, Austin, TX 78701\n"
            "Permanent Address: H.No 4-51, Gandhi Nagar, Hyderabad, 500028"
        )
        redacted = redact_pii(text)
        assert "123 Main Street" not in redacted
        assert "Gandhi Nagar" not in redacted
        assert "78701" not in redacted
        assert "500028" not in redacted
        assert PLACEHOLDER_ADDRESS in redacted

    def test_standalone_address_lines_with_postal_codes(self):
        text = (
            "Flat 402, Sunshine Apartments, MG Road, Indiranagar, Bangalore - 560038\n"
            "Plot No. 12, Sector 18, Noida, Uttar Pradesh 201301\n"
            "42 Silicon Vista Boulevard, Apt 4B, San Francisco, CA 94107"
        )
        redacted = redact_pii(text)
        assert "Sunshine Apartments" not in redacted
        assert "Noida" not in redacted
        assert "San Francisco" not in redacted
        assert "560038" not in redacted
        assert "201301" not in redacted
        assert "94107" not in redacted
        assert PLACEHOLDER_ADDRESS in redacted

    def test_pincode_label_redaction(self):
        text = "Pin Code: 560001\nPostal Code: 110001"
        redacted = redact_pii(text)
        assert "560001" not in redacted
        assert "110001" not in redacted
        assert PLACEHOLDER_ADDRESS in redacted


# ---------------------------------------------------------------------------
# 6. Web Links / Profile Redaction Tests
# ---------------------------------------------------------------------------

class TestLinkRedaction:
    def test_web_links_and_social_profiles(self):
        text = (
            "GitHub: https://github.com/developer\n"
            "LinkedIn: linkedin.com/in/developer-profile\n"
            "Portfolio: www.candidate-portfolio.dev"
        )
        redacted = redact_pii(text)
        assert "https://github.com/developer" not in redacted
        assert "linkedin.com/in/developer-profile" not in redacted
        assert "www.candidate-portfolio.dev" not in redacted
        assert PLACEHOLDER_LINK in redacted


# ---------------------------------------------------------------------------
# 7. Configuration Flag Tests
# ---------------------------------------------------------------------------

class TestConfigurationToggle:
    def test_redaction_disabled_via_argument(self):
        text = "Contact: test.candidate@example.org or +91 98765 43210"
        redacted = redact_pii(text, enabled=False)
        assert redacted == text
        assert "test.candidate@example.org" in redacted
        assert "+91 98765 43210" in redacted

    def test_redaction_disabled_via_config(self, monkeypatch):
        monkeypatch.setattr(config, "ENABLE_PII_REDACTION", False)
        text = "Contact: test.candidate@example.org or +91 98765 43210"
        redacted = redact_pii(text)
        assert redacted == text
        assert "test.candidate@example.org" in redacted

    def test_redaction_enabled_via_config(self, monkeypatch):
        monkeypatch.setattr(config, "ENABLE_PII_REDACTION", True)
        text = "Contact: test.candidate@example.org or +91 98765 43210"
        redacted = redact_pii(text)
        assert "test.candidate@example.org" not in redacted
        assert PLACEHOLDER_EMAIL in redacted
        assert PLACEHOLDER_PHONE in redacted


# ---------------------------------------------------------------------------
# 8. Detection Helpers Tests
# ---------------------------------------------------------------------------

class TestDetectionHelpers:
    def test_has_pii(self):
        assert has_pii(SAMPLE_PII_RESUME) is True
        assert has_pii(SAMPLE_CLEAN_RESUME) is False
        assert has_pii("") is False

    def test_get_pii_counts(self):
        counts = get_pii_counts(SAMPLE_PII_RESUME)
        assert counts["emails"] >= 2
        assert counts["phones"] >= 2
        assert counts["addresses"] >= 1
        assert counts["links"] >= 2

    def test_detect_pii_structured_report(self):
        report = detect_pii(SAMPLE_PII_RESUME)
        assert report["has_pii"] is True
        assert "aarav.patel99@gmail.com" in report["emails"]
        assert any("98765" in p for p in report["phones"])
        assert report["total_count"] >= 5


# ---------------------------------------------------------------------------
# 9. Section Standardization & ATS Compatibility Tests
# ---------------------------------------------------------------------------

class TestATSAndSectionCompatibility:
    def test_section_detection_works_with_placeholders(self):
        redacted = redact_pii(SAMPLE_PII_RESUME)
        sections = standardize_resume_sections(redacted)
        assert "summary" in sections
        assert "experience" in sections
        assert "education" in sections
        assert "Full-Stack Engineer" in sections["summary"]
        assert "CloudTech Labs" in sections["experience"]
        assert "IIT Bombay" in sections["education"]

    def test_resume_agent_ats_scoring_with_placeholders(self):
        agent = ResumeAgent()
        mock_data = {
            "ats_score": 85,
            "summary": "Candidate profile contains placeholders [EMAIL] and [PHONE].",
            "strengths": ["Strong Python experience", "Clear project achievements"],
            "weaknesses": ["Add more metrics"],
            "missing_skills": ["Docker"],
            "overall_recommendation": "Tailor resume bullets."
        }
        processed = agent.process(mock_data)
        assert processed["ats_score"] == 85
        assert "Strong Python experience" in processed["strengths"]


# ---------------------------------------------------------------------------
# 10. Coordinator Agent Integration Tests
# ---------------------------------------------------------------------------

class TestCoordinatorAgentIntegration:
    @patch("agents.coordinator.generate_json_response")
    def test_coordinator_prompt_contains_no_raw_pii(self, mock_generate, monkeypatch):
        """Verifies that the prompt sent to Gemini contains placeholders and zero raw contact info."""
        monkeypatch.setattr(config, "ENABLE_PII_REDACTION", True)

        mock_generate.return_value = {
            "resume_analysis": {
                "ats_score": 82,
                "summary": "Strong candidate",
                "strengths": ["Python"],
                "weaknesses": [],
                "grammar_suggestions": [],
                "formatting_suggestions": [],
                "project_feedback": "Solid projects",
                "experience_feedback": "Good experience",
                "missing_skills": [],
                "overall_recommendation": "Ready to apply"
            },
            "job_match": {
                "match_percentage": 80,
                "matched_skills": ["Python", "React"],
                "missing_skills": [],
                "required_certifications": [],
                "recommended_improvements": [],
                "top_5_resume_changes": []
            },
            "skill_gap": [],
            "learning_roadmap": [],
            "interview_questions": {
                "technical_questions": ["What is GIL?"],
                "hr_questions": ["Tell me about yourself"],
                "behavioral_questions": ["Describe a challenge"]
            },
            "overall_recommendation_summary": "Highly recommended"
        }

        coordinator = CoordinatorAgent()
        coordinator.analyze(
            resume_text=SAMPLE_PII_RESUME,
            job_description="Seeking Python / React Engineer",
            company_name="Acme"
        )

        assert mock_generate.called
        call_kwargs = mock_generate.call_args.kwargs
        prompt_text = call_kwargs["prompt"]

        # Crucial assertions: prompt sent to Gemini must contain NO raw email or phone
        assert "aarav.patel99@gmail.com" not in prompt_text
        assert "a.patel@alumni.iitb.ac.in" not in prompt_text
        assert "98765 43210" not in prompt_text
        assert "09876543210" not in prompt_text
        assert "+1 (555) 234-5678" not in prompt_text
        assert "Sunshine Apartments" not in prompt_text

        # Placeholders MUST be present in prompt
        assert PLACEHOLDER_EMAIL in prompt_text
        assert PLACEHOLDER_PHONE in prompt_text

    @patch("agents.coordinator.generate_json_response")
    def test_coordinator_redaction_disabled_preserves_raw_text(self, mock_generate, monkeypatch):
        """When config.ENABLE_PII_REDACTION is False, prompt retains original raw text."""
        monkeypatch.setattr(config, "ENABLE_PII_REDACTION", False)

        mock_generate.return_value = {
            "resume_analysis": {"ats_score": 70, "summary": "OK"},
            "job_match": {"match_percentage": 70, "matched_skills": []},
            "skill_gap": [],
            "learning_roadmap": [],
            "interview_questions": {},
            "overall_recommendation_summary": "OK"
        }

        coordinator = CoordinatorAgent()
        coordinator.analyze(
            resume_text=SAMPLE_PII_RESUME,
            job_description="Seeking Python Engineer",
            company_name="Acme"
        )

        assert mock_generate.called
        prompt_text = mock_generate.call_args.kwargs["prompt"]
        assert "aarav.patel99@gmail.com" in prompt_text
        assert "98765 43210" in prompt_text
