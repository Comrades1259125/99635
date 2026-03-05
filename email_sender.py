"""
email_sender.py - Send PDF reports via Gmail SMTP
Uses App Password for authentication (2FA required on Gmail account).
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


def send_pdf_email(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    archive_id: str,
    passkey: str,
    sat_name: str,
):
    """
    Send a PDF report as email attachment via Gmail SMTP.

    Args:
        sender_email: Gmail address (sender)
        app_password: Gmail App Password (NOT the regular password)
        recipient_email: Recipient email address
        pdf_bytes: The PDF file content as bytes
        pdf_filename: Filename for the attachment (e.g. REF-123-20260305.pdf)
        archive_id: Archive reference ID
        passkey: PDF encryption password
        sat_name: Satellite name for the subject line

    Returns:
        (success: bool, message: str)
    """
    try:
        # Build the email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = f"[SAT-REPORT] Mission Archive Report - {archive_id} | {sat_name}"

        # Email body (HTML)
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;
                    background: #f9f9f9; padding: 30px; border-radius: 12px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #333; margin: 0;">SATELLITE TELEMETRY SYSTEM</h2>
                <p style="color: #888; font-size: 0.8rem; letter-spacing: 3px;">ระบบติดตามดาวเทียม — Secure Protocol</p>
            </div>
            <hr style="border: 0; border-top: 1px solid #ddd;">
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;
                        border: 1px solid #eee; text-align: center;">
                <p style="color: #888; font-size: 0.75rem; letter-spacing: 2px; margin-bottom: 5px;">ARCHIVE ID</p>
                <h1 style="color: #FF0000; font-family: 'Courier New', monospace; font-weight: 900;
                           margin: 0 0 15px 0; font-size: 1.8rem;">{archive_id}</h1>
                <p style="color: #888; font-size: 0.75rem; letter-spacing: 2px; margin-bottom: 5px;">PASSWORD</p>
                <h2 style="color: #000; font-family: 'Courier New', monospace; font-weight: 700;
                           margin: 0; font-size: 1.4rem;">{passkey}</h2>
            </div>
            <div style="background: #fff3cd; padding: 12px; border-radius: 8px; border: 1px solid #ffc107;
                        margin: 15px 0;">
                <p style="color: #856404; margin: 0; font-size: 0.85rem;">
                    <strong>Note:</strong> The attached PDF is encrypted. Use the password above to open it.
                </p>
            </div>
            <p style="color: #666; font-size: 0.8rem; margin-top: 20px;">
                Satellite: <strong>{sat_name}</strong><br>
                File: <strong>{pdf_filename}</strong>
            </p>
            <hr style="border: 0; border-top: 1px solid #ddd; margin-top: 20px;">
            <p style="color: #aaa; font-size: 0.7rem; text-align: center;">
                This is an automated message from Satellite Telemetry System.<br>
                Do not reply to this email. Document contains mission-critical data.
            </p>
        </div>
        """
        msg.attach(MIMEText(body_html, "html"))

        # Attach PDF
        pdf_part = MIMEBase("application", "octet-stream")
        pdf_part.set_payload(pdf_bytes)
        encoders.encode_base64(pdf_part)
        pdf_part.add_header(
            "Content-Disposition",
            f"attachment; filename={pdf_filename}",
        )
        msg.attach(pdf_part)

        # Send via Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)

        return True, f"Email sent successfully to {recipient_email}"

    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your Gmail address and App Password."
    except smtplib.SMTPRecipientsRefused:
        return False, f"Recipient email '{recipient_email}' was refused by the server."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"
