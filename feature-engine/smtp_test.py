import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.elasticemail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")

required = {
    "SMTP_SERVER": SMTP_SERVER,
    "SMTP_USERNAME": SMTP_USERNAME,
    "ALERT_EMAIL_FROM": ALERT_EMAIL_FROM,
    "ALERT_EMAIL_TO": ALERT_EMAIL_TO,
}

missing = [name for name, val in required.items() if not val]
if missing:
    print(
        "❌ Erreur : Les variables "
        + ", ".join(missing)
        + " doivent être définies."
    )
    sys.exit(1)

msg = MIMEMultipart()
msg["From"] = ALERT_EMAIL_FROM
msg["To"] = ALERT_EMAIL_TO
msg["Subject"] = "SMTP test"
msg.attach(MIMEText("This is a test email from smtp_test.py", "plain"))

try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(ALERT_EMAIL_FROM, [ALERT_EMAIL_TO], msg.as_string())
    print("✅ Email envoyé avec succès")
except Exception as e:
    print(f"❌ Erreur lors de l'envoi de l'email: {e}")
