from __future__ import annotations

import html
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status

from core.config import (
    PASSWORD_RESET_CODE_EXPIRE_MINUTES,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_USE_TLS,
)


def _send_message(message: EmailMessage) -> None:
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send email right now.",
        ) from exc


def _ensure_email_configured() -> None:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured.",
        )


def send_password_reset_code(*, to_email: str, code: str) -> None:
    _ensure_email_configured()

    message = EmailMessage()
    message["Subject"] = "Smart Complaint Portal | Password Reset OTP"
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        "Hello,\n\n"
        "We received a request to reset your Smart Complaint Portal password.\n\n"
        f"Your one-time password (OTP) is: {code}\n"
        f"This OTP expires in {PASSWORD_RESET_CODE_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not request this reset, you can safely ignore this email.\n"
        "For your security, please do not share this OTP with anyone.\n\n"
        "Regards,\n"
        "Smart Complaint Portal Team"
    )
    message.add_alternative(
        f"""
        <html>
          <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 0;">
              <tr>
                <td align="center">
                  <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
                    <tr>
                      <td style="padding:20px 24px;background:#0f172a;color:#e2e8f0;font-size:18px;font-weight:700;">
                        Smart Complaint Portal
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:24px;">
                        <p style="margin:0 0 12px 0;font-size:15px;line-height:1.6;">Hello,</p>
                        <p style="margin:0 0 14px 0;font-size:15px;line-height:1.6;">
                          We received a request to reset your Smart Complaint Portal password.
                        </p>
                        <p style="margin:0 0 8px 0;font-size:14px;color:#334155;">Use this one-time password (OTP):</p>
                        <div style="display:inline-block;margin:6px 0 16px 0;padding:10px 14px;background:#0f172a;color:#f8fafc;font-size:24px;font-weight:700;letter-spacing:4px;border-radius:8px;">
                          {code}
                        </div>
                        <p style="margin:0 0 12px 0;font-size:14px;color:#334155;">
                          This OTP expires in {PASSWORD_RESET_CODE_EXPIRE_MINUTES} minutes.
                        </p>
                        <p style="margin:0 0 14px 0;font-size:14px;color:#334155;">
                          If you did not request this reset, you can safely ignore this email.
                        </p>
                        <p style="margin:0;font-size:14px;color:#334155;">
                          For your security, never share this OTP with anyone.
                        </p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:16px 24px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;color:#64748b;">
                        Smart Complaint Portal Team
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """,
        subtype="html",
    )

    try:
        _send_message(message)
    except HTTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send reset code email right now.",
        ) from exc


def send_complaint_assigned_email(
    *,
    to_email: str,
    student_name: str,
    complaint_id: str,
    complaint_title: str,
    department_name: str,
) -> None:
    _ensure_email_configured()

    safe_title = complaint_title.strip()
    message = EmailMessage()
    message["Subject"] = f"Complaint Assigned | {safe_title[:80]}"
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        f"Hello {student_name},\n\n"
        "Your complaint has been assigned to a department.\n\n"
        f"Complaint ID: {complaint_id}\n"
        f"Title: {safe_title}\n"
        f"Assigned Department: {department_name}\n"
        "Current Status: assigned\n\n"
        "You can track updates in the Smart Complaint Portal.\n\n"
        "Regards,\n"
        "Smart Complaint Portal Team"
    )
    message.add_alternative(
        f"""
        <html>
          <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 0;">
              <tr><td align="center">
                <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;">
                  <tr><td style="padding:18px 24px;background:#0f172a;color:#e2e8f0;font-size:18px;font-weight:700;">Smart Complaint Portal</td></tr>
                  <tr><td style="padding:24px;">
                    <p style="margin:0 0 12px 0;">Hello {html.escape(student_name)},</p>
                    <p style="margin:0 0 14px 0;">Your complaint has been assigned to a department.</p>
                    <table role="presentation" cellspacing="0" cellpadding="0" style="font-size:14px;line-height:1.7;color:#334155;">
                      <tr><td style="padding-right:10px;"><strong>Complaint ID:</strong></td><td>{html.escape(complaint_id)}</td></tr>
                      <tr><td style="padding-right:10px;"><strong>Title:</strong></td><td>{html.escape(safe_title)}</td></tr>
                      <tr><td style="padding-right:10px;"><strong>Department:</strong></td><td>{html.escape(department_name)}</td></tr>
                      <tr><td style="padding-right:10px;"><strong>Status:</strong></td><td>assigned</td></tr>
                    </table>
                    <p style="margin:14px 0 0 0;">Track updates in the Smart Complaint Portal dashboard.</p>
                  </td></tr>
                </table>
              </td></tr>
            </table>
          </body>
        </html>
        """,
        subtype="html",
    )
    _send_message(message)


def send_complaint_status_updated_email(
    *,
    to_email: str,
    student_name: str,
    complaint_id: str,
    complaint_title: str,
    previous_status: str,
    current_status: str,
) -> None:
    _ensure_email_configured()

    safe_title = complaint_title.strip()
    message = EmailMessage()
    message["Subject"] = f"Complaint Status Updated | {safe_title[:80]}"
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        f"Hello {student_name},\n\n"
        "Your complaint status has been updated.\n\n"
        f"Complaint ID: {complaint_id}\n"
        f"Title: {safe_title}\n"
        f"Previous Status: {previous_status}\n"
        f"Current Status: {current_status}\n\n"
        "Please check the Smart Complaint Portal for details.\n\n"
        "Regards,\n"
        "Smart Complaint Portal Team"
    )
    message.add_alternative(
        f"""
        <html>
          <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 0;">
              <tr><td align="center">
                <table role="presentation" width="560" cellspacing="0" cellpadding="0" style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;">
                  <tr><td style="padding:18px 24px;background:#0f172a;color:#e2e8f0;font-size:18px;font-weight:700;">Smart Complaint Portal</td></tr>
                  <tr><td style="padding:24px;">
                    <p style="margin:0 0 12px 0;">Hello {html.escape(student_name)},</p>
                    <p style="margin:0 0 14px 0;">Your complaint status has been updated.</p>
                    <table role="presentation" cellspacing="0" cellpadding="0" style="font-size:14px;line-height:1.7;color:#334155;">
                      <tr><td style="padding-right:10px;"><strong>Complaint ID:</strong></td><td>{html.escape(complaint_id)}</td></tr>
                      <tr><td style="padding-right:10px;"><strong>Title:</strong></td><td>{html.escape(safe_title)}</td></tr>
                      <tr><td style="padding-right:10px;"><strong>Previous:</strong></td><td>{html.escape(previous_status)}</td></tr>
                      <tr><td style="padding-right:10px;"><strong>Current:</strong></td><td>{html.escape(current_status)}</td></tr>
                    </table>
                    <p style="margin:14px 0 0 0;">Please check the Smart Complaint Portal for details.</p>
                  </td></tr>
                </table>
              </td></tr>
            </table>
          </body>
        </html>
        """,
        subtype="html",
    )
    _send_message(message)
