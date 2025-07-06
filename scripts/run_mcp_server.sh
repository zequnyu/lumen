#!/bin/bash

# Script to prepare the MCP server environment
# Usage: ./scripts/run_mcp_server.sh
# 
# The MCP server automatically searches ALL books regardless of embedding model used during indexing

echo "🚀 Preparing MCP server environment..."
echo "🔍 Will search all books from both local and Gemini embeddings automatically"

# Start only Elasticsearch (MCP server will be started by Claude Desktop)
echo "🔧 Starting Elasticsearch..."
docker-compose up -d elasticsearch

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch to be ready..."
while ! curl -s http://localhost:9200/_health >/dev/null 2>&1; do
    sleep 2
done
echo "✅ Elasticsearch is ready"

echo "✅ Environment is ready for MCP server"
echo "📋 The MCP server will be started by Claude Desktop when needed"
echo "📋 To stop Elasticsearch: docker-compose stop elasticsearch"
echo "📋 To test MCP server manually: ./start_mcp_server.sh"