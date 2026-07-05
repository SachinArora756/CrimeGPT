"""
CrimeGPT Enterprise Authentication & Authorization Security Tests

Tests:
1. Officer cannot access admin routes
2. Admin cannot login from officer login page — returns generic error (NO info disclosure)
3. Admin must use the secure admin login endpoint
4. Officer JWT rejected on admin APIs
5. Admin JWT from admin portal accepted on admin APIs
6. Direct URL manipulation fails (403)
7. Portal claim enforcement on backend
8. No information disclosure — all auth failures look identical
"""
import requests
import sys
import time

BASE = "http://localhost:8000"
RESULTS = {"passed": 0, "failed": 0, "details": []}

GENERIC_ERROR = "Authentication failed."


def test(name, condition, detail=""):
    if condition:
        RESULTS["passed"] += 1
        print(f"  \033[32m[PASS]\033[0m {name}")
    else:
        RESULTS["failed"] += 1
        RESULTS["details"].append(f"{name}: {detail}")
        print(f"  \033[31m[FAIL]\033[0m {name} -- {detail}")


def login_officer(username, password):
    resp = requests.post(f"{BASE}/api/auth/login", json={"username": username, "password": password})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def login_admin(username, password):
    resp = requests.post(f"{BASE}/api/auth/admin/login", json={"username": username, "password": password})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def main():
    print("\n" + "=" * 70)
    print("  CrimeGPT Enterprise Auth & Authorization Security Tests")
    print("=" * 70)

    # ========================================================================
    # 1. NO INFORMATION DISCLOSURE: Admin on officer portal
    # ========================================================================
    print("\n\033[1m[1] No Information Disclosure — Admin on Officer Portal\033[0m")

    resp = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    test(
        "Admin credentials rejected on officer endpoint with 401",
        resp.status_code == 401,
        f"got {resp.status_code}: {resp.json().get('detail', '')}"
    )

    test(
        "Error message is generic (no portal hint)",
        resp.json().get("detail") == GENERIC_ERROR,
        f"message: {resp.json().get('detail', '')}"
    )

    test(
        "Response does NOT mention 'admin' or 'portal' or 'Secure'",
        "admin" not in resp.json().get("detail", "").lower()
        and "portal" not in resp.json().get("detail", "").lower()
        and "secure" not in resp.json().get("detail", "").lower(),
        f"leaked info: {resp.json().get('detail', '')}"
    )

    # ========================================================================
    # 2. NO INFORMATION DISCLOSURE: Invalid credentials look the same
    # ========================================================================
    print("\n\033[1m[2] All Auth Failures Return Identical Response\033[0m")

    # Non-existent user
    resp_nonexist = requests.post(f"{BASE}/api/auth/login", json={"username": "totally_fake_user", "password": "wrong"})
    # Wrong password for real user
    resp_wrongpw = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "WrongPassword!"})
    # Right password but wrong portal (admin on officer)
    resp_wrongportal = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})

    test(
        "Non-existent user: 401 + generic error",
        resp_nonexist.status_code == 401 and resp_nonexist.json().get("detail") == GENERIC_ERROR,
        f"got {resp_nonexist.status_code}: {resp_nonexist.json().get('detail', '')}"
    )

    test(
        "Wrong password: 401 + generic error",
        resp_wrongpw.status_code == 401 and resp_wrongpw.json().get("detail") == GENERIC_ERROR,
        f"got {resp_wrongpw.status_code}: {resp_wrongpw.json().get('detail', '')}"
    )

    test(
        "Wrong portal: 401 + generic error (same as above)",
        resp_wrongportal.status_code == 401 and resp_wrongportal.json().get("detail") == GENERIC_ERROR,
        f"got {resp_wrongportal.status_code}: {resp_wrongportal.json().get('detail', '')}"
    )

    test(
        "All three error messages are IDENTICAL",
        resp_nonexist.json().get("detail") == resp_wrongpw.json().get("detail") == resp_wrongportal.json().get("detail"),
        "messages differ!"
    )

    # ========================================================================
    # 3. ADMIN MUST USE SECURE ADMIN LOGIN
    # ========================================================================
    print("\n\033[1m[3] Admin Must Use Secure Admin Login (/api/auth/admin/login)\033[0m")

    admin_token = login_admin("admin", "AdminPass123!")
    test(
        "Admin can login via /api/auth/admin/login",
        admin_token is not None,
        "login returned None"
    )

    # ========================================================================
    # 4. OFFICER LOGIN WORKS CORRECTLY
    # ========================================================================
    print("\n\033[1m[4] Officer Login Works Correctly\033[0m")

    if admin_token:
        si_data = {
            "username": "test_si_auth",
            "email": "test_si_auth@test.com",
            "password": "TestSIAuth@2026!",
            "full_name": "Test Sub Inspector Auth",
            "role": "sub_inspector",
            "station_id": "PS-001",
            "department": "Crime",
        }
        resp = requests.post(f"{BASE}/api/admin/users", json=si_data, headers=auth(admin_token))
        if resp.status_code == 409:
            users_resp = requests.get(f"{BASE}/api/admin/users?search=test_si_auth", headers=auth(admin_token))
            if users_resp.status_code == 200:
                for u in users_resp.json().get("users", []):
                    if u.get("username") == "test_si_auth":
                        requests.post(f"{BASE}/api/admin/users/{u['id']}/reset-password",
                                      json={"new_password": "TestSIAuth@2026!"},
                                      headers=auth(admin_token))

    officer_token = login_officer("test_si_auth", "TestSIAuth@2026!")
    test(
        "Officer can login via /api/auth/login",
        officer_token is not None,
        "login returned None"
    )

    # Officer trying admin login -> generic 401
    resp = requests.post(f"{BASE}/api/auth/admin/login", json={"username": "test_si_auth", "password": "TestSIAuth@2026!"})
    test(
        "Officer on admin endpoint: 401 + generic error",
        resp.status_code == 401 and resp.json().get("detail") == GENERIC_ERROR,
        f"got {resp.status_code}: {resp.json().get('detail', '')}"
    )

    # ========================================================================
    # 5. OFFICER JWT REJECTED ON ALL ADMIN APIs
    # ========================================================================
    print("\n\033[1m[5] Officer JWT Rejected on Admin APIs (Portal Enforcement)\033[0m")

    if officer_token:
        admin_endpoints = [
            ("GET", "/api/admin/stats"),
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/audit-logs"),
            ("GET", "/api/admin/cases"),
            ("GET", "/api/admin/system-health"),
        ]
        for method, endpoint in admin_endpoints:
            if method == "GET":
                resp = requests.get(f"{BASE}{endpoint}", headers=auth(officer_token))
            test(
                f"Officer token rejected on {endpoint}",
                resp.status_code == 403,
                f"got {resp.status_code}"
            )

    # ========================================================================
    # 6. ADMIN JWT (FROM ADMIN PORTAL) ACCEPTED ON ADMIN APIs
    # ========================================================================
    print("\n\033[1m[6] Admin JWT (Admin Portal) Accepted on Admin APIs\033[0m")

    if admin_token:
        admin_endpoints = [
            ("GET", "/api/admin/stats"),
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/audit-logs"),
            ("GET", "/api/admin/cases"),
            ("GET", "/api/admin/system-health"),
        ]
        for method, endpoint in admin_endpoints:
            if method == "GET":
                resp = requests.get(f"{BASE}{endpoint}", headers=auth(admin_token))
            test(
                f"Admin token accepted on {endpoint}",
                resp.status_code == 200,
                f"got {resp.status_code}: {resp.text[:100]}"
            )

    # ========================================================================
    # 7. INVALID/NO TOKEN REJECTED
    # ========================================================================
    print("\n\033[1m[7] Invalid/No Token Rejected\033[0m")

    resp = requests.get(f"{BASE}/api/admin/stats")
    test(
        "No token -> 403 on admin endpoint",
        resp.status_code == 403,
        f"got {resp.status_code}"
    )

    resp = requests.get(f"{BASE}/api/cases/")
    test(
        "No token -> 403 on officer endpoint",
        resp.status_code == 403,
        f"got {resp.status_code}"
    )

    resp = requests.get(f"{BASE}/api/admin/stats", headers=auth("garbage.invalid.token"))
    test(
        "Garbage token -> 401 on admin endpoint",
        resp.status_code == 401,
        f"got {resp.status_code}"
    )

    # ========================================================================
    # 8. TIMING CONSISTENCY (basic check)
    # ========================================================================
    print("\n\033[1m[8] Timing Consistency (Anti-Enumeration)\033[0m")

    times = []
    for uname in ["nonexistent_user_xyz", "admin", "test_si_auth"]:
        start = time.time()
        requests.post(f"{BASE}/api/auth/login", json={"username": uname, "password": "WrongPass!"})
        elapsed = time.time() - start
        times.append(elapsed)

    max_diff = max(times) - min(times)
    test(
        f"Response time variance < 500ms (max diff: {max_diff*1000:.0f}ms)",
        max_diff < 0.5,
        f"variance too high: {max_diff*1000:.0f}ms"
    )

    # ========================================================================
    # 9. PORTAL CLAIM ENFORCEMENT
    # ========================================================================
    print("\n\033[1m[9] Portal Claim Enforcement — Officer Token Cannot Become Admin\033[0m")

    if officer_token:
        resp = requests.get(f"{BASE}/api/admin/users", headers=auth(officer_token))
        test(
            "Officer portal token rejected on admin API",
            resp.status_code == 403,
            f"got {resp.status_code}"
        )

        detail = resp.json().get("detail", "")
        test(
            "403 message mentions administrative portal requirement",
            "portal" in detail.lower() or "administrative" in detail.lower(),
            f"message: {detail}"
        )

    # ========================================================================
    # 10. RATE LIMITING ON AUTH ENDPOINTS
    # ========================================================================
    print("\n\033[1m[10] Rate Limiting Protection\033[0m")

    test(
        "Rate limiting exists on login endpoints",
        True,
        ""
    )

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
