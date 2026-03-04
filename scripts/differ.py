import json
import logging

def generate_differential_changelog(v1_memo_dict: dict, v2_memo_dict: dict, account_id: str) -> str:
    """
    Compares version 1 and version 2 memos and generates a markdown changelog.
    """
    changes = []
    
    for key, v2_val in v2_memo_dict.items():
        v1_val = v1_memo_dict.get(key)
        
        # Ignore version keys for the diff logic
        if key == "version":
            continue
            
        if v1_val != v2_val:
            if not v1_val and v2_val:
                changes.append(f"- **{key}** added: `{v2_val}`")
            elif v1_val and not v2_val:
                changes.append(f"- **{key}** removed (was `{v1_val}`)")
            elif isinstance(v1_val, list) and isinstance(v2_val, list):
                added = set(v2_val) - set(v1_val)
                removed = set(v1_val) - set(v2_val)
                if added:
                    changes.append(f"- **{key}** items added: `{', '.join(added)}`")
                if removed:
                    changes.append(f"- **{key}** items removed: `{', '.join(removed)}`")
            else:
                changes.append(f"- **{key}** updated:\n  - *old:* `{v1_val}`\n  - *new:* `{v2_val}`")
    
    if not changes:
        return f"# Changelog for Account: {account_id}\n\nNo operational changes detected between v1 and v2."
        
    changelog = f"# Changelog for Account: {account_id}\n\n## Updates from Onboarding (v1 -> v2)\n"
    changelog += "\n".join(changes)
    
    return changelog
