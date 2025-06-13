"""
Custom retrievers for different use cases.
"""

from typing import List, Dict, Any
from langchain.schema import BaseRetriever, Document
from langfuse import observe


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining multiple retrieval strategies."""
    
    def __init__(self, vector_retriever, keyword_retriever, weights: Dict[str, float] = None):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.weights = weights or {"vector": 0.7, "keyword": 0.3}
    
    @observe()
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve documents using hybrid approach."""
        # Get results from both retrievers
        vector_docs = self.vector_retriever.get_relevant_documents(query)
        keyword_docs = self.keyword_retriever.get_relevant_documents(query)
        
        # Combine and rank results (simplified implementation)
        combined_docs = vector_docs + keyword_docs
        
        # Remove duplicates and return top results
        seen_content = set()
        unique_docs = []
        for doc in combined_docs:
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                unique_docs.append(doc)
        
        return unique_docs[:10]  # Return top 10
    
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version of get_relevant_documents."""
        return self.get_relevant_documents(query)


class ContextualRetriever(BaseRetriever):
    """Retriever that considers conversation context."""
    
    def __init__(self, base_retriever, context_window: int = 3):
        self.base_retriever = base_retriever
        self.context_window = context_window
        self.conversation_history: List[str] = []
    
    @observe()
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Retrieve documents considering conversation context."""
        # Add query to conversation history
        self.conversation_history.append(query)
        
        # Keep only recent context
        if len(self.conversation_history) > self.context_window:
            self.conversation_history = self.conversation_history[-self.context_window:]
        
        # Create enhanced query with context
        enhanced_query = " ".join(self.conversation_history)
        
        return self.base_retriever.get_relevant_documents(enhanced_query)
    
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version of get_relevant_documents."""
        return self.get_relevant_documents(query)
