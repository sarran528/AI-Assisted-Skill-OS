"""
RAG service - retrieval-augmented generation for skill-specific context.
"""
from typing import Optional
import json


class RAGService:
    """Retrieves skill-specific context for LLM-assisted responses."""

    def __init__(self, vector_store=None):
        """
        Initialize RAG service.
        
        Args:
            vector_store: Optional pgvector or embedding store
        """
        self.vector_store = vector_store

    def retrieve_context(
        self,
        query: str,
        skill_id: str,
        phase: Optional[str] = None,
        technique_id: Optional[str] = None,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Retrieve relevant skill documentation chunks.
        
        Args:
            query: User's query or question
            skill_id: Target skill ID
            phase: Optional phase filter
            technique_id: Optional technique filter
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        # TODO: Implement actual vector search against pgvector
        # For now, return mock data
        return [
            {
                "chunk_id": "chunk_1",
                "content": f"Documentation for {skill_id}",
                "metadata": {
                    "skill_id": skill_id,
                    "phase": phase,
                    "technique_id": technique_id,
                },
                "similarity": 0.95,
            }
        ]

    def build_prompt_context(
        self,
        user_query: str,
        retrieved_chunks: list[dict],
    ) -> str:
        """
        Build a RAG-augmented prompt.
        
        Args:
            user_query: Original user question
            retrieved_chunks: Retrieved context chunks
            
        Returns:
            Augmented prompt for LLM
        """
        context = "\n\n".join(
            [f"Source {i}: {chunk['content']}" for i, chunk in enumerate(retrieved_chunks, 1)]
        )

        return f"""Context:
{context}

User Question:
{user_query}

Based on the above context, provide a clear and helpful answer to the user's question."""
