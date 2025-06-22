"""
Configuration loader for the AI system core.
Handles loading different configurations (dev, prod) and API keys.
"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

class CoreConfigLoader:
    def __init__(self, base_project_root: Path, config_dir_name: str = "config"):
        """
        Initializes the config loader.
        Args:
            base_project_root: The absolute path to the 'optimized_project' root.
            config_dir_name: The name of the directory within 'optimized_project' that holds config.yaml files.
        """
        self.project_root = base_project_root
        self.config_dir = self.project_root / config_dir_name # e.g., optimized_project/config/

        # Load .env file from optimized_project root
        env_path = self.project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded environment variables from {env_path}")
        else:
            print(f".env file not found at {env_path}. API keys should be set in the environment.")

    def load_config_yaml(self, config_name: str = "development") -> Dict[str, Any]:
        """Load YAML configuration by name (e.g., development.yaml)."""
        config_path = self.config_dir / f"{config_name}.yaml"

        if not config_path.exists():
            # Fallback to development config if production is requested but not found
            if config_name == "production":
                print(f"Warning: Configuration file {config_path} not found. Trying development.yaml.")
                config_path = self.config_dir / "development.yaml"
                if not config_path.exists():
                    raise FileNotFoundError(f"Fallback configuration file {config_path} also not found.")
            else:
                raise FileNotFoundError(f"Configuration file {config_path} not found.")

        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def get_api_key(self, service_name: str, config_yaml: Dict[str, Any]) -> str | None:
        """
        Retrieves an API key.
        Priority:
        1. Environment variable (e.g., GEMINI_API_KEY)
        2. Value from config_yaml (e.g., config_yaml['api_keys']['gemini'])
        """
        env_var_name = f"{service_name.upper()}_API_KEY"
        api_key = os.getenv(env_var_name)

        if api_key:
            # print(f"Loaded {service_name} API key from environment variable {env_var_name}")
            return api_key

        if config_yaml and 'api_keys' in config_yaml and service_name in config_yaml['api_keys']:
            key_from_yaml = config_yaml['api_keys'][service_name]
            # print(f"Loaded {service_name} API key from YAML config.")
            return key_from_yaml

        # print(f"Warning: {service_name} API key not found in environment variables or YAML config.")
        return None

    def get_model_config(self, model_name: str, config_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieves model-specific configurations."""
        return config_yaml.get("models", {}).get(model_name, {})

    def get_vector_store_config(self, config_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieves vector store configurations."""
        return config_yaml.get("vector_store", {})

# Note: A global instance is not created here.
# The AISystem or other core components will instantiate CoreConfigLoader.
# Example usage:
# project_root = Path(__file__).resolve().parent.parent # Get optimized_project root
# config_loader = CoreConfigLoader(base_project_root=project_root)
# core_settings = config_loader.load_config_yaml("development")
# gemini_key = config_loader.get_api_key("gemini", core_settings)

"""
Example development.yaml (to be placed in optimized_project/config/development.yaml):

api_keys:
  gemini: "YOUR_GEMINI_API_KEY_HERE_OR_SET_ENV_VAR" # Or leave empty if using ENV VAR
  # google_cloud_tts: "YOUR_GOOGLE_CLOUD_TTS_API_KEY_HERE_OR_SET_ENV_VAR" # Example for specific service
  # google_cloud_stt: "YOUR_GOOGLE_CLOUD_STT_API_KEY_HERE_OR_SET_ENV_VAR" # Example

models:
  gemini_pro:
    temperature: 0.7
    max_tokens: 2048
  # Specific models for agents if needed
  maestro_model:
    # inherits from gemini_pro or specific settings
    temperature: 0.6
  data_guardian_model:
    temperature: 0.5

vector_store:
  type: "FAISS" # or "Chroma", "Pinecone" etc.
  persist_directory: "data/vector_store_db" # Relative to optimized_project root
  embedding_model: "all-MiniLM-L6-v2" # Example sentence transformer

# Other core system settings
logging_level: "INFO"

"""
