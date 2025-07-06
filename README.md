# Ebook MCP Tool

Search your ebooks with AI using Claude Desktop's MCP integration.

## Quick Start

**First time setup:**
```bash
# Index your books
docker-compose run --rm lumen index --mode all

# Start the server for Claude Desktop
docker-compose run --rm lumen start
```

**Adding new books:**
1. Drop your `.epub` or `.pdf` file in `ebooks/` folder
2. Run: `docker-compose run --rm lumen index --mode new`
3. New book is immediately available in Claude Desktop

**Daily usage:**
```bash
# Start when you want to use Claude Desktop
docker-compose run --rm lumen start

# Stop when done
docker-compose run --rm lumen stop
```

## Lumen Commands

### Index Books

Index your ebook collection for search:

```bash
# Index only new books with local embeddings (default)
docker-compose run --rm lumen index

# Index all books (reindex everything)
docker-compose run --rm lumen index --mode all

# Use Gemini embeddings instead of local
docker-compose run --rm lumen index --model gemini

# Combine options
docker-compose run --rm lumen index --mode all --model gemini
```

**Options:**
- `--mode {new,all}`: 
  - `new` (default): Only index books that haven't been indexed before
  - `all`: Reindex all books, including previously indexed ones
- `--model {local,gemini}`:
  - `local` (default): Use SentenceTransformers local embeddings (384D)
  - `gemini`: Use Google Gemini embeddings (768D, requires GEMINI_API_KEY)

### Start Server

Start the MCP server environment for Claude Desktop:

```bash
docker-compose run --rm lumen start
```

This command:
- Starts Elasticsearch in Docker
- Waits for Elasticsearch to be ready
- Prepares the environment for Claude Desktop to connect
- Shows next steps for using Claude Desktop

### Stop Server

Stop and clean up the MCP server environment:

```bash
docker-compose run --rm lumen stop
```

This command:
- Stops all Docker containers
- Removes Docker containers completely
- Cleans up the environment

### Get Help

```bash
docker-compose run --rm lumen --help
docker-compose run --rm lumen index --help
```

## Typical Workflow

1. **First time setup:**
   ```bash
   # Index your books
   docker-compose run --rm lumen index --mode all
   
   # Start the server for Claude Desktop
   docker-compose run --rm lumen start
   ```

2. **Adding new books:**
   ```bash
   # Add new ebooks to the ebooks/ directory
   # Index only the new books
   docker-compose run --rm lumen index --mode new
   ```

3. **Daily usage:**
   ```bash
   # Start when you want to use Claude Desktop
   docker-compose run --rm lumen start
   
   # Stop when done
   docker-compose run --rm lumen stop
   ```

## Environment Variables

- `GEMINI_API_KEY`: Required when using `--model gemini`
- `ELASTICSEARCH_URL`: Override Elasticsearch URL (default: http://localhost:9200)

## File Support

- **EPUB files**: Full support with metadata extraction
- **PDF files**: Full support with metadata extraction
- Both formats support chunking and embedding generation

## Architecture

- **Lumen CLI**: Unified command tool that manages everything
- **Elasticsearch**: Stores book chunks with vector embeddings
- **MCP Server**: Claude Desktop connects to search your books
- **indexed_books.json**: Registry of all your books with metadata
- **Automatic Cleanup**: All commands handle Docker lifecycle automatically

## Advanced Features

- **Multi-model Support**: Index books with different embedding models simultaneously
- **Smart Indexing**: Only processes new books by default to save time
- **Automatic Cleanup**: All operations clean up Docker containers automatically
- **Universal Search**: MCP server searches across all books regardless of embedding model used
- **Metadata Tracking**: Tracks embedding model, dimensions, timestamps, and chunk counts

## Embedding Models

| Model | Dimensions | Speed | Quality | API Required |
|-------|------------|-------|---------|--------------|
| Local (SentenceTransformers) | 384D | Fast | Good | No |
| Google Gemini | 768D | Slower | Better | Yes (GEMINI_API_KEY) |

## Notes

- The `lumen start` command prepares the environment but doesn't start the MCP server directly - that's handled by Claude Desktop
- You can have books indexed with different embedding models simultaneously
- The MCP server automatically searches across all indexed books regardless of which embedding model was used
- All Lumen commands handle Docker container lifecycle automatically
- Use `docker-compose run --rm lumen stop` to clean up when you're done working

That's it! Drop books in `ebooks/`, run the indexer, search in Claude Desktop.