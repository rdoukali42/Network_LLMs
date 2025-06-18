"""
Unit tests for the AI system components.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config.config_loader import ConfigLoader
from agents import MaestroAgent, DataGuardianAgent
from tools.custom_tools import CalculatorTool, DocumentAnalysisTool


class TestConfigLoader:
    """Test cases for ConfigLoader."""
    
    def test_config_loader_initialization(self):
        """Test ConfigLoader can be initialized."""
        loader = ConfigLoader()
        assert loader.config_dir.name == "configs"
    
    def test_merge_configs(self):
        """Test configuration merging."""
        loader = ConfigLoader()
        
        base = {"a": 1, "b": {"x": 1, "y": 2}}
        override = {"b": {"x": 999}, "c": 3}
        
        result = loader._merge_configs(base, override)
        
        assert result["a"] == 1
        assert result["b"]["x"] == 999
        assert result["b"]["y"] == 2
        assert result["c"] == 3


class TestAgents:
    """Test cases for agents."""
    
    def test_maestro_agent_initialization(self):
        """Test MaestroAgent can be initialized."""
        agent = MaestroAgent()
        assert agent.name == "MaestroAgent"
        assert len(agent.tools) == 0
    
    def test_data_guardian_agent_initialization(self):
        """Test DataGuardianAgent can be initialized."""
        agent = DataGuardianAgent()
        assert agent.name == "DataGuardianAgent"
        assert len(agent.tools) == 0
    
    def test_agent_system_prompt(self):
        """Test agents have system prompts."""
        maestro_agent = MaestroAgent()
        data_guardian_agent = DataGuardianAgent()
        
        assert "maestro" in maestro_agent.get_system_prompt().lower()
        assert "guardian" in data_guardian_agent.get_system_prompt().lower()


class TestTools:
    """Test cases for custom tools."""
    
    def test_calculator_tool(self):
        """Test CalculatorTool."""
        tool = CalculatorTool()
        
        # Test valid calculation
        result = tool._run("2 + 2")
        assert result == "4"
        
        # Test invalid calculation
        result = tool._run("invalid expression")
        assert "Error" in result


if __name__ == "__main__":
    pytest.main([__file__])
