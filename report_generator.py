from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import logging

logger = logging.getLogger(__name__)

def generate_report(report_data: Dict[str, Any], output_file: str):
    logger.info(f"Starting report generation: {output_file}")
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph("Vulnerability Scan Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    if 'final_analysis' in report_data:
        logger.info("Adding final analysis to report")
        story.append(Paragraph("Final Analysis", styles['Heading2']))
        story.append(Paragraph(report_data['final_analysis'], styles['BodyText']))
    
    logger.info(f"Building PDF report: {output_file}")
    doc.build(story)
    logger.info(f"Report generation completed: {output_file}")