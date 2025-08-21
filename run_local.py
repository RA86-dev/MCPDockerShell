#!/usr/bin/env python3
"""
Simple launcher for MCPDocker Enhanced without Docker containerization
"""

import sys
import os
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    required_packages = [
        "mcp",
        "docker",
        "fastapi",
        "uvicorn",
        "pydantic",
        "aiofiles",
        "psutil",
        "pyyaml",
        "cachetools",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("📦 Install with: pip install -r requirements-simple.txt")
        return False

    print("✅ All required dependencies found")
    return True


def check_docker():
    """Check if Docker is available"""
    print("🐳 Checking Docker availability...")

    try:
        result = subprocess.run(
            ["docker", "version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ Docker is available")
            return True
        else:
            print("❌ Docker is not running")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker is not installed or not accessible")
        return False


def setup_environment():
    """Setup the local environment"""
    print("🛠️ Setting up local environment...")

    # Create necessary directories
    directories = ["logs", "data", "config", "backups", "documentation"]
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)

    print("✅ Directory structure created")


def main():
    """Main function"""
    print("🚀 MCPDocker Enhanced - Local Runner")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check Docker
    if not check_docker():
        print("⚠️ Docker not available - some features will be limited")
        print("🔧 Install Docker Desktop to enable full functionality")

    # Setup environment
    setup_environment()

    print("\n🎯 Starting MCPDocker Enhanced...")
    print("🌐 The server will be available at: http://localhost:8080")
    print("📊 Configuration UI will be available at: http://localhost:8081")
    print("⏹️ Press Ctrl+C to stop the server")
    print("-" * 50)

    # Import and run the main server
    try:
        from main import main as main_server

        main_server()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("🔧 Check the logs for more details")
        sys.exit(1)


if __name__ == "__main__":
    main()
