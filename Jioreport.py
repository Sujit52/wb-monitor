import os
import smtplib
import time
from email.mime.text import MIMEText

# ---- Config (values come from GitHub Secrets, never hardcode) ----
EMAIL_ENABLED  = True
EMAIL_SENDERS  = os.environ.get("EMAIL_SENDERS", "").split(",")
EMAIL_PASSWORDS = os.environ.get("EMAIL_PASSWORDS", "").split(",")
EMAIL_RECEIVERS = os.environ.get("EMAIL_RECEIVERS", "sujithembram52@gmail.com")

SUBJECT = "Network Issue Complaint - Jio Service Quality Degradation"

BODY = """Dear Jio Support Team,

I am writing to report a persistent network issue in my area. For the past few days, I've been experiencing:

- Frequent call drops
- Slow internet speed, especially in downloads
- Weak signal strength, even in places where the signal used to be strong earlier

Everything was working fine earlier, but recently the service quality has dropped significantly.
Due to this, I've been forced to recharge on another operator's SIM to stay connected, and I have stopped recharging my Jio number.
Kindly look into the matter and take necessary steps to improve the network performance in this area.

Location: Kalparashi, Silda, Jhargram, 721515
Landmark: Near Kalparashi NSSG Club
Registered Jio Number: 6295367590

I hope for a quick resolution to this issue.

Sincerely,
Sujit Hembram
"""

def send_email_from_sender(sender_email, sender_password, receiver_email):
    """Send email from a specific sender"""
    try:
        msg = MIMEText(BODY, "plain")
        msg["Subject"] = SUBJECT
        msg["From"] = sender_email
        msg["To"] = receiver_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [receiver_email], msg.as_string())
        
        print(f"✅ Email sent successfully from {sender_email} to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email from {sender_email}: {e}")
        return False

def send_emails():
    if not EMAIL_ENABLED:
        print("Email sending is disabled.")
        return

    # Validate sender credentials
    if len(EMAIL_SENDERS) != len(EMAIL_PASSWORDS):
        raise RuntimeError(
            "Number of senders and passwords do not match. "
            "Please ensure EMAIL_SENDERS and EMAIL_PASSWORDS have same count."
        )

    # Remove empty strings
    senders = [s.strip() for s in EMAIL_SENDERS if s.strip()]
    passwords = [p.strip() for p in EMAIL_PASSWORDS if p.strip()]

    if not senders or not passwords:
        raise RuntimeError(
            "EMAIL_SENDERS or EMAIL_PASSWORDS not set properly. "
            "Add them as GitHub Secrets with comma-separated values."
        )

    print(f"📧 Starting to send emails from {len(senders)} sender accounts...")

    success_count = 0
    failure_count = 0

    for i, (sender, password) in enumerate(zip(senders, passwords)):
        print(f"\n📤 Attempt {i+1}/{len(senders)}: Sending from {sender}")
        
        if send_email_from_sender(sender, password, EMAIL_RECEIVERS):
            success_count += 1
        else:
            failure_count += 1
        
        # Add delay between emails to avoid rate limiting (2 seconds)
        if i < len(senders) - 1:
            print("⏳ Waiting 2 seconds before next email...")
            time.sleep(2)

    print(f"\n📊 Summary: {success_count} emails sent successfully, {failure_count} failed.")

if __name__ == "__main__":
    send_emails()
