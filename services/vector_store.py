# ==============================================================================
# File: services/vector_store.py
# Description: Handles vector embeddings and interaction with MongoDB.
# ==============================================================================
import os
from pymongo import MongoClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# --- Configuration ---
MONGO_URI = os.environ.get("MONGO_URI")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not MONGO_URI or not GOOGLE_API_KEY:
    raise ValueError("Please set the MONGO_URI and GOOGLE_API_KEY environment variables.")

# --- Initialize Connections ---
client = MongoClient(MONGO_URI)
db = client.PrabhankarDatabase # Using your database name
collection = db.document_chunks # Collection name

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def add_chunks_to_store(chunks):
    """Generates embeddings for text chunks and stores them in MongoDB."""
    print(f"Generating embeddings for {len(chunks)} chunks...")
    chunk_embeddings = embeddings.embed_documents(chunks)
    
    documents_to_insert = []
    for i, chunk in enumerate(chunks):
        documents_to_insert.append({
            "text": chunk,
            "embedding": chunk_embeddings[i]
        })
        
    collection.delete_many({})
    print("Cleared old document chunks from the database.")
    
    collection.insert_many(documents_to_insert)
    print(f"Successfully inserted {len(documents_to_insert)} new chunks into the database.")

def find_relevant_chunks(query, top_k=5):
    """Finds the most relevant text chunks for a given query using vector search."""
    query_embedding = embeddings.embed_query(query)
    
    pipeline = [
        {
            "$vectorSearch": {
                # --- THIS IS THE FIX ---
                # Changed from "vector_search_index" to "default" to match your Atlas setup
                "index": "default", 
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": top_k
            }
        },
        {
            "$project": {
                "text": 1,
                "_id": 0,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    print(f"Vector search found {len(results)} relevant chunks.")
    return [result['text'] for result in results]
