from pathlib import Path
import sys,json,csv,sqlite3,hashlib,html,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from app import db
S=getSampleStyleSheet();S.add(ParagraphStyle(name='KTitle',fontName='Helvetica-Bold',fontSize=18,leading=22,textColor=colors.HexColor('#15324F'),spaceAfter=12));S.add(ParagraphStyle(name='KBody',fontName='Helvetica',fontSize=10.5,leading=14.5,spaceAfter=7));S.add(ParagraphStyle(name='KHead',fontName='Helvetica-Bold',fontSize=11,leading=14,spaceBefore=8,spaceAfter=5,textColor=colors.HexColor('#15324F')));S.add(ParagraphStyle(name='KMeta',fontName='Helvetica',fontSize=9,leading=12,textColor=colors.HexColor('#53616E'),spaceAfter=4));S.add(ParagraphStyle(name='KWarn',fontName='Helvetica-Bold',fontSize=9.5,leading=13,textColor=colors.HexColor('#913D2E'),spaceAfter=10))
def footer(canvas,doc):
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#53616E'));canvas.drawString(48,28,'SOAR.AI DEVELOPER FIXTURE | NOT FOR AIRCRAFT MAINTENANCE');canvas.drawRightString(564,28,str(doc.page))
with db.connect(R/'database/seed.sqlite') as c:
 for d in db.fetch(c,'SELECT * FROM documents ORDER BY doc_id'):
  flow=[Paragraph('SIMULATION ONLY',S['KWarn']),Paragraph(html.escape(d['title']),S['KTitle']),Paragraph(html.escape(f"{d['doc_id']} | Revision {d['revision']} | {d['doc_type']}"),S['KMeta']),Paragraph(html.escape(f"Operator {d['operator_id']} | {d['aircraft_type']} | {d['config_code']} | Station {d['station']}"),S['KMeta']),Paragraph(html.escape(f"Status {d['status']} | Trust {d['trust_status']} | Effective {d['valid_from'][:10]} to {d['valid_to'][:10]}"),S['KMeta']),Spacer(1,8)]
  for ch in db.fetch(c,'SELECT * FROM doc_chunks WHERE doc_id=? ORDER BY ordinal',(d['doc_id'],)):
   flow.append(KeepTogether([Paragraph(html.escape(f"{ch['ordinal']}. {ch['section']}"),S['KHead']),Paragraph(html.escape(ch['content']),S['KBody'])]))
  SimpleDocTemplate(str(R/d['pdf_path']),pagesize=letter,leftMargin=48,rightMargin=48,topMargin=42,bottomMargin=48,title=d['title'],author='Sovereign SLM Labs - simulation fixtures').build(flow,onFirstPage=footer,onLaterPages=footer)

print('Rendered knowledge PDFs. Run scripts/validate_data.py.')
