#!/usr/bin/env python3
"""
Production deployment script for LeetCoach backend
"""
import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        sys.exit(1)
    
    print("✅ Environment variables check passed")

def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def run_migrations():
    """Run database migrations"""
    try:
        # Create migrations directory if it doesn't exist
        migrations_dir = Path("migrations")
        migrations_dir.mkdir(exist_ok=True)
        
        # Initialize alembic if not already done
        if not (migrations_dir / "alembic.ini").exists():
            subprocess.run(["alembic", "init", "migrations"], check=True, capture_output=True)
        
        # Run migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True)
        print("✅ Database migrations completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run migrations: {e}")
        sys.exit(1)

def start_gunicorn():
    """Start the application with Gunicorn"""
    # Gunicorn configuration
    workers = os.getenv("GUNICORN_WORKERS", "4")
    bind = os.getenv("BIND_ADDRESS", "0.0.0.0:8000")
    timeout = os.getenv("TIMEOUT", "120")
    
    cmd = [
        "gunicorn",
        "main:app",
        "--workers", workers,
        "--bind", bind,
        "--timeout", timeout,
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--log-level", "info"
    ]
    
    print(f"🚀 Starting LeetCoach with Gunicorn...")
    print(f"   Workers: {workers}")
    print(f"   Bind: {bind}")
    print(f"   Timeout: {timeout}s")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main deployment function"""
    print("🏗️  Deploying LeetCoach Backend...")
    
    # Check environment
    check_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Run migrations
    run_migrations()
    
    # Start server
    start_gunicorn()

if __name__ == "__main__":
    main() 