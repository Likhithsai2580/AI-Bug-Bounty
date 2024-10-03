from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import logging
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)

async def generate_vulnerability_chart(vulnerabilities):
    severity_counts = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'Unknown')
        if severity in severity_counts:
            severity_counts[severity] += 1

    plt.figure(figsize=(8, 6))
    plt.bar(severity_counts.keys(), severity_counts.values())
    plt.title('Vulnerability Severity Distribution')
    plt.xlabel('Severity')
    plt.ylabel('Count')
    plt.savefig('vulnerability_chart.png')
    plt.close()

    return 'vulnerability_chart.png'

async def generate_report(report_data: Dict[str, Any], output_file: str):
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
    
    if 'vulnerabilities' in report_data:
        logger.info("Adding vulnerability details to report")
        story.append(Paragraph("Detected Vulnerabilities", styles['Heading2']))
        chart_file = await generate_vulnerability_chart(report_data['vulnerabilities'])
        story.append(Paragraph("Vulnerability Distribution", styles['Heading2']))
        story.append(Image(chart_file, width=400, height=300))
        for vuln in report_data['vulnerabilities']:
            story.append(Paragraph(f"CVE: {vuln['cve']}", styles['Heading3']))
            story.append(Paragraph(f"Severity: {vuln['severity']}", styles['BodyText']))
            story.append(Paragraph(f"Description: {vuln['description']}", styles['BodyText']))
            story.append(Paragraph(f"Recommendation: {vuln['recommendation']}", styles['BodyText']))
            story.append(Spacer(1, 12))
    
    if 'scan_summary' in report_data:
        logger.info("Adding scan summary to report")
        story.append(Paragraph("Scan Summary", styles['Heading2']))
        summary_data = [
            ["Metric", "Value"],
            ["Total URLs Scanned", str(report_data['scan_summary']['total_urls'])],
            ["Scan Duration", f"{report_data['scan_summary']['duration']:.2f} seconds"],
            ["Vulnerabilities Found", str(report_data['scan_summary']['total_vulnerabilities'])],
        ]
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
    
    logger.info(f"Building PDF report: {output_file}")
    doc.build(story)
    logger.info(f"Report generation completed: {output_file}")