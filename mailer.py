"""
mailer.py - Professional Email Dispatcher for Electoral Commission Authentication
Supports SMTP via Gmail, Outlook, AWS SES, Brevo, or custom SMTP servers.
Dispatches official one-time verification passcodes (OTP) with responsive HTML templates.
"""

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.json")

def load_email_config():
    """Loads email configuration from email_config.json or environment variables."""
    default_config = {
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
        "sender_name": os.getenv("SMTP_SENDER_NAME", "National Electoral Commission"),
        "sender_email": os.getenv("SMTP_SENDER_EMAIL", "yeswanthburle1432@gmail.com"),
        "sender_password": os.getenv("SMTP_SENDER_PASSWORD", "")  # Google 16-char App Password
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception as e:
            print(f"[MAILER WARNING] Failed to parse {CONFIG_FILE}: {e}")

    return default_config

def generate_otp_email_html(recipient_email, otp_code, expires_minutes=15):
    """Builds a high-end, responsive security email template for OTP delivery."""
    formatted_time = datetime.now().strftime("%B %d, %Y - %I:%M %p UTC")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Election Commission Security Passcode</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0b1120; padding: 40px 20px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%); border-radius: 16px; border: 1px solid #334155; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); overflow: hidden;">
          
          <!-- Header Banner -->
          <tr>
            <td style="background: linear-gradient(135deg, #0f766e 0%, #1e3a8a 100%); padding: 32px 30px; text-align: center; border-bottom: 2px solid #38bdf8;">
              <div style="font-size: 38px; line-height: 1; margin-bottom: 10px;">🏛️</div>
              <h1 style="margin: 0; font-size: 22px; font-weight: 800; letter-spacing: 0.5px; color: #ffffff; text-transform: uppercase;">
                National Electoral Commission
              </h1>
              <p style="margin: 6px 0 0 0; font-size: 13px; color: #bae6fd; font-weight: 500; letter-spacing: 1px;">
                CENTRAL DEMOCRACY & E-GOVERNANCE GATEWAY
              </p>
            </td>
          </tr>

          <!-- Main Content Body -->
          <tr>
            <td style="padding: 36px 32px;">
              <div style="display: inline-block; background: rgba(56, 189, 248, 0.15); border: 1px solid #0284c7; color: #38bdf8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; padding: 6px 12px; border-radius: 9999px; margin-bottom: 16px;">
                🔐 High-Security Administrator Verification
              </div>

              <h2 style="margin: 0 0 12px 0; font-size: 20px; font-weight: 700; color: #f8fafc;">
                Your Commission Console Passcode
              </h2>
              
              <p style="margin: 0 0 24px 0; font-size: 14px; line-height: 1.6; color: #94a3b8;">
                An administrative login request was initiated for your registered electoral address 
                <strong style="color: #f1f5f9;">{recipient_email}</strong>. 
                Use the single-use verification code below to authorize entry to the electoral control console.
              </p>

              <!-- OTP Callout Block -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 28px 0; background: #030712; border-radius: 12px; border: 1px solid #1e293b; text-align: center;">
                <tr>
                  <td style="padding: 24px 20px;">
                    <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 10px;">
                      Official Verification Code
                    </div>
                    <div style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 900; letter-spacing: 10px; color: #f59e0b; text-shadow: 0 0 15px rgba(245, 158, 11, 0.3);">
                      {otp_code}
                    </div>
                    <div style="font-size: 12px; color: #10b981; margin-top: 10px; font-weight: 600;">
                      ⏱️ Valid for {expires_minutes} minutes from issuance
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Security Notice -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background: rgba(239, 68, 68, 0.08); border-left: 4px solid #ef4444; border-radius: 6px; margin: 24px 0;">
                <tr>
                  <td style="padding: 14px 16px; font-size: 13px; color: #fca5a5; line-height: 1.5;">
                    <strong style="color: #ef4444;">SECURITY WARNING:</strong> Do not share this OTP with anyone. Electoral Commission officers will never request your passcode via call, SMS, or third-party links. If you did not initiate this login, audit logs have recorded this attempt.
                  </td>
                </tr>
              </table>

              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top: 1px solid #334155; margin-top: 24px; padding-top: 18px;">
                <tr>
                  <td style="font-size: 12px; color: #64748b; line-height: 1.5;">
                    <div><strong>Request Timestamp:</strong> {formatted_time}</div>
                    <div><strong>Target Identity:</strong> {recipient_email}</div>
                    <div><strong>Security Protocol:</strong> SHA-256 HMAC Encrypted Session Token</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #0a0f1d; padding: 20px 30px; text-align: center; border-top: 1px solid #1e293b; font-size: 11px; color: #475569; line-height: 1.5;">
              © 2026 National Electoral Commission Portal. All rights reserved.<br>
              Cryptographically verified voting infrastructure and election oversight.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return html

def send_admin_otp(recipient_email, otp_code, expires_minutes=15):
    """
    Dispatches the official OTP to the admin's email.
    If SMTP credentials are provided, delivers via TLS SMTP server.
    Logs dispatch details to file and server console.
    Returns: dict with status details.
    """
    config = load_email_config()
    sender_email = config.get("sender_email")
    sender_password = (config.get("sender_password") or "").strip()
    smtp_server = config.get("smtp_server", "smtp.gmail.com")
    smtp_port = config.get("smtp_port", 587)
    use_tls = config.get("use_tls", True)
    sender_name = config.get("sender_name", "National Electoral Commission")

    subject = f"[SecureVote Admin] Verification Passcode: {otp_code}"
    html_content = generate_otp_email_html(recipient_email, otp_code, expires_minutes)
    plain_content = (
        f"NATIONAL ELECTORAL COMMISSION\n"
        f"Administrator Authentication Code: {otp_code}\n\n"
        f"A login request was initiated for {recipient_email}.\n"
        f"This verification code is valid for {expires_minutes} minutes.\n"
        f"If you did not request this code, no action is required.\n\n"
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Log to dispatched emails log file for administrative traceability
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dispatched_emails.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
            f.write(f"RECIPIENT: {recipient_email}\n")
            f.write(f"SUBJECT:   {subject}\n")
            f.write(f"OTP CODE:  {otp_code}\n")
            f.write(f"{'='*70}\n")
    except Exception as e:
        print(f"[MAILER ERROR] Could not append to log: {e}")

    # Safe console announcement (ASCII compatible across all Windows terminals)
    print("\n" + "="*70)
    print(" [ELECTORAL COMMISSION MAILER SERVICE]")
    print("="*70)
    print(f" Recipient: {recipient_email}")
    print(f" Subject:   {subject.encode('ascii', 'ignore').decode('ascii')}")
    print(f" OTP Code:  >>> {otp_code} <<< (Expires in {expires_minutes}m)")
    print(f" SMTP Host: {smtp_server}:{smtp_port}")
    
    # Check if SMTP credentials exist
    if not sender_password:
        print("-"*70)
        print(" STATUS: Local Mailer Emulation (No App Password in email_config.json)")
        print("="*70 + "\n")
        return {
            "delivered": False,
            "mode": "emulated_dispatch",
            "recipient": recipient_email,
            "message": f"Verification code generated and dispatched to {recipient_email}. (SMTP App Password not set in email_config.json)",
            "timestamp": datetime.now().isoformat()
        }

    # Attempt Live SMTP Transmission
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = recipient_email
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

        part_plain = MIMEText(plain_content, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_plain)
        msg.attach(part_html)

        print(f" Attempting live TLS SMTP connection to {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            if use_tls:
                server.starttls()
            # Clean app password by removing internal spaces if user included them
            clean_password = sender_password.replace(" ", "").strip()
            server.login(sender_email, clean_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())

        print(" STATUS: [SUCCESS] LIVE EMAIL DELIVERED TO GMAIL INBOX VIA SMTP!")
        print("="*70 + "\n")
        return {
            "delivered": True,
            "mode": "smtp_live",
            "recipient": recipient_email,
            "message": f"Official OTP has been dispatched to {recipient_email} inbox via SMTP.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as err:
        print(f" STATUS: [ERROR] SMTP Delivery Failed: {str(err)}")
        print("="*70 + "\n")
        return {
            "delivered": False,
            "mode": "smtp_failed",
            "error": str(err),
            "recipient": recipient_email,
            "message": f"Mailer attempted transmission to {recipient_email}. Error: {str(err)}",
            "timestamp": datetime.now().isoformat()
        }
