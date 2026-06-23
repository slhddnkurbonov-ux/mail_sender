import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://flyup.uz"}})

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")  # must be a verified domain/sender in Resend

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    subject = data.get('subject')
    body = data.get('body')
    if not all([subject, body]):
        return jsonify({"error": "Missing required fields"}), 400

    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        json={
            "from": FROM_EMAIL,
            "to": [TO_EMAIL],
            "subject": subject,
            "text": body
        }
    )

    if response.status_code >= 400:
        return jsonify({"error": "Failed to send email", "details": response.text}), 502

    return jsonify({"message": "Email successfully sent"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
