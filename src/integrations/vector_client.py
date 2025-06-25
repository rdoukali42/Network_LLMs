"""
Vector Database Client for document search and retrieval.
Provides centralized interface for vector operations with ChromaDB integration.
"""

import logging
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from config.settings import Settings
from utils.exceptions import VectorError, ServiceError


class DocumentType(Enum):
    """Types of documents in the vector store."""
    POLICY = "policy"
    PROCEDURE = "procedure"
    FAQ = "faq"
    KNOWLEDGE_BASE = "knowledge_base"
    CODE_OF_CONDUCT = "code_of_conduct"
    GENERAL = "general"


@dataclass
class Document:
    """Document model for vector storage."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    doc_type: DocumentType = DocumentType.GENERAL
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Search result with similarity score."""
    document: Document
    similarity_score: float
    rank: int


@dataclass
class VectorStats:
    """Vector database statistics."""
    total_documents: int = 0
    documents_by_type: Dict[str, int] = field(default_factory=dict)
    total_queries: int = 0
    average_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0


class VectorClient:
    """
    Vector database client for document search and retrieval.
    
    Features:
    - ChromaDB integration
    - Document indexing and search
    - Metadata filtering
    - Similarity search optimization
    - Query caching
    - Usage analytics
    """

    def __init__(self, settings: Settings):
        """
        Initialize the Vector Client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # ChromaDB client
        self._client = None
        self._collection = None
        
        # Configuration
        self._collection_name = "ai_ticket_system_docs"
        self._embedding_model = "all-MiniLM-L6-v2"  # Default embedding model
        
        # Caching
        self._query_cache: Dict[str, List[SearchResult]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_enabled = True
        
        # Statistics
        self._stats = VectorStats()
        
        # Initialize client
        self._initialize_client()
        
        self.logger.info("Vector Client initialized")

    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            # Get database path from settings
            db_path = self.settings.get_setting("CHROMA_DB_PATH", "data/chroma_db")
            
            # Initialize client
            self._client = chromadb.PersistentClient(
                path=db_path,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self._collection = self._client.get_collection(
                    name=self._collection_name
                )
                self.logger.info(f"Connected to existing collection: {self._collection_name}")
            except Exception:
                self._collection = self._client.create_collection(
                    name=self._collection_name,
                    metadata={"description": "AI Ticket System document collection"}
                )
                self.logger.info(f"Created new collection: {self._collection_name}")
            
            # Update stats
            self._update_collection_stats()
            
        except ImportError:
            self.logger.error("ChromaDB not available. Install with: pip install chromadb")
            raise VectorError("ChromaDB not available")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector client: {str(e)}")
            raise VectorError(f"Vector client initialization failed: {str(e)}")

    def _update_collection_stats(self):
        """Update collection statistics."""
        try:
            if self._collection:
                count = self._collection.count()
                self._stats.total_documents = count
                
                # Get documents by type
                if count > 0:
                    results = self._collection.get(include=["metadatas"])
                    type_counts = {}
                    
                    for metadata in results.get("metadatas", []):
                        doc_type = metadata.get("doc_type", "general")
                        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                    
                    self._stats.documents_by_type = type_counts
                
        except Exception as e:
            self.logger.error(f"Failed to update collection stats: {str(e)}")

    def add_document(
        self,
        content: str,
        doc_id: Optional[str] = None,
        doc_type: DocumentType = DocumentType.GENERAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a document to the vector store.
        
        Args:
            content: Document content
            doc_id: Optional document ID (auto-generated if not provided)
            doc_type: Type of document
            metadata: Additional metadata
            
        Returns:
            Document ID
            
        Raises:
            VectorError: If document addition fails
        """
        try:
            if not self._collection:
                raise VectorError("Vector client not initialized")
            
            # Generate ID if not provided
            if not doc_id:
                doc_id = self._generate_document_id(content)
            
            # Prepare metadata
            doc_metadata = {
                "doc_type": doc_type.value,
                "created_at": datetime.now().isoformat(),
                "content_length": len(content)
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            # Add to collection
            self._collection.add(
                documents=[content],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            self.logger.info(f"Added document {doc_id} to vector store")
            
            # Update stats
            self._update_collection_stats()
            
            # Clear cache since new document added
            if self._cache_enabled:
                self._query_cache.clear()
            
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Failed to add document: {str(e)}")
            raise VectorError(f"Document addition failed: {str(e)}")

    def add_documents_batch(self, documents: List[Document]) -> List[str]:
        """
        Add multiple documents in batch.
        
        Args:
            documents: List of documents to add
            
        Returns:
            List of document IDs
            
        Raises:
            VectorError: If batch addition fails
        """
        try:
            if not self._collection:
                raise VectorError("Vector client not initialized")
            
            if not documents:
                return []
            
            # Prepare batch data
            doc_ids = []
            contents = []
            metadatas = []
            
            for doc in documents:
                doc_ids.append(doc.id)
                contents.append(doc.content)
                
                metadata = {
                    "doc_type": doc.doc_type.value,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat(),
                    "content_length": len(doc.content)
                }
                metadata.update(doc.metadata)
                metadatas.append(metadata)
            
            # Add batch to collection
            self._collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=doc_ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to vector store")
            
            # Update stats
            self._update_collection_stats()
            
            # Clear cache
            if self._cache_enabled:
                self._query_cache.clear()
            
            return doc_ids
            
        except Exception as e:
            self.logger.error(f"Failed to add documents batch: {str(e)}")
            raise VectorError(f"Batch addition failed: {str(e)}")

    def search(
        self,
        query: str,
        limit: int = 10,
        doc_type: Optional[DocumentType] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
        use_cache: bool = True
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            doc_type: Filter by document type
            metadata_filter: Additional metadata filters
            min_similarity: Minimum similarity score
            use_cache: Whether to use query caching
            
        Returns:
            List of search results
            
        Raises:
            VectorError: If search fails
        """
        start_time = datetime.now()
        
        try:
            if not self._collection:
                raise VectorError("Vector client not initialized")
            
            # Check cache first
            if use_cache and self._cache_enabled:
                cache_key = self._get_cache_key(query, limit, doc_type, metadata_filter)
                if cache_key in self._query_cache:
                    self._stats.cache_hits += 1
                    return self._query_cache[cache_key]
            
            # Build where clause for filtering
            where_clause = {}
            
            if doc_type:
                where_clause["doc_type"] = doc_type.value
            
            if metadata_filter:
                where_clause.update(metadata_filter)
            
            # Perform search
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            search_results = []
            
            if results["documents"] and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                ids = results["ids"][0] if results["ids"] else []
                
                for i, (doc_id, content) in enumerate(zip(ids, documents)):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity = max(0.0, 1.0 - distance)
                    
                    # Apply minimum similarity filter
                    if similarity < min_similarity:
                        continue
                    
                    # Create document
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    doc_type_value = metadata.get("doc_type", "general")
                    
                    try:
                        document_type = DocumentType(doc_type_value)
                    except ValueError:
                        document_type = DocumentType.GENERAL
                    
                    document = Document(
                        id=doc_id,
                        content=content,
                        metadata=metadata,
                        doc_type=document_type,
                        created_at=datetime.fromisoformat(
                            metadata.get("created_at", datetime.now().isoformat())
                        )
                    )
                    
                    search_results.append(SearchResult(
                        document=document,
                        similarity_score=similarity,
                        rank=i + 1
                    ))
            
            # Update statistics
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_query_stats(query_time)
            
            # Cache results
            if use_cache and self._cache_enabled:
                cache_key = self._get_cache_key(query, limit, doc_type, metadata_filter)
                self._query_cache[cache_key] = search_results
                self._stats.cache_misses += 1
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Vector search failed: {str(e)}")
            raise VectorError(f"Search failed: {str(e)}")

    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get a specific document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        try:
            if not self._collection:
                return None
            
            results = self._collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if results["documents"] and results["documents"][0]:
                content = results["documents"][0][0]
                metadata = results["metadatas"][0][0] if results["metadatas"] else {}
                
                doc_type_value = metadata.get("doc_type", "general")
                try:
                    document_type = DocumentType(doc_type_value)
                except ValueError:
                    document_type = DocumentType.GENERAL
                
                return Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    doc_type=document_type,
                    created_at=datetime.fromisoformat(
                        metadata.get("created_at", datetime.now().isoformat())
                    )
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get document {doc_id}: {str(e)}")
            return None

    def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing document.
        
        Args:
            doc_id: Document ID
            content: New content (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if successful
        """
        try:
            if not self._collection:
                return False
            
            # Get existing document
            existing = self.get_document(doc_id)
            if not existing:
                return False
            
            # Prepare update data
            update_data = {}
            
            if content is not None:
                update_data["documents"] = [content]
            
            if metadata is not None:
                updated_metadata = existing.metadata.copy()
                updated_metadata.update(metadata)
                updated_metadata["updated_at"] = datetime.now().isoformat()
                update_data["metadatas"] = [updated_metadata]
            
            # Update document
            if update_data:
                self._collection.update(
                    ids=[doc_id],
                    **update_data
                )
            
            # Clear cache
            if self._cache_enabled:
                self._query_cache.clear()
            
            self.logger.info(f"Updated document {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update document {doc_id}: {str(e)}")
            return False

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            if not self._collection:
                return False
            
            self._collection.delete(ids=[doc_id])
            
            # Update stats
            self._update_collection_stats()
            
            # Clear cache
            if self._cache_enabled:
                self._query_cache.clear()
            
            self.logger.info(f"Deleted document {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete document {doc_id}: {str(e)}")
            return False

    def get_similar_documents(
        self,
        doc_id: str,
        limit: int = 5,
        exclude_self: bool = True
    ) -> List[SearchResult]:
        """
        Find documents similar to a given document.
        
        Args:
            doc_id: Reference document ID
            limit: Maximum number of results
            exclude_self: Whether to exclude the reference document
            
        Returns:
            List of similar documents
        """
        try:
            # Get the reference document
            ref_doc = self.get_document(doc_id)
            if not ref_doc:
                return []
            
            # Search using the document content
            results = self.search(
                query=ref_doc.content[:1000],  # Use first 1000 chars
                limit=limit + (1 if exclude_self else 0)
            )
            
            # Filter out self if requested
            if exclude_self:
                results = [r for r in results if r.document.id != doc_id]
                results = results[:limit]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to find similar documents: {str(e)}")
            return []

    def _generate_document_id(self, content: str) -> str:
        """Generate a unique document ID based on content."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"doc_{timestamp}_{content_hash[:8]}"

    def _get_cache_key(
        self,
        query: str,
        limit: int,
        doc_type: Optional[DocumentType],
        metadata_filter: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for query."""
        cache_data = {
            "query": query,
            "limit": limit,
            "doc_type": doc_type.value if doc_type else None,
            "metadata_filter": metadata_filter
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _update_query_stats(self, query_time: float):
        """Update query statistics."""
        self._stats.total_queries += 1
        
        # Update average query time
        if self._stats.total_queries == 1:
            self._stats.average_query_time = query_time
        else:
            current_avg = self._stats.average_query_time
            self._stats.average_query_time = (
                (current_avg * (self._stats.total_queries - 1) + query_time) /
                self._stats.total_queries
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics."""
        return {
            "total_documents": self._stats.total_documents,
            "documents_by_type": dict(self._stats.documents_by_type),
            "total_queries": self._stats.total_queries,
            "average_query_time": self._stats.average_query_time,
            "cache_hits": self._stats.cache_hits,
            "cache_misses": self._stats.cache_misses,
            "cache_hit_rate": (
                self._stats.cache_hits / (self._stats.cache_hits + self._stats.cache_misses) * 100
                if (self._stats.cache_hits + self._stats.cache_misses) > 0 else 0
            ),
            "cache_size": len(self._query_cache),
            "collection_name": self._collection_name
        }

    def clear_cache(self):
        """Clear query cache."""
        self._query_cache.clear()
        self.logger.info("Vector query cache cleared")

    def set_cache_enabled(self, enabled: bool):
        """Enable or disable query caching."""
        self._cache_enabled = enabled
        self.logger.info(f"Vector query caching {'enabled' if enabled else 'disabled'}")

    def initialize_with_existing_documents(self) -> int:
        """
        Initialize vector store with existing documents from the data/raw directory.
        
        Returns:
            Number of documents added
        """
        try:
            import os
            
            docs_added = 0
            raw_data_path = "data/raw"
            
            if not os.path.exists(raw_data_path):
                self.logger.warning(f"Raw data directory not found: {raw_data_path}")
                return 0
            
            # Process each file in the raw directory
            for filename in os.listdir(raw_data_path):
                if filename.endswith(('.txt', '.md')):
                    file_path = os.path.join(raw_data_path, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        if content:
                            # Determine document type based on filename
                            doc_type = DocumentType.GENERAL
                            if 'code_of_conduct' in filename.lower():
                                doc_type = DocumentType.CODE_OF_CONDUCT
                            elif 'policy' in filename.lower() or 'principle' in filename.lower():
                                doc_type = DocumentType.POLICY
                            elif 'scope' in filename.lower():
                                doc_type = DocumentType.PROCEDURE
                            
                            # Add document
                            doc_id = self.add_document(
                                content=content,
                                doc_type=doc_type,
                                metadata={
                                    "filename": filename,
                                    "source": "raw_data"
                                }
                            )
                            
                            docs_added += 1
                            self.logger.info(f"Added document from {filename}: {doc_id}")
                    
                    except Exception as e:
                        self.logger.error(f"Failed to process file {filename}: {str(e)}")
            
            self.logger.info(f"Initialized vector store with {docs_added} documents")
            return docs_added
            
        except Exception as e:
            self.logger.error(f"Failed to initialize with existing documents: {str(e)}")
            return 0
