#!/bin/bash
set -e

# Lumen Containerized Installation Script
# Everything runs in Docker - no files stored on host except ebooks

echo "🌟 Installing Lumen (Fully Containerized) - AI-powered ebook search via MCP"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    echo "📋 Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is required but not installed."
    echo "📋 Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Set directories
EBOOKS_DIR="$HOME/lumen-ebooks"
LUMEN_DATA_DIR="$HOME/.lumen-data"

echo "📚 Ebooks directory: $EBOOKS_DIR"
echo "💾 Lumen data directory: $LUMEN_DATA_DIR"
echo

# Create directories
mkdir -p "$EBOOKS_DIR"
mkdir -p "$LUMEN_DATA_DIR"

# Pull pre-built Lumen Docker image
echo "⬇️  Pulling Lumen Docker image..."
docker pull zequnyu/lumen:latest
docker tag zequnyu/lumen:latest lumen:latest

# Create temporary docker-compose for installation
cat > /tmp/lumen-install-compose.yml << 'EOF'
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ulimits:
      memlock:
        soft: -1
        hard: -1
    ports:
      - "9200:9200"
    networks:
      - lumen-network

  lumen:
    image: lumen:latest
    depends_on:
      - elasticsearch
    volumes:
      - ${LUMEN_EBOOKS_DIR}:/app/ebooks
      - ${LUMEN_DATA_DIR}:/app/data
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - PYTHONPATH=/app
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    env_file:
      - /app/data/.env
    entrypoint: ["python3", "/app/lumen.py"]
    networks:
      - lumen-network

networks:
  lumen-network:
    driver: bridge
EOF

# Image pulled successfully

# Create global lumen command that uses Docker
echo "🔧 Creating global lumen command..."
sudo tee /usr/local/bin/lumen > /dev/null << EOF
#!/bin/bash

# Lumen fully containerized wrapper
EBOOKS_DIR="$EBOOKS_DIR"
LUMEN_DATA_DIR="$LUMEN_DATA_DIR"

# Ensure directories exist
mkdir -p "\$EBOOKS_DIR"
mkdir -p "\$LUMEN_DATA_DIR"

# Show helpful message for first-time users
if [ "\$1" = "" ]; then
    echo "🌟 Lumen - AI-powered ebook search via MCP"
    echo
    echo "📚 Your ebooks directory: \$EBOOKS_DIR"
    echo
    echo "🚀 Quick start:"
    echo "  1. Add .epub/.pdf files to: \$EBOOKS_DIR"
    echo "  2. lumen index --mode all"
    echo "  3. lumen start"
    echo "  4. Use your MCP client to search your books!"
    echo
    echo "💡 Commands:"
    echo "  lumen index          # Index new books"
    echo "  lumen start          # Start MCP server"
    echo "  lumen stop           # Stop and cleanup"
    echo "  lumen --help         # Show all options"
    echo
    exit 0
fi

# Run Lumen in Docker with proper volume mounts
LUMEN_EBOOKS_DIR="\$EBOOKS_DIR" LUMEN_DATA_DIR="\$LUMEN_DATA_DIR" \\
docker-compose -f /tmp/lumen-install-compose.yml -p lumen run --rm lumen "\$@"
EOF

sudo chmod +x /usr/local/bin/lumen

# Create MCP server startup script (containerized)
echo "🔧 Creating containerized MCP server script..."
MCP_SCRIPT="$LUMEN_DATA_DIR/start_mcp_server.sh"
cat > "$MCP_SCRIPT" << EOF
#!/bin/bash
# Containerized MCP server startup script

EBOOKS_DIR="$EBOOKS_DIR"
LUMEN_DATA_DIR="$LUMEN_DATA_DIR"

# Check if Elasticsearch is already running, if not start it
if ! curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "Starting Elasticsearch..." >&2
    LUMEN_EBOOKS_DIR="\$EBOOKS_DIR" LUMEN_DATA_DIR="\$LUMEN_DATA_DIR" \\
    docker-compose -f /tmp/lumen-install-compose.yml -p lumen up -d elasticsearch >&2
    
    # Wait for Elasticsearch to be ready
    echo "Waiting for Elasticsearch to be ready..." >&2
    for i in {1..30}; do
        if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
            echo "Elasticsearch is ready" >&2
            break
        fi
        sleep 2
    done
else
    echo "Elasticsearch is already running" >&2
fi

# Start MCP server
LUMEN_EBOOKS_DIR="\$EBOOKS_DIR" LUMEN_DATA_DIR="\$LUMEN_DATA_DIR" \\
docker-compose -f /tmp/lumen-install-compose.yml -p lumen run --rm \\
    --entrypoint "python3" lumen /app/src/mcp_server.py
EOF
chmod +x "$MCP_SCRIPT"

# Configure MCP client (Claude Desktop by default)
echo "⚙️  Configuring MCP client (Claude Desktop)..."
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Create Claude config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Backup existing config if it exists
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup.$(date +%s)"
    echo "📋 Backed up existing MCP client config"
fi

# Create or update Claude Desktop config
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    # Update existing config
    python3 -c "
import json
import sys

config_file = '$CLAUDE_CONFIG_FILE'
try:
    with open(config_file, 'r') as f:
        config = json.load(f)
except:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['lumen'] = {
    'command': '$MCP_SCRIPT',
    'args': []
}

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print('✅ Updated MCP client configuration')
"
else
    # Create new config
    cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "lumen": {
      "command": "$MCP_SCRIPT",
      "args": []
    }
  }
}
EOF
    echo "✅ Created MCP client configuration"
fi

echo
echo "🎉 Lumen (Containerized) installation completed!"
echo
echo "🐳 Everything runs in Docker containers - no files on your host system!"
echo
echo "📋 Next steps:"
echo "1. Add your ebook files (.epub, .pdf) to: $EBOOKS_DIR"
echo "2. Index your books: lumen index --mode all"
echo "3. Start Lumen: lumen start"
echo "4. Open your MCP client and start searching your books!"
echo
echo "💡 Useful commands:"
echo "  lumen index          # Index new books"
echo "  lumen start          # Start MCP server"
echo "  lumen stop           # Stop and cleanup"
echo "  lumen --help         # Show all options"
echo
echo "📚 Your ebooks go in: $EBOOKS_DIR"
echo "💾 Lumen data stored in: $LUMEN_DATA_DIR"
echo "🐳 Everything else runs in containers!"
echo