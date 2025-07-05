import asyncio
import json
import logging
import os
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
    def __init__(self, elasticsearch_url: str = None, index_name: str = "ebooks", model: str = "gemini"):
        self.elasticsearch_url = elasticsearch_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.index_name = index_name
        self.es_client = Elasticsearch([self.elasticsearch_url])
        self.model = model
        
        # Initialize embedding model
        if self.model == "gemini":
            if not os.getenv("GEMINI_API_KEY"):
                raise ValueError("GEMINI_API_KEY environment variable is required for Gemini model")
            self.embedding_model = None
        elif self.model == "local":
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            raise ValueError(f"Unsupported model: {self.model}")
        
    def create_embeddings(self, text: str):
        """Create embeddings for text using the specified model"""
        if self.model == "gemini":
            try:
                import google.generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY environment variable not set")
                
                genai.configure(api_key=api_key)
                
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text
                )
                return result['embedding']
            except Exception as e:
                logger.error(f"Gemini embedding failed: {e}")
                raise
        elif self.model == "local":
            return self.embedding_model.encode(text).tolist()
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    async def search_ebooks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant ebook content using vector similarity"""
        try:
            # Create query embedding
            query_embedding = self.create_embeddings(query)
            
            # Elasticsearch query
            search_query = {
                "size": limit,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embeddings') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                },
                "_source": ["title", "author", "content", "file_path", "file_type"]
            }
            
            response = self.es_client.search(index=self.index_name, body=search_query)
            
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                results.append({
                    'content': source.get('content', ''),
                    'title': source.get('title', 'Unknown'),
                    'author': source.get('author', 'Unknown'),
                    'file_type': source.get('file_type', 'Unknown'),
                    'score': hit['_score']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching ebooks: {str(e)}")
            return []
    
    async def get_book_list(self) -> List[Dict[str, Any]]:
        """Get list of all books in the database"""
        try:
            # Use scroll to efficiently get all unique books
            books_dict = {}
            
            # Initial search with scroll
            search_query = {
                "size": 1000,
                "_source": ["title", "author", "file_type", "total_chunks"],
                "query": {"match_all": {}}
            }
            
            response = self.es_client.search(
                index=self.index_name, 
                body=search_query,
                scroll='2m'
            )
            
            scroll_id = response['_scroll_id']
            hits = response['hits']['hits']
            
            # Process initial batch
            for hit in hits:
                source = hit['_source']
                key = (source.get('title', 'Unknown'), source.get('author', 'Unknown'))
                if key not in books_dict:
                    books_dict[key] = {
                        'title': source.get('title', 'Unknown'),
                        'author': source.get('author', 'Unknown'),
                        'file_type': source.get('file_type', 'Unknown'),
                        'chunks': source.get('total_chunks', 0)
                    }
            
            # Continue scrolling until no more hits
            while len(hits) > 0:
                response = self.es_client.scroll(scroll_id=scroll_id, scroll='2m')
                scroll_id = response['_scroll_id']
                hits = response['hits']['hits']
                
                for hit in hits:
                    source = hit['_source']
                    key = (source.get('title', 'Unknown'), source.get('author', 'Unknown'))
                    if key not in books_dict:
                        books_dict[key] = {
                            'title': source.get('title', 'Unknown'),
                            'author': source.get('author', 'Unknown'),
                            'file_type': source.get('file_type', 'Unknown'),
                            'chunks': source.get('total_chunks', 0)
                        }
            
            # Clean up scroll
            self.es_client.clear_scroll(scroll_id=scroll_id)
            
            return list(books_dict.values())
            
        except Exception as e:
            logger.error(f"Error getting book list: {str(e)}")
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
            
            response = self.es_client.search(index=self.index_name, body=search_query)
            
            if not response['hits']['hits']:
                return {"error": f"Book '{title}' not found"}
            
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
                    f"({book['file_type']}, {book['chunks']} chunks)"
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