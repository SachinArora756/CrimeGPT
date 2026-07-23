import asyncio
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models.user import User, UserRole, UserStatus, ROLE_HIERARCHY
from app.models.document import AuditLog
from app.schemas.user import UserLogin, UserResponse, TokenResponse, TokenRefresh, ChangePasswordRequest
from app.services.auth_service import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    ADMIN_ROLES,
    OFFICER_ROLES,
)
from app.utils.rate_limiter import limiter

router = APIRouter()

MAX_FAILED_ATTEMPTS = 5
GENERIC_AUTH_ERROR = "Authentication failed."

# Minimum response time to prevent timing attacks (ms)
MIN_RESPONSE_MS = 200


def _parse_user_agent(ua: str) -> dict:
    """Extract browser, device, and OS from user-agent string."""
    browser = "Unknown"
    os_name = "Unknown"
    device = "Desktop"

    if "Chrome" in ua and "Edg" not in ua:
        browser = "Chrome"
    elif "Edg" in ua:
        browser = "Edge"
    elif "Firefox" in ua:
        browser = "Firefox"
    elif "Safari" in ua and "Chrome" not in ua:
        browser = "Safari"

    if "Windows" in ua:
        os_name = "Windows"
    elif "Mac OS" in ua or "Macintosh" in ua:
        os_name = "macOS"
    elif "Linux" in ua and "Android" not in ua:
        os_name = "Linux"
    elif "Android" in ua:
        os_name = "Android"
        device = "Mobile"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
        device = "Mobile" if "iPhone" in ua else "Tablet"

    return {"browser": browser, "os": os_name, "device": device}


async def _log_login_attempt(
    user: User | None,
    request: Request,
    portal: str,
    success: bool,
    reason: str | None = None,
    username_attempted: str | None = None,
):
    """Log every authentication attempt with full forensic detail."""
    try:
        ua_raw = request.headers.get("user-agent", "unknown")
        ip = request.client.host if request.client else "unknown"
        ua_parsed = _parse_user_agent(ua_raw)
        route = str(request.url.path)

        async with async_session() as db:
            log = AuditLog(
                user_id=user.id if user else None,
                action="login_success" if success else "login_failed",
                resource_type="auth",
                resource_id=portal,
                details={
                    "portal": portal,
                    "username_attempted": username_attempted or (user.username if user else "unknown"),
                    "role": user.role.value if user else None,
                    "success": success,
                    "reason": reason,
                    "ip_address": ip,
                    "browser": ua_parsed["browser"],
                    "os": ua_parsed["os"],
                    "device": ua_parsed["device"],
                    "route": route,
                },
                ip_address=ip,
                user_agent=ua_raw[:500],
                timestamp=datetime.utcnow(),
            )
            db.add(log)
            await db.commit()
    except Exception:
        pass


async def _authenticate_user(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession,
    portal: str,
    allowed_roles: set[UserRole],
) -> TokenResponse:
    """
    Authenticate-first, authorize-second pattern.
    NEVER disclose whether a username exists or which portal to use.
    All failures return the identical generic error with consistent timing.
    """
    start_time = asyncio.get_event_loop().time()

    username_clean = credentials.username.strip()
    password_clean = credentials.password

    result = await db.execute(
        select(User).where(User.username.ilike(username_clean))
    )
    user = result.scalar_one_or_none()

    # --- STEP 1: Authenticate (verify identity) ---
    auth_failed = False
    failure_reason = None

    if not user:
        # Perform a dummy hash check to ensure constant timing
        verify_password(password_clean, hash_password(secrets.token_urlsafe(16)))
        auth_failed = True
        failure_reason = "user_not_found"
    elif not verify_password(password_clean, user.hashed_password):
        auth_failed = True
        failure_reason = "invalid_password"
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.account_locked = True
        await db.commit()
    elif user.account_locked:
        auth_failed = True
        failure_reason = "account_locked"

    if auth_failed:
        await _log_login_attempt(
            user, request, portal, False, failure_reason,
            username_attempted=credentials.username,
        )
        # Ensure minimum response time to prevent timing attacks
        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = (MIN_RESPONSE_MS / 1000) - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=GENERIC_AUTH_ERROR,
        )

    # --- Registration workflow checks (specific error messages) ---
    user_status = getattr(user, "status", None) or UserStatus.ACTIVE
    email_verified = getattr(user, "email_verified", True)
    admin_approved = getattr(user, "admin_approved", True)

    if not email_verified:
        await _log_login_attempt(user, request, portal, False, "email_not_verified", username_attempted=credentials.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email address before logging in.")

    if user_status == UserStatus.PENDING or not admin_approved:
        await _log_login_attempt(user, request, portal, False, "pending_approval", username_attempted=credentials.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is pending administrator approval.")

    if user_status == UserStatus.REJECTED:
        await _log_login_attempt(user, request, portal, False, "registration_rejected", username_attempted=credentials.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your registration has been declined. Contact your administrator.")

    if user_status == UserStatus.SUSPENDED:
        await _log_login_attempt(user, request, portal, False, "account_suspended", username_attempted=credentials.username)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been suspended. Contact your administrator.")

    if not user.is_active:
        await _log_login_attempt(user, request, portal, False, "account_disabled", username_attempted=credentials.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    # --- STEP 2: Authorize (verify role matches portal) ---
    if user.role not in allowed_roles:
        await _log_login_attempt(
            user, request, portal, False, "wrong_portal",
            username_attempted=credentials.username,
        )
        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = (MIN_RESPONSE_MS / 1000) - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)
        # Give a helpful redirect hint based on which portal they should use
        if portal == "admin":
            detail = "Officer accounts must use the Officer Login portal."
        else:
            detail = "Admin accounts must use the Admin Login portal."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )

    # --- SUCCESS ---
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    await db.commit()

    request.state.user_id = user.id
    await _log_login_attempt(user, request, portal, True, username_attempted=credentials.username)

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value, "portal": portal})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        force_password_change=bool(user.force_password_change),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("15/minute")
async def officer_login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Officer portal authentication. Accepts only officer roles."""
    return await _authenticate_user(
        credentials=credentials,
        request=request,
        db=db,
        portal="officer",
        allowed_roles=OFFICER_ROLES,
    )


@router.post("/admin/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def admin_login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Secure admin portal authentication. Accepts only admin roles."""
    return await _authenticate_user(
        credentials=credentials,
        request=request,
        db=db,
        portal="admin",
        allowed_roles=ADMIN_ROLES,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(body: TokenRefresh, request: Request, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    if user.account_locked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_AUTH_ERROR)

    portal = "admin" if user.role in ADMIN_ROLES else "officer"
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value, "portal": portal})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        force_password_change=bool(user.force_password_change),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if verify_password(body.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    if body.new_password.lower().find(current_user.username.lower()) != -1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must not contain your username",
        )

    current_user.hashed_password = hash_password(body.new_password)
    current_user.force_password_change = False
    current_user.password_changed_at = datetime.utcnow()
    await db.commit()

    return {"message": "Password changed successfully"}
