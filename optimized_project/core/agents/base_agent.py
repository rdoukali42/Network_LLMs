"""
Base agent class for all agents in the optimized_project system.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from langchain.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI # Assuming Gemini is the primary LLM
# from langchain_openai import ChatOpenAI # Example if you were to support OpenAI

# Langfuse for observability, assuming it's kept
from langfuse import observe

# Configuration related imports
# from config.core_config import CoreConfigLoader # Agents will receive config dict directly

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Agents are initialized with a configuration dictionary and a list of tools.
    """

    def __init__(self, name: str, agent_config: Dict[str, Any], tools: Optional[List[BaseTool]] = None):
        """
        Initializes the BaseAgent.
        Args:
            name: The name of the agent.
            agent_config: A dictionary containing configuration for this agent,
                          including LLM settings and API keys (or how to get them).
                          Expected structure:
                          {
                              "llm_provider": "google_gemini", # or "openai"
                              "model_name": "gemini-pro",
                              "temperature": 0.7,
                              "api_key_env_var": "GEMINI_API_KEY" # Environment variable name for the API key
                          }
            tools: An optional list of Langchain tools available to this agent.
        """
        self.name = name
        self.tools = tools or []
        self.agent_config = agent_config

        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> Optional[Any]:
        """Initializes the language model based on agent_config."""
        llm_provider = self.agent_config.get("llm_provider", "google_gemini")
        model_name = self.agent_config.get("model_name")
        temperature = self.agent_config.get("temperature", 0.7)
        api_key_env_var = self.agent_config.get("api_key_env_var")

        api_key = None
        if api_key_env_var:
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                print(f"Warning: Environment variable {api_key_env_var} for agent '{self.name}' not set.")

        if not model_name:
            print(f"Warning: No model_name configured for agent '{self.name}'. LLM will not be initialized.")
            return None

        try:
            if llm_provider == "google_gemini":
                # ChatGoogleGenerativeAI uses GOOGLE_API_KEY by default if api_key is None
                # or a specific key if provided.
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=float(temperature), # Ensure temperature is float
                    google_api_key=api_key # Pass the specific key if found
                )
            # Example for OpenAI:
            # elif llm_provider == "openai":
            #     if not api_key: # OpenAI client strictly needs the key
            #         print(f"Error: API key for OpenAI (env var: {api_key_env_var}) not found for agent '{self.name}'.")
            #         return None
            #     return ChatOpenAI(model_name=model_name, temperature=float(temperature), openai_api_key=api_key)
            else:
                print(f"Warning: Unsupported LLM provider '{llm_provider}' for agent '{self.name}'.")
                return None
        except Exception as e:
            print(f"Error initializing LLM for agent '{self.name}' with provider '{llm_provider}': {e}")
            return None

    @abstractmethod
    @observe() # Keep Langfuse decorator if desired
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with given input.
        This method must be implemented by subclasses.
        Args:
            input_data: A dictionary containing the input for the agent.
                        The structure depends on the specific agent.
        Returns:
            A dictionary containing the agent's output.
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt for this agent.
        This method must be implemented by subclasses.
        """
        pass

# Example of how an agent might get its config in AISystem:
# agent_specific_config = core_config_dict.get("agents", {}).get("maestro_agent", {})
# merged_llm_config = {**core_config_dict.get("models", {}).get("default_llm", {}), **agent_specific_config.get("llm", {})}
# maestro_agent_config = {
#     "llm_provider": merged_llm_config.get("provider", "google_gemini"),
#     "model_name": merged_llm_config.get("model_name", "gemini-pro"), # Fallback to a default
#     "temperature": merged_llm_config.get("temperature", 0.7),
#     "api_key_env_var": merged_llm_config.get("api_key_env_var", "GEMINI_API_KEY") # Central default
# }
# maestro = MaestroAgent(agent_config=maestro_agent_config, tools=[...])
