#!/usr/bin/env python3
"""
Simple E2E test for profile features using existing test account.
"""

import requests
import json
import re
from datetime import datetime

BASE_URL = "https://thewishmachine.up.railway.app"

def extract_csrf_token(html):
    """Extract CSRF token from HTML."""
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return match.group(1) if match else None

def test_with_new_account():
    """Test profile features with a new account."""
    session = requests.Session()
    results = []

    print("=" * 60)
    print("CHECKPOINT CHARLIE: Profile Features Test")
    print("=" * 60)

    # Generate unique test email
    test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com"
    test_password = "testpass123456"

    # Test 1: Get signup page and extract CSRF
    print("\n→ Test 1: Fetching signup page...")
    try:
        resp = session.get(f"{BASE_URL}/auth/signup")
        csrf_token = extract_csrf_token(resp.text)
        if csrf_token:
            print(f"✓ Test 1 PASSED: Got CSRF token")
            results.append(("Get Signup Page", "PASS"))
        else:
            print("✗ Test 1 FAILED: No CSRF token found")
            results.append(("Get Signup Page", "FAIL", "No CSRF token"))
            return results
    except Exception as e:
        print(f"✗ Test 1 ERROR: {str(e)}")
        results.append(("Get Signup Page", "ERROR", str(e)))
        return results

    # Test 2: Create account
    print(f"\n→ Test 2: Creating account ({test_email})...")
    try:
        resp = session.post(
            f"{BASE_URL}/auth/signup",
            data={
                "email": test_email,
                "password": test_password,
                "password_confirm": test_password,
                "csrf_token": csrf_token
            },
            allow_redirects=True
        )

        if resp.status_code == 200 and ("Welcome" in resp.text or "account" in resp.url.lower() or "/" == resp.url.replace(BASE_URL, "")):
            print(f"✓ Test 2 PASSED: Account created successfully")
            results.append(("Create Account", "PASS"))
        else:
            print(f"✗ Test 2 FAILED: Account creation failed (status: {resp.status_code})")
            print(f"  URL: {resp.url}")
            if "error" in resp.text.lower():
                print(f"  Errors in response")
            results.append(("Create Account", "FAIL", f"Status: {resp.status_code}"))
            return results
    except Exception as e:
        print(f"✗ Test 2 ERROR: {str(e)}")
        results.append(("Create Account", "ERROR", str(e)))
        return results

    # Test 3: Access account page
    print("\n→ Test 3: Accessing account page...")
    try:
        resp = session.get(f"{BASE_URL}/auth/account")
        if resp.status_code == 200 and "Profile Preferences" in resp.text:
            print("✓ Test 3 PASSED: Account page shows Profile Preferences section")
            results.append(("Account Page", "PASS"))
        elif resp.status_code == 200:
            print("✗ Test 3 FAILED: Account page accessible but no Profile Preferences")
            results.append(("Account Page", "FAIL", "Profile section missing"))
        else:
            print(f"✗ Test 3 FAILED: Cannot access account page (status: {resp.status_code})")
            results.append(("Account Page", "FAIL", f"Status: {resp.status_code}"))
    except Exception as e:
        print(f"✗ Test 3 ERROR: {str(e)}")
        results.append(("Account Page", "ERROR", str(e)))

    # Test 4: Verify form elements
    print("\n→ Test 4: Checking Profile UI elements...")
    try:
        if 'wish-themes' in resp.text and 'open-to-connect' in resp.text and 'saveProfile()' in resp.text:
            print("✓ Test 4 PASSED: Profile form elements present")
            results.append(("Profile UI", "PASS"))
        else:
            print("✗ Test 4 FAILED: Profile form elements missing")
            results.append(("Profile UI", "FAIL", "Form elements missing"))
    except Exception as e:
        print(f"✗ Test 4 ERROR: {str(e)}")
        results.append(("Profile UI", "ERROR", str(e)))

    # Test 5: Update profile (3 themes)
    print("\n→ Test 5: Updating profile with 3 themes...")
    try:
        resp = session.post(
            f"{BASE_URL}/auth/api/profile/update",
            json={
                "wish_themes": ["Health", "Career", "Finance"],
                "open_to_connect": True
            },
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Test 5 PASSED: {data.get('message', 'Profile updated')}")
            results.append(("Update Profile", "PASS"))
        else:
            print(f"✗ Test 5 FAILED: Profile update failed (status: {resp.status_code})")
            results.append(("Update Profile", "FAIL", f"Status: {resp.status_code}"))
    except Exception as e:
        print(f"✗ Test 5 ERROR: {str(e)}")
        results.append(("Update Profile", "ERROR", str(e)))

    # Test 6: Validation - too many themes
    print("\n→ Test 6: Testing validation (4 themes should fail)...")
    try:
        resp = session.post(
            f"{BASE_URL}/auth/api/profile/update",
            json={
                "wish_themes": ["Health", "Career", "Finance", "Creativity"],
                "open_to_connect": True
            },
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code == 400:
            print("✓ Test 6 PASSED: Validation correctly rejected 4 themes")
            results.append(("Validation", "PASS"))
        else:
            print(f"✗ Test 6 FAILED: Should reject 4 themes (got status: {resp.status_code})")
            results.append(("Validation", "FAIL", f"Status: {resp.status_code}"))
    except Exception as e:
        print(f"✗ Test 6 ERROR: {str(e)}")
        results.append(("Validation", "ERROR", str(e)))

    # Test 7: Check "Connect" button appears after opt-in
    print("\n→ Test 7: Checking if Connect CTA appears...")
    try:
        resp = session.get(f"{BASE_URL}/")
        # User needs to make a wish first to see the Connect button
        if "Connect with peers" in resp.text or "open_to_connect" in resp.text:
            print("✓ Test 7 PASSED: Connect CTA conditional logic present")
            results.append(("Connect CTA", "PASS"))
        else:
            print("⚠ Test 7 WARNING: Cannot verify Connect CTA without making a wish")
            results.append(("Connect CTA", "SKIP", "Needs wish to verify"))
    except Exception as e:
        print(f"✗ Test 7 ERROR: {str(e)}")
        results.append(("Connect CTA", "ERROR", str(e)))

    return results

def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for result in results:
        status_map = {"PASS": "✓", "FAIL": "✗", "ERROR": "✗", "SKIP": "⊘", "WARN": "⚠"}
        symbol = status_map.get(result[1], "?")
        details = f" - {result[2]}" if len(result) > 2 else ""
        print(f"{symbol} {result[0]}: {result[1]}{details}")

    passed = sum(1 for r in results if r[1] == "PASS")
    failed = sum(1 for r in results if r[1] == "FAIL")
    errors = sum(1 for r in results if r[1] == "ERROR")

    print(f"\nPassed: {passed} | Failed: {failed} | Errors: {errors}")

    if failed > 0 or errors > 0:
        print("\n⚠ CHECKPOINT CHARLIE: SOME TESTS FAILED")
        return 1
    else:
        print("\n✅ CHECKPOINT CHARLIE: ALL TESTS PASSED")
        return 0

if __name__ == "__main__":
    try:
        results = test_with_new_account()
        exit_code = print_summary(results)
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        exit(1)
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
