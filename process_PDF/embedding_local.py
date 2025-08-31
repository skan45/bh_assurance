import os
import json
import uuid
from datetime import datetime
import numpy as np
import faiss
from fastembed import TextEmbedding
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Configuration
FAISS_INDEX_FILE = "embeddings.index"
METADATA_FILE = "metadata.json"

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def store_pdf_embeddings_locally(pdf_path: str, faiss_index_file: str = FAISS_INDEX_FILE, metadata_file: str = METADATA_FILE):
    # Initialize embedding model
    embedding_model = TextEmbedding()
    
    # Get embedding dimension
    test_embedding = list(embedding_model.embed(["test"]))[0]
    embedding_dim = len(test_embedding)
    
    # Initialize FAISS index (HNSW for fast cosine similarity)
    index = faiss.IndexHNSWFlat(embedding_dim, 32)  # 32 is the number of neighbors for HNSW
    index.hnsw.efConstruction = 40  # Higher values improve index quality
    index.hnsw.efSearch = 20  # Higher values improve search accuracy
    
    # Initialize lists for new embeddings and metadata
    new_embeddings = []
    new_metadata = []
    
    # Extract text from PDF page by page
    try:
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if not page_text:
                continue
            # Generate embedding for the page content
            embedding = list(embedding_model.embed([page_text]))[0]
            # Prepare metadata for the page
            metadata = {
                "id": str(uuid.uuid4()),
                "content": page_text,
                "url": pdf_path,
                "metadata": {
                    "title": os.path.basename(pdf_path),
                    "page_number": i + 1,
                    "crawl_date": datetime.now().isoformat()
                }
            }
            new_embeddings.append(embedding)
            new_metadata.append(metadata)
            print(f"Generated embeddings for page {i+1} of {pdf_path}")
        
        # Load existing FAISS index and metadata if they exist
        existing_metadata = []
        if os.path.exists(faiss_index_file) and os.path.exists(metadata_file):
            try:
                # Load existing FAISS index
                index = faiss.read_index(faiss_index_file)
                # Load existing metadata
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                print(f"Loaded existing FAISS index with {index.ntotal} vectors and metadata.")
            except Exception as e:
                print(f"Error loading existing index or metadata: {str(e)}. Starting with a new index.")
                index = faiss.IndexHNSWFlat(embedding_dim, 32)
                index.hnsw.efConstruction = 40
                index.hnsw.efSearch = 20
        
        # Append new embeddings to FAISS index
        if new_embeddings:
            embeddings_array = np.array(new_embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)  # Normalize for cosine similarity
            index.add(embeddings_array)
        
        # Append new metadata to existing metadata
        existing_metadata.extend(new_metadata)
        
        # Save updated FAISS index
        try:
            faiss.write_index(index, faiss_index_file)
            print(f"Saved FAISS index to {faiss_index_file} with {index.ntotal} vectors.")
        except Exception as e:
            print(f"Error saving FAISS index: {str(e)}")
        
        # Save updated metadata to JSON file
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
            print(f"Saved metadata for {len(existing_metadata)} embeddings to {metadata_file}")
        except Exception as e:
            print(f"Error saving metadata: {str(e)}")
        
        print(f"Successfully stored embeddings for all pages of {pdf_path} in FAISS index.")
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

# Example usage
if __name__ == "__main__":
    pdf_path = './BH_TOUS_CG.pdf'
    try:
        store_pdf_embeddings_locally(pdf_path)
    except Exception as e:
        print(f"Error: {str(e)}")
