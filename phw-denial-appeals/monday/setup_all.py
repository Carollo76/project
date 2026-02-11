#!/usr/bin/env python3
"""
PHW Denial Appeals — Monday.com Full Setup Script
Deletes old boards, creates pipeline board with columns/statuses/groups,
and creates analytics dashboard.

Usage:
    python setup_all.py <API_TOKEN>
    # or
    MONDAY_API_TOKEN=<token> python setup_all.py
"""

import json
import sys
import time

from monday_client import (
    change_column_metadata,
    create_board,
    create_column,
    create_group,
    delete_board,
    delete_group,
    execute_query,
    get_board_columns,
    get_board_groups,
)

# Configuration
WORKSPACE_ID = 11690254
OLD_BOARD_IDS = [18399114481]  # 18399114818 already deleted

BOARD_NAME = "PHW Denial Appeals"
BOARD_DESC = (
    "Optum/UHC denial appeal pipeline tracking from intake through resolution. "
    "Tracks denial codes, appeal status, filing deadlines, and outcomes for all "
    "4 Manhattan locations and 11 entities."
)

# Columns to create (Name column auto-exists)
COLUMNS = [
    {
        "title": "Denial Code",
        "type": "dropdown",
        "defaults": {
            "labels": [
                {"name": "PTOT08A - MTB Reached"},
                {"name": "PTOT05 - Non-Skilled"},
                {"name": "PTOT21 - Re-eval Bundled"},
                {"name": "PTOT19 - Dup Eval"},
            ]
        },
    },
    {"title": "DOS", "type": "date"},
    {"title": "Amount", "type": "numbers"},
    {
        "title": "Plan Type",
        "type": "dropdown",
        "defaults": {
            "labels": [
                {"name": "Fully Insured"},
                {"name": "Self-Funded (ERISA)"},
            ]
        },
    },
    {"title": "Denial Date", "type": "date"},
    {"title": "Filing Deadline", "type": "date"},
    {"title": "Appeal Status", "type": "status"},
    {"title": "Appeal Letter", "type": "link"},
    {
        "title": "Provider",
        "type": "dropdown",
        "defaults": {
            "labels": [
                {"name": "Dr. Bilitsis"},
                {"name": "Provider 2"},
                {"name": "Provider 3"},
                {"name": "Provider 4"},
            ]
        },
    },
    {
        "title": "Location",
        "type": "dropdown",
        "defaults": {
            "labels": [
                {"name": "Location 1"},
                {"name": "Location 2"},
                {"name": "Location 3"},
                {"name": "Location 4"},
            ]
        },
    },
    {"title": "Outcome Amount", "type": "numbers"},
]

# Appeal Status custom labels
STATUS_LABELS = {
    "labels": {
        "0": {"color": "#579bfc", "label": "New"},
        "1": {"color": "#fdab3d", "label": "Drafted"},
        "2": {"color": "#a25ddc", "label": "Under Review"},
        "3": {"color": "#0086c0", "label": "Submitted"},
        "4": {"color": "#ffcb00", "label": "Awaiting Decision"},
        "5": {"color": "#00c875", "label": "Won", "is_done": True},
        "6": {"color": "#df2f4a", "label": "Lost"},
        "7": {"color": "#bb3354", "label": "Escalated"},
    }
}

# Groups to create (in order, first = top)
GROUPS = [
    {"name": "New Denials", "color": "#579bfc"},
    {"name": "In Progress", "color": "#fdab3d"},
    {"name": "Submitted", "color": "#0086c0"},
    {"name": "Resolved", "color": "#00c875"},
]


def main():
    token = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("PHW Denial Appeals — Monday.com Setup")
    print("=" * 60)

    # Step 1: Delete old boards
    print("\n[1/6] Cleaning up old boards...")
    for board_id in OLD_BOARD_IDS:
        result = delete_board(board_id, api_token=token)
        if result.get("data", {}).get("delete_board"):
            print(f"  Deleted board {board_id}")
        else:
            print(f"  Board {board_id} — may already be deleted or not found")
            if result.get("errors"):
                for err in result["errors"]:
                    print(f"    Error: {err.get('message', err)}")
    time.sleep(1)

    # Step 2: Create new pipeline board
    print("\n[2/6] Creating PHW Denial Appeals board...")
    board_id = create_board(BOARD_NAME, WORKSPACE_ID, BOARD_DESC, api_token=token)
    print(f"  Board created — ID: {board_id}")
    time.sleep(1)

    # Step 3: Create columns
    print("\n[3/6] Creating columns...")
    status_column_id = None
    for col in COLUMNS:
        defaults = col.get("defaults")
        result = create_column(board_id, col["title"], col["type"], defaults, api_token=token)
        col_id = result["id"]
        print(f"  Created: {col['title']} ({col['type']}) — ID: {col_id}")
        if col["title"] == "Appeal Status":
            status_column_id = col_id
        time.sleep(0.5)  # Rate limiting

    # Step 4: Configure Appeal Status labels
    print("\n[4/6] Configuring Appeal Status labels...")
    if status_column_id:
        result = change_column_metadata(
            board_id, status_column_id, "labels", json.dumps(STATUS_LABELS["labels"]), api_token=token
        )
        if result.get("data", {}).get("change_column_metadata"):
            print(f"  Status labels configured on column {status_column_id}")
        else:
            print(f"  Warning: Status label config may have issues")
            print(f"  Response: {json.dumps(result, indent=2)}")
    else:
        print("  ERROR: Could not find Appeal Status column ID!")

    time.sleep(1)

    # Step 5: Create groups
    print("\n[5/6] Creating groups...")
    created_group_ids = []
    for group in GROUPS:
        result = create_group(board_id, group["name"], group.get("color"), api_token=token)
        group_id = result["id"]
        created_group_ids.append(group_id)
        print(f"  Created group: {group['name']} — ID: {group_id}")
        time.sleep(0.5)

    # Delete default groups (any group not in our created list)
    print("\n[6/6] Cleaning up default groups...")
    all_groups = get_board_groups(board_id, api_token=token)
    for group in all_groups:
        if group["id"] not in created_group_ids:
            try:
                delete_group(board_id, group["id"], api_token=token)
                print(f"  Deleted default group: {group['title']} ({group['id']})")
            except Exception as e:
                print(f"  Could not delete group {group['title']}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"  Board ID: {board_id}")
    print(f"  Board Name: {BOARD_NAME}")
    print(f"  Workspace: Billing ({WORKSPACE_ID})")
    print(f"  Columns: {len(COLUMNS) + 1} (including Name)")
    print(f"  Groups: {len(GROUPS)}")
    print(f"  Status Labels: {len(STATUS_LABELS['labels'])}")

    # Verification
    print("\n[Verification]")
    columns = get_board_columns(board_id, api_token=token)
    print(f"  Columns found: {len(columns)}")
    for col in columns:
        print(f"    - {col['title']} ({col['type']})")

    groups = get_board_groups(board_id, api_token=token)
    print(f"  Groups found: {len(groups)}")
    for g in groups:
        print(f"    - {g['title']} ({g['id']})")

    print(f"\n  Board URL: https://phw-team.monday.com/boards/{board_id}")
    print(f"\n  Save this Board ID for dashboard setup: {board_id}")

    return board_id


if __name__ == "__main__":
    main()
