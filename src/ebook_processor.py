import os
import logging
import warnings
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import ebooklib
from ebooklib import epub
import PyPDF2
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

# Suppress specific ebooklib FutureWarning that we can't fix (library bug)
warnings.filterwarnings('ignore', message='This search incorrectly ignores the root element*')

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class EbookProcessor:
    def __init__(self, elasticsearch_url: str = None, index_name: str = "ebooks", index_mode: str = "new", use_gemini: bool = False):
        self.elasticsearch_url = elasticsearch_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.index_name = index_name
        self.index_mode = index_mode
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.use_gemini = use_gemini or os.getenv("GEMINI_API_KEY") is not None
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2') if not self.use_gemini else None
        self.indexed_books_file = Path(__file__).parent.parent / "indexed_books.json"
        
    def load_indexed_books(self) -> Set[str]:
        """Load the set of previously indexed books"""
        if self.indexed_books_file.exists():
            try:
                with open(self.indexed_books_file, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading indexed books: {str(e)}")
                return set()
        return set()
    
    def save_indexed_books(self, indexed_books: Set[str]):
        """Save the set of indexed books"""
        try:
            with open(self.indexed_books_file, 'w') as f:
                json.dump(list(indexed_books), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving indexed books: {str(e)}")
        
    def extract_text_from_epub(self, file_path: str) -> Dict[str, Any]:
        """Extract text content from EPUB file"""
        try:
            book = epub.read_epub(file_path, options={'ignore_ncx': True})
            title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown"
            author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
            
            text_content = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    if text.strip():
                        text_content.append(text.strip())
            
            return {
                'title': title,
                'author': author,
                'content': '\n\n'.join(text_content),
                'file_path': file_path,
                'file_type': 'epub'
            }
        except Exception as e:
            logger.error(f"Error extracting text from EPUB {file_path}: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text content from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text.strip())
                
                # Extract metadata
                metadata = pdf_reader.metadata
                title = metadata.get('/Title', 'Unknown') if metadata else 'Unknown'
                author = metadata.get('/Author', 'Unknown') if metadata else 'Unknown'
                
                return {
                    'title': title,
                    'author': author,
                    'content': '\n\n'.join(text_content),
                    'file_path': file_path,
                    'file_type': 'pdf'
                }
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return None
    
    def process_ebook(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process a single ebook file"""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.epub':
            return self.extract_text_from_epub(file_path)
        elif file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_extension}")
            return None
    
    def create_embeddings(self, text: str):
        """Create embeddings for text using Gemini or SentenceTransformer"""
        if self.use_gemini:
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
                if self.embedding_model is None:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                return self.embedding_model.encode(text)
        else:
            return self.embedding_model.encode(text)
    
    def split_text_into_chunks(self, book_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split book content into chunks for vector storage"""
        if not book_data or not book_data.get('content'):
            return []
        
        # Simple text splitting
        content = book_data['content']
        chunks = []
        
        # Split by sentences approximately
        sentences = content.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    chunks.append(sentence)
            else:
                current_chunk += ". " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                'content': chunk,
                'title': book_data['title'],
                'author': book_data['author'],
                'file_path': book_data['file_path'],
                'file_type': book_data['file_type'],
                'chunk_id': i,
                'total_chunks': len(chunks)
            }
            documents.append(doc)
        
        return documents
    
    def store_in_elasticsearch(self, documents: List[Dict[str, Any]], current_book: int = 0, total_books: int = 0) -> bool:
        """Store documents in Elasticsearch with embeddings"""
        try:
            from elasticsearch import Elasticsearch
            
            es = Elasticsearch([self.elasticsearch_url])
            es.info()  # Test connectivity
            
            # Create index if it doesn't exist
            if not es.indices.exists(index=self.index_name):
                mapping = {
                    "properties": {
                        "content": {"type": "text"},
                        "title": {"type": "text"},
                        "author": {"type": "text"},
                        "file_path": {"type": "keyword"},
                        "file_type": {"type": "keyword"},
                        "chunk_id": {"type": "integer"},
                        "total_chunks": {"type": "integer"},
                        "embeddings": {"type": "dense_vector", "dims": 768 if self.use_gemini else 384}
                    }
                }
                es.indices.create(index=self.index_name, mappings=mapping)
            
            # Store documents with embeddings
            for i, doc in enumerate(documents):
                print(f"\r📊 {current_book}/{total_books} books | 📄 {i+1}/{len(documents)} chunks", end='', flush=True)
                embeddings = self.create_embeddings(doc['content'])
                if self.use_gemini:
                    doc_body = {"embeddings": embeddings, **doc}
                else:
                    doc_body = {"embeddings": embeddings.tolist(), **doc}
                es.index(index=self.index_name, document=doc_body)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing documents in Elasticsearch: {str(e)}")
            return False
    
    def process_directory(self, directory_path: str) -> Dict[str, Any]:
        """Process all ebook files in a directory"""
        results = {'processed': 0, 'failed': 0, 'total_chunks': 0, 'books': []}
        
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return results
        
        # Find all supported ebook files
        ebook_files = []
        for extension in ['*.epub', '*.pdf']:
            ebook_files.extend(directory.glob(extension))
        
        # Load previously indexed books
        indexed_books = self.load_indexed_books()
        print(f"🔍 Debug: Loaded {len(indexed_books)} previously indexed books")
        print(f"🔍 Debug: Index mode = {self.index_mode}")
        
        if self.index_mode == "new":
            # Filter out already indexed books
            original_count = len(ebook_files)
            if indexed_books:
                print(f"🔍 Debug: Sample indexed book path: {list(indexed_books)[0]}")
            if ebook_files:
                print(f"🔍 Debug: Sample current file path: {str(ebook_files[0])}")
            ebook_files = [f for f in ebook_files if str(f) not in indexed_books]
            print(f"🔍 Debug: Filtered {original_count} files to {len(ebook_files)} new files")
        # In 'all' mode, process all files regardless of indexing status
        
        total_books = len(ebook_files)
        if self.index_mode == "new":
            all_files = len(list(directory.glob('*.epub')) + list(directory.glob('*.pdf')))
            skipped = all_files - total_books
            print(f"📚 Found {total_books} new ebook files to process ({skipped} already indexed)")
        else:
            print(f"📚 Found {total_books} ebook files to process (all mode - reprocessing everything)")
        
        for idx, file_path in enumerate(ebook_files, 1):
            try:
                print(f"\n📖 Processing book {idx}/{total_books}: {file_path.name}")
                
                # Extract text from ebook
                book_data = self.process_ebook(str(file_path))
                if not book_data:
                    results['failed'] += 1
                    continue
                
                # Split into chunks
                documents = self.split_text_into_chunks(book_data)
                if not documents:
                    results['failed'] += 1
                    continue
                
                # Store in Elasticsearch
                if self.store_in_elasticsearch(documents, idx, total_books):
                    results['processed'] += 1
                    results['total_chunks'] += len(documents)
                    results['books'].append({
                        'title': book_data['title'],
                        'author': book_data['author'],
                        'file_path': str(file_path),
                        'chunks': len(documents)
                    })
                    # Track this book as indexed
                    indexed_books.add(str(file_path))
                    print(f" ✅ Completed")
                else:
                    results['failed'] += 1
                    print(f" ❌ Failed")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                results['failed'] += 1
                print(f" ❌ Error: {str(e)}")
        
        # Save the updated list of indexed books
        self.save_indexed_books(indexed_books)
        
        print(f"\n\n🎉 Processing complete: {results['processed']} successful, {results['failed']} failed")
        return results

def main():
    """Main function to process ebooks"""
    parser = argparse.ArgumentParser(description="Process ebook files for indexing")
    parser.add_argument("--mode", choices=["new", "all"], default="new",
                        help="Indexing mode: 'new' to index only new books, 'all' to index all books")
    parser.add_argument("--use-gemini", action="store_true",
                        help="Use Gemini embedding API instead of local model")
    
    args = parser.parse_args()
    
    processor = EbookProcessor(index_mode=args.mode, use_gemini=args.use_gemini)
    project_root = Path(__file__).parent.parent
    ebooks_dir = project_root / "ebooks"
    
    if ebooks_dir.exists():
        processor.process_directory(str(ebooks_dir))
    else:
        print(f"❌ Ebooks directory not found: {ebooks_dir}")

if __name__ == "__main__":
    main()