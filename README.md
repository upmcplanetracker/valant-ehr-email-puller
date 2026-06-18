Valant Facesheet Email Extractor
================================

A small tool that reads email addresses from Valant EHR Facesheet CSV exports, deduplicates them, and splits them into text files of **80 addresses each**, ready to copy/paste into Gmail's **BCC** field.

* * *

Prerequisites
-------------

*   **Ubuntu** (or any Linux/macOS system with Bash – small adjustments may be needed on macOS)
*   **Python 3** (≥3.6)
*   Python **venv** module (usually installed with `python3-venv`)
*   **`pandas`** Python package (installed inside a virtual environment)

* * *

Setup
-----

1.  **Clone or copy the scripts** into your home directory (or anywhere you like).  
    The default paths expect:
    *   Shell script: anywhere (you'll run it from the terminal)
    *   Python script: `~/emailpuller/processor.py`
    *   Python virtual environment: `~/emailpuller/venv/`
2.  **Create the virtual environment and install `pandas`:**
    
        mkdir -p ~/emailpuller
        python3 -m venv ~/emailpuller/venv
        ~/emailpuller/venv/bin/pip install pandas
    
3.  **Place the scripts:**
    *   Save the shell script as `pull_emails.sh` (for example).
    *   Save the Python script as `~/emailpuller/processor.py`.
4.  **Make the shell script executable:**
    
        chmod +x pull_emails.sh
    
* * *

Usage
-----

### 1\. Export the Facesheet CSV from Valant

*   In Valant EHR, go to:  
    **Tools → System Reports → Clinical → Facesheets → Patient → All Patients → Preview**
*   Wait for the report to finish rendering.
*   Click the **Download** arrow in the toolbar and choose **CSV format**.
*   Save the file directly into the folder:  
    `~/emailpuller/`  
    (The file is usually called `Facesheets.csv`, but any `.csv` filename works.)

### 2\. Run the extractor

Open a terminal and run the shell script:

    ./pull_emails.sh

This will:

*   Find all `.csv` files in `~/emailpuller/`
*   Extract and deduplicate all valid email addresses
*   Create numbered BCC files (`bcc_emails1.txt`, `bcc_emails2.txt`, …) in `~/Desktop/emailpuller/`
*   **Move** the original CSV(s) into `~/emailpuller/processed/` for your records

#### Optional: delete the original CSV(s)

If you prefer to delete the source files after extraction instead of moving them, use the `--delete-original` flag:

    ./pull_emails.sh --delete-original

⚠️ **Warning:** This permanently removes the CSV files from `~/emailpuller/`. Be sure you have backups if needed.

### Archive of previous output

The script **never deletes old BCC files**.  
Before writing new ones, it moves any existing `bcc_emails*.txt` files into a timestamped archive folder inside `~/Desktop/emailpuller/`, like this:

    ~/Desktop/emailpuller/
    ├── bcc_emails1.txt          ← newest run
    ├── archive_2026-06-18_1430/
    │   ├── bcc_emails1.txt      ← previous run
    │   └── bcc_emails2.txt
    └── archive_2026-06-19_0900/
        ├── bcc_emails1.txt
        └── ...

This way you always have a history of every extraction you’ve made, and you can safely run the script as often as you like without losing anything.

🧹 **Tip:** Over time the archive folders will pile up. Delete old ones manually when you no longer need them.

### 3\. Use the email files

*   Open the files in `~/Desktop/emailpuller/`
*   Each file contains exactly 80 email addresses separated by semicolons (`;`), ready to be pasted into Gmail's BCC field.

* * *

Output Example
--------------

    ~/Desktop/emailpuller/
    ├── bcc_emails1.txt     ← 80 addresses
    ├── bcc_emails2.txt     ← 80 addresses
    └── ...

* * *

Troubleshooting
---------------

| Problem | Solution |
|---|---|
| “Python virtual environment not found” | Run the setup steps again, making sure the venv is at `~/emailpuller/venv` and `python3` is installed. |
| “No CSV files found” | Confirm you saved the Facesheet CSV directly into `~/emailpuller/`, and that the filename ends with `.csv`. |
| The script runs but no email files appear | The CSV may not contain an email column, or the column name may not contain “email” and the first few rows lack a “@” – check your Valant export. |
| Files are not split exactly to 80 addresses | This is normal if the total number of unique emails is not a multiple of 80 – the last file will have fewer than 80. |
| Encoding errors | The script uses UTF-8 with BOM handling. If you still see encoding issues, try re-exporting the Facesheet from Valant. |

* * *

License
-------

MIT license. Feel free to use and modify for your own practice. No warranty – use at your own risk.

* * *

Privacy
-------

Remember to follow all applicable rules regardng HIPAA/PHI.
