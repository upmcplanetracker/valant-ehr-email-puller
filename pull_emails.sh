#!/bin/bash
set -euo pipefail

DELETE_ORIGINAL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --delete-original)
            DELETE_ORIGINAL=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--delete-original]" >&2
            exit 1
            ;;
    esac
done

VENV_PYTHON="$HOME/emailpuller/venv/bin/python3"
SCRIPT="$HOME/emailpuller/processor.py"
INPUT_DIR="$HOME/emailpuller"
OUTPUT_DIR="$HOME/Desktop/emailpuller"
PROCESSED_DIR="$INPUT_DIR/processed"

mkdir -p "$OUTPUT_DIR"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "ERROR: Python virtual environment not found at $VENV_PYTHON" >&2
    exit 1
fi
if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: processor.py not found at $SCRIPT" >&2
    exit 1
fi

RESULT=$("$VENV_PYTHON" "$SCRIPT" 2>/dev/null) || {
    echo "No emails found or no CSV files present in $INPUT_DIR." >&2
    echo "Check if Facesheets.csv is actually inside $INPUT_DIR" >&2
    exit 1
}

TOTAL_EMAILS=$(echo "$RESULT" | cut -d'|' -f2)

echo "------------------------------------------"
echo "Extraction complete!"
echo "Total Unique Emails Found: $TOTAL_EMAILS"
echo "Files created in $OUTPUT_DIR"

shopt -s nullglob
CSV_FILES=( "$INPUT_DIR"/*.csv )
if [[ ${#CSV_FILES[@]} -gt 0 ]]; then
    if $DELETE_ORIGINAL; then
        rm -f "$INPUT_DIR"/*.csv
        echo "Original CSV files have been deleted from $INPUT_DIR."
    else
        mkdir -p "$PROCESSED_DIR"
        mv "$INPUT_DIR"/*.csv "$PROCESSED_DIR/"
        echo "Original CSV files have been moved to $PROCESSED_DIR."
    fi
else
    echo "No CSV files found to clean up."
fi
echo "------------------------------------------"
