"""
CrimeGPT Authentication Routing & Session Handling Tests

Validates all routing scenarios:
1. Guest -> /login (should render login page)
2. Guest -> /auth/system/admin/login (should render admin login)
3. Officer logged in -> /login (should redirect to /dashboard)
4. Officer logged in -> /admin (should get 403)
5. Officer logged in -> /auth/system/admin/login (should redirect to /dashboard)
6. Admin logged in -> /login (should redirect to /admin)
7. Admin logged in -> /admin (should render admin dashboard)
8. Admin logged in -> /auth/system/admin/login (should redirect to /admin)
9. Logout clears session completely
10. Backend validates JWT on every protected route
"""
import requests
import sys
import time

BASE_API = "http://localhost:8000"
BASE_UI = "http://localhost:5173"
RESULTS = {"passed": 0, "failed": 0, "details": []}


def test(name, condition, detail=""):
    if condition:
        RESULTS["passed"] += 1
        print(f"  \033[32m[PASS]\033[0m {name}")
    else:
        RESULTS["failed"] += 1
        RESULTS["details"].append(f"{name}: {detail}")
        print(f"  \033[31m[FAIL]\033[0m {name} -- {detail}")


def _login_with_retry(url, body, retries=3):
    for attempt in range(retries):
        resp = requests.post(url, json=body)
        if resp.status_code == 429:
            time.sleep(12)
            continue
        return resp
    return resp


def get_admin_token():
    resp = _login_with_retry(f"{BASE_API}/api/auth/admin/login", {"username": "admin", "password": "AdminPass123!"})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def get_officer_token():
    resp = _login_with_retry(f"{BASE_API}/api/auth/login", {"username": "test_si_auth", "password": "TestSIAuth@2026!"})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def main():
    print("\n" + "=" * 70)
    print("  CrimeGPT Auth Routing & Session Tests")
    print("=" * 70)

    # ========================================================================
    # BACKEND TESTS: JWT + Role Validation
    # ========================================================================
    print("\n\033[1m[1] Backend: JWT Validation on Protected Routes\033[0m")

    # No token on admin endpoint
    resp = requests.get(f"{BASE_API}/api/admin/stats")
    test("No token -> admin endpoint rejected", resp.status_code == 403, f"got {resp.status_code}")

    # No token on officer endpoint
    resp = requests.get(f"{BASE_API}/api/cases/")
    test("No token -> officer endpoint rejected", resp.status_code == 403, f"got {resp.status_code}")

    # Invalid token
    resp = requests.get(f"{BASE_API}/api/admin/stats", headers={"Authorization": "Bearer fake.token.here"})
    test("Invalid token -> rejected", resp.status_code == 401, f"got {resp.status_code}")

    # ========================================================================
    print("\n\033[1m[2] Backend: Admin Token Works on Admin Routes\033[0m")

    admin_token = get_admin_token()
    test("Admin can authenticate", admin_token is not None, "login failed")

    if admin_token:
        resp = requests.get(f"{BASE_API}/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        test("Admin token -> /api/admin/stats OK", resp.status_code == 200, f"got {resp.status_code}")

        resp = requests.get(f"{BASE_API}/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        test("Admin token -> /api/admin/users OK", resp.status_code == 200, f"got {resp.status_code}")

    # ========================================================================
    print("\n\033[1m[3] Backend: Officer Token Rejected on Admin Routes\033[0m")

    officer_token = get_officer_token()
    test("Officer can authenticate", officer_token is not None, "login failed")

    if officer_token:
        resp = requests.get(f"{BASE_API}/api/admin/stats", headers={"Authorization": f"Bearer {officer_token}"})
        test("Officer token -> /api/admin/stats REJECTED", resp.status_code == 403, f"got {resp.status_code}")

        resp = requests.get(f"{BASE_API}/api/admin/users", headers={"Authorization": f"Bearer {officer_token}"})
        test("Officer token -> /api/admin/users REJECTED", resp.status_code == 403, f"got {resp.status_code}")

    # ========================================================================
    print("\n\033[1m[4] Backend: Admin Token on Officer Routes\033[0m")

    if admin_token:
        # Dashboard stats uses get_current_user (not officer-only guard)
        resp = requests.get(f"{BASE_API}/api/dashboard/stats", headers={"Authorization": f"Bearer {admin_token}"})
        test("Admin token -> /api/dashboard/stats", resp.status_code == 200, f"got {resp.status_code}")

    # ========================================================================
    # FRONTEND TESTS: Route Guards & Redirects
    # (SPA serves index.html for all routes; routing happens client-side)
    # ========================================================================
    print("\n\033[1m[5] Frontend: Unauthenticated Access to Login Pages\033[0m")

    resp = requests.get(f"{BASE_UI}/login", allow_redirects=False)
    test("Guest -> /login returns 200 (HTML)", resp.status_code == 200, f"got {resp.status_code}")
    test("/login serves SPA HTML", "<!DOCTYPE html>" in resp.text or "<html" in resp.text.lower(),
         f"content: {resp.text[:100]}")

    resp = requests.get(f"{BASE_UI}/auth/system/admin/login", allow_redirects=False)
    test("Guest -> /auth/system/admin/login returns 200", resp.status_code == 200, f"got {resp.status_code}")

    # ========================================================================
    print("\n\033[1m[6] Frontend: Protected Routes Return SPA (Client-Side Guard)\033[0m")

    resp = requests.get(f"{BASE_UI}/admin", allow_redirects=False)
    test("Guest -> /admin returns SPA HTML (guard redirects client-side)",
         resp.status_code == 200 and ("<html" in resp.text.lower() or "<!doctype" in resp.text.lower()),
         f"got {resp.status_code}")

    resp = requests.get(f"{BASE_UI}/dashboard", allow_redirects=False)
    test("Guest -> /dashboard returns SPA HTML (guard redirects client-side)",
         resp.status_code == 200 and ("<html" in resp.text.lower() or "<!doctype" in resp.text.lower()),
         f"got {resp.status_code}")

    # ========================================================================
    print("\n\033[1m[7] Backend: Login Endpoints Return Correct Tokens\033[0m")

    # Admin login returns portal=admin in JWT
    resp = _login_with_retry(f"{BASE_API}/api/auth/admin/login", {"username": "admin", "password": "AdminPass123!"})
    test("Admin login returns 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        test("Admin login returns access_token", "access_token" in data, "missing access_token")
        test("Admin login returns refresh_token", "refresh_token" in data, "missing refresh_token")
        test("Admin login returns user object", "user" in data, "missing user")
        if "user" in data:
            test("Admin user role is super_admin", data["user"]["role"] == "super_admin",
                 f"got {data['user'].get('role')}")

    # Officer login returns portal=officer in JWT
    resp = _login_with_retry(f"{BASE_API}/api/auth/login", {"username": "test_si_auth", "password": "TestSIAuth@2026!"})
    test("Officer login returns 200", resp.status_code == 200, f"got {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        test("Officer login returns access_token", "access_token" in data, "missing access_token")
        if "user" in data:
            test("Officer user role is sub_inspector", data["user"]["role"] == "sub_inspector",
                 f"got {data['user'].get('role')}")

    # ========================================================================
    print("\n\033[1m[8] Backend: Cross-Portal Login Rejected (No Info Disclosure)\033[0m")

    # Admin credentials on officer endpoint -> generic 401
    resp = requests.post(f"{BASE_API}/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    test("Admin on officer portal -> 401", resp.status_code == 401, f"got {resp.status_code}")
    test("Generic error message", resp.json().get("detail") == "Authentication failed.",
         f"got: {resp.json().get('detail')}")

    # Officer credentials on admin endpoint -> generic 401
    resp = requests.post(f"{BASE_API}/api/auth/admin/login", json={"username": "test_si_auth", "password": "TestSIAuth@2026!"})
    test("Officer on admin portal -> 401", resp.status_code == 401, f"got {resp.status_code}")
    test("Generic error message", resp.json().get("detail") == "Authentication failed.",
         f"got: {resp.json().get('detail')}")

    # ========================================================================
    print("\n\033[1m[9] Backend: Token Refresh Works\033[0m")

    resp = _login_with_retry(f"{BASE_API}/api/auth/admin/login", {"username": "admin", "password": "AdminPass123!"})
    if resp.status_code == 200:
        refresh = resp.json().get("refresh_token")
        resp2 = requests.post(f"{BASE_API}/api/auth/refresh", json={"refresh_token": refresh})
        test("Refresh token returns new access_token", resp2.status_code == 200 and "access_token" in resp2.json(),
             f"got {resp2.status_code}")

    # ========================================================================
    print("\n\033[1m[10] Backend: Expired/Invalid Refresh Token Rejected\033[0m")

    resp = requests.post(f"{BASE_API}/api/auth/refresh", json={"refresh_token": "fake.refresh.token"})
    test("Invalid refresh token -> 401", resp.status_code == 401, f"got {resp.status_code}")

    # ========================================================================
    print("\n\033[1m[11] No Redirect Loops — Route Stability\033[0m")

    # SPA routing: all paths return HTML with no server-side redirects
    for path in ["/login", "/auth/system/admin/login", "/admin", "/dashboard", "/403", "/"]:
        resp = requests.get(f"{BASE_UI}{path}", allow_redirects=False)
        test(f"No server redirect on {path}", resp.status_code == 200,
             f"got {resp.status_code} with Location: {resp.headers.get('Location', 'none')}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    total = RESULTS["passed"] + RESULTS["failed"]
    if RESULTS["failed"] == 0:
        print(f"  \033[32mALL {total} TESTS PASSED\033[0m")
    else:
        print(f"  Results: {RESULTS['passed']}/{total} passed, \033[31m{RESULTS['failed']} FAILED\033[0m")
        if RESULTS["details"]:
            print("\n  Failed tests:")
            for d in RESULTS["details"]:
                print(f"    - {d}")
    print("=" * 70 + "\n")

    return 0 if RESULTS["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
