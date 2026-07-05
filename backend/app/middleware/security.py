import re
import logging
from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r"(?i)(ignore|forget|disregard)\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions|prompts|rules)",
    r"(?i)(ignore|forget|disregard)\s+(previous|above|all|any|every)\s+.{0,20}(instructions|prompts|rules)",
    r"(?i)you\s+are\s+now\s+",
    r"(?i)act\s+as\s+(if|a)\s+",
    r"(?i)system\s*:\s*",
    r"(?i)```\s*(system|admin|root)",
    r"(?i)\[INST\]",
    r"(?i)<\|im_start\|>",
    r"(?i)reveal\s+(the\s+)?(system|hidden)\s+(prompt|instructions)",
    r"(?i)override\s+(safety|security|content)\s+(filter|guard|policy)",
]


def check_prompt_injection(text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def sanitize_input(text: str) -> str:
    if check_prompt_injection(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input contains potentially malicious content",
        )
    return text.strip()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path in self.DOCS_PATHS:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' data: https://fastapi.tiangolo.com; font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; font-src 'self'; connect-src 'self'"
            )
        return response
