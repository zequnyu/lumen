# Ebook MCP Tool

Query your ebook collection using Claude Desktop through the Model Context Protocol (MCP). This tool processes EPUB and PDF files, creates semantic embeddings (using Google Gemini or local models), and provides intelligent search capabilities through Claude Desktop.

## Features

- **Semantic Search**: Search across your entire ebook collection using natural language queries
- **Google Gemini Integration**: Uses Google Gemini embeddings for superior search quality
- **Local Model Fallback**: Falls back to local SentenceTransformer models when Gemini is unavailable
- **Docker-based**: Runs in Docker containers for easy deployment and dependency management
- **Elasticsearch Backend**: Fast, scalable search with Elasticsearch
- **MCP Integration**: Seamlessly integrates with Claude Desktop

## Project Structure

```
ebook-mcp-tool/
├── src/                    # Source code
│   ├── ebook_processor.py  # Main processing logic
│   └── mcp_server.py       # MCP server implementation
├── tests/                  # Test files
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── scripts/               # Utility scripts
│   ├── process_single_book.py  # Process individual books
│   └── run_mcp_server.sh      # Start MCP server
├── ebooks/               # Your ebook files (EPUB/PDF)
├── data/                 # Generated data and indexes
├── docker-compose.yml    # Docker services configuration
└── requirements.txt      # Python dependencies
```

## How to Start Server and Run Claude Desktop

### 1. Start Docker Services (Elasticsearch)
```bash
# Start Elasticsearch and other services
docker-compose up -d elasticsearch
```

### 2. Start the MCP Server
```bash
./scripts/run_mcp_server.sh
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
./scripts/run_mcp_server.sh
```

### Step 5: Verify in Claude Desktop
- The new books should now appear when you ask Claude to list available books
- You can search across all books including the new ones

**Important**: Always restart the MCP server after adding new books for them to be available in Claude Desktop.

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (optional, falls back to local embeddings)
- `ELASTICSEARCH_URL`: Elasticsearch URL (default: http://localhost:9200)
- `PYTHONPATH`: Python path for imports

### Gemini Embeddings

For best search quality, set up Google Gemini embeddings:

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)
2. Set the environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
3. The system will automatically use Gemini embeddings when available

## Testing

The project includes comprehensive tests organized into unit and integration tests:

### Run All Tests
```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

### Test Individual Components
```bash
# Test embedding models
python tests/unit/test_models.py

# Test search functionality
python tests/integration/test_search.py

# Verify Gemini integration
python tests/integration/verify_gemini.py
```

## Utility Scripts

### Process Single Book
```bash
# Process a specific book for testing
python scripts/process_single_book.py
```

### Start MCP Server
```bash
# Start the MCP server
./scripts/run_mcp_server.sh
```

## Troubleshooting

### Common Issues

**Elasticsearch Connection Issues**
```bash
# Check if Elasticsearch is running
docker-compose ps

# View Elasticsearch logs
docker-compose logs elasticsearch

# Restart Elasticsearch
docker-compose restart elasticsearch
```

**MCP Server Not Responding**
```bash
# Check server logs
docker-compose logs ebook-processor

# Restart the MCP server
./scripts/run_mcp_server.sh
```

**Books Not Appearing**
1. Ensure books are in the `ebooks/` directory
2. Re-run the book processing: `docker-compose run --rm ebook-processor python src/ebook_processor.py`
3. Restart the MCP server: `./scripts/run_mcp_server.sh`

**Gemini API Issues**
- Verify your API key is set: `echo $GEMINI_API_KEY`
- Check API quota and billing in Google AI Studio
- The system will fall back to local embeddings if Gemini fails

### Debug Mode

Run tests with debug output:
```bash
# Test Elasticsearch connectivity
python tests/integration/test_es.py

# Test embedding generation
python tests/unit/test_models.py

# Verify Gemini configuration
python tests/integration/verify_gemini.py
```