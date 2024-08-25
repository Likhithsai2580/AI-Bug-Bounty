from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_report(agent_results: Dict[str, Dict[str, Any]], output_file: str):
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph("Vulnerability Scan Report", styles['Title']))
    story.append(Spacer(1, 12))
    
    for agent_name, results in agent_results.items():
        story.append(Paragraph(f"Results from Agent: {agent_name}", styles['Heading2']))
        story.append(Spacer(1, 6))
        
        for plugin_name, plugin_result in results.items():
            if plugin_name != 'final_analysis':
                story.append(Paragraph(f"Plugin: {plugin_name}", styles['Heading3']))
                story.append(Paragraph(str(plugin_result), styles['BodyText']))
                story.append(Spacer(1, 6))
        
        if 'final_analysis' in results:
            story.append(Paragraph("Final Analysis", styles['Heading3']))
            story.append(Paragraph(results['final_analysis'], styles['BodyText']))
        
        story.append(Spacer(1, 12))
    
    doc.build(story)