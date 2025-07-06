#!/usr/bin/env python3
"""
Lumen CLI - Unified command tool for ebook MCP server management
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
import time
from typing import Optional, List

# Constants
ELASTICSEARCH_HEALTH_ENDPOINT = "_health"
DEFAULT_MAX_RETRIES = 30
DEFAULT_RETRY_DELAY = 2


class LumenCLI:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.in_docker = os.path.exists('/.dockerenv')
        
        # Ensure we're running inside Docker
        if not self.in_docker:
            print("❌ Error: Lumen must be run via Docker Compose")
            print("📋 Use: docker-compose run --rm lumen [command]")
            print("📋 Available commands: index, start, stop")
            sys.exit(1)
        
    def run_command(self, command: str, description: str, capture_output: bool = False) -> bool | str:
        """Run a command and handle errors"""
        print(f"Running: {description}")
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, cwd=self.project_root)
                return result.stdout.strip()
            else:
                subprocess.run(command, shell=True, check=True, cwd=self.project_root)
            print(f"✓ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ {description} failed: {e}")
            if capture_output and e.stderr:
                print(f"Error output: {e.stderr}")
            return False

    def _wait_for_elasticsearch(self, es_url: str, max_retries: int = DEFAULT_MAX_RETRIES) -> bool:
        """Wait for Elasticsearch to become ready"""
        print("⏳ Waiting for Elasticsearch to be ready...")
        
        for i in range(max_retries):
            # Wait before checking (except first attempt)
            if i > 0:
                time.sleep(DEFAULT_RETRY_DELAY)
            
            # Silent health check
            try:
                result = subprocess.run(f"curl -s {es_url}/{ELASTICSEARCH_HEALTH_ENDPOINT}", 
                                      shell=True, capture_output=True, check=True, 
                                      cwd=self.project_root)
                if result.returncode == 0:
                    print("✅ Elasticsearch is ready")
                    return True
            except subprocess.CalledProcessError:
                # Continue trying silently
                pass
        
        print("❌ Elasticsearch failed to become ready after waiting")
        return False

    def _start_elasticsearch(self) -> bool:
        """Start Elasticsearch container if not already running"""
        # When running inside Docker, Elasticsearch is managed by Docker Compose
        return True

    def _cleanup_elasticsearch(self) -> None:
        """Clean up Elasticsearch container"""
        print("🛑 Stopping and removing Elasticsearch container...")
        # Stop and remove the Elasticsearch container that was started for this operation
        commands = [
            ("docker stop ebook-elasticsearch", "Stopping Elasticsearch container"),
            ("docker rm ebook-elasticsearch", "Removing Elasticsearch container"),
        ]
        
        for command, description in commands:
            self.run_command(command, description)

    def _print_server_ready_message(self) -> None:
        """Print server ready message with next steps"""
        print("✅ Environment is ready for MCP server")
        print("📋 The MCP server will be started by Claude Desktop when needed")
        if not self.in_docker:
            print("📋 To stop Elasticsearch: docker-compose stop elasticsearch")
            print("📋 To test MCP server manually: ./start_mcp_server.sh")
        print("\n✅ Lumen is ready for Claude Desktop!")
        print("📋 Next steps:")
        print("1. Make sure Claude Desktop is configured with the MCP server")
        print("2. Open Claude Desktop and start using the ebook search functionality")
        print("3. Use 'lumen stop' to clean up when done")


    def index_books(self, mode: str = "new", model: str = "local") -> bool:
        """Index books with automatic cleanup"""
        print("📚 Starting ebook indexing with automatic cleanup...")
        print(f"📚 Indexing books with mode: {mode}, model: {model}")
        
        # Start Elasticsearch and wait for it to be ready
        if not self._start_elasticsearch():
            return False
        
        if not self._wait_for_elasticsearch("http://elasticsearch:9200"):
            return False
        
        # Build and run the ebook processor command
        args = []
        if mode:
            args.extend(["--mode", mode])
        if model:
            args.extend(["--model", model])
        
        print("🚀 Running ebook indexer...")
        command = f"python src/ebook_processor.py {' '.join(args)}"
        
        success = self.run_command(command, f"Indexing books with {mode} mode and {model} model")
        
        # Always clean up, regardless of success or failure
        self._cleanup_elasticsearch()
        
        if success:
            print("✅ Indexing completed successfully and cleanup done!")
        else:
            print("❌ Indexing failed but cleanup completed")
        
        return success

    def start_server(self) -> bool:
        """Start the MCP server environment for Claude Desktop"""
        print("🚀 Preparing MCP server environment...")
        print("🔍 Will search all books from both local and Gemini embeddings automatically")
        
        print("✅ Elasticsearch should already be running due to Docker Compose dependencies")
        es_url = "http://elasticsearch:9200"
        
        # Wait for Elasticsearch to be ready
        if not self._wait_for_elasticsearch(es_url):
            return False
        
        self._print_server_ready_message()
        return True

    def stop_server(self) -> bool:
        """Stop and clean up the MCP server environment"""
        print("🛑 Stopping Lumen MCP server environment...")
        
        commands = [
            ("docker-compose stop", "Stopping all Docker containers"),
            ("docker-compose down", "Removing Docker containers"),
        ]
        
        success = True
        for command, description in commands:
            if not self.run_command(command, description):
                success = False
        
        if success:
            print("\n✅ Lumen environment stopped and cleaned up!")
        else:
            print("\n⚠️  Some cleanup steps may have failed")
        
        return success


def main():
    parser = argparse.ArgumentParser(description="Lumen CLI - Ebook MCP server management tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index ebooks')
    index_parser.add_argument('--mode', choices=['new', 'all'], default='new', 
                             help='Indexing mode: new (only new books) or all (reindex all books)')
    index_parser.add_argument('--model', choices=['local', 'gemini'], default='local',
                             help='Embedding model: local (SentenceTransformers) or gemini (Google Gemini)')
    
    
    # Start command
    subparsers.add_parser('start', help='Start MCP server environment for Claude Desktop')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop and clean up MCP server environment')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = LumenCLI()
    
    try:
        if args.command == 'index':
            success = cli.index_books(mode=args.mode, model=args.model)
        elif args.command == 'start':
            success = cli.start_server()
        elif args.command == 'stop':
            success = cli.stop_server()
        else:
            parser.print_help()
            return
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()