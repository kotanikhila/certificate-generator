import qrcode
import uuid
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

os.makedirs("certificates", exist_ok=True)

def generate_certificate_code():
    return f"CERT-{uuid.uuid4().hex[:8].upper()}-{datetime.now().strftime('%Y')}"

def generate_qr_code(certificate_code, verification_url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"{verification_url}?code={certificate_code}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_filename = f"certificates/qr_{certificate_code}.png"
    img.save(qr_filename)
    return qr_filename

def generate_pdf_certificate(data):
    certificate_code = generate_certificate_code()
    pdf_filename = f"certificates/cert_{certificate_code}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=32, alignment=TA_CENTER, spaceAfter=30, textColor=colors.HexColor('#1a237e'))
    name_style = ParagraphStyle('NameStyle', parent=styles['Heading1'], fontSize=36, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#0d47a1'))
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=18, alignment=TA_CENTER, spaceAfter=10)
    org_style = ParagraphStyle('OrgStyle', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#424242'))
    
    content = []
    content.append(Paragraph("CERTIFICATE OF ACHIEVEMENT", title_style))
    content.append(Spacer(1, 20))
    content.append(Paragraph("This certificate is presented to", body_style))
    content.append(Spacer(1, 10))
    content.append(Paragraph(data['student_name'], name_style))
    content.append(Spacer(1, 10))
    content.append(Paragraph(f"For {data['achievement']}", body_style))
    content.append(Spacer(1, 15))
    content.append(Paragraph(f"at {data['event_name']} organized by {data['organization_name']}", org_style))
    content.append(Spacer(1, 20))
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER)
    content.append(Paragraph(f"Issued on: {datetime.now().strftime('%B %d, %Y')}", date_style))
    content.append(Spacer(1, 20))
    code_style = ParagraphStyle('CodeStyle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#757575'))
    content.append(Paragraph(f"Certificate Code: {certificate_code}", code_style))
    doc.build(content)
    return pdf_filename, certificate_code

def generate_certificate(data, verification_url):
    pdf_path, certificate_code = generate_pdf_certificate(data)
    qr_path = generate_qr_code(certificate_code, verification_url)
    return {'certificate_code': certificate_code, 'qr_path': qr_path, 'pdf_path': pdf_path}
