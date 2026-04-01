import hashlib
from typing import List, Dict
from dataclasses import dataclass
import os

# Pinecone index name: "truthlens-facts"
# Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast, on-premise)
# Fallback: text-embedding-ada-002 (OpenAI, 1536-dim, higher quality)
# Prefer local embedding to avoid API cost at indexing time

class MockSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name
    def encode(self, text):
        return [0.1] * 384
EMBED_MODEL = MockSentenceTransformer("all-MiniLM-L6-v2")

class MockTextSplitter:
    def split_text(self, text):
        # mock LangChain RecursiveCharacterTextSplitter
        # max 400 tokens per chunk, 50-token overlap
        return [text[i:i+400] for i in range(0, len(text), 350)] 

text_splitter = MockTextSplitter()

@dataclass
class Document:
    text: str
    url: str
    title: str
    published_date: str

def get_pinecone_index():
    # [MOCK]
    # from pinecone import Pinecone, ServerlessSpec
    # pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    # return pc.Index("truthlens-facts")
    class MockIndex:
        def upsert(self, vectors):
            pass
        def delete(self, filter):
            pass
    return MockIndex()

def index_documents(documents: List[Document], source_name: str):
    # Document schema: {text: str, url: str, title: str, published_date: str}
    # Chunk documents: max 400 tokens per chunk, 50-token overlap
    # Use LangChain RecursiveCharacterTextSplitter
    index = get_pinecone_index()
    
    vectors = []
    chunks_indexed = 0
    
    for doc in documents:
        chunks = text_splitter.split_text(doc.text)
        for chunk in chunks:
            # For each chunk:
            #   embedding = EMBED_MODEL.encode(chunk.text)
            embedding = EMBED_MODEL.encode(chunk)
            
            #   metadata = {source: source_name, url: doc.url, title: doc.title, date: doc.published_date}
            metadata = {
                "source": source_name,
                "url": doc.url,
                "title": doc.title,
                "date": doc.published_date,
                "text": chunk
            }
            #   upsert to Pinecone with id = hash(chunk.text)
            chunk_id = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": metadata
            })
            
            # Batch upserts in groups of 100 (Pinecone limit per request)
            if len(vectors) >= 100:
                index.upsert(vectors=vectors)
                chunks_indexed += len(vectors)
                vectors = []
                
    if vectors:
        index.upsert(vectors=vectors)
        chunks_indexed += len(vectors)
        
    # Log: chunks indexed, source, timestamp
    print(f"[INDEXER] Indexed {chunks_indexed} chunks for source {source_name}")

def delete_source_vectors(source_name: str):
    # Delete all vectors with metadata.source == source_name before re-indexing
    # Use Pinecone delete with metadata filter
    index = get_pinecone_index()
    index.delete(filter={"source": source_name})
    print(f"[INDEXER] Deleted vectors for source {source_name}")
