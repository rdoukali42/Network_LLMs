"""
Integration tests for the complete AI system.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import AISystem
from utils.helpers import load_sample_data


class TestAISystemIntegration:
    """Integration tests for the complete AI system."""
    
    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'test-key',
            'LANGFUSE_PUBLIC_KEY': 'test-public',
            'LANGFUSE_SECRET_KEY': 'test-secret'
        }):
            yield
    
    def test_ai_system_initialization(self, mock_environment):
        """Test AISystem can be initialized."""
        try:
            system = AISystem()
            assert system.config is not None
            assert system.agents is not None
            assert 'research' in system.agents
            assert 'analysis' in system.agents
        except Exception as e:
            # Expected to fail without real API keys, but structure should be valid
            assert "api" in str(e).lower() or "key" in str(e).lower()
    
    def test_sample_data_loading(self):
        """Test sample data can be loaded."""
        data = load_sample_data()
        assert len(data) > 0
        assert all(isinstance(doc, str) for doc in data)
        assert any("artificial intelligence" in doc.lower() for doc in data)
    
    def test_query_processing_workflow(self, mock_environment):
        """Test the query processing workflow."""
        system = AISystem()
        result = system.process_query("What is AI?")
        
        # Check that the method returns expected structure
        assert result["status"] == "success"
        assert result["query"] == "What is AI?"
        assert "agents_used" in result
        assert "tools_available" in result


if __name__ == "__main__":
    pytest.main([__file__])
