# Lumen

Search your ebooks with AI using MCP (Model Context Protocol) integration.

**🐳 Fully Containerized** - Easy one-command installation with complete Docker isolation.

## ⚡ Quick Install & Use

### **Prerequisites**
- **Docker Desktop** - [Install from docker.com](https://docs.docker.com/get-docker/)
- **MCP-Compatible Client** - Such as Claude Desktop, Cline, or other MCP clients

### **Installation (5 minutes)**

```bash
# 1. Install Lumen
curl -sSL https://raw.githubusercontent.com/zequnyu/lumen/main/install.sh | bash

# 2. Add your ebooks
cp ~/Downloads/*.epub ~/lumen-ebooks/
cp ~/Downloads/*.pdf ~/lumen-ebooks/

# 3. Index your books
lumen index --mode all

# 4. IMPORTANT: Restart your MCP client
# For Claude Desktop: Quit completely (Cmd+Q), then reopen
# For other MCP clients: Restart according to client documentation

# 5. Start Lumen
lumen start

# 6. Use your MCP client!
# Ask: "What does Morgan Housel say about compound interest?"
```

### **Daily Usage**
```bash
# Add new books
cp new-book.epub ~/lumen-ebooks/
lumen index          # Index new books (fast)

# Use with your MCP client
lumen start          # Start when needed
lumen stop           # Stop when done
```

## 📚 Features

- **AI-Powered Search** - Ask natural language questions about your books
- **Multiple Formats** - EPUB and PDF support with metadata extraction
- **Smart Indexing** - Only processes new books by default
- **Embedding Models** - Local (fast) or Google Gemini (better quality)
- **Complete Isolation** - Everything runs in Docker containers
- **Auto-Configuration** - MCP client setup is automatic

## 💡 Commands

```bash
lumen index --mode all     # Index all books
lumen index --model gemini # Use Gemini embeddings (requires GEMINI_API_KEY)
lumen start               # Start MCP server
lumen stop                # Stop and cleanup all containers
lumen --help              # Show all options
```

**Note:** `lumen stop` now properly cleans up all Docker containers and resources.

## 🗑️ Uninstall

**Complete Removal (preserves your ebooks):**
```bash
curl -sSL https://raw.githubusercontent.com/zequnyu/lumen/main/uninstall.sh | bash
```

**What gets removed:**
- Lumen command (`/usr/local/bin/lumen`)
- All Docker containers and images
- Lumen data directory (`~/.lumen-data`)
- MCP client configuration

**What's preserved:**
- Your ebooks in `~/lumen-ebooks/` (safe to keep)

**To reinstall later:**
```bash
curl -sSL https://raw.githubusercontent.com/zequnyu/lumen/main/install.sh | bash
```

## 🆘 Troubleshooting

**MCP client not finding books?**
```bash
# 1. Make sure you restarted your MCP client after installation
# 2. Check if Lumen is running:
lumen start

# 3. Verify your MCP client configuration has been updated
# Check your MCP client documentation for config file location
```

**Want to start fresh?** See the [Uninstall section](#🗑️-uninstall) above for complete removal and reinstallation.

## 📁 File Locations

- **Your ebooks**: `~/lumen-ebooks/` (add .epub/.pdf files here)
- **Lumen data**: `~/.lumen-data/` (indexed metadata)
- **MCP config**: Check your MCP client documentation for config location

---

## 🛠️ Development

**For developers working on Lumen:**

### **Local Development Setup**

```bash
# Clone repository
git clone https://github.com/zequnyu/lumen.git
cd lumen

# Development workflow
docker-compose run --rm lumen index --mode all
docker-compose run --rm lumen start
docker-compose run --rm lumen stop
```

### **Docker Compose Commands**

```bash
# Index books (development)
docker-compose run --rm lumen index --mode all --model local
docker-compose run --rm lumen index --mode all --model gemini

# Start MCP server environment
docker-compose run --rm lumen start

# Stop and cleanup
docker-compose run --rm lumen stop

# Get help
docker-compose run --rm lumen --help
```

### **Architecture**

- **Lumen CLI** (`lumen.py`) - Unified command tool with Docker lifecycle management
- **MCP Server** (`src/mcp_server.py`) - MCP client integration
- **Ebook Processor** (`src/ebook_processor.py`) - Text extraction and embedding generation
- **Elasticsearch** - Vector database for book chunks and search
- **Docker Compose** - Development environment orchestration

### **Environment Variables**

- `GEMINI_API_KEY` - Required for Gemini embeddings
- `ELASTICSEARCH_URL` - Elasticsearch connection (default: http://elasticsearch:9200)

### **Embedding Models**

| Model | Dimensions | Speed | Quality | API Required |
|-------|------------|-------|---------|--------------|
| Local (SentenceTransformers) | 384D | Fast | Good | No |
| Google Gemini | 768D | Slower | Better | Yes (GEMINI_API_KEY) |

### **Development Notes**

- All commands enforce Docker-only execution for consistency
- Elasticsearch lifecycle is automatically managed (startup/cleanup)
- Books are chunked into ~1000 character segments with 200 character overlap
- Supports both new book indexing and full reindexing
- MCP server searches across all indexed books regardless of embedding model used

---

*Transform your ebook collection into an AI-searchable library accessible through any MCP client! 📚✨*