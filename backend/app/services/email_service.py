import hashlib
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from app.config import settings


class EmailBackend(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, html_body: str) -> bool:
        ...


class ConsoleEmailBackend(EmailBackend):
    async def send(self, to: str, subject: str, html_body: str) -> bool:
        print(f"\n{'='*60}")
        print(f"[EMAIL] To: {to}")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Body:\n{html_body}")
        print(f"{'='*60}\n")
        return True


class ResendEmailBackend(EmailBackend):
    async def send(self, to: str, subject: str, html_body: str) -> bool:
        import resend
        resend.api_key = settings.resend_api_key
        resend.Emails.send({
            "from": f"{settings.email_from_name} <{settings.email_from_address}>",
            "to": [to],
            "subject": subject,
            "html": html_body,
        })
        return True


class BrevoEmailBackend(EmailBackend):
    async def send(self, to: str, subject: str, html_body: str) -> bool:
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.brevo_api_key
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to}],
            sender={"name": settings.email_from_name, "email": settings.email_from_address},
            subject=subject,
            html_content=html_body,
        )
        try:
            api_instance.send_transac_email(send_smtp_email)
            return True
        except ApiException:
            return False


def get_email_backend() -> EmailBackend:
    if settings.email_backend == "resend":
        return ResendEmailBackend()
    elif settings.email_backend == "brevo":
        return BrevoEmailBackend()
    return ConsoleEmailBackend()


def generate_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hash)."""
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def get_verification_expiry() -> datetime:
    return datetime.utcnow() + timedelta(hours=settings.email_verification_expire_hours)


def get_reset_expiry() -> datetime:
    return datetime.utcnow() + timedelta(hours=settings.password_reset_expire_hours)


async def send_verification_email(to_email: str, full_name: str, token: str):
    link = f"{settings.frontend_url}/verify-email/{token}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #3b82f6;">Welcome to CrimeGPT</h2>
        <p>Hi {full_name},</p>
        <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                Verify Email Address
            </a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">Or copy this link: {link}</p>
        <p style="color: #6b7280; font-size: 14px;">This link expires in {settings.email_verification_expire_hours} hours.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
        <p style="color: #9ca3af; font-size: 12px;">CrimeGPT - AI Investigation System</p>
    </div>
    """
    backend = get_email_backend()
    await backend.send(to_email, "Verify Your CrimeGPT Account", html)


async def send_password_reset_email(to_email: str, full_name: str, token: str):
    link = f"{settings.frontend_url}/reset-password/{token}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #3b82f6;">Password Reset Request</h2>
        <p>Hi {full_name},</p>
        <p>We received a request to reset your password. Click the button below to set a new password:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                Reset Password
            </a>
        </p>
        <p style="color: #6b7280; font-size: 14px;">Or copy this link: {link}</p>
        <p style="color: #6b7280; font-size: 14px;">This link expires in {settings.password_reset_expire_hours} hour(s). If you didn't request this, ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
        <p style="color: #9ca3af; font-size: 12px;">CrimeGPT - AI Investigation System</p>
    </div>
    """
    backend = get_email_backend()
    await backend.send(to_email, "CrimeGPT Password Reset", html)


async def send_approval_email(to_email: str, full_name: str):
    login_link = f"{settings.frontend_url}/login"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #10b981;">Account Approved!</h2>
        <p>Hi {full_name},</p>
        <p>Your CrimeGPT account has been approved by an administrator. You can now log in to the system.</p>
        <p>On your first login, you will be prompted to change your password for security purposes.</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{login_link}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                Log In Now
            </a>
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
        <p style="color: #9ca3af; font-size: 12px;">CrimeGPT - AI Investigation System</p>
    </div>
    """
    backend = get_email_backend()
    await backend.send(to_email, "Your CrimeGPT Account Has Been Approved", html)


async def send_rejection_email(to_email: str, full_name: str, reason: str | None = None):
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #ef4444;">Registration Declined</h2>
        <p>Hi {full_name},</p>
        <p>Your CrimeGPT registration has been reviewed and unfortunately was not approved.</p>
        {"<p><strong>Reason:</strong> " + reason + "</p>" if reason else ""}
        <p>If you believe this was in error, please contact your department administrator.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
        <p style="color: #9ca3af; font-size: 12px;">CrimeGPT - AI Investigation System</p>
    </div>
    """
    backend = get_email_backend()
    await backend.send(to_email, "CrimeGPT Registration Update", html)


async def send_suspension_email(to_email: str, full_name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #f59e0b;">Account Suspended</h2>
        <p>Hi {full_name},</p>
        <p>Your CrimeGPT account has been suspended by an administrator. You will not be able to log in until your account is reactivated.</p>
        <p>Please contact your department administrator for more information.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
        <p style="color: #9ca3af; font-size: 12px;">CrimeGPT - AI Investigation System</p>
    </div>
    """
    backend = get_email_backend()
    await backend.send(to_email, "CrimeGPT Account Suspended", html)
