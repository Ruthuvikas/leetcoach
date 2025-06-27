#!/usr/bin/env python3
"""
Development startup script for LeetCoach backend
"""
import os
import sys
import subprocess

def main():
    """Start the development server"""
    # Set development environment variables
    os.environ["ALLOW_DEFAULT_SECRET"] = "true"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Set a default OpenAI API key if not provided (for development)
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-development"
        print("⚠️  Warning: Using dummy OpenAI API key for development")
        print("   Set OPENAI_API_KEY environment variable for real AI features")
    
    print("🚀 Starting LeetCoach Backend in Development Mode...")
    print("   Debug: Enabled")
    print("   Log Level: DEBUG")
    print("   Secret Key: Using default (allowed in dev)")
    
    try:
        # Start uvicorn with development settings
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "debug"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start development server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 