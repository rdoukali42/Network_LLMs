"""
Vector store implementation and management.
"""

import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langfuse import observe


class VectorStoreManager:
    """Manages vector store operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=config['embeddings']['model']
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunking']['chunk_size'],
            chunk_overlap=config['chunking']['chunk_overlap'],
            separators=config['chunking']['separators']
        )
        self.vectorstore = self._initialize_vectorstore()
    
    def _initialize_vectorstore(self) -> Chroma:
        """Initialize the vector store."""
        persist_directory = self.config['vectorstore']['persist_directory']
        collection_name = self.config['vectorstore']['collection_name']
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
    
    @observe()
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None) -> None:
        """Add documents to the vector store."""
        # Split documents into chunks and properly assign metadata
        texts = []
        chunk_metadatas = []
        
        for i, doc in enumerate(documents):
            chunks = self.text_splitter.split_text(doc)
            texts.extend(chunks)
            
            # Get metadata for this document (or create default if none provided)
            if metadatas and i < len(metadatas):
                doc_metadata = metadatas[i].copy()
            else:
                doc_metadata = {"source": f"document_{i}", "document_index": i}
            
            # Assign the same metadata to all chunks from this document
            # but add chunk-specific information
            for chunk_idx, chunk in enumerate(chunks):
                chunk_metadata = doc_metadata.copy()
                chunk_metadata.update({
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks),
                    "chunk_length": len(chunk)
                })
                chunk_metadatas.append(chunk_metadata)
        
        # Add to vector store with properly matched metadata
        self.vectorstore.add_texts(texts, metadatas=chunk_metadatas)
    
    @observe()
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Perform similarity search."""
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
    
    def get_retriever(self, search_kwargs: Dict[str, Any] = None):
        """Get a retriever for the vector store."""
        search_kwargs = search_kwargs or {"k": 4}
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)
