"""
process.py — CLI entry point for direct transcript processing.
Usage:
  python process.py --file data/inbox/demo_1.txt --type demo
  python process.py --file data/inbox/onboarding_1.txt --type onboarding --account-id account_abc123
"""

import argparse
import sys
import os

# Add scripts dir to path when running from project root
sys.path.insert(0, os.path.dirname(__file__))

from extractor import extract_memo_from_transcript
from agent_builder import build_agent_spec
from differ import generate_diff
from tracker import create_task
from version_manager import save_artifact, load_artifact, version_exists
from main import merge_memos
import uuid


def main():
    parser = argparse.ArgumentParser(description="Clara Pipeline — Process a transcript")
    parser.add_argument("--file", required=True, help="Path to transcript .txt file")
    parser.add_argument("--type", choices=["demo", "onboarding"], required=True)
    parser.add_argument("--account-id", default=None, help="Account ID (auto-generated if omitted)")
    parser.add_argument("--company", default=None, help="Company name hint")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        sys.exit(1)

    with open(args.file) as f:
        transcript_text = f.read()

    account_id = args.account_id or f"account_{uuid.uuid4().hex[:8]}"
    print(f"[INFO] Processing {args.file}")
    print(f"[INFO] Account: {account_id}  Type: {args.type}")

    if args.type == "demo":
        if version_exists(account_id, "v1"):
            print(f"[SKIP] {account_id}/v1 already exists. Use a new account_id to reprocess.")
            sys.exit(0)

        memo = extract_memo_from_transcript(transcript_text, "demo", account_id, args.company)
        spec = build_agent_spec(memo)
        save_artifact(account_id, "v1", "memo.json", memo.model_dump())
        save_artifact(account_id, "v1", "agent_spec.json", spec.model_dump())
        create_task(account_id, "demo_processed", {"unknowns": len(memo.questions_or_unknowns)})

        print(f"[OK] Saved outputs/accounts/{account_id}/v1/")
        print(f"[OK] Unknowns to resolve: {len(memo.questions_or_unknowns)}")
        if memo.questions_or_unknowns:
            for q in memo.questions_or_unknowns:
                print(f"     ? {q}")

    elif args.type == "onboarding":
        v1_data = load_artifact(account_id, "v1", "memo.json")
        if not v1_data:
            print(f"[ERROR] No v1 memo found for {account_id}. Run demo first.")
            sys.exit(1)

        if version_exists(account_id, "v2"):
            print(f"[SKIP] {account_id}/v2 already exists.")
            sys.exit(0)

        from schemas import AccountMemo
        v1_memo = AccountMemo(**v1_data)
        onboarding_memo = extract_memo_from_transcript(transcript_text, "onboarding", account_id, args.company)
        merged = merge_memos(v1_memo, onboarding_memo)

        spec = build_agent_spec(merged)
        spec.version = "v2"

        save_artifact(account_id, "v2", "memo.json", merged.model_dump())
        save_artifact(account_id, "v2", "agent_spec.json", spec.model_dump())
        generate_diff(account_id, v1_memo.model_dump(), merged.model_dump())
        create_task(account_id, "onboarding_processed", {})

        print(f"[OK] Saved outputs/accounts/{account_id}/v2/")
        print(f"[OK] Changelog: changelogs/{account_id}_diff.md")


if __name__ == "__main__":
    main()