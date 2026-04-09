#!/usr/bin/env python3
"""
Sports Betting Daily Runner
Runs soccer and hockey reports for today, then starts the dashboards
"""

import subprocess
import sys
import os
import time
from datetime import datetime

PROJECT_DIR = "/Users/dickgibbons/AI Projects/sports-betting"
DATE = datetime.now().strftime('%Y-%m-%d')

def run_command(cmd, description, background=False):
    """Run a shell command and handle output"""
    print(f"\n{'=' * 80}")
    print(f"⚡ {description}")
    print(f"{'=' * 80}")
    
    if background:
        # Run in background with nohup
        log_file = f"{PROJECT_DIR}/logs/{description.lower().replace(' ', '_')}_{DATE}.log"
        os.makedirs(f"{PROJECT_DIR}/logs", exist_ok=True)
        cmd = f"cd {PROJECT_DIR} && nohup {cmd} > {log_file} 2>&1 &"
        print(f"   Running in background (log: {log_file})")
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0
    else:
        # Run in foreground
        print(f"   Command: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=PROJECT_DIR)
        success = result.returncode == 0
        if success:
            print(f"   ✅ {description} completed successfully")
        else:
            print(f"   ❌ {description} failed (exit code: {result.returncode})")
        return success

def check_port_in_use(port):
    """Check if a port is already in use"""
    result = subprocess.run(
        f"lsof -ti:{port}",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def kill_process_on_port(port):
    """Kill process running on a specific port"""
    result = subprocess.run(
        f"lsof -ti:{port} | xargs kill -9 2>/dev/null",
        shell=True
    )
    return result.returncode == 0

def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("🏆 SPORTS BETTING - DAILY RUNNER")
    print("=" * 80)
    print(f"Date: {DATE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Create necessary directories
    os.makedirs(f"{PROJECT_DIR}/logs", exist_ok=True)
    os.makedirs(f"{PROJECT_DIR}/reports/{DATE}", exist_ok=True)
    
    success_count = 0
    total_steps = 5
    
    # STEP 1: Run Soccer Daily Reports
    print("\n" + "=" * 80)
    print("⚽ STEP 1: RUNNING SOCCER DAILY REPORTS")
    print("=" * 80)
    soccer_success = run_command(
        "./run_soccer_daily.sh",
        "Soccer Daily Reports",
        background=False
    )
    if soccer_success:
        success_count += 1
    
    # STEP 2: Run Hockey Daily Reports
    print("\n" + "=" * 80)
    print("🏒 STEP 2: RUNNING HOCKEY DAILY REPORTS")
    print("=" * 80)
    hockey_success = run_command(
        "./run_hockey_daily.sh",
        "Hockey Daily Reports",
        background=False
    )
    if hockey_success:
        success_count += 1
    
    # STEP 3: Start Soccer Dashboard
    print("\n" + "=" * 80)
    print("🌐 STEP 3: STARTING SOCCER DASHBOARD")
    print("=" * 80)
    
    # Check if soccer dashboard is already running (ports 8502 or 8504)
    soccer_ports = [8502, 8504]
    soccer_running = any(check_port_in_use(port) for port in soccer_ports)
    
    if soccer_running:
        print("   ℹ️  Soccer dashboard already running")
        for port in soccer_ports:
            if check_port_in_use(port):
                print(f"   ✅ Port {port} is in use")
        success_count += 1  # Count as completed if already running
    else:
        # Kill any existing soccer dashboard processes
        subprocess.run("pkill -f soccer_dashboard.py", shell=True)
        time.sleep(1)
        
        # Start soccer dashboard (try 8504 version first, fallback to 8502)
        if os.path.exists(f"{PROJECT_DIR}/dashboards/soccer/soccer_dashboard_8504.py"):
            dashboard_script = "dashboards/soccer/soccer_dashboard_8504.py"
            port = 8504
        else:
            dashboard_script = "dashboards/soccer/soccer_dashboard.py"
            port = 8502
        
        dashboard_success = run_command(
            f"python3 {dashboard_script}",
            f"Soccer Dashboard (port {port})",
            background=True
        )
        
        if dashboard_success:
            success_count += 1
            time.sleep(3)  # Give it time to start
            print(f"   🌐 Soccer Dashboard: http://127.0.0.1:{port}")
    
    # STEP 4: Generate Consolidated CSV
    print("\n" + "=" * 80)
    print("📊 STEP 4: GENERATING CONSOLIDATED SELECTIONS CSV")
    print("=" * 80)
    csv_success = run_command(
        "python3 core/consolidated_daily_selections.py",
        "Consolidated Daily Selections CSV",
        background=False
    )
    if csv_success:
        success_count += 1
    
    # STEP 5: Start Hockey Dashboard
    print("\n" + "=" * 80)
    print("🌐 STEP 5: STARTING HOCKEY DASHBOARD")
    print("=" * 80)
    
    hockey_port = 8501
    hockey_running = check_port_in_use(hockey_port)
    
    if hockey_running:
        print(f"   ℹ️  Hockey dashboard already running on port {hockey_port}")
        success_count += 1  # Count as completed if already running
    else:
        # Kill any existing hockey dashboard processes
        subprocess.run("pkill -f hockey_dashboard.py", shell=True)
        time.sleep(1)
        
        dashboard_success = run_command(
            "python3 dashboards/hockey/hockey_dashboard.py",
            f"Hockey Dashboard (port {hockey_port})",
            background=True
        )
        
        if dashboard_success:
            success_count += 1
            time.sleep(3)  # Give it time to start
            print(f"   🌐 Hockey Dashboard: http://127.0.0.1:{hockey_port}")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"✅ Completed: {success_count}/{total_steps} steps")
    print(f"\n📁 Reports saved to: {PROJECT_DIR}/reports/{DATE}/")
    print(f"📊 Consolidated CSV: {PROJECT_DIR}/daily_selections_consolidated.csv")
    print(f"\n🌐 Dashboards:")
    
    # Check which dashboards are running
    for port in [8501, 8502, 8504]:
        if check_port_in_use(port):
            sport = "Hockey" if port == 8501 else "Soccer"
            print(f"   ✅ {sport} Dashboard: http://127.0.0.1:{port}")
    
    print("\n" + "=" * 80)
    print("🎉 SPORTS BETTING DAILY RUN COMPLETE")
    print("=" * 80)
    
    return 0 if success_count == total_steps else 1

if __name__ == '__main__':
    sys.exit(main())
