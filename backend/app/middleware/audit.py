import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.database import async_session
from app.models.document import AuditLog

logger = logging.getLogger(__name__)

SENSITIVE_GET_PATHS = ("/api/cases/", "/api/evidence/", "/api/documents/download/")


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        if not path.startswith("/api/"):
            return response

        should_audit = False
        action = ""
        resource_type = "unknown"

        if path == "/api/auth/login" and response.status_code == 401:
            should_audit = True
            action = "login_failed"
            resource_type = "auth"
        elif path == "/api/auth/login" and response.status_code == 200:
            should_audit = True
            action = "login_success"
            resource_type = "auth"
        elif response.status_code == 403:
            should_audit = True
            resource_type = self._extract_resource(path)
            action = f"access_denied_{resource_type}"
        elif request.method in ("POST", "PUT", "DELETE") and response.status_code < 400:
            should_audit = True
            resource_type = self._extract_resource(path)
            action = f"{request.method.lower()}_{resource_type}"
        elif request.method == "GET" and response.status_code < 400:
            if any(path.startswith(p) for p in SENSITIVE_GET_PATHS):
                resource_id = self._extract_id(path)
                if resource_id:
                    should_audit = True
                    resource_type = self._extract_resource(path)
                    action = f"view_{resource_type}"

        if should_audit:
            try:
                user_id = getattr(request.state, "user_id", None)
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent", "")[:500]

                async with async_session() as db:
                    log = AuditLog(
                        user_id=user_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=self._extract_id(path),
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={"status_code": response.status_code},
                    )
                    db.add(log)
                    await db.commit()
            except Exception as e:
                logger.error(f"Audit log failed: {e}")

        return response

    def _extract_resource(self, path: str) -> str:
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            return parts[1]
        return "unknown"

    def _extract_id(self, path: str) -> str | None:
        parts = path.strip("/").split("/")
        for p in parts:
            if p.isdigit():
                return p
        return None
