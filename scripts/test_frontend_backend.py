"""
Test the connection between frontend and backend
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def check_backend_health():
    """Check if backend is running and responsive"""
    try:
        response = requests.get("http://localhost:8000/api/v1/search/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not accessible: {e}")
        return False

def start_backend():
    """Start the backend server if not running"""
    if check_backend_health():
        return
    
    print("Starting backend server...")
    backend_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(Path(__file__).parent.parent),
    )
    
    # Wait for backend to start
    max_attempts = 10
    for attempt in range(max_attempts):
        print(f"Waiting for backend to start (attempt {attempt+1}/{max_attempts})...")
        time.sleep(2)
        if check_backend_health():
            return
    
    print("❌ Failed to start backend")
    sys.exit(1)

def check_frontend_env():
    """Check if frontend .env.local file has correct API URL"""
    env_path = Path(__file__).parent.parent / "frontend" / ".env.local"
    if not env_path.exists():
        print("❌ Frontend .env.local file not found")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    if "NEXT_PUBLIC_API_URL=http://localhost:8000" in content:
        print("✅ Frontend .env.local file has correct API URL")
        return True
    else:
        print("❌ Frontend .env.local file does not have correct API URL")
        # Fix it
        with open(env_path, 'w') as f:
            f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
            f.write("NEXT_PUBLIC_APP_NAME=Flipkart Search\n")
            f.write("NEXT_PUBLIC_APP_VERSION=1.0.0\n")
        print("✅ Updated frontend .env.local file with correct API URL")
        return True

def start_frontend():
    """Start the frontend server"""
    print("Starting frontend server...")
    frontend_dir = Path(__file__).parent.parent / "frontend"
    subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
    )
    print("✅ Frontend server started")
    print("You can access the frontend at http://localhost:3000")

if __name__ == "__main__":
    print("=== Testing Frontend-Backend Connection ===\n")
    
    # Check backend
    print("Checking backend...")
    start_backend()
    
    # Check frontend
    print("\nChecking frontend configuration...")
    check_frontend_env()
    
    # Start frontend
    print("\nStarting frontend...")
    start_frontend()
    
    print("\n=== Setup Complete ===")
    print("You can now access the search system at http://localhost:3000")
    print("Press Ctrl+C to stop the servers when done")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
