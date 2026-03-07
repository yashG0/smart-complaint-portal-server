from __future__ import annotations

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


def send_password_reset_code(*, to_email: str, code: str) -> None:
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured.",
        )

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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send reset code email right now.",
        ) from exc
