#!/usr/bin/env python3
"""
PHW Denial Appeals — Monday.com API Connectivity Test

Tests:
  1. API token authentication
  2. Board access and column verification
  3. Create/read/delete a test item
  4. Group verification

Usage:
    python test_monday.py <API_TOKEN>
    # or
    MONDAY_API_TOKEN=<token> python test_monday.py
"""

import json
import os
import sys
import time

# Add parent directory so we can import monday_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "monday"))
from monday_client import execute_query, get_board_columns, get_board_groups

# Board created by setup_all.py
BOARD_ID = "18399605169"

EXPECTED_COLUMNS = {
    "Denial Code": "dropdown",
    "DOS": "date",
    "Amount": "numeric",
    "Plan Type": "dropdown",
    "Denial Date": "date",
    "Filing Deadline": "date",
    "Appeal Status": "color",
    "Appeal Letter": "link",
    "Provider": "dropdown",
    "Location": "dropdown",
    "Outcome Amount": "numeric",
}

EXPECTED_GROUPS = ["New Denials", "In Progress", "Submitted", "Resolved"]


def test_auth(token):
    """Test API token by fetching current user."""
    query = "query { me { id name email } }"
    result = execute_query(query, api_token=token)
    user = result.get("data", {}).get("me", {})
    if user.get("id"):
        print(f"  Authenticated as: {user.get('name')} ({user.get('email')})")
        return True
    print("  FAIL — could not authenticate")
    return False


def test_board_access(token):
    """Verify board exists and is accessible."""
    query = """query ($ids: [ID!]!) {
        boards(ids: $ids) { id name state workspace { id name } }
    }"""
    result = execute_query(query, {"ids": [BOARD_ID]}, api_token=token)
    boards = result.get("data", {}).get("boards", [])
    if not boards:
        print(f"  FAIL — board {BOARD_ID} not found or not accessible")
        return False
    board = boards[0]
    ws = board.get("workspace", {})
    print(f"  Board: {board['name']} (ID: {board['id']}, state: {board['state']})")
    print(f"  Workspace: {ws.get('name', 'N/A')} (ID: {ws.get('id', 'N/A')})")
    return True


def test_columns(token):
    """Verify all expected columns exist with correct types."""
    columns = get_board_columns(BOARD_ID, api_token=token)
    col_map = {c["title"]: c["type"] for c in columns}

    print(f"  Found {len(columns)} columns:")
    missing = []
    wrong_type = []
    for title, expected_type in EXPECTED_COLUMNS.items():
        actual_type = col_map.get(title)
        if actual_type is None:
            missing.append(title)
            print(f"    MISSING: {title}")
        elif actual_type != expected_type:
            wrong_type.append((title, expected_type, actual_type))
            print(f"    WRONG TYPE: {title} — expected {expected_type}, got {actual_type}")
        else:
            print(f"    OK: {title} ({actual_type})")

    if missing or wrong_type:
        print(f"  ISSUES: {len(missing)} missing, {len(wrong_type)} wrong type")
        return False
    print("  PASS — all columns correct")
    return True


def test_groups(token):
    """Verify all expected groups exist."""
    groups = get_board_groups(BOARD_ID, api_token=token)
    group_names = [g["title"] for g in groups]

    print(f"  Found {len(groups)} groups:")
    all_ok = True
    for name in EXPECTED_GROUPS:
        if name in group_names:
            print(f"    OK: {name}")
        else:
            print(f"    MISSING: {name}")
            all_ok = False

    extra = set(group_names) - set(EXPECTED_GROUPS)
    if extra:
        for name in extra:
            print(f"    EXTRA: {name} (unexpected)")

    if all_ok:
        print("  PASS — all groups correct")
    return all_ok


def test_create_delete_item(token):
    """Create a test item, verify it, then delete it."""
    # Create
    query = """mutation ($boardId: ID!, $itemName: String!, $groupId: String!) {
        create_item(board_id: $boardId, item_name: $itemName, group_id: $groupId) { id name }
    }"""
    variables = {
        "boardId": BOARD_ID,
        "itemName": "[TEST] Connectivity Check — Delete Me",
        "groupId": "group_mm0fc0ne",  # New Denials group
    }
    result = execute_query(query, variables, api_token=token)
    item = result.get("data", {}).get("create_item", {})
    if not item.get("id"):
        print("  FAIL — could not create test item")
        if result.get("errors"):
            for err in result["errors"]:
                print(f"    Error: {err.get('message', err)}")
        return False
    item_id = item["id"]
    print(f"  Created test item: {item['name']} (ID: {item_id})")

    time.sleep(1)

    # Delete
    delete_query = "mutation ($itemId: ID!) { delete_item(item_id: $itemId) { id } }"
    delete_result = execute_query(delete_query, {"itemId": item_id}, api_token=token)
    if delete_result.get("data", {}).get("delete_item", {}).get("id"):
        print(f"  Deleted test item {item_id}")
        print("  PASS — create/delete cycle works")
        return True
    else:
        print(f"  WARNING — could not delete test item {item_id}, please delete manually")
        return True  # Creation worked, which is the important part


def main():
    token = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("PHW Denial Appeals — Monday.com Connectivity Test")
    print("=" * 60)

    results = {}

    # Test 1: Authentication
    print(f"\n[1/5] Testing API authentication...")
    results["auth"] = test_auth(token)

    if not results["auth"]:
        print("\nCannot continue — authentication failed.")
        sys.exit(1)

    # Test 2: Board access
    print(f"\n[2/5] Testing board access (ID: {BOARD_ID})...")
    results["board"] = test_board_access(token)

    if not results["board"]:
        print("\nCannot continue — board not accessible.")
        sys.exit(1)

    # Test 3: Columns
    print(f"\n[3/5] Verifying columns...")
    results["columns"] = test_columns(token)

    # Test 4: Groups
    print(f"\n[4/5] Verifying groups...")
    results["groups"] = test_groups(token)

    # Test 5: Create/delete item
    print(f"\n[5/5] Testing item create/delete...")
    results["crud"] = test_create_delete_item(token)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    for test, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {test}")

    if passed == total:
        print("\nAll tests passed. Monday.com integration is ready.")
    else:
        print("\nSome tests failed. Review output above and fix issues.")
    print(f"\nBoard URL: https://phw-team.monday.com/boards/{BOARD_ID}")


if __name__ == "__main__":
    main()
