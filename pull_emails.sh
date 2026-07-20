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
            echo "Usage: ${BASH_SOURCE[0]:-$0} [--delete-original]" >&2
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

# Capture stdout only. Stderr goes to terminal naturally.
PYTHON_EXIT=0
RAW_OUTPUT=$("$VENV_PYTHON" "$SCRIPT") || PYTHON_EXIT=$?

if [[ $PYTHON_EXIT -ne 0 ]]; then
    echo "Python script failed with exit code $PYTHON_EXIT." >&2
    exit 1
fi

# Check for the explicit success marker
SUCCESS_LINE=$(echo "$RAW_OUTPUT" | grep '^SUCCESS|' || true)
if [[ -z "$SUCCESS_LINE" ]]; then
    echo "Extraction failed: no SUCCESS marker found in output." >&2
    echo "Raw output:" >&2
    echo "$RAW_OUTPUT" >&2
    exit 1
fi

TOTAL_EMAILS=$(echo "$SUCCESS_LINE" | cut -d'|' -f2)
if ! [[ "$TOTAL_EMAILS" =~ ^[0-9]+$ ]]; then
    echo "ERROR: Invalid email count returned: '$TOTAL_EMAILS'" >&2
    exit 1
fi

echo "------------------------------------------"
echo "Extraction complete!"
echo "Total Unique Emails Found: $TOTAL_EMAILS"
echo "Files created in $OUTPUT_DIR"

# Clean up original CSV files — match same case-insensitive pattern as Python
(
    shopt -s nullglob
    CSV_FILES=( "$INPUT_DIR"/*.[cC][sS][vV] )
    if [[ ${#CSV_FILES[@]} -eq 0 ]]; then
        echo "No CSV files found to clean up."
    else
        if $DELETE_ORIGINAL; then
            rm -f "${CSV_FILES[@]}"
            echo "Original CSV files have been deleted from $INPUT_DIR."
        else
            mkdir -p "$PROCESSED_DIR"
            TS=$(date -u +"%Y%m%d_%H%M%S_UTC")
            for csvfile in "${CSV_FILES[@]}"; do
                base=$(basename "$csvfile")
                # Strip original extension (any case), add timestamp + .csv
                ext="${base##*.}"
                stem="${base%.*}"
                newname="${stem}_${TS}.csv"
                # Avoid collisions: if file exists, append a counter
                dest="$PROCESSED_DIR/$newname"
                counter=1
                while [[ -e "$dest" ]]; do
                    newname="${stem}_${TS}_${counter}.csv"
                    dest="$PROCESSED_DIR/$newname"
                    ((counter++))
                done
                mv "$csvfile" "$dest"
            done
            echo "Original CSV files have been moved to $PROCESSED_DIR (timestamped)."
        fi
    fi
)

echo "------------------------------------------"
