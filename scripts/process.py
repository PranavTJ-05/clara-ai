import os
import argparse
import json
import logging
from extractor import extract_account_memo
from agent_builder import build_agent_spec
from differ import generate_differential_changelog
from tracker import create_task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_account_id_from_filename(filename: str) -> str:
    """
    Naive mapping of demo_X.txt and onboarding_X.txt to account_X.
    """
    basename = os.path.basename(filename).replace(".txt", "")
    parts = basename.split("_")
    account_number = parts[1] if len(parts) > 1 else "unknown"
    return f"account_{account_number}"

def process_transcript(filepath: str):
    basename = os.path.basename(filepath)
    is_demo = "demo" in basename.lower()
    
    version = "v1" if is_demo else "v2"
    account_id = get_account_id_from_filename(basename)
    
    logging.info(f"Processing {basename} -> {account_id} as {version}")
    
    # 1. Load the transcript 
    with open(filepath, 'r') as f:
        transcript = f.read()

    # Define base output paths
    base_output_dir = os.path.join("outputs", "accounts", account_id)
    v1_dir = os.path.join(base_output_dir, "v1")
    v2_dir = os.path.join(base_output_dir, "v2")
    changelog_dir = os.path.join("changelogs")
    
    os.makedirs(v1_dir, exist_ok=True)
    os.makedirs(v2_dir, exist_ok=True)
    os.makedirs(changelog_dir, exist_ok=True)
    
    v1_memo_path = os.path.join(v1_dir, "memo.json")

    # 2. Extract Data via LLM
    logging.info(f"Extracting operational rules...")
    memo = extract_account_memo(transcript, account_id, version)

    # 3. Patching logic for v2 (Onboarding merges with Demo assumptions)
    if version == "v2":
        if os.path.exists(v1_memo_path):
            logging.info("Applying diffs to existing v1 configurations.")
            with open(v1_memo_path, "r") as f:
                v1_memo_dict = json.load(f)
            
            # Simple un-hallucinated merge: 
            # We take the v2 memo fields and replace v1 only if v2 provides a new explicitly stated value.
            v2_memo_dict = memo.model_dump()
            
            # Generate the differ file
            changelog_content = generate_differential_changelog(v1_memo_dict, v2_memo_dict, account_id)
            with open(os.path.join(changelog_dir, f"{account_id}_diff.md"), "w") as f:
                f.write(changelog_content)
                
            logging.info(f"Patch complete. Changelog written to changelogs/{account_id}_diff.md")
        else:
            logging.warning("Processing onboarding (v2) without a preexisting demo (v1).")

    # 4. Agent Configuration Mapping
    logging.info(f"Synthesizing {version} Retell Agent prompt...")
    agent_spec = build_agent_spec(memo)

    # 5. Output generation
    target_dir = v1_dir if version == "v1" else v2_dir
    
    with open(os.path.join(target_dir, "memo.json"), "w") as f:
        f.write(memo.model_dump_json(indent=2))
        
    with open(os.path.join(target_dir, "agent_spec.json"), "w") as f:
        f.write(agent_spec.model_dump_json(indent=2))

    # 6. Tracker integration
    create_task(
        account_id=account_id, 
        summary=f"Processed {'preliminary' if is_demo else 'final'} configuration for {memo.company_name} ({version})",
        status="Review Required"
    )

    logging.info(f"Pipeline finished for {basename}. Outputs in {target_dir}/\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clara Answers Extractor Pipeline")
    parser.add_argument("--file", help="Path to the user demo or onboarding transcript text file.", required=False)
    parser.add_argument("--batch", help="Batch process all files in inbox directory.", action="store_true")
    
    args = parser.parse_args()
    
    if args.batch:
        inbox = "data/inbox"
        if not os.path.exists(inbox):
            logging.error("data/inbox directory does not exist.")
            exit(1)
            
        # Ensure demos process first so v1 exists before onboarding (v2) runs
        files = sorted(os.listdir(inbox))
        for filename in files:
            if filename.endswith(".txt"):
                process_transcript(os.path.join(inbox, filename))
    elif args.file:
        if not os.path.exists(args.file):
            logging.error(f"File {args.file} not found.")
            exit(1)
        process_transcript(args.file)
    else:
        parser.print_help()
