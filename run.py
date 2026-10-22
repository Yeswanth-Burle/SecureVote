"""
run.py - One-Click Launcher for SecureVote
Course: CSE494 - Intelligent NoSQL Databases
Project: SecureVote - Online Voting System using PyMongo & MongoDB
"""

import os
import sys
import webbrowser
import threading
import time
from database import setup_database, get_db
import seed_data

def check_mongodb():
    print("[1/4] Checking MongoDB connectivity...")
    db = get_db()
    if db is None:
        print("\n" + "!"*60)
        print(" [ERROR] Could not connect to local MongoDB server on port 27017!")
        print(" Please make sure the MongoDB service is running.")
        print(" Windows Command: net start MongoDB")
        print("!"*60 + "\n")
        sys.exit(1)
    print("  -> MongoDB connection active!")

def verify_or_seed_data():
    db = get_db()
    setup_database(drop_existing=False)
    voters_count = db.voters.count_documents({})
    print(f"[2/4] Voter registry status: {voters_count} registered voter(s). Ready for live sign-ups.")

def launch_browser():
    time.sleep(1.5)
    print("[4/4] Opening SecureVote interface in your default browser...")
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("="*65)
    print("   SECUREVOTE - Online Voting System (PyMongo & MongoDB)")
    print("   Lovely Professional University • CSE494 Academic Task 2")
    print("="*65)

    check_mongodb()
    verify_or_seed_data()

    print("[3/4] Starting Flask Web Server on http://127.0.0.1:5000...")
    threading.Thread(target=launch_browser, daemon=True).start()

    from app import app
    app.run(host="127.0.0.1", port=5000, debug=False)
