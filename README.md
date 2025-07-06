# Ebook MCP Tool

Search your ebooks with AI using Claude Desktop's MCP integration.

## Quick Start

**Using the system:**
- Just open Claude Desktop - it automatically starts all services and you can search your books!

**Adding new books:**
1. Drop your `.epub` file in `ebooks/` folder
2. Run: `docker-compose run --rm ebook-processor python src/ebook_processor.py`
3. New book is immediately available in Claude Desktop

## Commands

**Index with local embeddings (default):**
```bash
docker-compose run --rm ebook-processor python src/ebook_processor.py
```

**Index with Gemini embeddings:**
```bash
docker-compose run --rm ebook-processor python src/ebook_processor.py --model gemini
```

**View indexed books:**
```bash
cat indexed_books.json
```

**Stop services when done:**
```bash
docker-compose stop
```

## How it Works

- **Elasticsearch**: Stores book chunks with vector embeddings
- **MCP Server**: Claude Desktop connects to search your books
- **indexed_books.json**: Registry of all your books (used for book listing)

That's it! Drop books in `ebooks/`, run the indexer, search in Claude Desktop.