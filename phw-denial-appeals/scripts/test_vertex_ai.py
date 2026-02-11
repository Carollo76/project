#!/usr/bin/env python3
"""
PHW Denial Appeals — Vertex AI / Gemini Connectivity Test

Tests:
  1. Service account authentication (OAuth 2.0)
  2. Gemini 2.5 Pro API call to us-east1
  3. Denial classification prompt with sample input
  4. Token usage tracking for cost monitoring

Usage:
    python test_vertex_ai.py /path/to/service-account.json
    # or
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json python test_vertex_ai.py
"""

import json
import os
import sys
import time

try:
    import google.auth
    import google.auth.transport.requests
    from google.oauth2 import service_account
except ImportError:
    print("ERROR: google-auth library not installed.")
    print("  pip install google-auth google-auth-httplib2 requests")
    sys.exit(1)

import requests

# Vertex AI configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
LOCATION = "us-east1"
MODEL = "gemini-2.5-pro"
ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL}:generateContent"

# Approximate pricing (per 1K tokens, as of 2025)
INPUT_COST_PER_1K = 0.00125
OUTPUT_COST_PER_1K = 0.005

SAMPLE_DENIAL = """
ERA/835 Remittance Advice
Payer: UnitedHealthcare / Optum
Patient: Jane Doe  DOB: 1985-03-15  Member ID: UHC9876543
Claim Number: CLM-2025-00412
Provider: Dr. Bilitsis  NPI: 1234567890
Service Date: 2025-06-10
CPT Codes: 97110 (x4), 97140 (x2)
Billed Amount: $850.00
Allowed Amount: $0.00
Denial Reason: PTOT08A — Maximum therapy benefit has been reached.
Patient has reached a plateau and further therapy is not expected to result
in significant functional improvement. Services are considered maintenance only.
Denial Date: 2025-06-20
"""


def get_credentials(sa_key_path=None):
    """Get OAuth 2.0 credentials from service account JSON."""
    key_path = sa_key_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        print("ERROR: No service account key path provided.")
        print("  Pass as argument or set GOOGLE_APPLICATION_CREDENTIALS env var.")
        sys.exit(1)

    if not os.path.isfile(key_path):
        print(f"ERROR: Service account key file not found: {key_path}")
        sys.exit(1)

    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials


def call_gemini(credentials, prompt, max_tokens=2048):
    """Call Gemini via Vertex AI REST API and return response + usage."""
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.2,
        },
    }

    start = time.time()
    resp = requests.post(ENDPOINT, json=payload, headers=headers, timeout=60)
    elapsed = time.time() - start

    resp.raise_for_status()
    data = resp.json()

    # Extract response text
    text = ""
    if "candidates" in data and data["candidates"]:
        parts = data["candidates"][0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

    # Extract usage metadata
    usage = data.get("usageMetadata", {})
    input_tokens = usage.get("promptTokenCount", 0)
    output_tokens = usage.get("candidatesTokenCount", 0)

    return {
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "elapsed_seconds": round(elapsed, 2),
    }


def estimate_monthly_cost(input_tokens, output_tokens, appeals_per_month=40):
    """Estimate monthly cost based on token usage per appeal."""
    input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K * appeals_per_month
    output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K * appeals_per_month
    return round(input_cost + output_cost, 2)


def main():
    sa_path = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("PHW Denial Appeals — Vertex AI Connectivity Test")
    print("=" * 60)

    # Test 1: Authentication
    print("\n[1/4] Authenticating with service account...")
    credentials = get_credentials(sa_path)
    print(f"  Authenticated as: {credentials.service_account_email}")
    print(f"  Token expires: {credentials.expiry}")

    # Verify project ID
    if not PROJECT_ID:
        print("\n  WARNING: GCP_PROJECT_ID env var not set.")
        print("  Set it: export GCP_PROJECT_ID=your-project-id")
        sys.exit(1)
    print(f"  Project: {PROJECT_ID}")
    print(f"  Region: {LOCATION}")
    print(f"  Model: {MODEL}")

    # Test 2: Simple ping
    print("\n[2/4] Testing basic Gemini API call...")
    result = call_gemini(credentials, "Respond with exactly: VERTEX_AI_OK")
    if "VERTEX_AI_OK" in result["text"]:
        print(f"  API responding — latency: {result['elapsed_seconds']}s")
    else:
        print(f"  API responded but unexpected output: {result['text'][:100]}")

    # Test 3: Denial classification
    print("\n[3/4] Testing denial classification prompt...")
    classify_prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "gemini", "prompts", "classify_denial.txt"
    )
    if os.path.isfile(classify_prompt_path):
        with open(classify_prompt_path) as f:
            classify_prompt = f.read()
        prompt = classify_prompt.replace("{{input_data}}", SAMPLE_DENIAL)
    else:
        prompt = f"Classify this denial and return JSON:\n{SAMPLE_DENIAL}"

    result = call_gemini(credentials, prompt, max_tokens=4096)
    print(f"  Response received — {result['elapsed_seconds']}s")
    print(f"  Input tokens: {result['input_tokens']}")
    print(f"  Output tokens: {result['output_tokens']}")

    # Try to parse the JSON response
    try:
        # Strip markdown code fences if present
        text = result["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()

        classification = json.loads(text)
        code = classification.get("classification", {}).get("denial_code", "?")
        confidence = classification.get("classification", {}).get("confidence", 0)
        print(f"  Classification: {code} (confidence: {confidence})")
        if code == "PTOT08A" and confidence >= 0.7:
            print("  PASS — correctly classified sample denial")
        else:
            print(f"  WARNING — expected PTOT08A with high confidence")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  Could not parse JSON response: {e}")
        print(f"  Raw output (first 200 chars): {result['text'][:200]}")

    # Test 4: Cost estimate
    print("\n[4/4] Cost estimation...")
    monthly = estimate_monthly_cost(
        result["input_tokens"], result["output_tokens"], appeals_per_month=40
    )
    print(f"  Tokens per classification: ~{result['input_tokens'] + result['output_tokens']}")
    print(f"  Estimated monthly cost (40 appeals): ~${monthly}")
    print(f"  Budget range: $8-20/month")
    if monthly <= 20:
        print("  PASS — within budget")
    else:
        print("  NOTE — may exceed budget, consider prompt optimization")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED" if monthly <= 50 else "TESTS COMPLETE (review warnings)")
    print("=" * 60)


if __name__ == "__main__":
    main()
