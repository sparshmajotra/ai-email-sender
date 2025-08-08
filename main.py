from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Warn if missing environment variables
missing_vars = [var for var, val in {
    "GROQ_API_KEY": GROQ_API_KEY,
    "SENDER_EMAIL": SENDER_EMAIL,
    "SENDER_PASSWORD": SENDER_PASSWORD
}.items() if not val]

if missing_vars:
    raise ValueError(f"Missing required environment variables in .env file: {', '.join(missing_vars)}")

app = FastAPI()

# Serve templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve homepage."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_email(prompt: str = Form(...)):
    """Generate an email using the Groq API."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are an assistant that writes professional and polite emails."},
            {"role": "user", "content": prompt.strip()}
        ]
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        result = response.json()

        if "error" in result:
            return JSONResponse({"error": result["error"].get("message", "Unknown error")}, status_code=500)

        choices = result.get("choices", [])
        if not choices:
            return JSONResponse({"error": "No response from AI model"}, status_code=500)

        message = choices[0].get("message", {}).get("content")
        if not message:
            message = choices[0].get("text", "")

        if not message:
            return JSONResponse({"error": "Invalid API response format"}, status_code=500)

        return JSONResponse({"email": message.strip()})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/send")
async def send_email(
    recipient: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...)
):
    """Send an email using Gmail SMTP."""
    recipient = recipient.strip()
    subject = subject.strip()
    body = body.strip()

    if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient):
        return {"status": "error", "message": "Invalid recipient email address"}

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return {"status": "success", "message": "Email sent successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
