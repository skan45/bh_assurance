import os
import uuid
import json
from datetime import datetime
import numpy as np
from fastembed import TextEmbedding
from PyPDF2 import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv


# Qdrant Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "pdf_embeddings"

# Initialize Qdrant client
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize embedding model
embedding_model = TextEmbedding()
test_embedding = list(embedding_model.embed(["test"]))[0]
embedding_dim = len(test_embedding)

# Ensure collection exists (create if not)
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(size=embedding_dim, distance=models.Distance.COSINE)
)

def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Extract text from PDF page by page."""
    try:
        reader = PdfReader(pdf_path)
        pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if not page_text:
                continue
            pages.append({
                "page_number": i + 1,
                "content": page_text
            })
        return pages
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def store_pdf_embeddings_in_qdrant(pdf_path: str):
    """Generate embeddings for PDF and store in Qdrant."""
    try:
        pages = extract_text_from_pdf(pdf_path)

        for page in pages:
            embedding = list(embedding_model.embed([page["content"]]))[0]

            payload = {
                "id": str(uuid.uuid4()),
                "content": page["content"],
                "source": pdf_path,
                "metadata": {
                    "title": os.path.basename(pdf_path),
                    "page_number": page["page_number"],
                    "crawl_date": datetime.now().isoformat()
                }
            }

            client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=payload["id"],
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            print(f"Stored embeddings for page {page['page_number']} of {pdf_path}")

        print(f"✅ Successfully stored all pages of {pdf_path} in Qdrant collection '{COLLECTION_NAME}'")

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

# Example usage
if __name__ == "__main__":
    pdf_path = 'process_PDF/BH_TOUS_CG.pdf'
    store_pdf_embeddings_in_qdrant(pdf_path)

