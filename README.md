# Lumen

AI-powered ebook search via MCP.

## Quick Start

**Prerequisites:**

-   [Docker Desktop](https://docs.docker.com/get-docker/)
-   MCP client ([Claude Desktop](https://claude.ai/download), Cline, etc.)

### 1. Install

```bash
bash <(curl -sSL https://raw.githubusercontent.com/zequnyu/lumen/main/install.sh)
```

### 2. Add Books

```bash
cp ~/Downloads/*.epub ~/lumen-ebooks/     # Copy your ebooks
lumen index                               # Index them
```

### 3. Use

Open your MCP client and ask: _"How many books are in my library?"_

### 4. Uninstall

```bash
bash <(curl -sSL https://raw.githubusercontent.com/zequnyu/lumen/main/uninstall.sh)
```

## Commands

```bash
lumen index                       # Index new books only (default)
lumen index --mode all            # Index all books (full reindex)
lumen index --model gemini        # Use Gemini embeddings (requires GEMINI_API_KEY)
lumen index --mode all --model gemini  # Full reindex with Gemini
lumen stop                        # Stop all containers
lumen --help                      # Show all options
```

**Indexing Modes:**

-   `new` (default) - Only index books not already processed
-   `all` - Reindex all books in library

**Embedding Models:**

-   `local` (default) - Fast SentenceTransformers model
-   `gemini` - Higher quality Google Gemini embeddings

## Features

-   **AI-Powered Search** - Ask natural language questions about your books
-   **Multiple Formats** - EPUB and PDF support with metadata extraction
-   **Smart Indexing** - Only processes new books by default
-   **Embedding Models** - Local (fast) or Google Gemini (better quality)
-   **Complete Isolation** - Everything runs in Docker containers
-   **Auto-Configuration** - MCP client setup is automatic

## Development

**Architecture:**

-   **Lumen CLI** (`lumen.py`) - Unified command tool with Docker lifecycle management
-   **MCP Server** (`src/mcp_server.py`) - MCP client integration
-   **Ebook Processor** (`src/ebook_processor.py`) - Text extraction and embedding generation
-   **Elasticsearch** - Vector database for book chunks and search

**For developers working on Lumen:**

```bash
# Clone repository
git clone https://github.com/zequnyu/lumen.git
cd lumen

# Development workflow
docker-compose run --rm lumen index --mode all --model local
docker-compose run --rm lumen index --mode all --model gemini
docker-compose run --rm lumen start
docker-compose run --rm lumen stop
docker-compose run --rm lumen --help

# Build and test
docker-compose build
docker-compose up -d elasticsearch
docker-compose run --rm lumen python -m pytest tests/
docker-compose down

# Debug and troubleshoot
docker-compose logs elasticsearch
docker-compose exec lumen bash
docker ps | grep lumen
```

**Environment Variables:**

-   `GEMINI_API_KEY` - Required for Gemini embeddings
-   `ELASTICSEARCH_URL` - Elasticsearch connection (default: http://elasticsearch:9200)

**Embedding Models:**
| Model | Speed | Quality | API Required |
|-------|-------|---------|--------------|
| Local (SentenceTransformers) | Fast | Good | No |
| Google Gemini | Slower | Better | Yes |

---

_Transform your ebook collection into an AI-searchable library! 📚_
