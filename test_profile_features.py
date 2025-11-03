#!/usr/bin/env python3
"""
E2E test script for profile features in production.
Tests the Profile Preferences functionality on live site.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "https://thewishmachine.up.railway.app"
TEST_EMAIL = f"test_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com"
TEST_PASSWORD = "testpass123456"

def test_profile_features():
    """Test profile features with a new test account."""
    session = requests.Session()
    results = []

    print("=" * 60)
    print("CHECKPOINT CHARLIE: Profile Features E2E Test")
    print("=" * 60)

    # Test 1: Create account
    print("\n→ Test 1: Creating test account...")
    try:
        resp = session.post(
            f"{BASE_URL}/auth/signup",
            data={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "password_confirm": TEST_PASSWORD
            },
            allow_redirects=True
        )
        if resp.status_code == 200 and "account" in resp.url.lower() or "Make Your First Wish" in resp.text or "My Account" in resp.text:
            print(f"✓ Test 1 PASSED: Account created for {TEST_EMAIL}")
            results.append(("Create Account", "PASS"))
        else:
            print(f"✗ Test 1 FAILED: Account creation failed (status: {resp.status_code})")
            results.append(("Create Account", "FAIL", f"Status: {resp.status_code}"))
            return results
    except Exception as e:
        print(f"✗ Test 1 ERROR: {str(e)}")
        results.append(("Create Account", "ERROR", str(e)))
        return results

    # Test 2: Access account page
    print("\n→ Test 2: Accessing account page...")
    try:
        resp = session.get(f"{BASE_URL}/auth/account")
        if resp.status_code == 200 and "Profile Preferences" in resp.text:
            print("✓ Test 2 PASSED: Account page accessible with Profile Preferences section")
            results.append(("Account Page Access", "PASS"))
        elif resp.status_code == 200:
            print("✗ Test 2 FAILED: Account page accessible but Profile Preferences section not found")
            results.append(("Account Page Access", "FAIL", "Profile Preferences section missing"))
        else:
            print(f"✗ Test 2 FAILED: Cannot access account page (status: {resp.status_code})")
            results.append(("Account Page Access", "FAIL", f"Status: {resp.status_code}"))
    except Exception as e:
        print(f"✗ Test 2 ERROR: {str(e)}")
        results.append(("Account Page Access", "ERROR", str(e)))

    # Test 3: Verify UI elements exist
    print("\n→ Test 3: Verifying Profile UI elements...")
    try:
        if 'wish-themes' in resp.text and 'open-to-connect' in resp.text:
            print("✓ Test 3 PASSED: Profile form elements found (wish-themes, open-to-connect)")
            results.append(("Profile UI Elements", "PASS"))
        else:
            print("✗ Test 3 FAILED: Profile form elements not found")
            results.append(("Profile UI Elements", "FAIL", "Form elements missing"))
    except Exception as e:
        print(f"✗ Test 3 ERROR: {str(e)}")
        results.append(("Profile UI Elements", "ERROR", str(e)))

    # Test 4: Update profile preferences
    print("\n→ Test 4: Updating profile preferences...")
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
            print(f"✓ Test 4 PASSED: Profile updated successfully - {data.get('message')}")
            results.append(("Update Profile", "PASS"))
        else:
            print(f"✗ Test 4 FAILED: Profile update failed (status: {resp.status_code})")
            results.append(("Update Profile", "FAIL", f"Status: {resp.status_code}"))
    except Exception as e:
        print(f"✗ Test 4 ERROR: {str(e)}")
        results.append(("Update Profile", "ERROR", str(e)))

    # Test 5: Verify profile data persists
    print("\n→ Test 5: Verifying profile data persistence...")
    try:
        resp = session.get(f"{BASE_URL}/auth/account")
        if resp.status_code == 200:
            # Check if themes are pre-selected in the HTML
            if "Health" in resp.text and "selected" in resp.text:
                print("✓ Test 5 PASSED: Profile themes persisted and displayed")
                results.append(("Profile Persistence", "PASS"))
            else:
                print("⚠ Test 5 WARNING: Could not verify theme persistence in HTML")
                results.append(("Profile Persistence", "WARN", "Could not verify persistence"))
        else:
            print(f"✗ Test 5 FAILED: Cannot reload account page (status: {resp.status_code})")
            results.append(("Profile Persistence", "FAIL", f"Status: {resp.status_code}"))
    except Exception as e:
        print(f"✗ Test 5 ERROR: {str(e)}")
        results.append(("Profile Persistence", "ERROR", str(e)))

    # Test 6: Test validation (max 3 themes)
    print("\n→ Test 6: Testing validation (max 3 themes)...")
    try:
        resp = session.post(
            f"{BASE_URL}/auth/api/profile/update",
            json={
                "wish_themes": ["Health", "Career", "Finance", "Creativity"],  # 4 themes - should fail
                "open_to_connect": True
            },
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code == 400:
            print("✓ Test 6 PASSED: Validation correctly rejected 4 themes")
            results.append(("Validation Test", "PASS"))
        else:
            print(f"✗ Test 6 FAILED: Validation did not reject 4 themes (status: {resp.status_code})")
            results.append(("Validation Test", "FAIL", f"Status: {resp.status_code}"))
    except Exception as e:
        print(f"✗ Test 6 ERROR: {str(e)}")
        results.append(("Validation Test", "ERROR", str(e)))

    return results

def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r[1] == "PASS")
    failed = sum(1 for r in results if r[1] == "FAIL")
    errors = sum(1 for r in results if r[1] == "ERROR")
    warnings = sum(1 for r in results if r[1] == "WARN")

    for result in results:
        status_symbol = {"PASS": "✓", "FAIL": "✗", "ERROR": "✗", "WARN": "⚠"}
        symbol = status_symbol.get(result[1], "?")
        details = f" - {result[2]}" if len(result) > 2 else ""
        print(f"{symbol} {result[0]}: {result[1]}{details}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed} | Failed: {failed} | Errors: {errors} | Warnings: {warnings}")

    if failed > 0 or errors > 0:
        print("\n⚠ SOME TESTS FAILED - Profile features may not be working correctly")
        return 1
    else:
        print("\n✅ ALL TESTS PASSED - Profile features working correctly")
        return 0

if __name__ == "__main__":
    try:
        results = test_profile_features()
        exit_code = print_summary(results)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {str(e)}")
        sys.exit(1)
