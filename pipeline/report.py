"""
Reporting layer: auto-generate an executive PDF from a pipeline run.

A non-technical stakeholder should be able to open this PDF and understand the
operational status without ever opening Power BI. Each run is archived by date.
"""
from datetime import datetime
from fpdf import FPDF

from pipeline.config import REPORTS_DIR


def generate_report(validation_report, anomaly_summary, key_findings, output_path=None):
    """Build a one-page executive PDF. Returns the path written."""
    if output_path is None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = REPORTS_DIR / f"report_{datetime.now():%Y-%m-%d}.pdf"

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Operations Intelligence Report", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.now():%Y-%m-%d %H:%M}", ln=True)
    pdf.cell(0, 8, f"Pipeline status: {validation_report.get('pipeline_status', 'n/a')}", ln=True)
    pdf.ln(4)

    # Validation section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. Data Quality Validation", ln=True)
    pdf.set_font("Arial", "", 10)
    for key, value in validation_report.items():
        pdf.cell(0, 7, f"   {key}: {value}", ln=True)
    pdf.ln(3)

    # Anomaly section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. Anomaly Detection Summary", ln=True)
    pdf.set_font("Arial", "", 10)
    for key, value in anomaly_summary.items():
        pdf.cell(0, 7, f"   {key}: {value}", ln=True)
    pdf.ln(3)

    # Findings section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "3. Key Findings", ln=True)
    pdf.set_font("Arial", "", 10)
    for finding in key_findings:
        pdf.set_x(pdf.l_margin)
        # Explicit width (effective page width) avoids fpdf2's w=0 edge cases.
        pdf.multi_cell(pdf.epw, 7, f"- {finding}")

    pdf.output(str(output_path))
    return output_path
