from typing import List
from dataclasses import dataclass
from app.rag.indexer import EMBED_MODEL, get_pinecone_index

@dataclass
class RetrievedDoc:
    text: str
    url: str
    title: str
    source: str
    similarity_score: float

def retrieve_for_claim(claim: str, top_k: int = 5) -> List[RetrievedDoc]:
    # Query-time semantic retrieval
    # Input: claim string
    # Embed claim using same EMBED_MODEL
    # Query Pinecone: top_k=5, filter by recency if claim contains date entities
    # Return: list of RetrievedDoc(text, url, title, source, similarity_score)
    
    query_embedding = EMBED_MODEL.encode(claim)
    if not isinstance(query_embedding, list):
        query_embedding = query_embedding.tolist()
        
    pinecone_index = get_pinecone_index()
    
    # [MOCK] querying Pinecone
    class MockMatch:
        def __init__(self, score):
            self.score = score
            self.metadata = {
                "text": "This is a mock retrieved document that mentions the claim.",
                "url": "https://example.com",
                "title": "Mock Source Document",
                "source": "mock_source"
            }
    
    class MockResults:
        def __init__(self):
            self.matches = [MockMatch(0.85), MockMatch(0.72), MockMatch(0.50)]
            
    # MOCK implementation overriding the actual query
    # results = pinecone_index.query(
    #     vector=query_embedding,
    #     top_k=top_k,
    #     include_metadata=True,
    # )
    results = MockResults()
    
    return [
        RetrievedDoc(
            text=match.metadata["text"],
            url=match.metadata.get("url", ""),
            title=match.metadata.get("title", ""),
            source=match.metadata.get("source", ""),
            similarity_score=match.score,
        )
        for match in results.matches
        if match.score > 0.65  # relevance threshold — discard low-similarity retrievals
    ]
