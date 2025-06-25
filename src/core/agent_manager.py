"""
Agent Manager for centralized agent lifecycle management.
Handles agent discovery, registration, health monitoring, and communication.
"""

import logging
from typing import Dict, List, Optional, Any, Type, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import inspect

from agents.base_agent import BaseAgent
from utils.exceptions import AgentError, ServiceError
from config.settings import Settings


class AgentStatus(Enum):
    """Agent status enumeration."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    name: str
    agent_class: Type[BaseAgent]
    instance: Optional[BaseAgent] = None
    status: AgentStatus = AgentStatus.INACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    average_response_time: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentManager:
    """
    Centralized agent management system.
    
    Provides:
    - Agent registration and discovery
    - Agent lifecycle management
    - Health monitoring and metrics
    - Load balancing and routing
    - Error handling and recovery
    """

    def __init__(self, settings: Settings):
        """
        Initialize the Agent Manager.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._agents: Dict[str, AgentInfo] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check = datetime.now()
        
        self.logger.info("Agent Manager initialized")

    def register_agent(
        self, 
        name: str, 
        agent_class: Type[BaseAgent], 
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an agent class with the manager.
        
        Args:
            name: Unique agent name
            agent_class: Agent class to register
            capabilities: List of agent capabilities
            metadata: Additional agent metadata
            
        Returns:
            True if registration successful
            
        Raises:
            AgentError: If registration fails
        """
        try:
            if name in self._agents:
                self.logger.warning(f"Agent {name} already registered, updating registration")
            
            # Validate agent class
            if not issubclass(agent_class, BaseAgent):
                raise AgentError(f"Agent class {agent_class.__name__} must inherit from BaseAgent")
            
            # Create agent info
            agent_info = AgentInfo(
                name=name,
                agent_class=agent_class,
                capabilities=capabilities or [],
                metadata=metadata or {}
            )
            
            self._agents[name] = agent_info
            self.logger.info(f"Agent {name} registered successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {name}: {str(e)}")
            raise AgentError(f"Agent registration failed: {str(e)}")

    def get_agent(self, name: str, auto_create: bool = True) -> Optional[BaseAgent]:
        """
        Get an agent instance by name.
        
        Args:
            name: Agent name
            auto_create: Whether to create instance if not exists
            
        Returns:
            Agent instance or None
            
        Raises:
            AgentError: If agent creation fails
        """
        try:
            if name not in self._agents:
                self.logger.error(f"Agent {name} not registered")
                return None
            
            agent_info = self._agents[name]
            
            # Return existing instance if available
            if agent_info.instance and agent_info.status == AgentStatus.ACTIVE:
                return agent_info.instance
            
            # Create new instance if requested
            if auto_create:
                return self._create_agent_instance(name)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get agent {name}: {str(e)}")
            raise AgentError(f"Failed to get agent: {str(e)}")

    def _create_agent_instance(self, name: str) -> BaseAgent:
        """
        Create a new agent instance.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance
            
        Raises:
            AgentError: If creation fails
        """
        try:
            agent_info = self._agents[name]
            
            # Get constructor parameters
            sig = inspect.signature(agent_info.agent_class.__init__)
            params = {}
            
            # Add common parameters if agent expects them
            if 'settings' in sig.parameters:
                params['settings'] = self.settings
            
            # Handle special agent requirements
            if name == "hr" and 'availability_tool' in sig.parameters:
                # Import and create availability tool for HR agent
                try:
                    from tools.availability_tool import AvailabilityTool
                    params['availability_tool'] = AvailabilityTool()
                    self.logger.info("Created AvailabilityTool for HR agent")
                except ImportError as e:
                    self.logger.warning(f"Could not import AvailabilityTool for HR agent: {e}")
                    params['availability_tool'] = None
            
            # Handle VocalAssistantAgent which expects 'config' instead of 'settings'
            if name == "vocal_assistant":
                if 'config' in sig.parameters:
                    # Convert settings to config dict for vocal assistant
                    params['config'] = self.settings.__dict__ if hasattr(self.settings, '__dict__') else {}
                if 'tools' in sig.parameters:
                    params['tools'] = []  # Empty tools list for now
            
            # Create instance
            instance = agent_info.agent_class(**params)
            
            # Update agent info
            agent_info.instance = instance
            agent_info.status = AgentStatus.ACTIVE
            agent_info.last_activity = datetime.now()
            
            # Store instance reference
            self._agent_instances[name] = instance
            
            self.logger.info(f"Created instance for agent {name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Failed to create agent instance {name}: {str(e)}")
            agent_info.status = AgentStatus.ERROR
            raise AgentError(f"Agent creation failed: {str(e)}")

    async def call_agent(
        self, 
        agent_name: str, 
        method_name: str, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Call a method on an agent with tracking and error handling.
        
        Args:
            agent_name: Name of the agent to call
            method_name: Method name to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Method result
            
        Raises:
            AgentError: If agent call fails
        """
        start_time = datetime.now()
        agent_info = self._agents.get(agent_name)
        
        if not agent_info:
            raise AgentError(f"Agent {agent_name} not registered")
        
        try:
            # Get agent instance
            agent = self.get_agent(agent_name)
            if not agent:
                raise AgentError(f"Could not get agent {agent_name}")
            
            # Update status
            agent_info.status = AgentStatus.BUSY
            
            # Call method
            if not hasattr(agent, method_name):
                raise AgentError(f"Agent {agent_name} does not have method {method_name}")
            
            method = getattr(agent, method_name)
            
            # Handle async methods
            if asyncio.iscoroutinefunction(method):
                result = await method(*args, **kwargs)
            else:
                result = method(*args, **kwargs)
            
            # Update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_agent_metrics(agent_name, True, response_time)
            
            agent_info.status = AgentStatus.ACTIVE
            agent_info.last_activity = datetime.now()
            
            return result
            
        except Exception as e:
            # Update metrics for failed call
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_agent_metrics(agent_name, False, response_time)
            
            agent_info.status = AgentStatus.ERROR
            self.logger.error(f"Agent call failed {agent_name}.{method_name}: {str(e)}")
            raise AgentError(f"Agent call failed: {str(e)}")

    async def execute_agent(
        self, 
        agent_name: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an agent with input data using the standard 'run' method.
        
        Args:
            agent_name: Name of the agent to execute
            input_data: Input data for the agent
            
        Returns:
            Agent execution result
            
        Raises:
            AgentError: If agent execution fails
        """
        return await self.call_agent(agent_name, "run", input_data)

    def _update_agent_metrics(self, agent_name: str, success: bool, response_time: float):
        """Update agent performance metrics."""
        agent_info = self._agents.get(agent_name)
        if not agent_info:
            return
        
        agent_info.total_calls += 1
        
        if success:
            agent_info.successful_calls += 1
        else:
            agent_info.failed_calls += 1
        
        # Update average response time
        if agent_info.total_calls == 1:
            agent_info.average_response_time = response_time
        else:
            # Running average calculation
            current_avg = agent_info.average_response_time
            agent_info.average_response_time = (
                (current_avg * (agent_info.total_calls - 1) + response_time) / agent_info.total_calls
            )

    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics for agents.
        
        Args:
            agent_name: Specific agent name or None for all agents
            
        Returns:
            Dictionary of agent metrics
        """
        if agent_name:
            if agent_name not in self._agents:
                return {}
            
            agent_info = self._agents[agent_name]
            return {
                "name": agent_info.name,
                "status": agent_info.status.value,
                "total_calls": agent_info.total_calls,
                "successful_calls": agent_info.successful_calls,
                "failed_calls": agent_info.failed_calls,
                "success_rate": (
                    agent_info.successful_calls / agent_info.total_calls * 100 
                    if agent_info.total_calls > 0 else 0
                ),
                "average_response_time": agent_info.average_response_time,
                "last_activity": agent_info.last_activity.isoformat() if agent_info.last_activity else None,
                "capabilities": agent_info.capabilities
            }
        
        # Return metrics for all agents
        metrics = {}
        for name, agent_info in self._agents.items():
            metrics[name] = {
                "status": agent_info.status.value,
                "total_calls": agent_info.total_calls,
                "successful_calls": agent_info.successful_calls,
                "success_rate": (
                    agent_info.successful_calls / agent_info.total_calls * 100 
                    if agent_info.total_calls > 0 else 0
                ),
                "average_response_time": agent_info.average_response_time
            }
        
        return metrics

    def get_available_agents(self, capability: Optional[str] = None) -> List[str]:
        """
        Get list of available agents, optionally filtered by capability.
        
        Args:
            capability: Optional capability filter
            
        Returns:
            List of agent names
        """
        available = []
        
        for name, agent_info in self._agents.items():
            if agent_info.status in [AgentStatus.ACTIVE, AgentStatus.INACTIVE]:
                if capability is None or capability in agent_info.capabilities:
                    available.append(name)
        
        return available

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all agents.
        
        Returns:
            Health check results
        """
        if datetime.now() - self._last_health_check < timedelta(seconds=self._health_check_interval):
            # Skip if recent health check
            return {"status": "skipped", "reason": "recent_check"}
        
        self._last_health_check = datetime.now()
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self._agents),
            "active_agents": 0,
            "inactive_agents": 0,
            "error_agents": 0,
            "agent_details": {}
        }
        
        for name, agent_info in self._agents.items():
            status = agent_info.status.value
            results["agent_details"][name] = {
                "status": status,
                "last_activity": agent_info.last_activity.isoformat() if agent_info.last_activity else None,
                "total_calls": agent_info.total_calls
            }
            
            if status == "active":
                results["active_agents"] += 1
            elif status == "inactive":
                results["inactive_agents"] += 1
            elif status == "error":
                results["error_agents"] += 1
        
        self.logger.info(f"Health check completed: {results['active_agents']} active, {results['error_agents']} errors")
        return results

    def shutdown_agent(self, agent_name: str) -> bool:
        """
        Shutdown a specific agent.
        
        Args:
            agent_name: Name of agent to shutdown
            
        Returns:
            True if successful
        """
        try:
            if agent_name not in self._agents:
                return False
            
            agent_info = self._agents[agent_name]
            
            # Clean up instance
            if agent_info.instance:
                # Call cleanup method if available
                if hasattr(agent_info.instance, 'cleanup'):
                    agent_info.instance.cleanup()
                
                agent_info.instance = None
            
            # Remove from instances
            if agent_name in self._agent_instances:
                del self._agent_instances[agent_name]
            
            agent_info.status = AgentStatus.INACTIVE
            
            self.logger.info(f"Agent {agent_name} shutdown successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown agent {agent_name}: {str(e)}")
            return False

    def shutdown_all(self):
        """Shutdown all agents."""
        self.logger.info("Shutting down all agents")
        
        for agent_name in list(self._agents.keys()):
            self.shutdown_agent(agent_name)
        
        self._agent_instances.clear()
        self.logger.info("All agents shutdown completed")

    def get_agent_by_capability(self, capability: str) -> Optional[str]:
        """
        Get the best available agent for a specific capability.
        
        Args:
            capability: Required capability
            
        Returns:
            Agent name or None
        """
        available_agents = []
        
        for name, agent_info in self._agents.items():
            if (capability in agent_info.capabilities and 
                agent_info.status in [AgentStatus.ACTIVE, AgentStatus.INACTIVE]):
                available_agents.append((name, agent_info))
        
        if not available_agents:
            return None
        
        # Sort by success rate and response time
        available_agents.sort(key=lambda x: (
            x[1].successful_calls / max(x[1].total_calls, 1),  # Success rate
            -x[1].average_response_time  # Negative for lower response time priority
        ), reverse=True)
        
        return available_agents[0][0]
