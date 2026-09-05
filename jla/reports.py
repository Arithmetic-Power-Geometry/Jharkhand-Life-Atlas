from __future__ import annotations
from io import BytesIO
from datetime import datetime, timezone
from html import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import mm

def _rows(df):
    try: return df.to_dicts()
    except Exception: return df or []

def html_report(title: str, place_rows, source_rows, release="1.1.0") -> bytes:
    now=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    places=_rows(place_rows); sources=_rows(source_rows)
    body=''.join(f"<tr><td>{escape(str(k))}</td><td>{escape(str(v if v is not None else 'Not available'))}</td></tr>" for row in places for k,v in row.items())
    refs=''.join(f"<li><strong>{escape(str(s.get('title','')))}</strong> — {escape(str(s.get('publisher','')))} ({escape(str(s.get('reference_year','')))}). {escape(str(s.get('url','')))}</li>" for s in sources)
    html=f"""<!doctype html><html><head><meta charset='utf-8'><title>{escape(title)}</title><style>body{{font-family:Arial,sans-serif;max-width:980px;margin:40px auto;color:#183028}}h1{{color:#176B55}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d7e3de;padding:8px;text-align:left}}.note{{background:#edf3f0;padding:12px;border-radius:8px}}</style></head><body><h1>{escape(title)}</h1><p>Jharkhand Life Atlas v{release} · generated {now}</p><div class='note'>Evidence profile. Missing data means unavailable/not validated; it does not mean zero. JLA is non-partisan and does not attribute political responsibility.</div><h2>Place record</h2><table>{body}</table><h2>Sources and references</h2><ol>{refs}</ol><p>Copyright (C) 2026 Mohammad Amir Khusru Akhtar · CC BY 4.0 for original JLA material.</p></body></html>"""
    return html.encode('utf-8')

def pdf_report(title: str, place_rows, source_rows, release="1.1.0") -> bytes:
    mem=BytesIO(); doc=SimpleDocTemplate(mem,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='JLA_Title', parent=styles['Title'], textColor=colors.HexColor('#176B55'), alignment=TA_CENTER, spaceAfter=12))
    story=[Paragraph(title,styles['JLA_Title']), Paragraph(f"Jharkhand Life Atlas v{release}",styles['Normal']), Spacer(1,8), Paragraph("Evidence profile. Missing data means unavailable/not validated; it does not mean zero. JLA is non-partisan and does not attribute political responsibility.",styles['BodyText']), Spacer(1,10)]
    for row in _rows(place_rows):
        data=[[Paragraph('<b>Field</b>',styles['BodyText']),Paragraph('<b>Value</b>',styles['BodyText'])]]
        for k,v in row.items(): data.append([Paragraph(str(k),styles['BodyText']),Paragraph(str(v if v is not None else 'Not available'),styles['BodyText'])])
        t=Table(data,colWidths=[65*mm,95*mm],repeatRows=1); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCDAD4')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EDF3F0')),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),5)])); story += [t,Spacer(1,12)]
    story += [Paragraph('Sources and references',styles['Heading2'])]
    for i,s in enumerate(_rows(source_rows),1): story.append(Paragraph(f"{i}. <b>{s.get('title','')}</b>. {s.get('publisher','')} ({s.get('reference_year','')}). {s.get('url','')}",styles['BodyText']))
    story += [Spacer(1,12),Paragraph('Copyright (C) 2026 Mohammad Amir Khusru Akhtar · CC BY 4.0 for original JLA material.',styles['Normal'])]
    doc.build(story); return mem.getvalue()
