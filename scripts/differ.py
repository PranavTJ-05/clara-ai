"""
differ.py — Generates human-readable changelog between v1 and v2 memos.
"""

import os
import json
from datetime import datetime, timezone


def generate_diff(account_id: str, v1: dict, v2: dict) -> str:
    """Compare v1 and v2 memos and write a markdown changelog."""
    lines = [
        f"# Changelog — {account_id}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Changes from v1 (Demo) → v2 (Onboarding)",
        ""
    ]

    changed = []
    added = []
    unchanged = []

    all_keys = set(list(v1.keys()) + list(v2.keys()))

    for key in sorted(all_keys):
        v1_val = v1.get(key)
        v2_val = v2.get(key)

        if v1_val == v2_val:
            unchanged.append(key)
        elif v1_val is None and v2_val is not None:
            added.append((key, v2_val))
        elif v1_val is not None and v2_val != v1_val:
            changed.append((key, v1_val, v2_val))

    if changed:
        lines.append("### ✏️ Updated Fields")
        for key, old, new in changed:
            lines.append(f"\n**{key}**")
            lines.append(f"- Before: `{_fmt(old)}`")
            lines.append(f"- After:  `{_fmt(new)}`")

    if added:
        lines.append("\n### ➕ New Fields (populated in onboarding)")
        for key, val in added:
            lines.append(f"\n**{key}**")
            lines.append(f"- Value: `{_fmt(val)}`")

    if unchanged:
        lines.append(f"\n### ✅ Unchanged Fields ({len(unchanged)})")
        lines.append(", ".join(unchanged))

    content = "\n".join(lines)

    os.makedirs("changelogs", exist_ok=True)
    path = f"changelogs/{account_id}_diff.md"
    with open(path, "w") as f:
        f.write(content)

    return content


def _fmt(val) -> str:
    if isinstance(val, (dict, list)):
        return json.dumps(val, indent=None)[:200]
    return str(val)[:200]