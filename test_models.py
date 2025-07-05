#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
import os
import google.generativeai as genai

# Test text
test_text = 'Money is a tool for managing risk and uncertainty.'

# Test local model directly
print("🔍 Testing Local SentenceTransformer:")
model = SentenceTransformer('all-MiniLM-L6-v2')
local_embedding = model.encode(test_text)
print(f"  - Dimensions: {len(local_embedding)}")
print(f"  - Sample values: {local_embedding[:3]}")
print()

# Test Gemini directly
print("🔍 Testing Gemini API:")
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    
    result = genai.embed_content(
        model='models/text-embedding-004',
        content=test_text
    )
    gemini_embedding = result['embedding']
    
    print(f"  - Dimensions: {len(gemini_embedding)}")
    print(f"  - Sample values: {gemini_embedding[:3]}")
    print()
    
    # Compare
    print("🔍 Comparison:")
    print(f"  - Local model: {len(local_embedding)} dimensions")
    print(f"  - Gemini model: {len(gemini_embedding)} dimensions") 
    print(f"  - Different values: {local_embedding[0] != gemini_embedding[0]}")
    
    if len(local_embedding) == 384 and len(gemini_embedding) == 768:
        print("  ✅ CONFIRMED: Models are different!")
    elif local_embedding[0] != gemini_embedding[0]:
        print("  ✅ CONFIRMED: Different embedding values (different models)")
    else:
        print("  ⚠️  Same results - might be using same model")
        
except Exception as e:
    print(f"  ❌ Gemini error: {e}")