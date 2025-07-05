#!/bin/bash

# Script to index books with automatic cleanup
# Usage: ./scripts/index_books.sh [--model local|gemini] [--mode new|all]

echo "📚 Starting ebook indexing with automatic cleanup..."

# Start Elasticsearch
echo "🔧 Starting Elasticsearch..."
docker-compose up -d elasticsearch

# Wait for Elasticsearch to be ready
echo "⏳ Waiting for Elasticsearch to be ready..."
while ! curl -s http://localhost:9200/_health >/dev/null 2>&1; do
    sleep 2
done
echo "✅ Elasticsearch is ready"

# Run the ebook processor with all passed arguments
echo "🚀 Running ebook indexer..."
docker-compose run --rm ebook-processor python src/ebook_processor.py "$@"

# Capture the exit code
EXIT_CODE=$?

# Remove Elasticsearch container completely
echo "🛑 Removing Elasticsearch container..."
docker-compose rm -f -s elasticsearch

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Indexing completed successfully and cleanup done!"
else
    echo "❌ Indexing failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE