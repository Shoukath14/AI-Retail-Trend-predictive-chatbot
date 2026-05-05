import os
import json
from datetime import datetime

def generate_pdf_report(analysis: dict, output_path: str) -> str:
    """Generate a PDF trend analysis report using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                     alignment=TA_CENTER, fontSize=20,
                                     textColor=colors.HexColor('#1a1a2e'),
                                     spaceAfter=6)
        story.append(Paragraph("🛍️ AI Retail Trend Analysis Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", 
                               ParagraphStyle('Sub', parent=styles['Normal'],
                                              alignment=TA_CENTER, textColor=colors.grey)))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#6c63ff')))
        story.append(Spacer(1, 0.5*cm))

        # Summary
        if 'summary' in analysis:
            s = analysis['summary']
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            summary_data = [
                ['Metric', 'Value'],
                ['Total Records', str(s.get('total_records', 'N/A'))],
                ['Date Range', s.get('date_range', 'N/A')],
                ['Total Units Sold', f"{s.get('total_units_sold', 0):,}"],
                ['Unique Products', str(s.get('unique_products', 'N/A'))],
                ['Unique Categories', str(s.get('unique_categories', 'N/A'))],
                ['Top Region', s.get('top_region', 'N/A')],
            ]
            t = Table(summary_data, colWidths=[8*cm, 8*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6c63ff')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f7ff')]),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))

        # Top Products
        if 'top_products' in analysis:
            story.append(Paragraph("Top Products by Volume", styles['Heading2']))
            rows = [['Rank', 'Product', 'Units Sold']]
            for i, (p, v) in enumerate(zip(
                    analysis['top_products']['labels'],
                    analysis['top_products']['values']), 1):
                rows.append([str(i), p, f"{v:,}"])
            t = Table(rows, colWidths=[2*cm, 10*cm, 4*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d2d5e')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0efff')]),
                ('PADDING', (0,0), (-1,-1), 7),
                ('ALIGN', (2,0), (2,-1), 'CENTER'),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))

        # Predictions
        if 'predictions' in analysis and analysis['predictions']:
            story.append(Paragraph("Trend Predictions (Next Quarter)", styles['Heading2']))
            rows = [['Product', 'Direction', 'Change %', 'Predicted Units', 'Confidence']]
            for p in analysis['predictions']:
                rows.append([
                    p['product'],
                    '📈 Rise' if p['direction'] == 'rise' else '📉 Decline',
                    f"{p['change_pct']}%",
                    f"{p['predicted_qty']:,}",
                    p['confidence']
                ])
            t = Table(rows, colWidths=[5*cm, 3*cm, 2.5*cm, 3.5*cm, 2.5*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d2d5e')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0efff')]),
                ('PADDING', (0,0), (-1,-1), 7),
            ]))
            story.append(t)

        doc.build(story)
        return output_path

    except Exception as e:
        raise RuntimeError(f"PDF generation failed: {e}")
