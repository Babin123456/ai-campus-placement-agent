import logging
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


def _escape_pdf_text(value) -> str:
    """Escape dynamic text for ReportLab's XML-like Paragraph parser.

    ReportLab's Paragraph intentionally accepts markup (for example ``<b>`` and
    ``<br/>``). Values derived from resumes or model output must be escaped
    before being interpolated into that markup, otherwise literal text such as
    ``std::vector<T>`` can be interpreted as formatting or break PDF creation.
    """
    if value is None:
        return ""
    return escape(str(value))


def _escape_pdf_list(items, fallback: str = "None") -> str:
    """Join a sequence of dynamic values after escaping each item."""
    if items is None or items == [] or items == "":
        return fallback
    if isinstance(items, (list, tuple)):
        values = [_escape_pdf_text(item) for item in items if item is not None and str(item)]
        return ", ".join(values) if values else fallback
    return _escape_pdf_text(items)


def generate_pdf_report(analysis_data: dict, output_path: str) -> str:
    """Generate a printable PDF placement-readiness report.

    Dynamic report content is escaped before being passed to ReportLab's
    ``Paragraph`` parser, while intentional formatting markup remains intact.
    """
    try:
        logger.info("Generating PDF report at: %s", output_path)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Color palette definition matching the existing blue-and-white style.
        primary_blue = colors.HexColor("#1a73e8")
        accent_light_blue = colors.HexColor("#e8f0fe")
        dark_text_color = colors.HexColor("#202124")
        light_grey_bg = colors.HexColor("#f8f9fa")
        border_grey = colors.HexColor("#dadce0")

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=primary_blue,
            alignment=TA_CENTER,
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#5f6368"),
            alignment=TA_CENTER,
        )

        h1_style = ParagraphStyle(
            "SectionH1",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=primary_blue,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=dark_text_color,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=dark_text_color,
        )

        bullet_style = ParagraphStyle(
            "ReportBullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=dark_text_color,
            leftIndent=15,
            firstLineIndent=-10,
        )

        table_hdr_style = ParagraphStyle(
            "TableHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white,
        )

        table_body_style = ParagraphStyle(
            "TableBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=dark_text_color,
        )

        story = []

        # Cover section
        story.append(Spacer(1, 30))
        story.append(Paragraph("AI CAMPUS PLACEMENT REPORT", title_style))
        story.append(Spacer(1, 10))
        company_name = _escape_pdf_text(analysis_data.get("company_name") or "Target Company")
        story.append(
            Paragraph(
                f"Preparation Analysis &amp; Learning Roadmap for {company_name}",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 20))

        # Summary metrics
        results = analysis_data.get("results") or {}
        resume_analysis = results.get("resume_analysis") or {}
        job_match = results.get("job_match") or {}

        ats_score = _escape_pdf_text(resume_analysis.get("ats_score", "N/A"))
        match_percentage = _escape_pdf_text(job_match.get("match_percentage", "N/A"))
        metrics_grid_data = [
            [
                Paragraph("<b>ATS Score:</b>", body_style),
                Paragraph(f"<b>{ats_score}/100</b>", body_style),
                Paragraph("<b>Job Match Score:</b>", body_style),
                Paragraph(f"<b>{match_percentage}%</b>", body_style),
            ]
        ]

        metrics_table = Table(metrics_grid_data, colWidths=[100, 100, 120, 100])
        metrics_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent_light_blue),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 10),
                    ("BOX", (0, 0), (-1, -1), 1.5, primary_blue),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#b0d4ff")),
                ]
            )
        )
        story.append(metrics_table)
        story.append(Spacer(1, 25))

        # Summary block
        story.append(Paragraph("Executive Resume Summary", h1_style))
        story.append(
            Paragraph(
                _escape_pdf_text(resume_analysis.get("summary") or "No summary available."),
                body_style,
            )
        )
        story.append(Spacer(1, 15))

        # Overall recommendation
        story.append(Paragraph("Overall Recommendation", h1_style))
        story.append(
            Paragraph(
                _escape_pdf_text(
                    resume_analysis.get("overall_recommendation") or "No recommendation available."
                ),
                body_style,
            )
        )
        story.append(Spacer(1, 15))
        story.append(PageBreak())

        # Resume feedback
        story.append(Paragraph("Resume Analysis Details", h1_style))
        story.append(Paragraph("Strengths", h2_style))
        for strength in resume_analysis.get("strengths", []):
            story.append(Paragraph(f"&bull; {_escape_pdf_text(strength)}", bullet_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("Weaknesses / Areas of Improvement", h2_style))
        for weakness in resume_analysis.get("weaknesses", []):
            story.append(Paragraph(f"&bull; {_escape_pdf_text(weakness)}", bullet_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("Grammar &amp; Formatting Suggestions", h2_style))
        suggestions = resume_analysis.get("grammar_suggestions", []) + resume_analysis.get(
            "formatting_suggestions", []
        )
        for suggestion in suggestions:
            story.append(Paragraph(f"&bull; {_escape_pdf_text(suggestion)}", bullet_style))
        story.append(Spacer(1, 15))

        # Job-match adjustments
        story.append(Paragraph("Top 5 Job Matching Adjustments", h1_style))
        for idx, change in enumerate(job_match.get("top_5_resume_changes", []), 1):
            story.append(Paragraph(f"<b>{idx}.</b> {_escape_pdf_text(change)}", bullet_style))

        story.append(PageBreak())

        # Skill-gaps table
        story.append(Paragraph("Skill Gap Assessment", h1_style))
        story.append(
            Paragraph(
                "The table below documents critical skills required for your target role and "
                "company that were not identified in your resume. Follow the recommended "
                "learning paths and projects to build these skills.",
                body_style,
            )
        )
        story.append(Spacer(1, 10))

        skill_gaps = results.get("skill_gap", [])
        if skill_gaps:
            gap_table_data = [
                [
                    Paragraph("Skill", table_hdr_style),
                    Paragraph("Importance", table_hdr_style),
                    Paragraph("Estimated Time", table_hdr_style),
                    Paragraph("Learning Resource &amp; Mini-Project", table_hdr_style),
                    Paragraph("Priority", table_hdr_style),
                ]
            ]

            for gap in skill_gaps:
                resource = _escape_pdf_text(gap.get("learning_resource", "N/A"))
                project = _escape_pdf_text(gap.get("project_suggestion", "N/A"))
                description_str = (
                    f"<b>Resource:</b> {resource}<br/><b>Project:</b> {project}"
                )
                gap_table_data.append(
                    [
                        Paragraph(_escape_pdf_text(gap.get("skill", "N/A")), table_body_style),
                        Paragraph(_escape_pdf_text(gap.get("importance", "N/A")), table_body_style),
                        Paragraph(_escape_pdf_text(gap.get("learning_time", "N/A")), table_body_style),
                        Paragraph(description_str, table_body_style),
                        Paragraph(_escape_pdf_text(gap.get("priority", "N/A")), table_body_style),
                    ]
                )

            gap_table = Table(gap_table_data, colWidths=[90, 65, 65, 220, 64])
            gap_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), primary_blue),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, border_grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_grey_bg]),
                    ]
                )
            )
            story.append(gap_table)
        else:
            story.append(
                Paragraph("No major skill gaps identified relative to the target role.", body_style)
            )

        story.append(Spacer(1, 15))
        story.append(PageBreak())

        # Six-week learning roadmap
        story.append(Paragraph("6-Week Learning Roadmap", h1_style))
        story.append(
            Paragraph(
                "Follow this personalized study plan step-by-step over the next 6 weeks to "
                "bridge any gaps and practice for interviews.",
                body_style,
            )
        )
        story.append(Spacer(1, 10))

        for week in results.get("learning_roadmap", []):
            week_story = [
                Paragraph(
                    f"<b>{_escape_pdf_text(week.get('week', 'Week X'))}</b> "
                    f"({_escape_pdf_text(week.get('estimated_hours', 10))} Hours)",
                    h2_style,
                ),
                Paragraph(
                    f"<b>Topics to Cover:</b> {_escape_pdf_list(week.get('topics', []))}",
                    body_style,
                ),
                Paragraph(
                    f"<b>Coding Practice:</b> {_escape_pdf_list(week.get('coding_practice', []))}",
                    body_style,
                ),
                Paragraph(
                    f"<b>Mini Project:</b> {_escape_pdf_list(week.get('mini_projects', []))}",
                    body_style,
                ),
                Paragraph("<b>Interview Questions:</b>", body_style),
            ]
            for interview_question in week.get("interview_questions", []):
                week_story.append(
                    Paragraph(f"&bull; {_escape_pdf_text(interview_question)}", bullet_style)
                )
            week_story.append(
                Paragraph(
                    f"<b>Revision Tasks:</b> {_escape_pdf_list(week.get('revision_tasks', []))}",
                    body_style,
                )
            )
            week_story.append(Spacer(1, 12))
            story.append(KeepTogether(week_story))

        doc.build(story)
        logger.info("PDF report compiled successfully.")
        return output_path

    except Exception as e:
        logger.error("Error compiling PDF report using ReportLab: %s", str(e))
        raise RuntimeError(f"ReportLab failure: {e}") from e
