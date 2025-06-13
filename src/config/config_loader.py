"""
Configuration loader for the AI project.
Handles loading different configurations (dev, prod, experiments).
"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
    
    def load_config(self, config_name: str = "development") -> Dict[str, Any]:
        """Load configuration by name."""
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file {config_path} not found")
        
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def load_experiment_config(self, experiment_name: str) -> Dict[str, Any]:
        """Load experiment configuration."""
        experiment_path = self.config_dir / "experiments" / f"{experiment_name}.yaml"
        
        if not experiment_path.exists():
            raise FileNotFoundError(f"Experiment config {experiment_path} not found")
        
        # Load base development config
        base_config = self.load_config("development")
        
        # Load experiment overrides
        with open(experiment_path, 'r') as file:
            experiment_config = yaml.safe_load(file)
        
        # Merge configurations
        return self._merge_configs(base_config, experiment_config)
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result


# Global config instance
config_loader = ConfigLoader()
