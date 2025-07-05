#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    """Setup script to initialize the ebook MCP tool"""
    print("Setting up Ebook MCP Tool...")
    
    # Check if Docker is running
    print("Checking Docker...")
    if run_command("docker --version", "Docker version check") is None:
        print("Docker is not installed or not running. Please install Docker first.")
        sys.exit(1)
    
    # Build Docker image
    if run_command("docker-compose build", "Building Docker image") is None:
        print("Failed to build Docker image")
        sys.exit(1)
    
    # Start Elasticsearch
    if run_command("docker-compose up -d elasticsearch", "Starting Elasticsearch") is None:
        print("Failed to start Elasticsearch")
        sys.exit(1)
    
    # Wait for Elasticsearch to be ready
    print("Waiting for Elasticsearch to be ready...")
    import time
    time.sleep(30)
    
    # Check Elasticsearch health
    if run_command("curl -s localhost:9200/_cluster/health", "Checking Elasticsearch health") is None:
        print("Elasticsearch is not responding")
        sys.exit(1)
    
    print("\n✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Place your ebook files (.epub, .pdf) in the 'ebooks' directory")
    print("2. Run 'python src/ebook_processor.py' to process your ebooks")
    print("3. Configure Claude Desktop with the provided configuration")
    print("4. Start using the MCP server with Claude Desktop")

if __name__ == "__main__":
    main()