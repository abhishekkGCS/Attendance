from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pymysql
import random
import smtplib
from email.message import EmailMessage

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ---------------- DB CONFIG ----------------
db = pymysql.connect(
    host="localhost",
    user="root",
    password="root123",
    database="employee_db"
)

# ---------------- SMTP CONFIG (cPanel) ----------------
SMTP_HOST = "mail.galacticclientservices.com"
SMTP_PORT = 587
SMTP_USER = "no-reply@galacticclientservices.com"
SMTP_PASS = "NoReply@2026"

# ---------------- OTP STORE (TEMP) ----------------
otp_store = {}

# ---------------- EMAIL PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def email_page(request: Request):
    return templates.TemplateResponse("email.html", {"request": request})


# ---------------- SEND OTP ----------------
@app.post("/send-otp", response_class=HTMLResponse)
def send_otp(request: Request, email: str = Form(...)):
    cursor = db.cursor()
    cursor.execute("SELECT Official_Email FROM master_employee_data WHERE Official_Email =%s", (email,))
    result = cursor.fetchone()

    if not result:
        return templates.TemplateResponse(
            "email.html",
            {"request": request, "error": "Email not found"}
        )

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = email
    msg["Subject"] = "Your Login OTP"
    msg.set_content(f"Your OTP is: {otp}")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    return templates.TemplateResponse(
        "otp.html",
        {"request": request, "email": email}
    )


# ---------------- VERIFY OTP ----------------
@app.post("/verify-otp", response_class=HTMLResponse)
def verify_otp(
    request: Request,
    email: str = Form(...),
    otp: str = Form(...)
):
    if otp_store.get(email) == otp:
        otp_store.pop(email)
        return HTMLResponse("<h2>Login Successful</h2>")
    else:
        return templates.TemplateResponse(
            "otp.html",
            {"request": request, "email": email, "error": "Invalid OTP"}
        )
