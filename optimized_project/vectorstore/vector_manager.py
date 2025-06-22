"""
Vector store implementation and management for the optimized project.
Uses ChromaDB and Google Generative AI Embeddings.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Langchain components will be used. Ensure they are in requirements.txt
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langfuse import observe # Assuming Langfuse is still desired

# Default configuration values (can be overridden by config from core_config.py)
DEFAULT_EMBEDDING_MODEL = "models/embedding-001" # Standard Google model
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_SEPARATORS = ["\n\n", "\n", " ", ""]
DEFAULT_PERSIST_DIRECTORY = "data/vector_store_db" # Relative to project root
DEFAULT_COLLECTION_NAME = "ai_support_tickets_collection"
DEFAULT_SEARCH_K = 4


class VectorStoreManager:
    """Manages vector store operations using ChromaDB."""

    def __init__(self, core_config: Dict[str, Any], project_root_path: Path):
        """
        Initializes the VectorStoreManager.
        Args:
            core_config: Dictionary containing configurations, typically loaded by CoreConfigLoader.
                         Expected keys: 'api_keys', 'vector_store', 'models' (for embedding model).
            project_root_path: The absolute path to the 'optimized_project' root.
        """
        self.project_root = project_root_path
        vs_config = core_config.get("vector_store", {})
        # Embedding model might be under models or a specific embedding config
        embedding_model_name = vs_config.get("embedding_model_name", DEFAULT_EMBEDDING_MODEL)

        # API key for GoogleGenerativeAIEmbeddings is typically handled by GOOGLE_API_KEY env var
        # or auto-detected if google-auth is set up.
        # CoreConfigLoader should ensure GEMINI_API_KEY (often used for Google AI Studio models) is available.
        # If a different key is needed for embeddings, it should be specified.
        # For now, assume GEMINI_API_KEY is sufficient or google-auth is configured.

        # No explicit API key passed here; it relies on environment setup for Google SDK
        self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model_name)

        # Text splitter configuration
        # In a more complex setup, chunking settings could also come from core_config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=vs_config.get("chunk_size", DEFAULT_CHUNK_SIZE),
            chunk_overlap=vs_config.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP),
            separators=vs_config.get("separators", DEFAULT_SEPARATORS)
        )

        self.persist_directory = self.project_root / vs_config.get("persist_directory", DEFAULT_PERSIST_DIRECTORY)
        self.collection_name = vs_config.get("collection_name", DEFAULT_COLLECTION_NAME)

        self.vectorstore = self._initialize_vectorstore()

    def _initialize_vectorstore(self) -> Chroma:
        """Initialize the Chroma vector store."""
        os.makedirs(self.persist_directory, exist_ok=True)
        # print(f"Initializing ChromaDB at: {self.persist_directory} with collection: {self.collection_name}")

        # Chroma client settings can be added here if needed (e.g., for remote Chroma)
        # For local Chroma, direct instantiation is fine.
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory) # Chroma expects string path
        )

    @observe() # Assuming Langfuse integration is kept
    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Add documents to the vector store.
        Args:
            documents: A list of document texts.
            metadatas: An optional list of metadata dictionaries, one for each document.
        """
        texts_to_embed: List[str] = []
        chunk_metadatas: List[Dict[str, Any]] = []

        for i, doc_text in enumerate(documents):
            chunks = self.text_splitter.split_text(doc_text)
            texts_to_embed.extend(chunks)

            # Get metadata for this document or create a default one
            doc_metadata = metadatas[i].copy() if metadatas and i < len(metadatas) else {"source": f"document_{i+1}"}

            for chunk_idx, chunk_content in enumerate(chunks):
                current_chunk_metadata = doc_metadata.copy()
                current_chunk_metadata.update({
                    "chunk_index": chunk_idx,
                    "total_chunks_in_doc": len(chunks),
                    "chunk_length_chars": len(chunk_content)
                })
                chunk_metadatas.append(current_chunk_metadata)

        if texts_to_embed:
            self.vectorstore.add_texts(texts=texts_to_embed, metadatas=chunk_metadatas)
            # print(f"Added {len(documents)} documents ({len(texts_to_embed)} chunks) to vector store.")
        else:
            print("No texts to add to vector store.")

    @observe()
    def similarity_search(self, query: str, k: Optional[int] = None, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform similarity search in the vector store.
        Args:
            query: The query string.
            k: Number of results to return. Defaults to value from config or DEFAULT_SEARCH_K.
            filter_criteria: Optional dictionary for metadata filtering.
        Returns:
            A list of search results, each containing 'content', 'metadata', and 'score'.
        """
        search_k = k if k is not None else self.vectorstore_config.get("search_k_results", DEFAULT_SEARCH_K)

        results_with_scores = self.vectorstore.similarity_search_with_score(
            query=query,
            k=search_k,
            filter=filter_criteria # Pass filter if provided
        )

        formatted_results: List[Dict[str, Any]] = []
        for doc, score in results_with_scores:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score) # Ensure score is float
            })
        return formatted_results

    def get_retriever(self, k: Optional[int] = None, filter_criteria: Optional[Dict[str, Any]] = None):
        """
        Get a Langchain retriever for the vector store.
        Args:
            k: Number of results the retriever should fetch.
            filter_criteria: Optional dictionary for metadata filtering.
        Returns:
            A Langchain retriever instance.
        """
        search_k = k if k is not None else self.vectorstore_config.get("search_k_results", DEFAULT_SEARCH_K)
        search_kwargs = {"k": search_k}
        if filter_criteria:
            search_kwargs["filter"] = filter_criteria

        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)

    @property
    def vectorstore_config(self) -> Dict[str, Any]:
        """Helper to get vector_store part of the main config, ensures it's a dict."""
        # This assumes self.core_config is set, which it isn't in current __init__
        # This property should be used carefully or core_config should be passed to __init__
        # For now, let's assume it's handled by the caller or defaults are used.
        # This is a placeholder for where it would get its runtime config.
        # In a real scenario, core_config would be passed to __init__
        # For this refactor, we'll rely on the defaults or direct config in AISystem.
        return {} # Placeholder, this needs to be connected to CoreConfigLoader instance

# Example of how it might be used with CoreConfigLoader:
if __name__ == '__main__':
    # This setup is for standalone testing of this module.
    # In the actual app, CoreConfigLoader and project_root would be provided by AISystem.

    # Determine project root assuming this file is in optimized_project/vectorstore/
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent

    print(f"Running VectorStoreManager example from: {current_file_path}")
    print(f"Determined project root: {project_root}")

    # Mock core_config or load it (requires config files to be in place)
    # For simplicity, using default values for this example.
    # In a real app, CoreConfigLoader would provide this.
    mock_core_config = {
        "vector_store": {
            "persist_directory": "data/temp_vector_store_db_example", # Use a temp dir for example
            "collection_name": "example_collection",
            "embedding_model_name": DEFAULT_EMBEDDING_MODEL, # models/embedding-001
            "search_k_results": 2
        },
        # GEMINI_API_KEY needs to be in the environment for GoogleGenerativeAIEmbeddings
    }

    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY environment variable not set. Embeddings might fail.")
        # You could set it here for testing if needed, but better to set in your shell:
        # os.environ["GEMINI_API_KEY"] = "YOUR_ACTUAL_KEY"

    try:
        vsm = VectorStoreManager(core_config=mock_core_config, project_root_path=project_root)
        print(f"VectorStoreManager initialized. DB path: {vsm.persist_directory}")

        # Test adding documents
        docs_to_add = [
            "Paris is the capital of France.",
            "The Eiffel Tower is a famous landmark in Paris.",
            "Machine learning is a subfield of artificial intelligence."
        ]
        metadata_to_add = [
            {"source": "geo_facts.txt", "topic": "geography"},
            {"source": "paris_landmarks.txt", "topic": "tourism"},
            {"source": "ai_terms.txt", "topic": "technology"}
        ]
        vsm.add_documents(docs_to_add, metadata_to_add)
        print("Documents added.")

        # Test similarity search
        query1 = "What is the capital of France?"
        results1 = vsm.similarity_search(query1)
        print(f"\nSearch results for '{query1}':")
        for res in results1:
            print(f"  Content: {res['content'][:50]}... Score: {res['score']:.4f}, Source: {res['metadata'].get('source')}")

        query2 = "Tell me about AI."
        results2 = vsm.similarity_search(query2, k=1)
        print(f"\nSearch results for '{query2}':")
        for res in results2:
            print(f"  Content: {res['content'][:50]}... Score: {res['score']:.4f}, Source: {res['metadata'].get('source')}")

        # Clean up the temporary directory used in example
        # import shutil
        # if os.path.exists(vsm.persist_directory):
        #     print(f"Cleaning up example vector store directory: {vsm.persist_directory}")
        #     shutil.rmtree(vsm.persist_directory)

    except Exception as e:
        print(f"An error occurred during the example: {e}")
        import traceback
        traceback.print_exc()
