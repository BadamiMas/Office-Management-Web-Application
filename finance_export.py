#!/usr/bin/env python3
"""
finance_export.py — PDF generator for TMT Quotations and Tax Invoices
Matches the exact letterhead and layout of the sample documents.
"""

import io
import json
from datetime import datetime

COMPANY_INFO = {
    'TQS': {
        'name': 'TMT QUICK SERVICE PTE LTD',
        'reg':  'ROC/GST Reg No. 201224469E',
        'submission': 'TMT Quick Service Pte Ltd',
        'director': 'Mr Abu Taleb',
        'account': '535-891329-001',
        'paynow':  '201224469E',
    },
    'TQB': {
        'name': 'TMT QUICK BUILDING & INDUSTRY SERVICE PTE LTD',
        'reg':  'ROC/GST Reg No. 201508561M',
        'submission': 'TMT Quick Building & Inds.Svc.P/L',
        'director': 'Mr Abu Taleb',
        'account': '689-508315-001',
        'paynow':  '201508561M',
    },
    'TQEA': {
        'name': 'TMT QUICK ENGINEERING & AUTOMATION',
        'reg':  'ROC/GST Reg No. 53147865C',
        'submission': 'TMT Quick Engineering & Automation',
        'director': 'Mr Abu Taleb',
        'account': '591-705835-001',
        'paynow':  '53147865C',
    },
    'TGC': {
        'name': 'TMT GROUP OF COMPANIES PTE LTD',
        'reg':  'ROC/GST Reg No. 202419343R',
        'submission': 'TMT Group of Companies Pte Ltd',
        'director': 'Mr Abu Taleb',
        'account': '596-683995-001',
        'paynow':  '202419343R',
    },
    'APJ': {
        'name': 'APJ PRIVATE LTD',
        'reg':  'ROC/GST Reg No. 201616561C',
        'submission': 'APJ Private Ltd',
        'director': 'Mr Abu Taleb',
        'account': '687-767038-001',
        'paynow':  '201616561C',
    },
}

SHARED = {
    'address': '60 Benoi Road Unit #02-01 Singapore 629906',
    'email':   'tmtquickservice@yahoo.com.sg',
    'website': 'www.tmtgroup.net',
    'tel':     'Tel: 62521461',
    'fax':     'Fax: 62521565',
}


def _get_reportlab():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    return (A4, colors, cm, mm, SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer, HRFlowable, getSampleStyleSheet,
            ParagraphStyle, TA_CENTER, TA_RIGHT, TA_LEFT)


def _letterhead(story, company_code, doc_type, colors, cm,
                Paragraph, Spacer, HRFlowable, Table, TableStyle,
                ParagraphStyle, TA_CENTER, TA_RIGHT, TA_LEFT,
                getSampleStyleSheet, full_width):
    """Builds the shared letterhead block used by both quote and invoice."""
    co   = COMPANY_INFO.get(company_code, COMPANY_INFO['TQS'])
    info = SHARED

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle('co_name', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1F3864'), leading=20)
    addr_style = ParagraphStyle('addr', parent=styles['Normal'],
        fontSize=8.5, fontName='Helvetica', leading=12)
    small_style = ParagraphStyle('small', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica', leading=11)

    # Logo
    import os
    from reportlab.platypus import Image as RLImage
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'static', 'images', 'tmt.png')
    if os.path.exists(logo_path):
        logo_cell = RLImage(logo_path, width=1.6*cm, height=1.4*cm)
    else:
        logo_cell = ''

    # Header table: [logo | company name + details]
    header_data = [[
        logo_cell,
        [
            Paragraph(co['name'], name_style),
            Paragraph(info['address'], addr_style),
            Paragraph(
                f"<b>E-mail:</b> {info['email']}&nbsp;&nbsp;&nbsp;"
                f"<b>Web site:</b> {info['website']}", small_style),
            Paragraph(
                f"<b>{info['tel']}</b>&nbsp;&nbsp;&nbsp;"
                f"<b>{info['fax']}</b>&nbsp;&nbsp;&nbsp;"
                f"<b>{co['reg']}</b>", small_style),
        ]
    ]]

    ht = Table(header_data, colWidths=[2*cm, full_width - 2*cm])
    ht.setStyle(TableStyle([
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
    ]))
    story.append(ht)
    story.append(HRFlowable(width='100%', thickness=1.5,
                             color=colors.HexColor('#1F3864')))
    story.append(Spacer(1, 6))

    # Doc type banner
    banner_style = ParagraphStyle('banner', parent=styles['Normal'],
        fontSize=13, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1F3864'),
        alignment=TA_CENTER, spaceAfter=6)
    banner = Table([[Paragraph(doc_type, banner_style)]],
                   colWidths=[full_width])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#E8EAF0')),
        ('BOX',        (0,0), (-1,-1), 1, colors.HexColor('#1F3864')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(banner)
    story.append(Spacer(1, 10))


# ─────────────────────────────────────────────────────────────
# QUOTATION PDF
# ─────────────────────────────────────────────────────────────

def generate_quotation_pdf(q):
    """
    q: dict with all quotation fields
    Returns BytesIO PDF
    """
    (A4, colors, cm, mm, SimpleDocTemplate, Table, TableStyle,
     Paragraph, Spacer, HRFlowable, getSampleStyleSheet,
     ParagraphStyle, TA_CENTER, TA_RIGHT, TA_LEFT) = _get_reportlab()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    full_width = A4[0] - 3.6*cm
    story = []
    styles = getSampleStyleSheet()

    normal = ParagraphStyle('n', parent=styles['Normal'],
                            fontSize=9, fontName='Helvetica', leading=13)
    bold   = ParagraphStyle('b', parent=styles['Normal'],
                            fontSize=9, fontName='Helvetica-Bold', leading=13)
    under  = ParagraphStyle('u', parent=styles['Normal'],
                            fontSize=9, fontName='Helvetica-Bold',
                            underlineProportion=0.05, leading=14)

    _letterhead(story, q.get('company_code','TQS'), 'QUOTATION',
                colors, cm, Paragraph, Spacer, HRFlowable,
                Table, TableStyle, ParagraphStyle,
                TA_CENTER, TA_RIGHT, TA_LEFT, getSampleStyleSheet, full_width)

    # To / Date / Ref block
    to_data = [
        [Paragraph(f"<b>To</b>", normal),
         Paragraph(f"<b>Date:</b> {q.get('quote_date','')}", normal)],
        [Paragraph(f"<b>Our Ref:</b> {q.get('ref_no','')}", normal), ''],
        [Paragraph('', normal), ''],
        [Paragraph(f"<b>{q.get('client_name','')}</b>", bold), ''],
        [Paragraph(q.get('client_address','').replace('\n','<br/>'), normal), ''],
    ]
    if q.get('client_attn'):
        to_data.append([Paragraph(f"ATTN: <b>{q['client_attn']}</b>", normal), ''])
    if q.get('client_email'):
        to_data.append([Paragraph(f"E-mail: {q['client_email']}", normal), ''])
    if q.get('client_tel'):
        to_data.append([Paragraph(
            f"Tel: {q['client_tel']}"
            + (f"  Fax: {q['client_fax']}" if q.get('client_fax') else ''), normal), ''])

    to_t = Table(to_data, colWidths=[full_width*0.6, full_width*0.4])
    to_t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(to_t)
    story.append(Spacer(1, 8))

    # Dear Sir/Madam + subject
    story.append(Paragraph('Dear Sir/ Madam,', normal))
    story.append(Spacer(1, 6))
    if q.get('subject'):
        story.append(Paragraph(
            f"<b><u>Ref: {q['subject']}</u></b>", bold))
        story.append(Spacer(1, 4))
    if q.get('intro'):
        story.append(Paragraph(q['intro'], normal))
        story.append(Spacer(1, 8))

    # ── MANPOWER TYPE ──
    if q.get('quote_type') == 'manpower':
        story.append(Paragraph('<b><u>Skilled worker\'s rate</u></b>', bold))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<b>A) Per Man Hour: ${float(q.get('rate_per_hour') or 0):.2f}</b>", bold))
        story.append(Spacer(1, 8))
        story.append(Paragraph('<b><u>Time Frame &amp; Payable Hours</u></b>', bold))
        story.append(Spacer(1, 4))
        tf = [
            'a) Monday to Friday — 0800 Hours To 1700 Hours normal Hours = 8 basic Hours',
            '   After 1700 Hours To 2300 Hours = X1.5 Per Hours',
            '   After 2400 Hours = X Doubles Hours',
            'b) Saturday 0800 Hours To 1200 Hours = X Basic Hours',
            '   After 1200 Hours To 2400 Hours = X 1.5 Per Hours',
            'c) Sunday and Public Holiday — 0800 Hours onward to whole day = X Double Hours',
        ]
        for line in tf:
            story.append(Paragraph(line, normal))
        story.append(Spacer(1, 8))

    # ── LINE ITEMS TYPE ──
    else:
        items = q.get('line_items') or []
        if isinstance(items, str):
            items = json.loads(items)

        tbl_data = [['Sn', 'Description', 'QTY', 'Rate', 'Amount']]
        total = 0
        for i, item in enumerate(items, 1):
            qty  = float(item.get('qty', 0))
            rate = float(item.get('rate', 0))
            amt  = qty * rate
            total += amt
            tbl_data.append([
                str(i),
                item.get('description', ''),
                f"{qty:,.2f}",
                f"$ {rate:,.2f}",
                f"$ {amt:,.2f}",
            ])
        # pad to 8 rows minimum
        while len(tbl_data) < 9:
            tbl_data.append(['', '', '', '', ''])
        tbl_data.append(['', '', 'Total', '', f"$ {total:,.2f}"])

        col_w = [1*cm, full_width-10.5*cm, 2.5*cm, 2.5*cm, 3*cm]
        lt = Table(tbl_data, colWidths=col_w, repeatRows=1)
        lt.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0), colors.HexColor('#1F3864')),
            ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
            ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0,0), (-1,-1), 9),
            ('ALIGN',       (2,0), (-1,-1), 'RIGHT'),
            ('ALIGN',       (0,0), (0,-1), 'CENTER'),
            ('GRID',        (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME',    (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('BACKGROUND',  (0,-1), (-1,-1), colors.HexColor('#D9E1F2')),
            ('TOPPADDING',  (0,0), (-1,-1), 4),
            ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        ]))
        story.append(lt)
        story.append(Spacer(1, 8))

    # Notes
    if q.get('notes'):
        story.append(Paragraph('<b><u>Note:</u></b>', bold))
        story.append(Spacer(1, 3))
        for i, line in enumerate(q['notes'].split('\n'), 1):
            if line.strip():
                story.append(Paragraph(f"{i}) {line.strip()}", normal))
        story.append(Spacer(1, 8))

    # T&C
    story.append(Paragraph('<b><u>Terms &amp; Conditions:</u></b>', bold))
    story.append(Spacer(1, 4))
    default_terms = [
        ('<b>Prices</b>', 'All Prices quoted in Singapore Dollars and Based on Ex-Works Singapore. GST Tax (9%) is excluded and if applicable, to be borne by clients.'),
        ('<b>Validity</b>', 'This quotation remains valid for period of 60 days from the date of Quotation.'),
        ('<b>Payment</b>', '07 days from the invoice date.'),
        ('<b>Transport</b>', f"Provided by {COMPANY_INFO.get(q.get('company_code','TQS'),COMPANY_INFO['TQS'])['submission']}."),
    ]
    if q.get('terms'):
        for line in q['terms'].split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), normal))
    else:
        for label, val in default_terms:
            story.append(Paragraph(f"{label} : {val}", normal))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        'We trust our quotation meets with your requirements and awaits your valued confirmation, '
        'should have any other queries, please feel free to contact us.', normal))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Thanking you and best regards,', normal))
    story.append(Paragraph('Yours truly,', normal))
    story.append(Spacer(1, 12))

    # Signature block
    co = COMPANY_INFO.get(q.get('company_code','TQS'), COMPANY_INFO['TQS'])
    sig_data = [[
        Paragraph(f"Submission By: <b>{co['submission']}</b>", normal),
        Paragraph(f"Approved By: <b>{q.get('client_name','')}</b>", normal),
    ],[
        Paragraph(f"<b>{co['director']}</b>", bold),
        Paragraph(f"<b>{q.get('client_approver_name','')}</b>", bold),
    ],[
        Paragraph('Director', normal),
        Paragraph(f"Designation: {q.get('client_approver_designation','')}", normal),
    ],[
        Paragraph('HP: +65 96405170', normal),
        Paragraph(f"HP: {q.get('client_approver_hp','')}", normal),
    ]]
    sig_t = Table(sig_data, colWidths=[full_width/2, full_width/2])
    sig_t.setStyle(TableStyle([
        ('VALIGN', (0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),3),
    ]))
    story.append(sig_t)
    story.append(Spacer(1, 10))
    story.append(Paragraph('This document is computer generated and does not require a physical signature.',
        ParagraphStyle('cg', parent=styles['Normal'],
                       fontSize=7.5, fontName='Helvetica-Oblique',
                       textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    output.seek(0)
    return output


# ─────────────────────────────────────────────────────────────
# INVOICE PDF
# ─────────────────────────────────────────────────────────────

def generate_invoice_pdf(inv):
    """
    inv: dict with all invoice fields
    Returns BytesIO PDF
    """
    (A4, colors, cm, mm, SimpleDocTemplate, Table, TableStyle,
     Paragraph, Spacer, HRFlowable, getSampleStyleSheet,
     ParagraphStyle, TA_CENTER, TA_RIGHT, TA_LEFT) = _get_reportlab()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    full_width = A4[0] - 3.6*cm
    story = []
    styles = getSampleStyleSheet()

    normal = ParagraphStyle('n', parent=styles['Normal'],
                            fontSize=9, fontName='Helvetica', leading=13)
    bold   = ParagraphStyle('b', parent=styles['Normal'],
                            fontSize=9, fontName='Helvetica-Bold', leading=13)

    _letterhead(story, inv.get('company_code','TQS'), 'TAX INVOICE',
                colors, cm, Paragraph, Spacer, HRFlowable,
                Table, TableStyle, ParagraphStyle,
                TA_CENTER, TA_RIGHT, TA_LEFT, getSampleStyleSheet, full_width)

    # Client + date/invoice block
    client_style = ParagraphStyle('cl', parent=styles['Normal'],
                                  fontSize=12, fontName='Helvetica-Bold', leading=16)
    meta_style   = ParagraphStyle('mt', parent=styles['Normal'],
                                  fontSize=9, fontName='Helvetica', leading=14)

    inv_date = inv.get('invoice_date', '')
    inv_no   = inv.get('invoice_no', '')
    currency = inv.get('currency', 'SGD')

    meta_data = [
        [Paragraph(f"<b>{inv.get('client_name','')}</b>", client_style),
         Paragraph(f"Date&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{inv_date}", meta_style)],
        [Paragraph(inv.get('client_address','').replace('\n','<br/>'), normal),
         Paragraph(f"Invoice No. <b>{inv_no}</b>", meta_style)],
        ['', ''],
        [Paragraph(f"Attn: <b>{inv.get('client_attn','')}</b>", normal),
         Paragraph(f"Currency&nbsp;&nbsp;&nbsp;<b>[{currency}]</b>", meta_style)],
    ]
    mt = Table(meta_data, colWidths=[full_width*0.55, full_width*0.45])
    mt.setStyle(TableStyle([
        ('VALIGN', (0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('BOTTOMPADDING',(0,0),(-1,-1),2),
    ]))
    story.append(mt)
    story.append(Spacer(1, 10))

    # Work order details
    wo_fields = [
        ('WORK ORDER', inv.get('work_order','')),
        ('VESSEL',     inv.get('vessel','')),
        ('ITEM NO',    inv.get('item_no','')),
        ('YARD',       inv.get('yard','')),
    ]
    for label, val in wo_fields:
        if val:
            story.append(Paragraph(
                f"<b>{label}</b>&nbsp;&nbsp;&nbsp;:&nbsp;&nbsp;&nbsp;{val}", normal))
    story.append(Spacer(1, 10))

    # Line items table
    items = inv.get('line_items') or []
    if isinstance(items, str):
        items = json.loads(items)

    tbl_data = [['Sn', 'Description', 'QTY', 'Rate', 'Amount']]
    subtotal = 0
    for i, item in enumerate(items, 1):
        qty  = float(item.get('qty', 0))
        rate = float(item.get('rate', 0))
        amt  = qty * rate
        subtotal += amt
        tbl_data.append([
            str(i),
            item.get('description', ''),
            f"{qty:,.2f}",
            f"$ {rate:,.2f}",
            f"$ {amt:,.2f}",
        ])
    # pad to 8 rows
    while len(tbl_data) < 9:
        tbl_data.append(['', '', '', '', ''])

    gst_amt   = subtotal * 0.09
    total_claim = subtotal + gst_amt

    tbl_data.append(['', 'Total',       '', '', f"$ {subtotal:,.2f}"])
    tbl_data.append(['', 'GST 9%',      '', '', f"$ {gst_amt:,.2f}"])
    tbl_data.append(['', 'Total Claim', '', '', f"$ {total_claim:,.2f}"])

    col_w = [1*cm, full_width-10.5*cm, 2.5*cm, 2.5*cm, 3*cm]
    lt = Table(tbl_data, colWidths=col_w, repeatRows=1)
    lt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1F3864')),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('ALIGN',         (2,0), (-1,-1), 'RIGHT'),
        ('ALIGN',         (0,0), (0,-1), 'CENTER'),
        ('GRID',          (0,0), (-1,-3), 0.5, colors.grey),
        ('LINEABOVE',     (0,-3),(-1,-3), 1, colors.black),
        ('FONTNAME',      (0,-3),(-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE',     (0,-1),(-1,-1), 1.5, colors.black),
        ('LINEBELOW',     (0,-1),(-1,-1), 1.5, colors.black),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(lt)
    story.append(Spacer(1, 10))

    # Closing note
    closing = inv.get('closing_note',
        'In view of above, we hereby submit our first progressive invoice for your kind attention. Thank you.')
    story.append(Paragraph(closing, normal))
    story.append(Spacer(1, 12))

    # Bottom: signature left, bank details right
    co = COMPANY_INFO.get(inv.get('company_code','TQS'), COMPANY_INFO['TQS'])
    terms_lines = [
        '<b>Terms of Payment:</b>',
        'a) Progress payment shall be paid within 2 weeks upon receipt of invoice.',
        'b) Final invoice shall be paid within 1 months upon receipt of invoice.',
    ]
    bank_lines = [
        '<b>Bank Details:</b>',
        'Bank Name: <b>OCBC</b>',
        'Branch&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Jurong North branch',
        f"Account No <b>{co['account']}</b>",
        'AC Type&nbsp;&nbsp;&nbsp;OCBC Current',
        '',
        f"<b>PAYNOW&nbsp;&nbsp;{co['paynow']}</b>",
    ]

    sig_cell = [
        Paragraph('_________________________', normal),
        Spacer(1, 4),
        Paragraph(f"<b>{co['director']}</b>", bold),
        Paragraph('<b>Managing Director</b>', bold),
        Spacer(1, 8),
    ] + [Paragraph(l, normal) for l in terms_lines]

    bank_cell = [Paragraph(l, normal) for l in bank_lines]

    bot = Table([[sig_cell, bank_cell]],
                colWidths=[full_width*0.5, full_width*0.5])
    bot.setStyle(TableStyle([
        ('VALIGN', (0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(0,-1),10),
    ]))
    story.append(bot)
    story.append(Spacer(1, 6))
    story.append(Paragraph('This document is computer generated and does not require a physical signature.',
        ParagraphStyle('cg', parent=styles['Normal'],
                       fontSize=7.5, fontName='Helvetica-Oblique',
                       textColor=colors.grey, alignment=TA_CENTER)))
    story.append(Paragraph('Page 1 of 1',
        ParagraphStyle('pg', parent=styles['Normal'],
                       fontSize=8, alignment=TA_CENTER)))

    doc.build(story)
    output.seek(0)
    return output