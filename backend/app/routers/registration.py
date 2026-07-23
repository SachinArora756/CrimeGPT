from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models.user import User, UserStatus
from app.models.document import AuditLog
from app.schemas.registration import (
    RegistrationRequest,
    RegistrationResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import hash_password
from app.services.email_service import (
    generate_token,
    hash_token,
    get_verification_expiry,
    get_reset_expiry,
    send_verification_email,
    send_password_reset_email,
)
from app.utils.rate_limiter import limiter

router = APIRouter()


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register(request: Request, data: RegistrationRequest, db: AsyncSession = Depends(get_db)):
    """Public self-registration endpoint for officers."""
    # Check uniqueness
    existing = await db.execute(
        select(User).where(
            or_(
                User.username == data.username,
                User.email == data.email,
                User.badge_number == data.badge_number,
            )
        )
    )
    existing_user = existing.scalar_one_or_none()
    if existing_user:
        if existing_user.username == data.username:
            raise HTTPException(status_code=409, detail="Username already taken")
        if existing_user.email == data.email:
            raise HTTPException(status_code=409, detail="Email already registered")
        if existing_user.badge_number == data.badge_number:
            raise HTTPException(status_code=409, detail="Employee/Badge ID already registered")

    # Generate verification token
    raw_token, token_hash = generate_token()

    # Create user with pending status
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        station_id=data.station_id,
        department=data.department,
        badge_number=data.badge_number,
        mobile_number=data.mobile_number,
        is_active=False,
        status=UserStatus.PENDING,
        email_verified=False,
        admin_approved=False,
        force_password_change=False,
        email_verification_token_hash=token_hash,
        email_verification_expiry=get_verification_expiry(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Send verification email
    try:
        await send_verification_email(user.email, user.full_name, raw_token)
    except Exception:
        pass  # Don't fail registration if email fails

    # Audit log
    try:
        async with async_session() as audit_db:
            log = AuditLog(
                user_id=user.id,
                action="user_registered",
                resource_type="auth",
                resource_id=str(user.id),
                ip_address=request.client.host if request.client else "unknown",
                details=f"Self-registration: {user.username} ({user.email})",
            )
            audit_db.add(log)
            await audit_db.commit()
    except Exception:
        pass

    return RegistrationResponse(
        message="Registration submitted successfully. Please verify your email. Your account will become active after administrator approval.",
        user_id=user.id,
        email=user.email,
    )


@router.post("/verify-email")
@limiter.limit("10/minute")
async def verify_email(request: Request, data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify email address using token from verification email."""
    token_hash = hash_token(data.token)

    result = await db.execute(
        select(User).where(
            User.email_verification_token_hash == token_hash,
            User.email_verification_expiry > datetime.utcnow(),
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    if user.email_verified:
        return {"message": "Email already verified"}

    user.email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expiry = None
    await db.commit()

    # Audit log
    try:
        async with async_session() as audit_db:
            log = AuditLog(
                user_id=user.id,
                action="email_verified",
                resource_type="auth",
                resource_id=str(user.id),
                ip_address=request.client.host if request.client else "unknown",
            )
            audit_db.add(log)
            await audit_db.commit()
    except Exception:
        pass

    return {"message": "Email verified successfully. Your account is pending administrator approval."}


@router.post("/resend-verification")
@limiter.limit("2/hour")
async def resend_verification(request: Request, data: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    """Resend verification email for pending registrations."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user or user.email_verified:
        return {"message": "If this email has a pending registration, a new verification link has been sent."}

    raw_token, token_hash = generate_token()
    user.email_verification_token_hash = token_hash
    user.email_verification_expiry = get_verification_expiry()
    await db.commit()

    try:
        await send_verification_email(user.email, user.full_name, raw_token)
    except Exception:
        pass

    return {"message": "If this email has a pending registration, a new verification link has been sent."}


@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset link."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Always return generic response to prevent email enumeration
    generic_response = {"message": "If this email is registered, a password reset link has been sent."}

    if not user or not user.is_active:
        return generic_response

    raw_token, token_hash = generate_token()
    user.password_reset_token_hash = token_hash
    user.password_reset_expiry = get_reset_expiry()
    await db.commit()

    try:
        await send_password_reset_email(user.email, user.full_name, raw_token)
    except Exception:
        pass

    # Audit log
    try:
        async with async_session() as audit_db:
            log = AuditLog(
                user_id=user.id,
                action="password_reset_requested",
                resource_type="auth",
                resource_id=str(user.id),
                ip_address=request.client.host if request.client else "unknown",
            )
            audit_db.add(log)
            await audit_db.commit()
    except Exception:
        pass

    return generic_response


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token from reset email."""
    token_hash = hash_token(data.token)

    result = await db.execute(
        select(User).where(
            User.password_reset_token_hash == token_hash,
            User.password_reset_expiry > datetime.utcnow(),
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user.hashed_password = hash_password(data.new_password)
    user.password_reset_token_hash = None
    user.password_reset_expiry = None
    user.password_changed_at = datetime.utcnow()
    user.force_password_change = False
    await db.commit()

    # Audit log
    try:
        async with async_session() as audit_db:
            log = AuditLog(
                user_id=user.id,
                action="password_reset_completed",
                resource_type="auth",
                resource_id=str(user.id),
                ip_address=request.client.host if request.client else "unknown",
            )
            audit_db.add(log)
            await audit_db.commit()
    except Exception:
        pass

    return {"message": "Password has been reset successfully. Please log in with your new password."}
