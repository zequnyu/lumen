#!/usr/bin/env python3
"""
Test the search functionality with Gemini embeddings
"""
import sys
import os
sys.path.append('../../src')

from mcp_server import EbookMCPServer
import asyncio

async def test_search():
    print("🔍 Testing Ebook Search with Gemini Embeddings\n")
    
    # Create server instance
    server = EbookMCPServer()
    print(f"Using Gemini: {server.use_gemini}")
    print(f"API Key set: {'GEMINI_API_KEY' in os.environ}")
    print()
    
    # Test searches
    test_queries = [
        "What is compound interest?",
        "How to invest money wisely?", 
        "psychology of spending",
        "wealth building strategies"
    ]
    
    for query in test_queries:
        print(f"🔍 Searching: '{query}'")
        results = await server.search_ebooks(query, limit=3)
        
        if results:
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"   {i}. Score: {result['score']:.3f}")
                print(f"      Book: {result['title']}")
                print(f"      Content: {result['content'][:100]}...")
                print()
        else:
            print("   ❌ No results found")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(test_search())