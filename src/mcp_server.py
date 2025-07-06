import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EbookMCPServer:
    def __init__(self, elasticsearch_url: str = None):
        self.elasticsearch_url = elasticsearch_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.es_client = Elasticsearch([self.elasticsearch_url])
        
        # Use all three indices to find all books
        self.local_index = "ebooks_local"
        self.gemini_index = "ebooks_gemini"
        self.legacy_index = "ebooks"  # Old index that might contain additional books
        self.all_indices = [self.local_index, self.gemini_index, self.legacy_index]
        
        # Initialize both embedding models for comprehensive search
        self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Try to initialize Gemini if API key is available
        self.has_gemini = os.getenv("GEMINI_API_KEY") is not None
        if not self.has_gemini:
            logger.info("GEMINI_API_KEY not set, will only search local embeddings index")
        
    def create_local_embedding(self, text: str):
        """Create local embedding using SentenceTransformers"""
        return self.local_model.encode(text).tolist()
    
    def create_gemini_embedding(self, text: str):
        """Create Gemini embedding if available"""
        if not self.has_gemini:
            return None
        
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return None
            
            genai.configure(api_key=api_key)
            
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text
            )
            return result['embedding']
        except Exception as e:
            logger.warning(f"Gemini embedding failed: {e}")
            return None

    async def search_ebooks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant ebook content across all available indices"""
        try:
            all_results = []
            
            # Create embeddings for both models
            local_embedding = self.create_local_embedding(query)
            gemini_embedding = self.create_gemini_embedding(query) if self.has_gemini else None
            
            # Search local index with local embeddings
            try:
                local_query = {
                    "size": limit,
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embeddings') + 1.0",
                                "params": {"query_vector": local_embedding}
                            }
                        }
                    },
                    "_source": ["title", "author", "content", "file_path", "file_type"]
                }
                
                response = self.es_client.search(index=self.local_index, body=local_query)
                for hit in response['hits']['hits']:
                    source = hit['_source']
                    all_results.append({
                        'content': source.get('content', ''),
                        'title': source.get('title', 'Unknown'),
                        'author': source.get('author', 'Unknown'),
                        'file_type': source.get('file_type', 'Unknown'),
                        'score': hit['_score'],
                        'source': 'local_embeddings'
                    })
            except Exception as e:
                logger.info(f"Local index search failed (expected if empty): {e}")
            
            # Search Gemini index with Gemini embeddings (if available)
            if gemini_embedding:
                try:
                    gemini_query = {
                        "size": limit,
                        "query": {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'embeddings') + 1.0",
                                    "params": {"query_vector": gemini_embedding}
                                }
                            }
                        },
                        "_source": ["title", "author", "content", "file_path", "file_type"]
                    }
                    
                    response = self.es_client.search(index=self.gemini_index, body=gemini_query)
                    for hit in response['hits']['hits']:
                        source = hit['_source']
                        all_results.append({
                            'content': source.get('content', ''),
                            'title': source.get('title', 'Unknown'),
                            'author': source.get('author', 'Unknown'),
                            'file_type': source.get('file_type', 'Unknown'),
                            'score': hit['_score'],
                            'source': 'gemini_embeddings'
                        })
                except Exception as e:
                    logger.info(f"Gemini index search failed (expected if empty): {e}")
            
            # Sort all results by score and deduplicate by (title, author)
            seen_books = set()
            unique_results = []
            
            for result in sorted(all_results, key=lambda x: x['score'], reverse=True):
                book_key = (result['title'], result['author'])
                if book_key not in seen_books:
                    seen_books.add(book_key)
                    unique_results.append(result)
            
            # Return top results up to limit
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching ebooks: {str(e)}")
            return []
    
    async def get_book_list(self) -> List[Dict[str, Any]]:
        """Get list of all books from indexed_books.json - simple and efficient!"""
        try:
            # Read the indexed books file directly - much simpler than querying Elasticsearch
            indexed_books_path = "/app/indexed_books.json"
            
            try:
                with open(indexed_books_path, 'r') as f:
                    indexed_books = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Indexed books file not found: {indexed_books_path}")
                return []
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in indexed books file: {indexed_books_path}")
                return []
            
            # Convert to book list format
            books = []
            for file_path, book_data in indexed_books.items():
                books.append({
                    'title': book_data.get('title', 'Unknown'),
                    'author': book_data.get('author', 'Unknown'),
                    'file_type': 'epub',  # Assuming epub for now
                    'total_chunks': book_data.get('chunks', 0),
                    'embedding_model': book_data.get('embedding_model', 'unknown'),
                    'dimensions': book_data.get('dimensions', 0),
                    'timestamp': book_data.get('timestamp', '')
                })
            
            logger.info(f"Found {len(books)} books in indexed_books.json")
            return books
            
        except Exception as e:
            logger.error(f"Error reading indexed books file: {str(e)}")
            return []
    
    async def get_book_summary(self, title: str) -> Dict[str, Any]:
        """Get summary information about a specific book"""
        try:
            # Search for all chunks of the book
            search_query = {
                "query": {
                    "match": {
                        "title": title
                    }
                },
                "size": 1000,
                "_source": ["title", "author", "file_type", "content"]
            }
            
            # Search all indices for comprehensive results
            indices_to_search = ["ebooks_local", "ebooks"]  # Include legacy index
            if self.has_gemini:
                indices_to_search.append("ebooks_gemini")
            
            all_hits = []
            for index_name in indices_to_search:
                try:
                    response = self.es_client.search(index=index_name, body=search_query)
                    all_hits.extend(response['hits']['hits'])
                except Exception as e:
                    logger.warning(f"Could not search index {index_name}: {e}")
            
            if not all_hits:
                return {"error": f"Book '{title}' not found"}
            
            response = {'hits': {'hits': all_hits}}
            
            
            # Get book metadata from first hit
            first_hit = response['hits']['hits'][0]['_source']
            
            # Calculate statistics
            total_chunks = len(response['hits']['hits'])
            total_chars = sum(len(hit['_source'].get('content', '')) for hit in response['hits']['hits'])
            
            return {
                'title': first_hit.get('title', 'Unknown'),
                'author': first_hit.get('author', 'Unknown'),
                'file_type': first_hit.get('file_type', 'Unknown'),
                'total_chunks': total_chunks,
                'total_characters': total_chars,
                'estimated_pages': total_chars // 2000  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Error getting book summary: {str(e)}")
            return {"error": str(e)}

# Initialize the MCP server
server = Server("ebook-mcp-server")
logger.info("Starting MCP server (searches all books from both embedding models)")
ebook_server = EbookMCPServer()

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="search_ebooks",
            description="Search for relevant content across all ebooks using semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant ebook content"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="list_books",
            description="Get a list of all books available in the database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_book_summary",
            description="Get detailed information about a specific book",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the book to get summary for"
                    }
                },
                "required": ["title"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        if name == "search_ebooks":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text="Error: Query parameter is required"
                )]
            
            results = await ebook_server.search_ebooks(query, limit)
            
            if not results:
                return [types.TextContent(
                    type="text",
                    text="No relevant content found for your query."
                )]
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                content = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
                
                formatted_results.append(
                    f"**Result {i}** (Score: {result['score']:.3f})\n"
                    f"**Book:** {result['title']}\n"
                    f"**Author:** {result['author']}\n"
                    f"**Content:**\n{content}\n"
                )
            
            return [types.TextContent(
                type="text",
                text="\n---\n".join(formatted_results)
            )]
            
        elif name == "list_books":
            books = await ebook_server.get_book_list()
            
            if not books:
                return [types.TextContent(
                    type="text",
                    text="No books found in the database."
                )]
            
            formatted_books = []
            for book in books:
                formatted_books.append(
                    f"**{book['title']}** by {book['author']} "
                    f"({book['file_type']}, {book['total_chunks']} chunks)"
                )
            
            return [types.TextContent(
                type="text",
                text="**Available Books:**\n" + "\n".join(formatted_books)
            )]
            
        elif name == "get_book_summary":
            title = arguments.get("title", "")
            
            if not title:
                return [types.TextContent(
                    type="text",
                    text="Error: Title parameter is required"
                )]
            
            summary = await ebook_server.get_book_summary(title)
            
            if "error" in summary:
                return [types.TextContent(
                    type="text",
                    text=f"Error: {summary['error']}"
                )]
            
            formatted_summary = (
                f"**Book Summary**\n"
                f"**Title:** {summary['title']}\n"
                f"**Author:** {summary['author']}\n"
                f"**File Type:** {summary['file_type']}\n"
                f"**Total Chunks:** {summary['total_chunks']}\n"
                f"**Total Characters:** {summary['total_characters']:,}\n"
                f"**Estimated Pages:** {summary['estimated_pages']}"
            )
            
            return [types.TextContent(
                type="text",
                text=formatted_summary
            )]
            
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Main function to run the MCP server"""
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ebook-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())