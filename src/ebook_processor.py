import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import ebooklib
from ebooklib import epub
import PyPDF2
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EbookProcessor:
    def __init__(self, elasticsearch_url: str = None, index_name: str = "ebooks"):
        self.elasticsearch_url = elasticsearch_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.index_name = index_name
        logger.info(f"Using Elasticsearch URL: {self.elasticsearch_url}")
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def extract_text_from_epub(self, file_path: str) -> Dict[str, Any]:
        """Extract text content from EPUB file"""
        try:
            book = epub.read_epub(file_path)
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
    
    def create_embeddings(self, text: str) -> np.ndarray:
        """Create embeddings for text using SentenceTransformer"""
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
    
    def store_in_elasticsearch(self, documents: List[Dict[str, Any]]) -> bool:
        """Store documents in Elasticsearch with embeddings"""
        try:
            from elasticsearch import Elasticsearch
            
            logger.info(f"Creating Elasticsearch client for {self.elasticsearch_url}")
            # Create Elasticsearch client
            es = Elasticsearch([self.elasticsearch_url])
            logger.info(f"Elasticsearch client created: {type(es)}")
            
            # Test basic connectivity first
            try:
                logger.info("Testing basic ES connectivity...")
                info = es.info()
                logger.info(f"ES info: {info}")
            except Exception as e:
                logger.error(f"ES connectivity test failed: {e}")
                raise
            
            logger.info(f"Checking if index {self.index_name} exists")
            
            # Check if index exists
            try:
                index_exists = es.indices.exists(index=self.index_name)
                logger.info(f"Index exists: {index_exists}")
            except Exception as e:
                logger.error(f"Error checking index existence: {e}")
                raise
            
            # Create index if it doesn't exist
            if not index_exists:
                logger.info("Creating index...")
                mapping = {
                    "properties": {
                        "content": {"type": "text"},
                        "title": {"type": "text"},
                        "author": {"type": "text"},
                        "file_path": {"type": "keyword"},
                        "file_type": {"type": "keyword"},
                        "chunk_id": {"type": "integer"},
                        "total_chunks": {"type": "integer"},
                        "embeddings": {
                            "type": "dense_vector",
                            "dims": 384
                        }
                    }
                }
                
                try:
                    es.indices.create(index=self.index_name, mappings=mapping)
                    logger.info(f"Created index: {self.index_name}")
                except Exception as e:
                    logger.error(f"Error creating index: {e}")
                    raise
            
            # Store documents with embeddings
            for i, doc in enumerate(documents):
                logger.info(f"Processing document {i+1}/{len(documents)}")
                embeddings = self.create_embeddings(doc['content'])
                logger.info(f"Created embeddings for document {i+1}")
                doc_body = {
                    "embeddings": embeddings.tolist(),
                    **doc
                }
                logger.info(f"Indexing document {i+1} to Elasticsearch")
                es.index(index=self.index_name, document=doc_body)
            
            logger.info(f"Successfully stored {len(documents)} documents in Elasticsearch")
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"Error storing documents in Elasticsearch: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            print(f"ERROR: {str(e)}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            return False
    
    def process_directory(self, directory_path: str) -> Dict[str, Any]:
        """Process all ebook files in a directory"""
        results = {
            'processed': 0,
            'failed': 0,
            'total_chunks': 0,
            'books': []
        }
        
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return results
        
        # Find all supported ebook files
        ebook_files = []
        for extension in ['*.epub', '*.pdf']:
            ebook_files.extend(directory.glob(extension))
        
        logger.info(f"Found {len(ebook_files)} ebook files to process")
        
        for file_path in ebook_files:
            try:
                logger.info(f"Processing: {file_path}")
                
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
                logger.info(f"About to store {len(documents)} documents in Elasticsearch")
                if self.store_in_elasticsearch(documents):
                    results['processed'] += 1
                    results['total_chunks'] += len(documents)
                    results['books'].append({
                        'title': book_data['title'],
                        'author': book_data['author'],
                        'file_path': str(file_path),
                        'chunks': len(documents)
                    })
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                import traceback
                logger.error(f"Error processing {file_path}: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                results['failed'] += 1
        
        return results

def main():
    """Main function to process ebooks"""
    processor = EbookProcessor()
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    ebooks_dir = project_root / "ebooks"
    
    if ebooks_dir.exists():
        results = processor.process_directory(str(ebooks_dir))
        logger.info(f"Processing complete: {results}")
    else:
        logger.warning(f"Ebooks directory not found: {ebooks_dir}")

if __name__ == "__main__":
    main()