import os
import smtplib
from email.mime.text import MIMEText

# ---- Config (values come from GitHub Secrets, never hardcode) ----
EMAIL_ENABLED  = True
EMAIL_SENDER   = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "sujithembram52@gmail.com")

SUBJECT = "Application For Aawas Plus"

BODY = """Name -Shrimath Hembram
Village. - Kalparashi
P.O. - Silda
G.P. - Silda
Block - Binpur 2
P.S. - Binpur
Dist. - Jhargram
Pincode- 721515
Mob. No. - 9734024615
"""


def send_email():
    if not EMAIL_ENABLED:
        print("Email sending is disabled.")
        return

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        raise RuntimeError(
            "EMAIL_SENDER or EMAIL_PASSWORD not set. "
            "Add them as GitHub Secrets and pass via env in the workflow."
        )

    msg = MIMEText(BODY, "plain")
    msg["Subject"] = SUBJECT
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        print(f"Email sent successfully to {EMAIL_RECEIVER}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


if __name__ == "__main__":
    send_email()
