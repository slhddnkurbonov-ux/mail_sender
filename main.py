import smtplib
from email.message import EmailMessage
import os
from flask import Flask, request, jsonify
from flask_cors import CORS  # 1. Import CORS

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "https://flyup.uz"}})

SENDER_EMAIL = os.getenv("SENDER_EMAIL")

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    to_email = os.getenv("TO_EMAIL")
    subject = data.get('subject')
    body = data.get('body')

    if not all([ subject, body]):
        return jsonify({"error": "Missing required fields: 'subject', or 'body'"}), 400

    # Ensure you are using your NEW App Password here!
    sender_password = os.getenv("SENDER_PASSWORD") 
    
    if not sender_password:
        return jsonify({"error": "Server misconfiguration: EMAIL_APP_PASSWORD is not set"}), 500

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        print(f"Connecting to SMTP server to send email to {to_email}...")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, sender_password)
            server.send_message(msg)
            
        print("Email sent successfully!")
        return jsonify({"message": f"Email successfully sent"}), 200
        
    except smtplib.SMTPAuthenticationError:
        return jsonify({"error": "SMTP Authentication failed."}), 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
