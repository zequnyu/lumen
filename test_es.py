#!/usr/bin/env python3
import os
from elasticsearch import Elasticsearch

# Simple test to check ES connectivity
es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
print(f"Testing ES connection to: {es_url}")

try:
    es = Elasticsearch([es_url])
    print("ES client created successfully")
    
    info = es.info()
    print(f"ES info: {info}")
    
    # Test index creation
    index_name = "test_index"
    mapping = {
        "properties": {
            "content": {"type": "text"},
            "embeddings": {
                "type": "dense_vector",
                "dims": 384
            }
        }
    }
    
    # Delete index if exists
    if es.indices.exists(index=index_name):
        print(f"Deleting existing index: {index_name}")
        es.indices.delete(index=index_name)
    
    print(f"Creating index: {index_name}")
    es.indices.create(index=index_name, mappings=mapping)
    print("Index created successfully")
    
    # Test document indexing
    doc = {
        "content": "test content",
        "embeddings": [0.1] * 384
    }
    
    print("Indexing test document...")
    es.index(index=index_name, document=doc)
    print("Document indexed successfully")
    
    # Clean up
    es.indices.delete(index=index_name)
    print("Test completed successfully")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")