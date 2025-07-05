#!/usr/bin/env python3
"""
Test the new metadata tracking system
"""
import sys
import os
import glob
sys.path.append('/app/src')

from ebook_processor import EbookProcessor

def test_metadata_tracking():
    print("🧪 Testing new metadata tracking system\n")
    
    # Find a book to process
    files = glob.glob('/app/ebooks/*Morgan*')
    if not files:
        print("❌ No Morgan Housel book found!")
        return
    
    test_file = files[0]
    print(f"📖 Testing with: {os.path.basename(test_file)}")
    
    # Create processor with Gemini
    processor = EbookProcessor(use_gemini=True)
    
    # Test metadata generation
    metadata = processor.get_book_metadata(test_file)
    print(f"📝 Generated metadata: {metadata}")
    print()
    
    # Process the book
    book_data = processor.process_ebook(test_file)
    if not book_data:
        print("❌ Failed to extract text")
        return
    
    # Create a few chunks for testing
    documents = processor.split_text_into_chunks(book_data)
    test_docs = documents[:3]  # Just first 3 chunks
    
    print(f"✂️ Created {len(test_docs)} test chunks")
    
    # Test the tracking system
    print("💾 Testing metadata tracking...")
    
    # Load existing (should be empty)
    indexed_books = processor.load_indexed_books()
    print(f"📚 Current indexed books: {len(indexed_books)}")
    
    # Store the test chunks
    success = processor.store_in_elasticsearch(test_docs, 1, 1)
    if success:
        # Manually track the book to test metadata system
        book_metadata = processor.get_book_metadata(test_file)
        book_metadata['chunks'] = len(test_docs)
        book_metadata['title'] = book_data['title']
        book_metadata['author'] = book_data['author']
        indexed_books[test_file] = book_metadata
        
        # Save the metadata
        processor.save_indexed_books(indexed_books)
        
        print("✅ Successfully tracked book with metadata!")
        print(f"📊 Metadata: {book_metadata}")
        
        # Test loading it back
        loaded_books = processor.load_indexed_books()
        print(f"🔄 Reloaded: {len(loaded_books)} books")
        
        if test_file in loaded_books:
            print("✅ Metadata persistence confirmed!")
            loaded_metadata = loaded_books[test_file]
            print(f"📝 Loaded metadata: {loaded_metadata}")
        else:
            print("❌ Metadata not found after reload")
    else:
        print("❌ Failed to store chunks")

if __name__ == "__main__":
    test_metadata_tracking()