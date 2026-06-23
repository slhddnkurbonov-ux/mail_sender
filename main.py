import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "https://flyup.uz"}})

limiter = Limiter(get_remote_address, app=app, default_limits=[])

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")  # e.g. "FlyUP Tashkent <noreply@flyup.uz>" or "onboarding@resend.dev"

ALLOWED_ORIGIN = "flyup.uz"


@app.route('/send-email', methods=['POST'])
@limiter.limit("5 per hour")
def send_email():
    # --- Origin check (blocks direct curl/script calls bypassing the browser) ---
    origin = request.headers.get('Origin', '')
    if ALLOWED_ORIGIN not in origin:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    # --- Honeypot: bots that auto-fill hidden fields get silently dropped ---
    if data.get('honeypot'):
        return jsonify({"message": "ok"}), 200

    subject = data.get('subject', '')
    customer_name = data.get('customer_name', '').strip()
    customer_email = data.get('customer_email', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    service = data.get('service', '').strip()
    message = data.get('message', '').strip()

    # --- Basic validation ---
    if not subject or not message or not customer_email:
        return jsonify({"error": "Missing required fields"}), 400

    if '@' not in customer_email or '.' not in customer_email:
        return jsonify({"error": "Invalid email address"}), 400

    if len(message) > 5000 or len(customer_name) > 200 or len(subject) > 300:
        return jsonify({"error": "Input too long"}), 400

    if not RESEND_API_KEY:
        return jsonify({"error": "Server misconfiguration: RESEND_API_KEY is not set"}), 500

    plain_text = (
        f"Name: {customer_name}\n"
        f"Phone: {customer_phone}\n"
        f"Email: {customer_email}\n"
        f"Service: {service}\n"
        f"Message: {message}"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f4f4f4; padding: 20px;">
      <div style="background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
        <h2 style="color: #1a1a1a; margin-top: 0; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
          New Inquiry — FlyUP Tashkent
        </h2>
        <table style="width: 100%; font-size: 15px; color: #333333; border-collapse: collapse;">
          <tr>
            <td style="padding: 6px 0; font-weight: bold; width: 100px;">Name:</td>
            <td style="padding: 6px 0;">{customer_name}</td>
          </tr>
          <tr>
            <td style="padding: 6px 0; font-weight: bold;">Email:</td>
            <td style="padding: 6px 0;">
              <a href="mailto:{customer_email}" style="color: #2563eb; text-decoration: none;">{customer_email}</a>
            </td>
          </tr>
          <tr>
            <td style="padding: 6px 0; font-weight: bold;">Phone:</td>
            <td style="padding: 6px 0;">{customer_phone}</td>
          </tr>
          <tr>
            <td style="padding: 6px 0; font-weight: bold;">Service:</td>
            <td style="padding: 6px 0;">{service}</td>
          </tr>
        </table>
        <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 20px 0;">
        <p style="color: #333333; font-size: 15px; line-height: 1.6; white-space: pre-line;">{message}</p>
        <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;">
        <p style="color: #999999; font-size: 12px;">
          Sent automatically from the flyup.uz contact form.
        </p>
      </div>
    </div>
    """

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": FROM_EMAIL,
                "to": [TO_EMAIL],
                "reply_to": customer_email,
                "subject": subject,
                "html": html_body,
                "text": plain_text
            },
            timeout=10
        )
    except requests.RequestException as e:
        return jsonify({"error": "Failed to reach email provider", "details": str(e)}), 502

    if response.status_code >= 400:
        return jsonify({"error": "Failed to send email", "details": response.text}), 502

    return jsonify({"message": "Email successfully sent"}), 200


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests. Please try again later."}), 429


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
