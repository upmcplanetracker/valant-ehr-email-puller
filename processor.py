#!/usr/bin/env python3
"""
Extract unique email addresses from CSV files in a source directory,
split them into files of N addresses each, and write them to an output directory.
"""

import argparse
import glob
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone

import pandas as pd

# Rejects obvious garbage like "a@b.c" or "user@1.2" but allows real-world emails
EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+-]{2,}@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
)
DEFAULT_CHUNK = 80


def read_csv(file_path: str) -> pd.DataFrame:
    """Fast path first, fall back to python engine on parse errors."""
    try:
        return pd.read_csv(file_path, engine="c", encoding="utf-8-sig")
    except (pd.errors.ParserError, UnicodeDecodeError):
        return pd.read_csv(file_path, engine="python", encoding="utf-8-sig")


def archive_old_files(output_dir: str) -> None:
    old = glob.glob(os.path.join(output_dir, "bcc_emails*.txt"))
    if not old:
        return

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S_UTC")
    archive = os.path.join(output_dir, f"archive_{ts}")
    os.makedirs(archive, exist_ok=True)

    for f in old:
        shutil.move(f, os.path.join(archive, os.path.basename(f)))
        print(f"Archived: {os.path.basename(f)}", file=sys.stderr)


def extract(input_dir: str, output_dir: str, chunk_size: int) -> int:
    csvs = glob.glob(os.path.join(input_dir, "*.[cC][sS][vV]"))
    if not csvs:
        print("No CSV files found.", file=sys.stderr)
        sys.exit(1)

    emails: set[str] = set()
    errors: list[str] = []

    for path in csvs:
        try:
            df = read_csv(path)
            cols = [c for c in df.columns if "email" in str(c).lower()]

            if not cols:
                for c in df.columns:
                    if df[c].dropna().astype(str).head(10).str.contains("@").any():
                        cols.append(c)
                        print(f"Using column '{c}' for {path}", file=sys.stderr)

            if not cols:
                print(f"No email columns in {path} — skipped.", file=sys.stderr)
                continue

            for c in cols:
                for raw in df[c].dropna().astype(str).str.strip().str.lower():
                    if EMAIL_RE.match(raw):
                        emails.add(raw)

        except Exception as e:
            errors.append(f"{path}: {e}")
            print(f"Error: {path}: {e}", file=sys.stderr)

    if errors and not emails:
        print("All files failed to parse. No emails extracted.", file=sys.stderr)
        sys.exit(1)

    if not emails:
        print("No valid email addresses found.", file=sys.stderr)
        sys.exit(1)

    sorted_emails = sorted(emails)
    total = len(sorted_emails)

    os.makedirs(output_dir, exist_ok=True)

    tmp = tempfile.mkdtemp(dir=output_dir, prefix=".tmp_")
    try:
        for i in range(0, total, chunk_size):
            chunk = sorted_emails[i : i + chunk_size]
            n = (i // chunk_size) + 1
            with open(os.path.join(tmp, f"bcc_emails{n}.txt"), "w") as f:
                f.write("; ".join(chunk))

        archive_old_files(output_dir)

        for fname in os.listdir(tmp):
            shutil.move(os.path.join(tmp, fname), os.path.join(output_dir, fname))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"PROCESSED|{json.dumps(report.files_ok)}")
    print(f"SUCCESS|{total}")
    return total


def main():
    p = argparse.ArgumentParser(description="Chunk emails from CSVs.")
    p.add_argument("--input", default="~/emailpuller")
    p.add_argument("--output", default="~/Desktop/emailpuller")
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK)
    args = p.parse_args()

    extract(
        os.path.expanduser(args.input),
        os.path.expanduser(args.output),
        args.chunk_size,
    )


if __name__ == "__main__":
    main()
