# Ebook MCP Tool

Query your ebook collection using Claude Desktop through the Model Context Protocol (MCP).

## How to Start Server and Run Claude Desktop

### 1. Start Docker Services (Elasticsearch)
```bash
# Start Elasticsearch and other services
docker-compose up -d elasticsearch
```

### 2. Start the MCP Server
```bash
./run_mcp_server.sh
```

### 3. Configure Claude Desktop
Add this to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "ebook-mcp-server": {
      "command": "python",
      "args": ["/Users/zequnyu/Documents/ebook-mcp-tool/src/mcp_server.py"],
      "env": {
        "ELASTICSEARCH_URL": "http://localhost:9200",
        "PYTHONPATH": "/Users/zequnyu/Documents/ebook-mcp-tool"
      }
    }
  }
}
```

**Note**: Update the path `/Users/zequnyu/Documents/ebook-mcp-tool` to match your actual project location.

### How to Restart the MCP Server
If you need to restart the MCP server:

1. **Stop the server**: Press `Ctrl+C` in the terminal where the server is running
2. **Start it again**: Run `./run_mcp_server.sh`

## What to Do When You Add a New Book

**Follow these 5 steps exactly every time you add a new book:**

### Step 1: Add Book File
```bash
# Place your new EPUB or PDF file in the ebooks directory
cp new-book.epub ebooks/
```

### Step 2: Start Docker Services (if not already running)
```bash
# Make sure Elasticsearch is running
docker-compose up -d elasticsearch
```

### Step 3: Process the New Book
```bash
# This processes ALL books (existing + new ones)
docker-compose run --rm ebook-processor python src/ebook_processor.py
```

### Step 4: Restart MCP Server
```bash
# Restart the server to pick up new books
./run_mcp_server.sh
```

### Step 5: Verify in Claude Desktop
- The new books should now appear when you ask Claude to list available books
- You can search across all books including the new ones

**Important**: Always restart the MCP server after adding new books for them to be available in Claude Desktop.