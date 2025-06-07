#!/usr/bin/env python3
"""
File Watcher for Automatic Results Generation

This script monitors the results/model_outputs directory and automatically 
runs the analysis generation script when new JSON files are added.

Usage:
    python scripts/watch_model_outputs.py
    
The script will run continuously and process new files as they appear.
Press Ctrl+C to stop the watcher.
"""

import time
import os
import sys
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
BASE_DIR = Path(__file__).parent.parent  # Go up to project root
MODEL_OUTPUTS_DIR = BASE_DIR / "results" / "model_outputs"
AUTO_GENERATE_SCRIPT = BASE_DIR / "scripts" / "auto_generate_results.py"

class ModelOutputHandler(FileSystemEventHandler):
    """Handler for monitoring model output files."""
    
    def __init__(self):
        self.processed_files = set()
        # Initialize with existing files to avoid reprocessing
        if MODEL_OUTPUTS_DIR.exists():
            self.processed_files.update(
                f.name for f in MODEL_OUTPUTS_DIR.glob("*.json")
            )
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process JSON files
        if file_path.suffix.lower() != '.json':
            return
        
        # Avoid processing the same file multiple times
        if file_path.name in self.processed_files:
            return
        
        print(f"\n🔍 New model output detected: {file_path.name}")
        
        # Wait a moment to ensure file is fully written
        time.sleep(2)
        
        # Verify file is complete and readable
        if self.is_file_complete(file_path):
            self.process_new_file(file_path)
            self.processed_files.add(file_path.name)
        else:
            print(f"⚠ File {file_path.name} appears incomplete, skipping for now")
    
    def on_moved(self, event):
        """Handle file move events (in case files are moved into the directory)."""
        if event.is_directory:
            return
        
        dest_path = Path(event.dest_path)
        
        # Only process JSON files moved into our monitored directory
        if (dest_path.suffix.lower() == '.json' and 
            dest_path.parent == MODEL_OUTPUTS_DIR and
            dest_path.name not in self.processed_files):
            
            print(f"\n📁 Model output moved into directory: {dest_path.name}")
            self.process_new_file(dest_path)
            self.processed_files.add(dest_path.name)
    
    def is_file_complete(self, file_path):
        """Check if file is complete and readable."""
        try:
            # Try to read the file and parse as JSON to ensure it's complete
            with open(file_path, 'r') as f:
                import json
                json.load(f)
            return True
        except (json.JSONDecodeError, IOError):
            return False
    
    def process_new_file(self, file_path):
        """Process a new model output file."""
        print(f"🚀 Starting automatic analysis for: {file_path.name}")
        
        try:
            # Run the auto-generate script
            result = subprocess.run([
                sys.executable, str(AUTO_GENERATE_SCRIPT), file_path.name
            ], cwd=BASE_DIR, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully processed {file_path.name}")
                print("📊 Generated files:")
                print("   - Analysis summary JSON")
                print("   - Comparison Excel file")
                print("   - Statistical analysis (if applicable)")
                print("   - Performance figures (if applicable)")
            else:
                print(f"❌ Error processing {file_path.name}:")
                print(result.stderr)
        
        except Exception as e:
            print(f"❌ Exception while processing {file_path.name}: {e}")

def main():
    """Main function to start the file watcher."""
    print("🔍 Model Output File Watcher")
    print("=" * 50)
    print(f"Monitoring directory: {MODEL_OUTPUTS_DIR}")
    print(f"Auto-generate script: {AUTO_GENERATE_SCRIPT}")
    print()
    
    # Check if directories exist
    if not MODEL_OUTPUTS_DIR.exists():
        print(f"❌ Error: Model outputs directory does not exist: {MODEL_OUTPUTS_DIR}")
        print("Please create the directory first.")
        sys.exit(1)
    
    if not AUTO_GENERATE_SCRIPT.exists():
        print(f"❌ Error: Auto-generate script not found: {AUTO_GENERATE_SCRIPT}")
        sys.exit(1)
    
    # Ensure model_outputs directory exists
    MODEL_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set up file watcher
    event_handler = ModelOutputHandler()
    observer = Observer()
    observer.schedule(event_handler, str(MODEL_OUTPUTS_DIR), recursive=False)
    
    # Start monitoring
    observer.start()
    print(f"👀 Watching for new model output files...")
    print("   - Supported formats: *.json")
    print("   - Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping file watcher...")
        observer.stop()
    
    observer.join()
    print("✅ File watcher stopped.")

if __name__ == "__main__":
    # Check if watchdog is installed
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("❌ Error: watchdog package is required for file monitoring.")
        print("Install it with: pip install watchdog")
        sys.exit(1)
    
    main() 