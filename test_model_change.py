#!/usr/bin/env python3
"""
Test embedding model change detection
"""
import sys
import os
sys.path.append('/app/src')

from ebook_processor import EbookProcessor

def test_model_change_detection():
    print("🔄 Testing embedding model change detection\n")
    
    # Test 1: Load with Gemini (should match existing)
    print("1️⃣ Testing Gemini processor (should match existing book):")
    processor_gemini = EbookProcessor(use_gemini=True)
    indexed_books = processor_gemini.load_indexed_books()
    
    if indexed_books:
        book_path = list(indexed_books.keys())[0]
        should_reprocess = processor_gemini.should_reprocess_book(book_path, indexed_books)
        print(f"   Book: {os.path.basename(book_path)}")
        print(f"   Stored model: {indexed_books[book_path]['embedding_model']}")
        print(f"   Current model: gemini")
        print(f"   Should reprocess: {should_reprocess} ✅" if not should_reprocess else f"   Should reprocess: {should_reprocess} ❌")
        print()
    
    # Test 2: Load with local model (should detect mismatch)
    print("2️⃣ Testing local processor (should detect model mismatch):")
    processor_local = EbookProcessor(use_gemini=False)
    
    if indexed_books:
        book_path = list(indexed_books.keys())[0]
        should_reprocess = processor_local.should_reprocess_book(book_path, indexed_books)
        print(f"   Book: {os.path.basename(book_path)}")
        print(f"   Stored model: {indexed_books[book_path]['embedding_model']}")
        print(f"   Current model: sentence-transformers")
        print(f"   Should reprocess: {should_reprocess} ✅" if should_reprocess else f"   Should reprocess: {should_reprocess} ❌")
        print()
    
    # Test 3: Test with new book (should always reprocess)
    print("3️⃣ Testing new book (should always reprocess):")
    fake_new_book = "/fake/path/new_book.epub"
    should_reprocess = processor_gemini.should_reprocess_book(fake_new_book, indexed_books)
    print(f"   Book: new_book.epub")
    print(f"   In index: False")
    print(f"   Should reprocess: {should_reprocess} ✅" if should_reprocess else f"   Should reprocess: {should_reprocess} ❌")
    print()
    
    # Test 4: Show metadata details
    print("4️⃣ Current indexed book metadata:")
    if indexed_books:
        for book_path, metadata in indexed_books.items():
            print(f"   📖 {os.path.basename(book_path)}")
            print(f"   🧮 Model: {metadata['embedding_model']} ({metadata['dimensions']}D)")
            print(f"   📄 Chunks: {metadata['chunks']}")
            print(f"   🕒 Timestamp: {metadata['timestamp']}")

if __name__ == "__main__":
    test_model_change_detection()