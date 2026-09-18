"""Rebuild the editable docket from docs/docket_content.json. Requires requirements-authoring.txt."""
from pathlib import Path
import json,sys
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
R=Path(__file__).resolve().parents[1];pages=json.loads((R/'docs/docket_content.json').read_text())
doc=Document();sec=doc.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=Inches(.68);sec.bottom_margin=Inches(.65);sec.left_margin=Inches(1);sec.right_margin=Inches(1);sec.footer_distance=Inches(.3)
styles=doc.styles
for el in list(doc.styles.element.xpath('.//w:pBdr')):el.getparent().remove(el)
for name in ['Normal','Body Text']:
 s=styles[name];s.font.name='Arial';s.font.size=Pt(11.2);s.paragraph_format.line_spacing=1.1;s.paragraph_format.space_after=Pt(7)
for name,size in [('Title',29),('Heading 1',22),('Heading 2',12)]:
 s=styles[name];s.font.name='Arial';s.font.size=Pt(size);s.font.color.rgb=RGBColor.from_string('15324F');s.font.bold=True;s.paragraph_format.space_before=Pt(10 if name=='Heading 2' else 0);s.paragraph_format.space_after=Pt(6 if name=='Heading 2' else 13);s.paragraph_format.keep_with_next=True
for name,size,color in [('Kicker',8.5,'446776'),('CodeBlock',9.1,'243E51'),('SourceURL',8.4,'466375'),('Note',10.2,'7C4933'),('SourceBody',9.7,'36414D')]:
 if name not in styles:styles.add_style(name,1)
 s=styles[name];s.font.name='Courier New' if name=='CodeBlock' else 'Arial';s.font.size=Pt(size);s.font.color.rgb=RGBColor.from_string(color);s.paragraph_format.space_after=Pt(7);s.paragraph_format.line_spacing=1.05 if name in ['CodeBlock','SourceBody','SourceURL'] else 1.1
styles['Kicker'].font.bold=True;styles['Kicker'].paragraph_format.space_after=Pt(9);styles['Kicker'].paragraph_format.keep_with_next=True
styles['Note'].font.italic=True;styles['Note'].paragraph_format.left_indent=Inches(.12)
styles['SourceURL'].paragraph_format.space_after=Pt(9)
# Page number only; useful in a developer handover, with no decorative rules.
f=sec.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=f.add_run('SSLM / Simulation only   |   ');run.font.name='Arial';run.font.size=Pt(8);run.font.color.rgb=RGBColor.from_string('667481')
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)

def shd(cell,fill):
 tcPr=cell._tc.get_or_add_tcPr();el=OxmlElement('w:shd');el.set(qn('w:fill'),fill);tcPr.append(el)
def margins(cell):
 props=cell._tc.get_or_add_tcPr();m=OxmlElement('w:tcMar')
 for side,value in [('top',85),('left',90),('bottom',85),('right',90)]:
  x=OxmlElement('w:'+side);x.set(qn('w:w'),str(value));x.set(qn('w:type'),'dxa');m.append(x)
 props.append(m)
def add_table(b):
 t=doc.add_table(rows=1,cols=len(b['headers']));t.alignment=WD_TABLE_ALIGNMENT.LEFT;t.autofit=False
 widths=b.get('widths') or [6.5/len(b['headers'])]*len(b['headers'])
 for i,w in enumerate(widths):t.columns[i].width=Inches(w)
 for rowidx,row in enumerate([b['headers']]+b['rows']):
  cells=t.rows[0].cells if rowidx==0 else t.add_row().cells
  for j,text in enumerate(row):
   cell=cells[j];cell.width=Inches(widths[j]);margins(cell);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=1.04;p.paragraph_format.keep_with_next=False
   r=p.add_run(text);r.font.name='Arial';r.font.size=Pt(10.1)
   if rowidx==0:r.bold=True;r.font.color.rgb=RGBColor(255,255,255);shd(cell,'15324F')
   else:r.font.color.rgb=RGBColor.from_string('293B4A')
  # Do not split a logical record over a page.
  prop=t.rows[rowidx]._tr.get_or_add_trPr();x=OxmlElement('w:cantSplit');prop.append(x)
  if rowidx==0:x=OxmlElement('w:tblHeader');prop.append(x)
 # Bottom-only light separators; no grid-like cell cages.
 for row in t.rows[1:]:
  for cell in row.cells:
   bd=OxmlElement('w:tcBorders');bot=OxmlElement('w:bottom');bot.set(qn('w:val'),'single');bot.set(qn('w:sz'),'4');bot.set(qn('w:color'),'DAE2E7');bd.append(bot);cell._tc.get_or_add_tcPr().append(bd)
 doc.add_paragraph().paragraph_format.space_after=Pt(1)

def hyperlink(text):
 p=doc.add_paragraph(style='SourceURL');rid=doc.part.relate_to(text,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
 h=OxmlElement('w:hyperlink');h.set(qn('r:id'),rid);r=OxmlElement('w:r');pr=OxmlElement('w:rPr');size=OxmlElement('w:sz');size.set(qn('w:val'),'16');pr.append(size);r.append(pr);t=OxmlElement('w:t');t.text=text;r.append(t);h.append(r);p._p.append(h)
for i,page in enumerate(pages):
 if i:doc.add_page_break()
 doc.add_paragraph(page['kicker'],'Kicker');doc.add_paragraph(page['title'],'Title' if i==0 else 'Heading 1')
 sourcepage=page['kicker'].startswith(('17 /','18 /'))
 for b in page['blocks']:
  if b['type']=='h':doc.add_paragraph(b['text'],'Heading 2')
  elif b['type']=='table':add_table(b)
  elif b['type']=='code':
   p=doc.add_paragraph(b['text'],'CodeBlock');p.paragraph_format.keep_together=True
   pp=p._p.get_or_add_pPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'F1F5F7');pp.append(shade)
  elif b['type']=='note':doc.add_paragraph(b['text'],'Note')
  elif b['type']=='url':hyperlink(b['text'])
  else:doc.add_paragraph(b['text'],'SourceBody' if sourcepage else 'Normal')
doc.core_properties.title='Soar.AI - Complete Developer Demo Docket';doc.core_properties.subject='Ground-based Sovereign SLM aircraft recovery preparation';doc.core_properties.author='Sovereign SLM Labs';doc.core_properties.keywords='simulation, developer handover, ground recovery, private AI'
out=R/'docs/Soar_AI_Complete_Developer_Docket.docx';doc.save(out);print(out)
