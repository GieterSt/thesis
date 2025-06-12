#!/usr/bin/env python3
"""
Cleanup Analysis Reports - Archive old reports, keep only the latest
"""

import os
import shutil
from pathlib import Path
import re
from datetime import datetime

def cleanup_analysis_reports():
    """Archive old analysis reports, keeping only the latest version"""
    
    reports_dir = Path("results/analysis_reports")
    archive_dir = reports_dir / "archive"
    
    # Create archive directory if it doesn't exist
    archive_dir.mkdir(exist_ok=True)
    
    print("🧹 CLEANING UP ANALYSIS REPORTS")
    print("=" * 50)
    
    # Find all HTML analysis reports
    html_files = list(reports_dir.glob("analysis_report_*.html"))
    
    if not html_files:
        print("❌ No analysis report HTML files found")
        return
    
    print(f"📊 Found {len(html_files)} analysis report files")
    
    # Sort by timestamp in filename (format: analysis_report_YYYYMMDD_HHMMSS.html)
    def extract_timestamp(filename):
        match = re.search(r'analysis_report_(\d{8}_\d{6})\.html', filename.name)
        if match:
            return match.group(1)
        return "00000000_000000"
    
    html_files.sort(key=extract_timestamp)
    
    # Keep the latest file, archive the rest
    if len(html_files) > 1:
        latest_file = html_files[-1]
        files_to_archive = html_files[:-1]
        
        print(f"📌 KEEPING LATEST: {latest_file.name}")
        print(f"📦 ARCHIVING: {len(files_to_archive)} older reports")
        
        # Move older files to archive
        archived_count = 0
        for file_path in files_to_archive:
            try:
                archive_path = archive_dir / file_path.name
                shutil.move(str(file_path), str(archive_path))
                print(f"   ✅ Archived: {file_path.name}")
                archived_count += 1
            except Exception as e:
                print(f"   ❌ Error archiving {file_path.name}: {e}")
        
        print(f"\n🎯 CLEANUP COMPLETE:")
        print(f"   • Latest report: {latest_file.name}")
        print(f"   • Archived: {archived_count} files")
        print(f"   • Archive location: {archive_dir}")
        
    else:
        print("✅ Only one report file found - no cleanup needed")
    
    # Also cleanup README files (keep only latest)
    readme_files = list(reports_dir.glob("README_*.md"))
    if len(readme_files) > 1:
        readme_files.sort(key=extract_timestamp)
        latest_readme = readme_files[-1]
        old_readmes = readme_files[:-1]
        
        print(f"\n📝 CLEANING UP README FILES:")
        print(f"📌 KEEPING: {latest_readme.name}")
        
        for readme in old_readmes:
            try:
                archive_path = archive_dir / readme.name
                shutil.move(str(readme), str(archive_path))
                print(f"   ✅ Archived: {readme.name}")
            except Exception as e:
                print(f"   ❌ Error archiving {readme.name}: {e}")

def add_cleanup_to_analysis_script():
    """Add automatic cleanup to the main analysis script"""
    
    analysis_script = Path("analysis_scripts/run_analysis.py")
    
    if not analysis_script.exists():
        print("❌ run_analysis.py not found")
        return
    
    # Read the current script
    with open(analysis_script, 'r') as f:
        content = f.read()
    
    # Check if cleanup is already added
    if "cleanup_analysis_reports" in content:
        print("✅ Cleanup already integrated in run_analysis.py")
        return
    
    # Add cleanup import and call at the end
    cleanup_code = '''
# Auto-cleanup: Archive old reports, keep only latest
try:
    import sys
    sys.path.append('..')
    from cleanup_analysis_reports import cleanup_analysis_reports
    cleanup_analysis_reports()
except ImportError:
    print("⚠️  Cleanup script not found - skipping archive cleanup")
except Exception as e:
    print(f"⚠️  Cleanup failed: {e}")
'''
    
    # Add before the final success message
    if 'print("🎉 ANALYSIS COMPLETE!")' in content:
        content = content.replace(
            'print("🎉 ANALYSIS COMPLETE!")',
            cleanup_code + '\nprint("🎉 ANALYSIS COMPLETE!")'
        )
        
        # Write back to file
        with open(analysis_script, 'w') as f:
            f.write(content)
        
        print("✅ Auto-cleanup integrated into run_analysis.py")
    else:
        print("⚠️  Could not integrate auto-cleanup - add manually if needed")

if __name__ == "__main__":
    cleanup_analysis_reports()
    add_cleanup_to_analysis_script() 