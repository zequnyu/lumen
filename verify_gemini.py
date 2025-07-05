#!/usr/bin/env python3
"""
Comprehensive verification that Gemini embeddings are being used
"""
import sys
import os
sys.path.append('/app/src')

from ebook_processor import EbookProcessor
from elasticsearch import Elasticsearch

def verify_gemini_usage():
    print("🔍 VERIFICATION: Checking if Gemini embeddings are being used\n")
    
    # 1. Check processor configuration
    processor = EbookProcessor()
    print(f"1️⃣ Processor configuration:")
    print(f"   - use_gemini: {processor.use_gemini}")
    print(f"   - API key present: {'GEMINI_API_KEY' in os.environ}")
    print(f"   - API key value: {os.environ.get('GEMINI_API_KEY', 'NOT SET')[:15]}...")
    print()
    
    # 2. Test embedding creation directly
    print(f"2️⃣ Direct embedding test:")
    test_text = "Money is a tool for managing risk and uncertainty."
    try:
        embeddings = processor.create_embeddings(test_text)
        print(f"   - Text: '{test_text}'")
        print(f"   - Embedding dimensions: {len(embeddings)}")
        print(f"   - Sample values: {embeddings[:3]}")
        
        if len(embeddings) == 768:
            print(f"   ✅ CONFIRMED: Gemini embeddings (768 dimensions)")
        elif len(embeddings) == 384:
            print(f"   ❌ WARNING: Local model embeddings (384 dimensions)")
        else:
            print(f"   ❓ Unknown model ({len(embeddings)} dimensions)")
    except Exception as e:
        print(f"   ❌ Error creating embeddings: {e}")
    print()
    
    # 3. Check stored data in Elasticsearch
    print(f"3️⃣ Elasticsearch verification:")
    try:
        es = Elasticsearch([os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200')])
        
        # Get index mapping
        mapping = es.indices.get_mapping(index='ebooks')
        dims = mapping['ebooks']['mappings']['properties']['embeddings']['dims']
        print(f"   - Index configured for: {dims} dimensions")
        
        # Check actual stored documents
        response = es.search(index='ebooks', size=3)
        total_docs = response['hits']['total']['value']
        print(f"   - Total documents stored: {total_docs}")
        
        if response['hits']['hits']:
            for i, hit in enumerate(response['hits']['hits'][:2]):
                doc = hit['_source']
                actual_dims = len(doc['embeddings'])
                print(f"   - Doc {i+1}: {actual_dims} dimensions")
                print(f"     Content: '{doc['content'][:50]}...'")
                
                if actual_dims == 768:
                    print(f"     ✅ Gemini embeddings")
                elif actual_dims == 384:
                    print(f"     ❌ Local model embeddings")
    except Exception as e:
        print(f"   ❌ Error checking Elasticsearch: {e}")
    print()
    
    # 4. Compare embedding values (Gemini vs Local would be different)
    print(f"4️⃣ Embedding comparison test:")
    try:
        # Test with Gemini
        processor_gemini = EbookProcessor(use_gemini=True)
        gemini_embedding = processor_gemini.create_embeddings(test_text)
        
        # Test with local model
        processor_local = EbookProcessor(use_gemini=False)
        local_embedding = processor_local.create_embeddings(test_text)
        
        print(f"   - Gemini: {len(gemini_embedding)} dims, values: {gemini_embedding[:3]}")
        print(f"   - Local:  {len(local_embedding)} dims, values: {local_embedding[:3]}")
        
        # They should be different models producing different results
        if len(gemini_embedding) == 768 and len(local_embedding) == 384:
            print(f"   ✅ CONFIRMED: Both models working, using Gemini by default")
        else:
            print(f"   ⚠️  Unexpected dimensions")
            
    except Exception as e:
        print(f"   ❌ Error in comparison: {e}")

if __name__ == "__main__":
    verify_gemini_usage()