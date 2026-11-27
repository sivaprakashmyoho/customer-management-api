
import os
import hmac
import hashlib
import requests

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

URL = "http://127.0.0.1:8000/webhooks/customer-events"

payload = b'{"event": "customer.created", "customer_id": 1}'

# Generate valid signature
signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    payload,
    hashlib.sha256
).hexdigest()

headers = {
    "X-Signature": signature,
    "Content-Type": "application/json"
}

# Test 1: Valid signature
response = requests.post(
    URL,
    data=payload,
    headers=headers
)

print("Test 1 - Valid signature")
print("Status:", response.status_code)
print("Response:", response.json())


# Test 2: Tampered payload
tampered_payload = b'{"event": "customer.created", "customer_id": 999}'

response = requests.post(
    URL,
    data=tampered_payload,
    headers=headers
)

print("\nTest 2 - Tampered payload")
print("Status:", response.status_code)
print("Response:", response.json())


# Test 3: Missing signature
response = requests.post(
    URL,
    data=payload
)

print("\nTest 3 - Missing signature")
print("Status:", response.status_code)
print("Response:", response.json())
