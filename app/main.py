from fastapi import FastAPI, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import os
import uuid
import csv
import io
import sqlite3
from datetime import datetime, timedelta
import hashlib
import qrcode
from reportlab.lib.pagesizes import A4, landscape, letter, A5, A3
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Email configuration
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "kotanikhila25@gmail.com"
EMAIL_PASSWORD = "itkqbhvoamrxhauo"

# Create directories
os.makedirs("templates", exist_ok=True)
os.makedirs("certificates", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Database setup
DB_PATH = "certificates.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            student_email TEXT NOT NULL,
            achievement TEXT NOT NULL,
            organization_name TEXT NOT NULL,
            event_name TEXT NOT NULL,
            certificate_code TEXT UNIQUE NOT NULL,
            qr_code_path TEXT,
            certificate_file_path TEXT,
            template_style TEXT DEFAULT 'classic',
            page_size TEXT DEFAULT 'A4',
            email_sent BOOLEAN DEFAULT 0,
            issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    return hash_password(plain_password) == hashed_password

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_demo_user():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE email = ?", ("demo@example.com",))
    if not c.fetchone():
        hashed = hash_password("demo123")
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
                  ("Demo User", "demo@example.com", hashed, "user"))
        conn.commit()
        print("✅ Demo user created: demo@example.com / demo123")
    conn.close()

def generate_certificate_code():
    return f"CERT-{uuid.uuid4().hex[:8].upper()}"

def generate_pdf_certificate(data, code, template_style='classic', page_size='A4'):
    filename = f"certificates/cert_{code}.pdf"
    
    # Page sizes
    if page_size == 'landscape':
        pagesize = landscape(A4)
    elif page_size == 'A4':
        pagesize = A4
    elif page_size == 'A3':
        pagesize = A3
    elif page_size == 'A5':
        pagesize = A5
    else:
        pagesize = A4
    
    qr_path = f"certificates/qr_{code}.png"
    
    doc = SimpleDocTemplate(filename, pagesize=pagesize, 
                           leftMargin=0.5*inch, rightMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Template Colors and Styles
    templates = {
        'classic': {
            'title_color': colors.HexColor('#1a237e'),
            'name_color': colors.HexColor('#0d47a1'),
            'accent_color': colors.HexColor('#667eea'),
            'bg_color': colors.HexColor('#f8f9ff'),
            'border_color': colors.HexColor('#667eea'),
            'title': 'CERTIFICATE OF ACHIEVEMENT',
            'font_family': 'Helvetica'
        },
        'modern': {
            'title_color': colors.HexColor('#2c3e50'),
            'name_color': colors.HexColor('#2980b9'),
            'accent_color': colors.HexColor('#3498db'),
            'bg_color': colors.HexColor('#ecf0f1'),
            'border_color': colors.HexColor('#3498db'),
            'title': 'CERTIFICATE OF EXCELLENCE',
            'font_family': 'Helvetica'
        },
        'elegant': {
            'title_color': colors.HexColor('#8b0000'),
            'name_color': colors.HexColor('#2c1810'),
            'accent_color': colors.HexColor('#8b0000'),
            'bg_color': colors.HexColor('#f5f0eb'),
            'border_color': colors.HexColor('#8b0000'),
            'title': 'CERTIFICATE OF ACHIEVEMENT',
            'font_family': 'Helvetica'
        },
        'premium': {
            'title_color': colors.HexColor('#1a1a2e'),
            'name_color': colors.HexColor('#e94560'),
            'accent_color': colors.HexColor('#e94560'),
            'bg_color': colors.HexColor('#f8f9fa'),
            'border_color': colors.HexColor('#e94560'),
            'title': 'CERTIFICATE OF EXCELLENCE',
            'font_family': 'Helvetica'
        },
        'gold': {
            'title_color': colors.HexColor('#b8860b'),
            'name_color': colors.HexColor('#8b6914'),
            'accent_color': colors.HexColor('#ffd700'),
            'bg_color': colors.HexColor('#fef9e7'),
            'border_color': colors.HexColor('#b8860b'),
            'title': 'CERTIFICATE OF ACHIEVEMENT',
            'font_family': 'Helvetica'
        },
        'corporate': {
            'title_color': colors.HexColor('#1a237e'),
            'name_color': colors.HexColor('#1a237e'),
            'accent_color': colors.HexColor('#ff6f00'),
            'bg_color': colors.HexColor('#e8eaf6'),
            'border_color': colors.HexColor('#1a237e'),
            'title': 'CERTIFICATE OF APPRECIATION',
            'font_family': 'Helvetica'
        }
    }
    
    # Get template or use classic as default
    template = templates.get(template_style, templates['classic'])
    
    # Title Style
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=28 if page_size == 'A5' else 32,
        alignment=TA_CENTER,
        spaceAfter=15,
        textColor=template['title_color'],
        fontName='Helvetica-Bold'
    )
    
    # Subtitle Style
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=16 if page_size == 'A5' else 18,
        alignment=TA_CENTER,
        spaceAfter=5,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica'
    )
    
    # Name Style (Large)
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontSize=34 if page_size == 'A5' else 40,
        alignment=TA_CENTER,
        spaceAfter=15,
        textColor=template['name_color'],
        fontName='Helvetica-Bold'
    )
    
    # Body Style
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=16 if page_size == 'A5' else 18,
        alignment=TA_CENTER,
        spaceAfter=8,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica'
    )
    
    # Achievement Style
    achievement_style = ParagraphStyle(
        'AchievementStyle',
        parent=styles['Normal'],
        fontSize=18 if page_size == 'A5' else 20,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=template['accent_color'],
        fontName='Helvetica-Bold'
    )
    
    # Info Style
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=14 if page_size == 'A5' else 16,
        alignment=TA_CENTER,
        spaceAfter=8,
        textColor=colors.HexColor('#555555'),
        fontName='Helvetica'
    )
    
    # Date Style
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12 if page_size == 'A5' else 14,
        alignment=TA_CENTER,
        spaceAfter=15,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica'
    )
    
    # Code Style
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=5,
        textColor=colors.HexColor('#888888'),
        fontName='Helvetica'
    )
    
    # Build Content
    content = []
    
    # Decorative Border (for premium, gold, and elegant templates)
    if template_style in ['premium', 'gold', 'elegant']:
        content.append(Spacer(1, 0.2*inch))
        content.append(Paragraph("=" * 80, body_style))
        content.append(Spacer(1, 0.1*inch))
    
    # Title
    content.append(Paragraph(template['title'], title_style))
    content.append(Spacer(1, 0.1*inch))
    content.append(Paragraph("—" * 30, subtitle_style))
    content.append(Spacer(1, 0.3*inch))
    
    # Presentation text
    content.append(Paragraph("This certificate is proudly presented to", body_style))
    content.append(Spacer(1, 0.1*inch))
    
    # Student Name (Large, prominent)
    content.append(Paragraph(data['student_name'], name_style))
    content.append(Spacer(1, 0.1*inch))
    
    # Achievement
    content.append(Paragraph("For outstanding achievement in", body_style))
    content.append(Paragraph(f"<b>{data['achievement']}</b>", achievement_style))
    content.append(Spacer(1, 0.15*inch))
    
    # Event and Organization
    content.append(Paragraph(f"at <b>{data['event_name']}</b>", info_style))
    content.append(Paragraph(f"organized by <b>{data['organization_name']}</b>", info_style))
    content.append(Spacer(1, 0.2*inch))
    
    # Date
    content.append(Paragraph(f"Issued on: {datetime.now().strftime('%B %d, %Y')}", date_style))
    content.append(Spacer(1, 0.2*inch))
    
    # Certificate Code
    content.append(Paragraph(f"Certificate Code: {code}", code_style))
    content.append(Spacer(1, 0.1*inch))
    
    # QR Code
    if os.path.exists(qr_path):
        qr_image = Image(qr_path, width=1.5*inch, height=1.5*inch)
        content.append(qr_image)
        content.append(Spacer(1, 0.05*inch))
        content.append(Paragraph("Scan QR code to verify", code_style))
    
    # Bottom decorative line
    if template_style in ['premium', 'gold', 'elegant']:
        content.append(Spacer(1, 0.1*inch))
        content.append(Paragraph("=" * 80, body_style))
    
    doc.build(content)
    return filename

def generate_qr_code(code):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"http://127.0.0.1:8080/verify?code={code}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"certificates/qr_{code}.png"
    img.save(filename)
    return filename

def send_certificate_email(recipient_email, student_name, certificate_code, pdf_path, achievement, event_name, organization_name):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = f"🎓 Your Certificate - {certificate_code}"
        
        verification_url = f"http://127.0.0.1:8080/verify?code={certificate_code}"
        
        body = f"""
Dear {student_name},

Congratulations on your achievement! 🎉

You have been awarded a certificate for:
📋 Achievement: {achievement}
🏢 Event: {event_name}
🏛️ Organization: {organization_name}

📋 Certificate Details:
• Certificate Code: {certificate_code}
• Issue Date: {datetime.now().strftime('%B %d, %Y')}

🔍 Verify your certificate online:
{verification_url}

📱 Scan the QR code on your certificate to verify instantly.

Best regards,
Certificate Generator System

---
This is an automated email. Please do not reply.
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= certificate_{certificate_code}.pdf')
            msg.attach(part)
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

# Initialize database
init_db()
create_demo_user()

# FastAPI app
app = FastAPI()

app.mount("/certificates", StaticFiles(directory="certificates"), name="certificates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def read_html(filename):
    try:
        with open(f"templates/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "<h1>File not found</h1>"

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=read_html("index.html"))

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=read_html("login.html"))

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    return HTMLResponse(content=read_html("signup.html"))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=read_html("dashboard.html"))

@app.get("/bulk-upload", response_class=HTMLResponse)
async def bulk_upload_page():
    return HTMLResponse(content=read_html("bulk_upload.html"))

@app.post("/api/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("user")
):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return JSONResponse({"success": False, "message": "Email already registered"}, status_code=400)
        hashed = hash_password(password)
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", (name, email, hashed, role))
        conn.commit()
        conn.close()
        return {"success": True, "message": "User created successfully", "user": {"name": name, "email": email, "role": role}}
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)

@app.post("/api/login")
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if not user:
            return JSONResponse({"success": False, "message": "User not found"}, status_code=401)
        if not verify_password(password, user['password']):
            return JSONResponse({"success": False, "message": "Invalid password"}, status_code=401)
        token = f"token_{uuid.uuid4().hex}_{user['id']}"
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user['id'], "name": user['name'], "email": user['email'], "role": user['role']}
        }
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)

@app.post("/api/generate-certificate")
async def generate_certificate(
    student_name: str = Form(...),
    student_email: str = Form(...),
    achievement: str = Form(...),
    organization_name: str = Form(...),
    event_name: str = Form(...),
    template_style: str = Form("classic"),
    page_size: str = Form("A4"),
    send_email: str = Form("true"),
    token: str = Form(...)
):
    if not token or not token.startswith("token_"):
        return JSONResponse({"success": False, "message": "Invalid token"}, status_code=401)
    
    try:
        code = generate_certificate_code()
        certificate_id = f"CERT-{uuid.uuid4().hex[:8]}"
        data = {
            'student_name': student_name,
            'student_email': student_email,
            'achievement': achievement,
            'organization_name': organization_name,
            'event_name': event_name
        }
        
        qr_path = generate_qr_code(code)
        pdf_path = generate_pdf_certificate(data, code, template_style, page_size)
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO certificates (
                certificate_id, student_name, student_email, achievement,
                organization_name, event_name, certificate_code,
                qr_code_path, certificate_file_path, template_style, page_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (certificate_id, student_name, student_email, achievement,
              organization_name, event_name, code, qr_path, pdf_path,
              template_style, page_size))
        conn.commit()
        conn.close()
        
        email_sent = False
        if send_email == "true" and student_email:
            email_sent = send_certificate_email(student_email, student_name, code, pdf_path, achievement, event_name, organization_name)
        
        with open(qr_path, "rb") as f:
            qr_data = base64.b64encode(f.read()).decode()
        
        with open(pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode()
        
        return {
            "success": True,
            "certificate_code": code,
            "student_name": student_name,
            "student_email": student_email,
            "achievement": achievement,
            "organization_name": organization_name,
            "event_name": event_name,
            "issued_date": datetime.now().isoformat(),
            "download_url": f"/download/{code}",
            "qr_code": f"data:image/png;base64,{qr_data}",
            "pdf_preview": f"data:application/pdf;base64,{pdf_data}",
            "template_style": template_style,
            "page_size": page_size,
            "email_sent": email_sent,
            "verification_url": f"http://127.0.0.1:8080/verify?code={code}"
        }
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)

@app.post("/api/bulk-upload")
async def bulk_upload(
    file: UploadFile = File(...),
    token: str = Form(...)
):
    if not token or not token.startswith("token_"):
        return JSONResponse({"success": False, "message": "Invalid token"}, status_code=401)
    
    if not file.filename.endswith('.csv'):
        return JSONResponse({"success": False, "message": "Please upload a CSV file"}, status_code=400)
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
        csv_file = io.StringIO(content_str)
        reader = csv.DictReader(csv_file)
        
        headers = reader.fieldnames
        if not headers:
            return JSONResponse({"success": False, "message": "CSV file is empty or invalid"}, status_code=400)
        
        required = ['student_name', 'student_email']
        missing = [col for col in required if col not in headers]
        if missing:
            return JSONResponse({
                "success": False, 
                "message": f"Missing required columns: {', '.join(missing)}"
            }, status_code=400)
        
        certificates = []
        errors = []
        row_count = 0
        
        for row in reader:
            row_count += 1
            if not row.get('student_name') or not row.get('student_email'):
                continue
            
            try:
                code = generate_certificate_code()
                certificate_id = f"CERT-{uuid.uuid4().hex[:8]}"
                
                data = {
                    'student_name': row['student_name'].strip(),
                    'student_email': row['student_email'].strip(),
                    'achievement': row.get('achievement', 'Achievement').strip() or 'Achievement',
                    'organization_name': row.get('organization_name', 'Organization').strip() or 'Organization',
                    'event_name': row.get('event_name', 'Event').strip() or 'Event'
                }
                
                qr_path = generate_qr_code(code)
                pdf_path = generate_pdf_certificate(data, code, 'classic', 'A4')
                
                conn = get_db()
                c = conn.cursor()
                c.execute('''
                    INSERT INTO certificates (
                        certificate_id, student_name, student_email, achievement,
                        organization_name, event_name, certificate_code,
                        qr_code_path, certificate_file_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    certificate_id, 
                    data['student_name'], 
                    data['student_email'],
                    data['achievement'], 
                    data['organization_name'], 
                    data['event_name'],
                    code, 
                    qr_path, 
                    pdf_path
                ))
                conn.commit()
                conn.close()
                
                certificates.append({
                    'certificate_code': code,
                    'student_name': data['student_name']
                })
                
            except Exception as e:
                errors.append(f"Row {row_count}: {str(e)}")
                continue
        
        if not certificates:
            return JSONResponse({
                "success": False, 
                "message": "No valid certificates generated. Please check your CSV format."
            }, status_code=400)
        
        return {
            "success": True,
            "message": f"Successfully generated {len(certificates)} certificates",
            "certificates": certificates,
            "errors": errors if errors else None,
            "total_rows": row_count
        }
        
    except Exception as e:
        return JSONResponse({
            "success": False, 
            "message": f"Error processing file: {str(e)}"
        }, status_code=500)

@app.get("/api/certificates")
async def get_certificates(token: str):
    if not token or not token.startswith("token_"):
        return JSONResponse({"success": False, "message": "Invalid token"}, status_code=401)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM certificates ORDER BY issued_date DESC")
    certs = c.fetchall()
    conn.close()
    return {"success": True, "certificates": [dict(cert) for cert in certs]}

@app.get("/verify")
async def verify_certificate(code: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM certificates WHERE certificate_code = ?", (code,))
    cert = c.fetchone()
    conn.close()
    if cert:
        return {
            "valid": True,
            "student_name": cert['student_name'],
            "achievement": cert['achievement'],
            "organization_name": cert['organization_name'],
            "event_name": cert['event_name'],
            "issued_date": cert['issued_date'],
            "template_style": cert['template_style'],
            "page_size": cert['page_size'],
            "certificate_code": cert['certificate_code']
        }
    return {"valid": False, "message": "Certificate not found"}

@app.get("/download/{code}")
async def download_certificate(code: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT certificate_file_path FROM certificates WHERE certificate_code = ?", (code,))
    result = c.fetchone()
    conn.close()
    if not result:
        raise HTTPException(404, "Certificate not found")
    return FileResponse(result['certificate_file_path'], filename=f"certificate_{code}.pdf", media_type="application/pdf")

@app.get("/view-certificate/{code}")
async def view_certificate(code: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT certificate_file_path FROM certificates WHERE certificate_code = ?", (code,))
    result = c.fetchone()
    conn.close()
    if not result:
        raise HTTPException(404, "Certificate not found")
    return FileResponse(result['certificate_file_path'], media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)