#!/usr/bin/env python3
"""
Extract unique email addresses from CSV files in a source directory,
split them into files of 80 addresses each, and write them to an output directory.
Previous BCC files are archived only *after* new ones are safely created.

Expected to be called by the companion shell script, but can be run standalone.
"""

import argparse
import glob
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime

import pandas as pd

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CHUNK_SIZE = 80


def archive_existing_bcc_files(output_dir: str) -> None:
    """Move any existing bcc_emails*.txt files into a timestamped archive folder."""
    old_files = glob.glob(os.path.join(output_dir, "bcc_emails*.txt"))
    if not old_files:
        return

    # Include seconds to avoid name collisions when run multiple times per minute
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archive_dir = os.path.join(output_dir, f"archive_{timestamp}")
    os.makedirs(archive_dir, exist_ok=True)

    for file_path in old_files:
        dest = os.path.join(archive_dir, os.path.basename(file_path))
        shutil.move(file_path, dest)
        print(f"Archived: {os.path.basename(file_path)} -> {archive_dir}/",
              file=sys.stderr)


def extract_emails(input_dir: str, output_dir: str) -> int:
    """Extract emails, safely write chunk files, then archive old ones.
    Returns total unique email count.
    """
    all_emails: set[str] = set()
    csv_files = glob.glob(os.path.join(input_dir, "*.[cC][sS][vV]"))

    if not csv_files:
        print("No CSV files found in input directory.", file=sys.stderr)
        sys.exit(1)

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path, engine="python", encoding="utf-8-sig")

            # 1. Try columns with 'email' in their name
            target_cols = [col for col in df.columns if "email" in str(col).lower()]

            # 2. Fallback: scan first 10 rows for any column containing '@'
            if not target_cols:
                for col in df.columns:
                    sample = df[col].dropna().astype(str).head(10)
                    if sample.str.contains("@").any():
                        target_cols.append(col)
                        print(
                            f"Using column '{col}' (no column with 'email' in name found).",
                            file=sys.stderr,
                        )

            if not target_cols:
                print(
                    f"No email-like columns found in {file_path}. Skipping.",
                    file=sys.stderr,
                )
                continue

            for col in target_cols:
                emails = (
                    df[col]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .tolist()
                )
                valid = [e for e in emails if EMAIL_RE.fullmatch(e)]
                all_emails.update(valid)

        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)

    if not all_emails:
        print("No valid email addresses found.", file=sys.stderr)
        sys.exit(1)

    sorted_emails = sorted(all_emails)
    total = len(sorted_emails)

    os.makedirs(output_dir, exist_ok=True)

    # --- Safety: write new files to a temp subdirectory ---
    tmpdir = tempfile.mkdtemp(dir=output_dir, prefix=".tmp_chunks_")
    try:
        for i in range(0, total, CHUNK_SIZE):
            chunk = sorted_emails[i : i + CHUNK_SIZE]
            file_num = (i // CHUNK_SIZE) + 1
            tmp_path = os.path.join(tmpdir, f"bcc_emails{file_num}.txt")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write("; ".join(chunk))

        # New files are written – now it’s safe to archive old ones
        archive_existing_bcc_files(output_dir)

        # Move new files from temp dir to output dir
        for fname in os.listdir(tmpdir):
            shutil.move(os.path.join(tmpdir, fname),
                        os.path.join(output_dir, fname))
    finally:
        # Clean up temp dir (empty now if successful)
        shutil.rmtree(tmpdir, ignore_errors=True)

    # Print a single parsable success line (only this goes to stdout)
    print(f"SUCCESS|{total}")
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Extract and chunk email addresses from CSV files."
    )
    parser.add_argument(
        "--input",
        default=os.path.expanduser("~/emailpuller"),
        help="Directory containing the CSV files (default: ~/emailpuller)",
    )
    parser.add_argument(
        "--output",
        default=os.path.expanduser("~/Desktop/emailpuller"),
        help="Directory where chunk files will be written (default: ~/Desktop/emailpuller)",
    )
    args = parser.parse_args()

    extract_emails(args.input, args.output)


if __name__ == "__main__":
    main()
