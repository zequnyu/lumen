#!/bin/bash

# This script starts the MCP server for Claude Desktop
# Claude Desktop will call this script directly

cd /Users/zequnyu/Documents/ebook-mcp-tool

# Ensure Elasticsearch is running
docker-compose up -d elasticsearch >/dev/null 2>&1

# Wait for Elasticsearch to be ready
while ! curl -s http://localhost:9200/_health >/dev/null 2>&1; do
    sleep 1
done

# Run the MCP server in the foreground for Claude Desktop
docker-compose run --rm ebook-processor python src/mcp_server.py