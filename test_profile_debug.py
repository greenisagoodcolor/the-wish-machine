#!/usr/bin/env python3
"""Debug the profile update endpoint."""

import requests
import json
import re
from datetime import datetime

BASE_URL = "https://thewishmachine.up.railway.app"

def extract_csrf_token(html):
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return match.group(1) if match else None

session = requests.Session()

# Create account
print("Creating test account...")
test_email = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com"
resp = session.get(f"{BASE_URL}/auth/signup")
csrf = extract_csrf_token(resp.text)

resp = session.post(
    f"{BASE_URL}/auth/signup",
    data={
        "email": test_email,
        "password": "testpass123456",
        "password_confirm": "testpass123456",
        "csrf_token": csrf
    },
    allow_redirects=True
)
print(f"Account created: {resp.status_code}")

# Try to update profile with detailed debugging
print("\n" + "=" * 60)
print("Testing profile update with 3 themes...")
print("=" * 60)

test_data = {
    "wish_themes": ["Health", "Career", "Finance"],
    "open_to_connect": True
}

print(f"\nSending data: {json.dumps(test_data, indent=2)}")

resp = session.post(
    f"{BASE_URL}/auth/api/profile/update",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"\nResponse status: {resp.status_code}")
print(f"Response headers: {dict(resp.headers)}")
print(f"Response body: {resp.text}")

try:
    print(f"Response JSON: {json.dumps(resp.json(), indent=2)}")
except:
    print("Could not parse response as JSON")

# Try with empty themes
print("\n" + "=" * 60)
print("Testing with empty themes array...")
resp2 = session.post(
    f"{BASE_URL}/auth/api/profile/update",
    json={"wish_themes": [], "open_to_connect": False},
    headers={"Content-Type": "application/json"}
)
print(f"Status: {resp2.status_code}")
print(f"Response: {resp2.text}")

# Try with just 1 theme
print("\n" + "=" * 60)
print("Testing with 1 theme...")
resp3 = session.post(
    f"{BASE_URL}/auth/api/profile/update",
    json={"wish_themes": ["Health"], "open_to_connect": False},
    headers={"Content-Type": "application/json"}
)
print(f"Status: {resp3.status_code}")
print(f"Response: {resp3.text}")
