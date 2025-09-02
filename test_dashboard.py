#!/usr/bin/env python3
"""
Test script to verify the dashboard integration works
"""
import subprocess
import time
import requests
import signal
import os

def test_dashboard():
    """Test the integrated dashboard"""
    print("🧪 Testing MCP Docker Server Dashboard Integration")
    
    # Start the server with dashboard enabled
    print("⚡ Starting MCP server with dashboard enabled...")
    server_process = subprocess.Popen([
        "python", "main.py", 
        "--transport", "sse",
        "--port", "8001",
        "--enable-dashboard"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        # Wait a moment for server to start
        time.sleep(3)
        
        # Test dashboard endpoint
        print("📊 Testing dashboard endpoint...")
        try:
            response = requests.get("http://localhost:8001/dashboard", timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard endpoint working!")
                if "MCP Docker Server Dashboard" in response.text:
                    print("✅ Dashboard HTML contains expected content!")
                else:
                    print("❌ Dashboard HTML missing expected content")
            else:
                print(f"❌ Dashboard endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Dashboard endpoint error: {e}")
        
        # Test API endpoints
        api_endpoints = [
            "/api/mcp-info",
            "/api/system-status", 
            "/api/gpu-status",
            "/api/docker-containers",
            "/api/health-check"
        ]
        
        for endpoint in api_endpoints:
            try:
                print(f"🔍 Testing {endpoint}...")
                response = requests.get(f"http://localhost:8001{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {endpoint} working!")
                else:
                    print(f"❌ {endpoint} failed: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} error: {e}")
        
        print("\n🎉 Dashboard integration test completed!")
        print("📋 To use the dashboard:")
        print("   1. Start the server: python main.py --transport sse --enable-dashboard")
        print("   2. Open browser: http://localhost:8000/dashboard")
        
    finally:
        # Clean up
        print("🧹 Cleaning up test server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

if __name__ == "__main__":
    test_dashboard()