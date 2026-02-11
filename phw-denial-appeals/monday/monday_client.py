"""
Monday.com GraphQL API client for PHW Denial Appeals automation.
Usage: Import and call functions, or run scripts that use this client.
API token should be passed as argument or set via MONDAY_API_TOKEN env var.
"""

import json
import os
import requests
import time

API_URL = "https://api.monday.com/v2"


def get_headers(api_token=None):
    token = api_token or os.environ.get("MONDAY_API_TOKEN")
    if not token:
        raise ValueError("Monday.com API token required. Pass as argument or set MONDAY_API_TOKEN env var.")
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "API-Version": "2024-10",
    }


def execute_query(query, variables=None, api_token=None):
    """Execute a GraphQL query against Monday.com API with retry logic."""
    headers = get_headers(api_token)
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    for attempt in range(4):
        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
            return data
        except requests.exceptions.RequestException as e:
            if attempt < 3:
                wait = 2 ** (attempt + 1)
                print(f"Request failed ({e}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def delete_board(board_id, api_token=None):
    query = "mutation ($id: ID!) { delete_board(board_id: $id) { id } }"
    return execute_query(query, {"id": board_id}, api_token)


def create_board(name, workspace_id, description="", board_kind="public", api_token=None):
    query = """mutation ($name: String!, $kind: BoardKind!, $ws: ID!) {
        create_board(board_name: $name, board_kind: $kind, workspace_id: $ws) { id }
    }"""
    variables = {"name": name, "kind": board_kind, "ws": workspace_id}
    result = execute_query(query, variables, api_token)
    return result["data"]["create_board"]["id"]


def create_column(board_id, title, column_type, defaults=None, api_token=None):
    query = """mutation ($boardId: ID!, $title: String!, $type: ColumnType!, $defaults: JSON) {
        create_column(board_id: $boardId, title: $title, column_type: $type, defaults: $defaults) { id title }
    }"""
    variables = {"boardId": board_id, "title": title, "type": column_type}
    if defaults:
        variables["defaults"] = json.dumps(defaults)
    result = execute_query(query, variables, api_token)
    return result["data"]["create_column"]


def change_column_metadata(board_id, column_id, column_property, value, api_token=None):
    query = """mutation ($boardId: ID!, $colId: String!, $prop: ColumnProperty!, $val: String!) {
        change_column_metadata(board_id: $boardId, column_id: $colId, column_property: $prop, value: $val) { id }
    }"""
    variables = {"boardId": board_id, "colId": column_id, "prop": column_property, "val": value}
    return execute_query(query, variables, api_token)


def create_group(board_id, group_name, group_color=None, api_token=None):
    query = """mutation ($boardId: ID!, $name: String!, $color: String) {
        create_group(board_id: $boardId, group_name: $name, group_color: $color) { id title }
    }"""
    variables = {"boardId": board_id, "name": group_name}
    if group_color:
        variables["color"] = group_color
    result = execute_query(query, variables, api_token)
    return result["data"]["create_group"]


def delete_group(board_id, group_id, api_token=None):
    query = """mutation ($boardId: ID!, $groupId: String!) {
        delete_group(board_id: $boardId, group_id: $groupId) { id }
    }"""
    return execute_query(query, {"boardId": board_id, "groupId": group_id}, api_token)


def get_board_groups(board_id, api_token=None):
    query = """query ($boardId: [ID!]!) {
        boards(ids: $boardId) { groups { id title color } }
    }"""
    result = execute_query(query, {"boardId": [board_id]}, api_token)
    return result["data"]["boards"][0]["groups"]


def get_board_columns(board_id, api_token=None):
    query = """query ($boardId: [ID!]!) {
        boards(ids: $boardId) { columns { id title type settings_str } }
    }"""
    result = execute_query(query, {"boardId": [board_id]}, api_token)
    return result["data"]["boards"][0]["columns"]


def create_dashboard(name, workspace_id, kind="public", api_token=None):
    query = """mutation ($name: String!, $kind: DashboardKind!) {
        create_dashboard(name: $name, kind: $kind) { id }
    }"""
    # Note: workspace_id may need to be handled differently depending on API version
    variables = {"name": name, "kind": kind}
    result = execute_query(query, variables, api_token)
    return result["data"]["create_dashboard"]["id"]
