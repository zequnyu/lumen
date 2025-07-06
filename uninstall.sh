#!/bin/bash
set -e

# Lumen Uninstall Script
# Removes all Lumen components and data

echo "🗑️  Uninstalling Lumen - AI-powered ebook search via MCP"
echo
echo "⚠️  WARNING: This will remove:"
echo "   - Lumen command (/usr/local/bin/lumen)"
echo "   - Docker containers and images"
echo "   - Lumen data directory (~/.lumen-data)"
echo "   - MCP client configuration"
echo
echo "📚 NOTE: Your ebooks in ~/lumen-ebooks/ will NOT be deleted"
echo

# Ask for confirmation
read -p "Are you sure you want to uninstall Lumen? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Uninstall cancelled"
    exit 0
fi

echo "🧹 Starting uninstall process..."
echo

# Stop any running Lumen containers
echo "🛑 Stopping Lumen containers..."
docker-compose -f /tmp/lumen-install-compose.yml -p lumen down --remove-orphans 2>/dev/null || true

# Remove Docker images
echo "🐳 Removing Docker images..."
docker rmi lumen:latest 2>/dev/null || true
docker rmi zequnyu/lumen:latest 2>/dev/null || true
docker rmi docker.elastic.co/elasticsearch/elasticsearch:8.11.0 2>/dev/null || true

# Remove Docker volumes
echo "📦 Removing Docker volumes..."
docker volume rm lumen_elasticsearch_data 2>/dev/null || true

# Remove global lumen command
echo "🗑️  Removing lumen command..."
sudo rm -f /usr/local/bin/lumen

# Remove Lumen data directory
echo "💾 Removing Lumen data directory..."
rm -rf ~/.lumen-data

# Remove temporary docker-compose file
echo "🧹 Cleaning up temporary files..."
rm -f /tmp/lumen-install-compose.yml

# Remove MCP configuration (backup first)
CLAUDE_CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    echo "⚙️  Removing MCP configuration..."
    
    # Backup the config
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup.$(date +%s)"
    echo "📋 Backed up MCP client config"
    
    # Remove Lumen from config using Python
    python3 -c "
import json
import sys

config_file = '$CLAUDE_CONFIG_FILE'
try:
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if 'mcpServers' in config and 'lumen' in config['mcpServers']:
        del config['mcpServers']['lumen']
        
        # If mcpServers is now empty, remove it
        if not config['mcpServers']:
            del config['mcpServers']
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print('✅ SUCCESS: Removed Lumen from MCP client configuration')
    else:
        print('ℹ️  INFO: Lumen not found in MCP client configuration')
        
except Exception as e:
    print(f'⚠️  WARNING: Could not modify MCP client config: {e}')
"
fi

# Remove MCP server startup script
rm -f ~/.lumen-data/start_mcp_server.sh 2>/dev/null || true

echo
echo "✅ SUCCESS: Lumen uninstall completed!"
echo
echo "📚 NOTE: Your ebooks in ~/lumen-ebooks/ have been preserved"
echo "ℹ️  INFO: You may need to restart your MCP client for changes to take effect"
echo
echo "🔄 To reinstall Lumen later:"
echo "   curl -sSL https://raw.githubusercontent.com/zequnyu/lumen/main/install.sh | bash"