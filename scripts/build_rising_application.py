"""Build the two private RISING application PDFs from output/pdf/source/application.json.

Requires reportlab, Pillow and pypdf. Fonts are the static Archivo instances in
output/pdf/source/fonts (OFL licensed). Outputs and personal source stay local.
"""
import html
import io
import json
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output/pdf'
DATA = json.loads((OUT / 'source/application.json').read_text())
WORK = json.loads((ROOT / 'content/rising.json').read_text())['projects']
W, H = A4
M = 43
INK = colors.HexColor('#111111')
GREY = colors.HexColor('#555555')
LIGHT = colors.HexColor('#dddddd')
for style in ['Regular', 'Medium', 'Bold', 'Black']:
    pdfmetrics.registerFont(TTFont(f'Archivo-{style}', str(OUT / f'source/fonts/Archivo-{style}.ttf')))
pdfmetrics.registerFontFamily('Archivo-Regular', normal='Archivo-Regular', bold='Archivo-Bold')


def text(c, s, x, y, size=10, font='Regular', color=INK):
    c.setFillColor(color)
    c.setFont(f'Archivo-{font}', size)
    c.drawString(x, H-y-size*.88, s)


def para(c, s, x, y, width, size=10, leading=14, font='Regular', color=INK):
    p = Paragraph(s, ParagraphStyle('body', fontName=f'Archivo-{font}', fontSize=size,
                  leading=leading, textColor=color, allowWidows=0, allowOrphans=0))
    _, height = p.wrap(width, H)
    if y + height > H - 55:
        raise ValueError(f'Text overflows page: {s[:70]} at {y+height}')
    p.drawOn(c, x, H-y-height)
    return y+height


def rule(c, y, x=M, width=None, color=LIGHT):
    c.setStrokeColor(color)
    c.setLineWidth(.5)
    c.line(x, H-y, x+(width if width is not None else W-2*M), H-y)


def link(c, label, url, x, y, size=9):
    text(c, label, x, y, size)
    width=pdfmetrics.stringWidth(label, 'Archivo-Regular', size)
    c.linkURL(url, (x,H-y-size-3,x+width,H-y+2),relative=0,thickness=0)
    rule(c,y+size+2,x,width,INK)


def page(c, label, number):
    text(c,'HTU.',M,30,17,'Black')
    text(c,label,M+119,35,8,'Medium')
    text(c,f'{number:02d} / 02',W-M-33,35,8)
    rule(c,63,color=INK)
    rule(c,H-43)
    text(c,'Hao Wei Tu',M,H-31,8,'Medium')
    link(c,'haowei@haoweitu.info','mailto:haowei@haoweitu.info',M+119,H-31,8)
    link(c,'haoweitu.info', 'https://haoweitu.info/',W-M-62,H-31,8)


def new_pdf(filename,title):
    c=canvas.Canvas(str(OUT/filename),pagesize=A4,pageCompression=1)
    c.setTitle(title)
    c.setAuthor('Hao Wei Tu')
    c.setSubject('Application for RISING Senior Designer, 2027')
    c.setCreator('HTU. / Archivo / custom application layout')
    c.setViewerPreference('DisplayDocTitle','true')
    return c


def cover_letter():
    c=new_pdf('Hao_Wei_Tu_RISING_Cover_Letter.pdf','Hao Wei Tu | RISING | Cover letter & selected work')
    page(c,'RISING 2027 / SENIOR DESIGNER',1)
    text(c,'HAO WEI TU',M,86,43,'Black')
    text(c,'Communication designer / Design Director',M,141,13)
    text(c,'Melbourne, Australia',M,164,9,color=GREY)
    rule(c,192,color=INK)
    text(c,'COVER LETTER',M,212,8,'Medium')
    text(c,'RISING',M,235,9)
    text(c,'Hiring team',M,249,9)
    x=M+119
    y=para(c,'Dear RISING team,',x,211,W-M-x,10.5,14.4)
    for p in DATA['letter']:
        y=para(c,html.escape(p),x,y+11,W-M-x,10.2,14.1)
    y=para(c,'Kind regards,<br/><b>Hao Wei Tu</b>',x,y+15,W-M-x,10.2,14.1)
    link(c,'Selected portfolio: haoweitu.info/rising/',DATA['portfolio'],x,y+14,9)
    c.showPage()
    page(c,'SELECTED WORK FOR RISING',2)
    text(c,'Selected work',M,84,34,'Black')
    text(c,'for RISING.',M,121,34,'Black')
    text(c,'Six projects across identity, print, motion and space.',M,166,10)
    text(c,'Click an image or title to open the full project.',M,183,8.5,color=GREY)
    gap=20
    cw=(W-2*M-gap)/2
    for i,p in enumerate(WORK):
        x=M+(i%2)*(cw+gap)
        top=216+(i//2)*184
        im=Image.open(ROOT/f'assets/work/{p["id"]}/{p["image"]}-1600.webp').convert('RGB')
        im.thumbnail((1100,700),Image.Resampling.LANCZOS)
        ih=112
        scale=min(cw/im.width,ih/im.height)
        dw,dh=im.width*scale,im.height*scale
        c.setFillColor(colors.HexColor('#f4f4f4'))
        c.rect(x,H-top-ih,cw,ih,fill=1,stroke=0)
        encoded=io.BytesIO()
        im.save(encoded,format='JPEG',quality=94,subsampling=0)
        encoded.seek(0)
        c.drawImage(ImageReader(encoded),x+(cw-dw)/2,H-top-ih+(ih-dh)/2,dw,dh)
        url=f'https://haoweitu.info/work/{p["id"]}/'
        c.linkURL(url,(x,H-top-ih,x+cw,H-top),relative=0,thickness=0)
        title=p['title']['en']
        fs=10.7
        while pdfmetrics.stringWidth(title,'Archivo-Bold',fs)>cw:
            fs-=.1
        text(c,title,x,top+121,fs,'Bold')
        c.linkURL(url,(x,H-top-137,x+cw,H-top-119),relative=0,thickness=0)
        caption=DATA['pdf_captions'][p['id']]
        fs=8.4
        while pdfmetrics.stringWidth(caption,'Archivo-Regular',fs)>cw:
            fs-=.1
        text(c,caption,x,top+138,fs)
        para(c,html.escape(p['role']['en']),x,top+153,cw,8,10.2,color=GREY)
    c.save()


def section(c,label,y):
    rule(c,y,color=INK)
    text(c,label,M,y+10,8,'Medium')
    return y+31


def resume():
    c=new_pdf('Hao_Wei_Tu_RISING_Resume.pdf','Hao Wei Tu | RISING | Resume')
    page(c,'RESUME / DESIGN PRACTICE',1)
    text(c,'HAO WEI TU',M,86,43,'Black')
    text(c,'Communication designer / Design Director',M,141,13)
    text(c,'Melbourne, Australia',M,165,9,color=GREY)
    link(c,'haoweitu.info/rising/',DATA['portfolio'],W-M-99,165,9)
    y=para(c,html.escape(DATA['profile']),M,198,W-2*M,10.5,14.5)+22
    y=section(c,'DESIGN EXPERIENCE',y)
    for e in DATA['experience']:
        text(c,e['dates'],M,y+2,8.8,color=GREY)
        x=M+119; width=W-M-x
        y=para(c,html.escape(e['role']),x,y,width,13,16,'Bold')
        y=para(c,html.escape(e['organisation']),x,y+2,width,10,13,color=GREY)+10
        for b in e['points']:
            text(c,'-',x,y,9)
            y=para(c,html.escape(b),x+11,y,width-11,10,13.2)+5
        y+=12
    y=section(c,'SELECTED RECOGNITION',y)
    fs=8.6
    while pdfmetrics.stringWidth(DATA['awards'],'Archivo-Regular',fs)>W-2*M: fs-=.1
    text(c,DATA['awards'],M,y,fs)
    c.showPage()
    page(c,'RESUME / CAPABILITIES & BACKGROUND',2)
    text(c,'Practice &',M,87,34,'Black')
    text(c,'perspective.',M,124,34,'Black')
    y=section(c,'CAPABILITIES & TOOLS',185)
    x=M+119; width=W-M-x
    for label,body in DATA['capabilities']:
        text(c,label,M,y+1,9,'Medium')
        y=para(c,html.escape(body),x,y,width,10.1,13.6)+11
    y=section(c,'SELECTED COMMISSIONS',y+5)
    y=para(c,html.escape(DATA['commissions']),M,y,W-2*M,9.8,13.4)+20
    y=section(c,'MENTORING & TEACHING',y)
    for b in DATA['mentoring']:
        y=para(c,html.escape(b),M,y,W-2*M,9.8,13.2)+6
    y=section(c,'EDUCATION & RESEARCH',y+11)
    for date,title,body in DATA['education']:
        text(c,date,M,y+1,8.8,color=GREY)
        y=para(c,html.escape(title),x,y,width,10,13,'Bold')
        y=para(c,html.escape(body),x,y+2,width,9.5,12.5)+9
    c.save()


if __name__=='__main__':
    cover_letter()
    resume()
    from pypdf import PdfReader
    for path in sorted(OUT.glob('*.pdf')):
        reader=PdfReader(path)
        assert len(reader.pages)==2, path
        print(f'{path.name}: 2 pages, {path.stat().st_size:,} bytes')
