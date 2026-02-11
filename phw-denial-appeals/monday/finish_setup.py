#!/usr/bin/env python3
"""
Finish setup for board 18399605169 (created with columns, needs groups).
Run this once, then delete this file.

Usage:
    python3 finish_setup.py <API_TOKEN>
"""

import sys
import time

from monday_client import (
    create_group,
    delete_group,
    get_board_columns,
    get_board_groups,
)

BOARD_ID = "18399605169"

GROUPS = [
    {"name": "New Denials", "color": "#579bfc"},
    {"name": "In Progress", "color": "#fdab3d"},
    {"name": "Submitted", "color": "#0086c0"},
    {"name": "Resolved", "color": "#00c875"},
]

STATUS_LABELS = [
    ("New", "#579bfc"),
    ("Drafted", "#fdab3d"),
    ("Under Review", "#a25ddc"),
    ("Submitted", "#0086c0"),
    ("Awaiting Decision", "#ffcb00"),
    ("Won", "#00c875"),
    ("Lost", "#df2f4a"),
    ("Escalated", "#bb3354"),
]


def main():
    token = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print(f"Finishing setup for board {BOARD_ID}")
    print("=" * 60)

    # Verify board exists and show columns
    print("\n[1/3] Verifying board columns...")
    columns = get_board_columns(BOARD_ID, api_token=token)
    print(f"  Found {len(columns)} columns:")
    for col in columns:
        print(f"    - {col['title']} ({col['type']}) — {col['id']}")

    # Create groups
    print("\n[2/3] Creating groups...")
    created_group_ids = []
    for group in GROUPS:
        result = create_group(BOARD_ID, group["name"], group.get("color"), api_token=token)
        group_id = result["id"]
        created_group_ids.append(group_id)
        print(f"  Created: {group['name']} — ID: {group_id}")
        time.sleep(0.5)

    # Delete default groups
    print("\n[3/3] Cleaning up default groups...")
    all_groups = get_board_groups(BOARD_ID, api_token=token)
    for group in all_groups:
        if group["id"] not in created_group_ids:
            try:
                delete_group(BOARD_ID, group["id"], api_token=token)
                print(f"  Deleted: {group['title']} ({group['id']})")
            except Exception as e:
                print(f"  Could not delete {group['title']}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"  Board URL: https://phw-team.monday.com/boards/{BOARD_ID}")
    print(f"  Groups: {len(GROUPS)}")

    # Status label instructions
    print("\n" + "-" * 60)
    print("MANUAL STEP: Set Appeal Status labels + colors")
    print("-" * 60)
    print("  Open the board, click any cell in the 'Appeal Status' column,")
    print("  then click the pencil icon to edit labels. Set these 8:")
    print()
    for label, color in STATUS_LABELS:
        print(f"    {label:20s}  {color}")
    print()
    print("  Mark 'Won' as the done/complete color.")
    print("  This takes ~2 minutes in the UI.")
    print("=" * 60)


if __name__ == "__main__":
    main()
