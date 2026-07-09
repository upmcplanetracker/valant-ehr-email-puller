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

# Run the Python script, capturing stdout ONLY. Errors go to the terminal (via stderr).
# We don't suppress stderr anymore so you can see real errors.
RAW_OUTPUT=$("$VENV_PYTHON" "$SCRIPT" 2>&1) || PYTHON_EXIT=$?
# (We'll handle the output and exit code below)

# Check for the explicit success marker
SUCCESS_LINE=$(echo "$RAW_OUTPUT" | grep '^SUCCESS|' || true)
if [[ -z "$SUCCESS_LINE" ]]; then
    echo "Extraction failed or no emails found." >&2
    # Print whatever the Python script emitted to help debugging
    echo "$RAW_OUTPUT" >&2
    exit 1
fi

TOTAL_EMAILS=$(echo "$SUCCESS_LINE" | cut -d'|' -f2)

echo "------------------------------------------"
echo "Extraction complete!"
echo "Total Unique Emails Found: $TOTAL_EMAILS"
echo "Files created in $OUTPUT_DIR"

# Clean up original CSV files
shopt -s nullglob
CSV_FILES=( "$INPUT_DIR"/*.csv )
if [[ ${#CSV_FILES[@]} -gt 0 ]]; then
    if $DELETE_ORIGINAL; then
        rm -f "$INPUT_DIR"/*.csv
        echo "Original CSV files have been deleted from $INPUT_DIR."
    else
        mkdir -p "$PROCESSED_DIR"
        # Append timestamp to avoid overwriting previous exports
        TS=$(date +"%Y%m%d_%H%M%S")
        for csvfile in "${CSV_FILES[@]}"; do
            base=$(basename "$csvfile")
            newname="${base%.csv}_${TS}.csv"
            mv "$csvfile" "$PROCESSED_DIR/$newname"
        done
        echo "Original CSV files have been moved to $PROCESSED_DIR (timestamped)."
    fi
else
    echo "No CSV files found to clean up."
fi
echo "------------------------------------------"
