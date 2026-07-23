"""
End-to-end tests for the self-registration authentication workflow.
Run against a live Docker environment: docker compose up -d --build
"""
import time
import requests

BASE_URL = "http://localhost:8000"
ADMIN_USER = "admin"
ADMIN_PASS = "AdminPass123!"


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def record(self, name: str, passed: bool, detail: str = ""):
        self.results.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            self.passed += 1
            print(f"  PASS: {name}")
        else:
            self.failed += 1
            print(f"  FAIL: {name} - {detail}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"RESULTS: {self.passed}/{total} passed, {self.failed} failed")
        print(f"{'='*60}")
        if self.failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - {r['name']}: {r['detail']}")


def get_admin_token() -> str:
    resp = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "username": ADMIN_USER, "password": ADMIN_PASS
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["access_token"]


def run_tests():
    results = TestResults()
    print("=" * 60)
    print("CrimeGPT Authentication Registration E2E Tests")
    print("=" * 60)

    # Wait for server to be ready
    for _ in range(10):
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=2)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(2)

    # ============ REGISTRATION TESTS ============
    print("\n--- Registration Tests ---")

    # Test 1: Successful registration
    reg_data = {
        "full_name": "Test Officer",
        "email": "test.officer@police.gov.in",
        "username": "test_officer_reg",
        "password": "TestPass@123!",
        "confirm_password": "TestPass@123!",
        "badge_number": "TEST-001",
        "role": "inspector",
        "station_id": "Test Station",
        "department": "Testing Department",
        "mobile_number": "+919876543210",
    }
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=reg_data)
    results.record("Register new officer", resp.status_code == 201, f"Status: {resp.status_code}, Body: {resp.text[:200]}")

    registered_user_id = None
    if resp.status_code == 201:
        registered_user_id = resp.json().get("user_id")

    # Test 2: Duplicate username
    dup_data = {**reg_data, "email": "other@test.com", "badge_number": "TEST-002"}
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=dup_data)
    results.record("Duplicate username rejected", resp.status_code == 409 and "Username" in resp.json().get("detail", ""), f"Status: {resp.status_code}")

    # Test 3: Duplicate email
    dup_data = {**reg_data, "username": "other_user", "badge_number": "TEST-003"}
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=dup_data)
    results.record("Duplicate email rejected", resp.status_code == 409 and "Email" in resp.json().get("detail", ""), f"Status: {resp.status_code}")

    # Test 4: Duplicate badge number
    dup_data = {**reg_data, "username": "other_user2", "email": "other2@test.com"}
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=dup_data)
    results.record("Duplicate badge ID rejected", resp.status_code == 409 and "Badge" in resp.json().get("detail", ""), f"Status: {resp.status_code}")

    # Test 5: Admin role self-registration blocked
    admin_reg = {**reg_data, "username": "bad_admin", "email": "bad@test.com", "badge_number": "BAD-001", "role": "super_admin"}
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=admin_reg)
    results.record("Admin role self-registration blocked", resp.status_code == 422, f"Status: {resp.status_code}")

    # Test 6: Weak password rejected
    weak_data = {**reg_data, "username": "weak_user", "email": "weak@test.com", "badge_number": "WEAK-001", "password": "weak", "confirm_password": "weak"}
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=weak_data)
    results.record("Weak password rejected", resp.status_code == 422, f"Status: {resp.status_code}")

    # ============ LOGIN BEFORE VERIFICATION ============
    print("\n--- Login Before Verification ---")

    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "test_officer_reg", "password": "TestPass@123!"
    })
    results.record("Login before email verification blocked",
                   resp.status_code == 403 and "verify" in resp.json().get("detail", "").lower(),
                   f"Status: {resp.status_code}, Detail: {resp.json().get('detail', '')}")

    # ============ ADMIN APPROVAL ============
    print("\n--- Admin Approval Tests ---")

    admin_token = get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Test: Admin can list registrations
    resp = requests.get(f"{BASE_URL}/api/admin/registrations", headers=headers, params={"status": "pending"})
    results.record("Admin can list pending registrations", resp.status_code == 200, f"Status: {resp.status_code}")

    # Test: Admin can view stats
    resp = requests.get(f"{BASE_URL}/api/admin/registrations/stats", headers=headers)
    results.record("Admin can view registration stats", resp.status_code == 200 and "pending" in resp.json(), f"Status: {resp.status_code}")

    if registered_user_id:
        # Simulate email verification by directly updating (since we're in console mode)
        # We'll verify the email via the verify endpoint by reading the token from DB
        # For this test, we'll approve without email verification to test the flow
        # In production, the user would click the link

        # Test: Approve user
        resp = requests.post(f"{BASE_URL}/api/admin/registrations/{registered_user_id}/action",
                             headers=headers, json={"action": "approve"})
        results.record("Admin can approve registration",
                       resp.status_code == 200,
                       f"Status: {resp.status_code}, Body: {resp.text[:200]}")

    # ============ EXISTING ADMIN LOGIN (backward compat) ============
    print("\n--- Backward Compatibility ---")

    resp = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
        "username": ADMIN_USER, "password": ADMIN_PASS
    })
    results.record("Existing admin login still works", resp.status_code == 200, f"Status: {resp.status_code}")

    # ============ FORGOT PASSWORD ============
    print("\n--- Forgot Password ---")

    resp = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": "admin@crimegpt.system"})
    results.record("Forgot password returns success for existing email", resp.status_code == 200, f"Status: {resp.status_code}")

    resp = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": "nonexistent@test.com"})
    results.record("Forgot password returns success for non-existent email (no enumeration)",
                   resp.status_code == 200, f"Status: {resp.status_code}")

    # ============ RESET PASSWORD (invalid token) ============
    print("\n--- Reset Password ---")

    resp = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
        "token": "invalid_token_xyz",
        "new_password": "NewSecure@Pass1!"
    })
    results.record("Reset with invalid token rejected", resp.status_code == 400, f"Status: {resp.status_code}")

    # ============ VERIFY EMAIL (invalid token) ============
    print("\n--- Email Verification ---")

    resp = requests.post(f"{BASE_URL}/api/auth/verify-email", json={"token": "invalid_token_xyz"})
    results.record("Verify with invalid token rejected", resp.status_code == 400, f"Status: {resp.status_code}")

    # ============ JWT SESSION INVALIDATION ============
    print("\n--- Session Invalidation ---")

    # Get a token, change password, try using old token
    admin_token_2 = get_admin_token()
    headers2 = {"Authorization": f"Bearer {admin_token_2}"}
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers2)
    results.record("Token valid before password change", resp.status_code == 200, f"Status: {resp.status_code}")

    # Change admin password
    resp = requests.post(f"{BASE_URL}/api/auth/change-password", headers=headers2, json={
        "current_password": ADMIN_PASS,
        "new_password": "NewAdmin@Pass123!",
    })
    password_changed = resp.status_code == 200
    results.record("Admin password change succeeds", password_changed, f"Status: {resp.status_code}")

    if password_changed:
        # Old token should now be invalid
        time.sleep(1)
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers2)
        results.record("Old token invalidated after password change", resp.status_code == 401, f"Status: {resp.status_code}")

        # Login with new password works
        resp = requests.post(f"{BASE_URL}/api/auth/admin/login", json={
            "username": ADMIN_USER, "password": "NewAdmin@Pass123!"
        })
        results.record("Login with new password works", resp.status_code == 200, f"Status: {resp.status_code}")

        # Revert password back
        new_token = resp.json()["access_token"] if resp.status_code == 200 else None
        if new_token:
            requests.post(f"{BASE_URL}/api/auth/change-password",
                          headers={"Authorization": f"Bearer {new_token}"},
                          json={"current_password": "NewAdmin@Pass123!", "new_password": ADMIN_PASS})

    # ============ CLEANUP ============
    print("\n--- Cleanup ---")
    # Delete test user
    if registered_user_id:
        admin_token_final = get_admin_token()
        resp = requests.delete(f"{BASE_URL}/api/admin/users/{registered_user_id}",
                               headers={"Authorization": f"Bearer {admin_token_final}"})
        results.record("Test user cleanup", resp.status_code == 200, f"Status: {resp.status_code}")

    results.summary()


if __name__ == "__main__":
    run_tests()
