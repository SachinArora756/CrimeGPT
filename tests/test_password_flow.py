"""
CrimeGPT End-to-End Password Change Flow Test

Tests the EXACT flow:
1. Admin resets officer password -> force_password_change = true
2. Officer logs in -> response has force_password_change = true
3. Officer changes password -> backend clears flag
4. Officer gets fresh token via refresh -> flag is now false
5. Officer /me endpoint returns force_password_change = false
6. Officer can access dashboard normally
"""
import requests
import sys
import time

BASE = "http://localhost:8000"
RESULTS = {"passed": 0, "failed": 0, "details": []}


def test(name, condition, detail=""):
    if condition:
        RESULTS["passed"] += 1
        print(f"  \033[32m[PASS]\033[0m {name}")
    else:
        RESULTS["failed"] += 1
        RESULTS["details"].append(f"{name}: {detail}")
        print(f"  \033[31m[FAIL]\033[0m {name} -- {detail}")


def login_with_retry(url, body, retries=3):
    for _ in range(retries):
        resp = requests.post(url, json=body)
        if resp.status_code == 429:
            time.sleep(15)
            continue
        return resp
    return resp


def main():
    print("\n" + "=" * 70)
    print("  CrimeGPT End-to-End Password Change Flow Test")
    print("=" * 70)

    OFFICER_USER = "test_si_auth"
    OFFICER_PASS_ORIGINAL = "TestSIAuth@2026!"
    OFFICER_PASS_NEW = "NewSecurePass@2026!"

    # ========================================================================
    # STEP 0: Ensure clean state — reset officer to known password with no flags
    # ========================================================================
    print("\n\033[1m[Step 0] Setup: Ensure clean state\033[0m")

    admin_resp = login_with_retry(f"{BASE}/api/auth/admin/login", {"username": "admin", "password": "AdminPass123!"})
    test("Admin login OK", admin_resp.status_code == 200, f"got {admin_resp.status_code}")
    if admin_resp.status_code != 200:
        print("  Cannot continue without admin token")
        return 1
    admin_token = admin_resp.json()["access_token"]

    # Find officer user ID
    users_resp = requests.get(f"{BASE}/api/admin/users?search={OFFICER_USER}",
                              headers={"Authorization": f"Bearer {admin_token}"})
    officer_id = None
    for u in users_resp.json().get("users", []):
        if u["username"] == OFFICER_USER:
            officer_id = u["id"]
            break
    test("Found officer user", officer_id is not None, "user not found")
    if not officer_id:
        return 1

    # Reset to known password WITHOUT force flag first
    reset_resp = requests.post(f"{BASE}/api/admin/users/{officer_id}/reset-password",
                               json={"new_password": OFFICER_PASS_ORIGINAL},
                               headers={"Authorization": f"Bearer {admin_token}"})
    test("Password reset successful", reset_resp.status_code == 200, f"got {reset_resp.status_code}")

    # ========================================================================
    # STEP 1: Verify force_password_change is TRUE after admin reset
    # ========================================================================
    print("\n\033[1m[Step 1] Verify force_password_change = true after reset\033[0m")

    officer_resp = login_with_retry(f"{BASE}/api/auth/login", {"username": OFFICER_USER, "password": OFFICER_PASS_ORIGINAL})
    test("Officer login succeeds", officer_resp.status_code == 200, f"got {officer_resp.status_code}")

    if officer_resp.status_code == 200:
        data = officer_resp.json()
        test("Response has force_password_change = true",
             data.get("force_password_change") == True,
             f"got force_password_change={data.get('force_password_change')}")
        test("User object also has force_password_change = true",
             data.get("user", {}).get("force_password_change") == True,
             f"got {data.get('user', {}).get('force_password_change')}")

        officer_token = data["access_token"]
        officer_refresh = data["refresh_token"]
    else:
        print("  Cannot continue without officer token")
        return 1

    # ========================================================================
    # STEP 2: Verify /me shows force_password_change = true
    # ========================================================================
    print("\n\033[1m[Step 2] /me endpoint reflects force_password_change = true\033[0m")

    me_resp = requests.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {officer_token}"})
    test("/me returns 200", me_resp.status_code == 200, f"got {me_resp.status_code}")
    if me_resp.status_code == 200:
        test("/me shows force_password_change = true",
             me_resp.json().get("force_password_change") == True,
             f"got {me_resp.json().get('force_password_change')}")

    # ========================================================================
    # STEP 3: Officer changes password
    # ========================================================================
    print("\n\033[1m[Step 3] Officer changes password\033[0m")

    change_resp = requests.post(f"{BASE}/api/auth/change-password",
                                json={"current_password": OFFICER_PASS_ORIGINAL, "new_password": OFFICER_PASS_NEW},
                                headers={"Authorization": f"Bearer {officer_token}"})
    test("Change password returns 200", change_resp.status_code == 200, f"got {change_resp.status_code}: {change_resp.text}")

    # ========================================================================
    # STEP 4: Verify force_password_change is now FALSE in database
    # ========================================================================
    print("\n\033[1m[Step 4] Verify flag cleared after password change\033[0m")

    me_resp = requests.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {officer_token}"})
    test("/me returns 200 after change", me_resp.status_code == 200, f"got {me_resp.status_code}")
    if me_resp.status_code == 200:
        test("/me shows force_password_change = false",
             me_resp.json().get("force_password_change") == False,
             f"got {me_resp.json().get('force_password_change')}")

    # ========================================================================
    # STEP 5: Token refresh returns force_password_change = false
    # ========================================================================
    print("\n\033[1m[Step 5] Token refresh returns updated flag\033[0m")

    refresh_resp = requests.post(f"{BASE}/api/auth/refresh", json={"refresh_token": officer_refresh})
    test("Refresh returns 200", refresh_resp.status_code == 200, f"got {refresh_resp.status_code}")
    if refresh_resp.status_code == 200:
        refresh_data = refresh_resp.json()
        test("Refresh response has force_password_change = false",
             refresh_data.get("force_password_change") == False,
             f"got {refresh_data.get('force_password_change')}")
        test("Refresh response user has force_password_change = false",
             refresh_data.get("user", {}).get("force_password_change") == False,
             f"got {refresh_data.get('user', {}).get('force_password_change')}")
        new_token = refresh_data["access_token"]
    else:
        new_token = officer_token

    # ========================================================================
    # STEP 6: Fresh login with new password also shows false
    # ========================================================================
    print("\n\033[1m[Step 6] Fresh login with new password\033[0m")

    fresh_resp = login_with_retry(f"{BASE}/api/auth/login", {"username": OFFICER_USER, "password": OFFICER_PASS_NEW})
    test("Fresh login with new password succeeds", fresh_resp.status_code == 200, f"got {fresh_resp.status_code}")
    if fresh_resp.status_code == 200:
        fresh_data = fresh_resp.json()
        test("Fresh login: force_password_change = false",
             fresh_data.get("force_password_change") == False,
             f"got {fresh_data.get('force_password_change')}")
        test("Fresh login: user.force_password_change = false",
             fresh_data.get("user", {}).get("force_password_change") == False,
             f"got {fresh_data.get('user', {}).get('force_password_change')}")
        fresh_token = fresh_data["access_token"]
    else:
        fresh_token = new_token

    # ========================================================================
    # STEP 7: Officer can access all protected endpoints
    # ========================================================================
    print("\n\033[1m[Step 7] Officer can access protected endpoints normally\033[0m")

    endpoints = [
        ("/api/dashboard/stats", "Dashboard stats"),
        ("/api/cases/", "Cases list"),
        ("/api/auth/me", "User profile"),
    ]
    for endpoint, label in endpoints:
        resp = requests.get(f"{BASE}{endpoint}", headers={"Authorization": f"Bearer {fresh_token}"})
        test(f"{label} accessible ({endpoint})", resp.status_code == 200, f"got {resp.status_code}")

    # ========================================================================
    # STEP 8: Clean up — reset password back to original (without force flag)
    # ========================================================================
    print("\n\033[1m[Step 8] Cleanup: Change back to original password\033[0m")

    change_back = requests.post(f"{BASE}/api/auth/change-password",
                                json={"current_password": OFFICER_PASS_NEW, "new_password": OFFICER_PASS_ORIGINAL},
                                headers={"Authorization": f"Bearer {fresh_token}"})
    test("Reverted password back to original", change_back.status_code == 200, f"got {change_back.status_code}")

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
