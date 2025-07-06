#!/bin/bash

# Script to run MCP server as a background service
# Usage: ./scripts/run_mcp_server.sh
# 
# The MCP server automatically searches ALL books regardless of embedding model used during indexing

echo "🚀 Starting MCP server as background service..."
echo "🔍 Will search all books from both local and Gemini embeddings automatically"

# Start both Elasticsearch and MCP server
echo "🔧 Starting Elasticsearch and MCP server..."
docker-compose up -d elasticsearch mcp-server

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch to be ready..."
while ! curl -s http://localhost:9200/_health >/dev/null 2>&1; do
    sleep 2
done
echo "✅ Elasticsearch is ready"

# Check MCP server status
echo "Checking MCP server status..."
sleep 3
if docker-compose ps mcp-server | grep -q "Up"; then
    echo "✅ MCP server is running and ready for Claude Desktop"
    echo "📋 To stop: docker-compose stop mcp-server"
    echo "📋 To view logs: docker-compose logs -f mcp-server"
else
    echo "❌ MCP server failed to start. Check logs:"
    docker-compose logs mcp-server
fi