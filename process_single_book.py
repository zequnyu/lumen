#!/usr/bin/env python3
"""
Process a single book with Gemini embeddings
"""
import sys
import os
import glob
sys.path.append('/app/src')

from ebook_processor import EbookProcessor

def process_book():
    # Find the Psychology of Money book
    files = glob.glob('/app/ebooks/*Morgan*')
    if not files:
        print("❌ Morgan Housel book not found!")
        return False
    
    test_file = files[0]
    print(f"📖 Processing: {os.path.basename(test_file)}")
    
    # Create processor with Gemini enabled
    processor = EbookProcessor(use_gemini=True)
    
    # Process the book
    book_data = processor.process_ebook(test_file)
    if not book_data:
        print("❌ Failed to extract text")
        return False
    
    print(f"✅ Title: {book_data['title']}")
    print(f"👤 Author: {book_data['author']}")
    print(f"📝 Content: {len(book_data['content'])} characters")
    
    # Create chunks
    documents = processor.split_text_into_chunks(book_data)
    print(f"📄 Created {len(documents)} chunks")
    
    # Store all chunks with Gemini embeddings
    print("🧮 Creating Gemini embeddings and storing in Elasticsearch...")
    success = processor.store_in_elasticsearch(documents, 1, 1)
    
    if success:
        print(f"✅ Successfully processed entire book with Gemini embeddings!")
        print(f"📊 Stored {len(documents)} chunks with 768-dimensional embeddings")
        return True
    else:
        print("❌ Failed to store in Elasticsearch")
        return False

if __name__ == "__main__":
    process_book()