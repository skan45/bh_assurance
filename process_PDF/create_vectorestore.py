import os
import uuid
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from fastembed import TextEmbedding
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "docs_embeddings"

def setup_qdrant_collection(qdrant_url: str, qdrant_api_key: str, collection_name: str = COLLECTION_NAME):
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    embedding_model = TextEmbedding()
    test_embedding = list(embedding_model.embed(["test"]))[0]
    embedding_dim = len(test_embedding)
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )
    except Exception as e:
        if "already exists" not in str(e):
            raise e
    return client, embedding_model

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

def store_pdf_embeddings(pdf_path: str, qdrant_url: str, qdrant_api_key: str, collection_name: str = COLLECTION_NAME):
    # Initialize Qdrant client and embedding model
    client, embedding_model = setup_qdrant_collection(qdrant_url, qdrant_api_key, collection_name)

    # Extract text from PDF page by page
    try:
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if not page_text:
                continue
            # Generate embedding for the page content
            embedding = list(embedding_model.embed([page_text]))[0]
            # Prepare payload for each page
            payload = {
                "content": page_text,
                "url": pdf_path,
                "metadata": {
                    "title": os.path.basename(pdf_path),
                    "page_number": i + 1,
                    "crawl_date": datetime.now().isoformat()
                }
            }
            # Store embedding in Qdrant
            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding.tolist(),
                        payload=payload
                    )
                ]
            )
            print(f"Stored embeddings for page {i+1} of {pdf_path}")
        print(f"Successfully stored embeddings for all pages of {pdf_path} in Qdrant collection {collection_name}")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

# Example usage
if __name__ == "__main__":
    pdf_path = 'C:/Users/Fedy/Desktop/BH_Hackathon/process_PDF/BH_TOUS_CG.pdf'
    try:
        store_pdf_embeddings(pdf_path, QDRANT_URL, QDRANT_API_KEY)
    except Exception as e:
        print(f"Error: {str(e)}")