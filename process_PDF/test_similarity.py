import os
import re
import json
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
COLLECTION_NAME = "docs_embeddings"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")



# Initialize Qdrant client and embedding model
def initialize_qdrant_and_embedding():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    embedding_model = TextEmbedding()
    return client, embedding_model

# Clean retrieved content
def clean_content(raw_text: str) -> str:
    text = raw_text
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r" +", " ", text)
    return text.strip()



# Persistent conversation memory
conversation_history = []
CONVERSATION_FILE = "conversation_history.json"

def save_conversation_to_file():
    try:
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {e}")

# Query Qdrant and generate response with OpenAI, using conversation memory
def ask_bh_assurance(query: str, client: QdrantClient, embedding_model: TextEmbedding):
    query_embedding = list(embedding_model.embed([query]))[0]
    search_response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=5,
        with_payload=True
    )
    context = ""
    for result in search_response.points:
        payload = result.payload or {}
        content = payload.get('content', '')
        cleaned_content = clean_content(content)
        context += cleaned_content + "\n\n"

    # Build conversation history for prompt
    history_text = ""
    if conversation_history:
        history_text = "Previous conversation:\n"
        for i, (q, r) in enumerate(conversation_history):
            history_text += f"Q{i+1}: {q}\nA{i+1}: {r}\n"

    prompt = f"""
You are a friendly, helpful, and knowledgeable assistant for BH Assurance, a leading insurance provider in Tunisia. Answer user questions about BH Assurance auto insurance contracts in a conversational, chat-like style—just like ChatGPT-4. Be clear, supportive, and approachable. Use specific details from BH Assurance documentation naturally, but don't reference the source. If you don't know something, give a general but helpful answer and suggest contacting BH Assurance for more info.

{history_text}
User: {query}

Context from BH Assurance documentation:
{context}

Respond in a chat format, making sure your answer is friendly, direct, and easy to understand.
"""
    # Initialize (or reuse) OpenAI client
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not set in environment (.env)."
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7
        )
        answer = response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"
    # Store the query and answer in memory
    conversation_history.append((query, answer))
    save_conversation_to_file()
    return answer

# Main function to handle queries
def main(queries: list):
    client, embedding_model = initialize_qdrant_and_embedding()
    
    for query in queries:
        print(f"\nQuery: {query}")
        response = ask_bh_assurance(query, client, embedding_model)
        print(f"Response: {response}")

# Example usage
if __name__ == "__main__":
    client, embedding_model = initialize_qdrant_and_embedding()
    print("Type your insurance question (or 'exit' to quit):")
    while True:
        query = input("> ")
        if query.lower() == "exit":
            break
        response = ask_bh_assurance(query, client, embedding_model)
        print(f"Response: {response}\n")