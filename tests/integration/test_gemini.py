#!/usr/bin/env python3
"""
Quick test script for Gemini embeddings on a single file
"""
import sys
import os
sys.path.append('../../src')

from ebook_processor import EbookProcessor

def test_single_file():
    # Find the Psychology of Money book
    import glob
    files = glob.glob('../../ebooks/*Morgan*')
    if not files:
        print("❌ Morgan Housel book not found!")
        return False
    test_file = files[0]
    
    print(f"🧪 Testing Gemini embeddings with: {test_file}")
    
    # Create processor with Gemini enabled
    processor = EbookProcessor(use_gemini=True)
    
    print(f"📝 Using Gemini: {processor.use_gemini}")
    print(f"🔑 API Key set: {'GEMINI_API_KEY' in os.environ}")
    
    # Process the single file
    print("📖 Extracting text...")
    book_data = processor.process_ebook(test_file)
    
    if not book_data:
        print("❌ Failed to extract text")
        return False
    
    print(f"✅ Extracted text: {len(book_data['content'])} characters")
    print(f"📚 Title: {book_data['title']}")
    print(f"👤 Author: {book_data['author']}")
    
    # Create chunks
    print("✂️ Creating chunks...")
    documents = processor.split_text_into_chunks(book_data)
    print(f"📄 Created {len(documents)} chunks")
    
    # Test embedding creation for first chunk
    print("🧮 Testing embedding creation...")
    try:
        first_chunk = documents[0]['content']
        embeddings = processor.create_embeddings(first_chunk)
        print(f"✅ Created embeddings: {len(embeddings)} dimensions")
        print(f"📊 Sample values: {embeddings[:5]}")
        
        # Store just the first few chunks to test ES
        print("💾 Testing Elasticsearch storage...")
        test_docs = documents[:3]  # Just first 3 chunks
        success = processor.store_in_elasticsearch(test_docs, 1, 1)
        
        if success:
            print("✅ Successfully stored test chunks in Elasticsearch!")
            return True
        else:
            print("❌ Failed to store in Elasticsearch")
            return False
            
    except Exception as e:
        print(f"❌ Error creating embeddings: {e}")
        return False

if __name__ == "__main__":
    test_single_file()