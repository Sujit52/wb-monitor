from flask import Flask, request, jsonify, send_file
import smtplib
from email.mime.text import MIMEText
import os
import logging

app = Flask(__name__)

# Enable logging
logging.basicConfig(level=logging.INFO)

# 🔴 YAHAN APNE EMAIL AUR PASSWORDS DAALEIN
EMAIL_SENDERS = [
    "skhembram692@gmail.com",
    "hembrambabu.com@gmail.com",
    "avengerassemble52@gmail.com",
    "babaramdevlite@gmail.com",
    "sujitother52@gmail.com",
    "gurupadahembram975@gmail.com",
    "skh721515@gmail.com",
    "freefiregamer262052@gmail.com"
]

EMAIL_PASSWORDS = [
    "mpri kcya mtsa nvux",
    "gxyr pcho ypwj hqyr",  # 🔴 CHANGE KAREIN
    "pflb ujfv hwdf ebox",  # 🔴 CHANGE KAREIN
    "ydhk fxhm bnow oers",  # 🔴 CHANGE KAREIN
    "nwve ailv byik rgxd",
    "bkik ekkx ifnh iexj",
    "mksx zrjx jrhr blvw",
    "yxag qdek oopd qezx"
]

RECEIVER_EMAIL = "sujithembram52@gmail.com"

# Location options (Yahan nayi location add karein)
LOCATION_OPTIONS = [
    "Kalparashi",
    "Samarbhola",
    "Dakaisol",
    "Dhuapahari",
    "Ledashuli"
]

# Landmark options (Yahan naya landmark add karein)
LANDMARK_OPTIONS = [
    "Near Kalparashi NSSG Club",
    "Dakaisol Madhyamik Sikshya Kendra",
    "Near Raj deep Saren"
]

def send_complaint_emails(name, mobile, location, landmark):
    """Send complaint from multiple email accounts"""

    BODY = f"""Dear Jio Support Team,

I am writing to report a persistent network issue in my area. For the past few days, I've been experiencing:

- Frequent call drops
- Slow internet speed, especially in downloads
- Weak signal strength, even in places where the signal used to be strong earlier

Everything was working fine earlier, but recently the service quality has dropped significantly.
Due to this, I've been forced to recharge on another operator's SIM to stay connected, and I have stopped recharging my Jio number.
Kindly look into the matter and take necessary steps to improve the network performance in this area.

Location: {location}, Silda, Jhargram, 721515
Landmark: {landmark}
Registered Jio Number: {mobile}

I hope for a quick resolution to this issue.

Sincerely,
{name}
"""

    SUBJECT = "Network Issue Complaint - Jio Service Quality Degradation"

    success_count = 0
    failed_emails = []

    for i, (sender, password) in enumerate(zip(EMAIL_SENDERS, EMAIL_PASSWORDS)):
        try:
            msg = MIMEText(BODY, "plain")
            msg["Subject"] = SUBJECT
            msg["From"] = sender
            msg["To"] = RECEIVER_EMAIL

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, [RECEIVER_EMAIL], msg.as_string())

            success_count += 1
            logging.info(f"✅ Email sent from {sender}")

        except Exception as e:
            failed_emails.append(sender)
            logging.error(f"❌ Failed from {sender}: {e}")

    return success_count, failed_emails

@app.route('/')
def index():
    """Serve the HTML form"""
    return send_file('index.html')

@app.route('/send-complaint', methods=['POST'])
def handle_complaint():
    """Handle complaint submission"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        mobile = data.get('mobile', '').strip()
        location = data.get('location', 'Kalparashi')
        landmark = data.get('landmark', 'Near Kalparashi NSSG Club')

        # Validate
        if not name:
            return jsonify({
                'success': False,
                'message': 'Please enter your name'
            })

        if not mobile:
            return jsonify({
                'success': False,
                'message': 'Please enter mobile number'
            })

        if not mobile.isdigit() or len(mobile) != 10:
            return jsonify({
                'success': False,
                'message': 'Please enter valid 10-digit mobile number (numbers only)'
            })

        if len(name) < 2:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid name (at least 2 characters)'
            })

        # Send emails
        success_count, failed_emails = send_complaint_emails(name, mobile, location, landmark)

        if success_count > 0:
            return jsonify({
                'success': True,
                'message': f'✅ Complaint sent successfully from {success_count} email accounts!',
                'sent_from': success_count,
                'total': len(EMAIL_SENDERS)
            })
        else:
            return jsonify({
                'success': False,
                'message': '❌ Failed to send complaint. Please try again later.'
            })

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({
            'success': False,
            'message': '❌ Server error. Please try again.'
        })

@app.route('/status')
def status():
    """Check if server is running"""
    return jsonify({
        'status': 'running',
        'total_senders': len(EMAIL_SENDERS)
    })

if __name__ == '__main__':
    app.run(debug=True)