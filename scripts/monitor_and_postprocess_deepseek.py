#!/usr/bin/env python3
"""
AUTOMATED DEEPSEEK R1 DISTILL MONITOR & POST-PROCESSOR

This script monitors for DeepSeek R1 Distill completion and automatically:
1. Detects when the distill process finishes
2. Runs post-processing to extract JSON from responses
3. Triggers comprehensive analysis update
4. Updates README.md and HTML automatically

Usage: python monitor_and_postprocess_deepseek.py
"""

import os
import time
import glob
import subprocess
import psutil
from pathlib import Path
from datetime import datetime

class DeepSeekDistillMonitor:
    def __init__(self):
        self.results_dir = Path("results/model_outputs")
        self.distill_process_name = "test_deepseek_r1_distill_qwen_7b.py"
        self.distill_output_pattern = "*deepseek*distill*.json"
        self.check_interval = 30  # Check every 30 seconds
        
    def is_distill_process_running(self):
        """Check if DeepSeek Distill process is still running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if self.distill_process_name in cmdline:
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None
    
    def find_distill_result_files(self):
        """Find DeepSeek Distill result files"""
        pattern = self.results_dir / self.distill_output_pattern
        files = list(glob.glob(str(pattern)))
        return files
    
    def get_file_age_minutes(self, filepath):
        """Get file age in minutes"""
        if not os.path.exists(filepath):
            return float('inf')
        file_time = os.path.getmtime(filepath)
        current_time = time.time()
        age_seconds = current_time - file_time
        return age_seconds / 60
    
    def run_post_processing(self, result_file):
        """Run post-processing on DeepSeek Distill results"""
        print(f"\n🔧 STARTING POST-PROCESSING")
        print("=" * 60)
        print(f"📁 Target file: {os.path.basename(result_file)}")
        
        try:
            # Run the post-processing script
            result = subprocess.run([
                'python', 'scripts/fix_deepseek_distill_responses.py'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ POST-PROCESSING SUCCESSFUL!")
                print(result.stdout)
                return True
            else:
                print("❌ POST-PROCESSING FAILED!")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ POST-PROCESSING TIMED OUT (5 minutes)")
            return False
        except Exception as e:
            print(f"❌ POST-PROCESSING ERROR: {e}")
            return False
    
    def trigger_comprehensive_analysis(self):
        """Trigger the comprehensive analysis system"""
        print(f"\n📊 TRIGGERING COMPREHENSIVE ANALYSIS UPDATE")
        print("=" * 60)
        
        try:
            result = subprocess.run([
                'python', 'auto_analyze_results.py'
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("✅ COMPREHENSIVE ANALYSIS UPDATED!")
                print("📝 README.md and HTML updated automatically")
                return True
            else:
                print("❌ ANALYSIS UPDATE FAILED!")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ ANALYSIS UPDATE TIMED OUT (10 minutes)")
            return False
        except Exception as e:
            print(f"❌ ANALYSIS UPDATE ERROR: {e}")
            return False
    
    def monitor_and_process(self):
        """Main monitoring loop"""
        print("🔍 DEEPSEEK R1 DISTILL MONITOR STARTED")
        print("=" * 60)
        print("👁️ Monitoring for DeepSeek R1 Distill completion...")
        print("🔧 Will auto-run post-processing when complete")
        print("📊 Will auto-update analysis and README")
        print("⏹️ Press Ctrl+C to stop monitoring")
        
        last_status_time = 0
        process_was_running = False
        
        while True:
            try:
                current_time = time.time()
                is_running, pid = self.is_distill_process_running()
                
                # Status update every 5 minutes
                if current_time - last_status_time > 300:
                    if is_running:
                        print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] DeepSeek Distill still running (PID: {pid})")
                    else:
                        print(f"\n⏸️ [{datetime.now().strftime('%H:%M:%S')}] DeepSeek Distill not running")
                    last_status_time = current_time
                
                # Track process state
                if is_running:
                    process_was_running = True
                elif process_was_running and not is_running:
                    # Process just finished!
                    print(f"\n🎉 DEEPSEEK DISTILL PROCESS COMPLETED!")
                    print("=" * 60)
                    
                    # Wait a moment for file to be fully written
                    print("⏳ Waiting 30 seconds for file completion...")
                    time.sleep(30)
                    
                    # Look for result files
                    result_files = self.find_distill_result_files()
                    
                    if result_files:
                        # Find the newest file
                        newest_file = max(result_files, key=os.path.getmtime)
                        file_age = self.get_file_age_minutes(newest_file)
                        
                        print(f"📁 Found result file: {os.path.basename(newest_file)}")
                        print(f"⏰ File age: {file_age:.1f} minutes")
                        
                        if file_age < 60:  # File created within last hour
                            # Run post-processing
                            success = self.run_post_processing(newest_file)
                            
                            if success:
                                # Wait for post-processed file to be created
                                print("⏳ Waiting for post-processed files...")
                                time.sleep(10)
                                
                                # Trigger comprehensive analysis
                                self.trigger_comprehensive_analysis()
                                
                                print(f"\n🎊 ALL PROCESSING COMPLETE!")
                                print("=" * 60)
                                print("✅ DeepSeek R1 Distill post-processed")
                                print("✅ Comprehensive analysis updated")
                                print("✅ README.md and HTML updated")
                                print("\n📈 Check results in:")
                                print("   - results/model_outputs/ (original + fixed)")
                                print("   - README.md (updated analysis)")
                                print("   - docs/LLM_LED_Optimization_Research_Results.html")
                                
                                # Exit after successful processing
                                return True
                            else:
                                print("❌ Post-processing failed - continuing to monitor")
                        else:
                            print(f"⚠️ File too old ({file_age:.1f} min) - continuing to monitor")
                    else:
                        print("📁 No DeepSeek Distill result files found - continuing to monitor")
                    
                    process_was_running = False
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print(f"\n⏹️ Monitoring stopped by user")
                return False
            except Exception as e:
                print(f"\n❌ Monitoring error: {e}")
                time.sleep(60)  # Wait longer on errors

if __name__ == "__main__":
    monitor = DeepSeekDistillMonitor()
    monitor.monitor_and_process() 