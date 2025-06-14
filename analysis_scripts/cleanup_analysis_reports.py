#!/usr/bin/env python3
"""
CLEANUP ANALYSIS REPORTS
Archives all but the most recent analysis reports (HTML and Markdown).
"""
import os
import glob
import shutil
from pathlib import Path

# Get the script's directory to build robust paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

REPORTS_DIR = PROJECT_ROOT / 'results/analysis_reports'
ARCHIVE_DIR = REPORTS_DIR / 'archive'

def cleanup_analysis_reports():
    """
    Moves all but the latest HTML and Markdown reports from the analysis_reports
    directory to an 'archive' subdirectory.
    """
    print(f"🗂️  Archiving old analysis reports in: {REPORTS_DIR}")

    # 1. Ensure the archive directory exists
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📂 Archive directory is: {ARCHIVE_DIR}")

    # 2. Get all HTML and Markdown files in the reports directory
    # We search directly in the REPORTS_DIR, not recursively, to avoid picking up archived files
    html_files = glob.glob(str(REPORTS_DIR / '*.html'))
    md_files = glob.glob(str(REPORTS_DIR / '*.md'))
    all_files = html_files + md_files

    if not all_files:
        print("✅ No reports found to clean up.")
        return

    # 3. Find the most recent file
    try:
        latest_file = max(all_files, key=os.path.getmtime)
        print(f"✅ Keeping latest file: {os.path.basename(latest_file)}")
    except ValueError:
        print("✅ No reports found to clean up.")
        return

    # 4. Move all other files to the archive
    files_to_move = [f for f in all_files if f != latest_file]
    moved_count = 0

    if not files_to_move:
        print("✅ Only one report exists, no archiving needed.")
        return

    print(f"🚚 Moving {len(files_to_move)} old reports to archive...")
    for file_path in files_to_move:
        try:
            filename = os.path.basename(file_path)
            destination = ARCHIVE_DIR / filename
            # To prevent errors if the file already exists in the archive, we check first
            if not os.path.exists(destination):
                shutil.move(file_path, destination)
                print(f"  -> Moved {filename}")
                moved_count += 1
            else:
                print(f"  -> Skipping {filename}, already in archive. Deleting local copy.")
                os.remove(file_path) # remove the duplicate from the main folder
        except Exception as e:
            print(f"❌ Error moving {filename}: {e}")

    print(f"🎉 Cleanup complete. Moved {moved_count} files to archive.")

if __name__ == "__main__":
    cleanup_analysis_reports() 