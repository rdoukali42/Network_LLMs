"""
LLM Client for centralized language model integration.
Provides unified interface for different LLM providers with error handling, caching, and monitoring.
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import hashlib

try:
    from config.settings import Settings
except ImportError:
    # Fallback for different import paths
    try:
        from config.settings import Settings
    except ImportError:
        Settings = None

try:
    from utils.exceptions import LLMError, ServiceError
except ImportError:
    # Fallback exceptions
    class LLMError(Exception):
        pass
    
    class ServiceError(Exception):
        pass


class LLMProvider(Enum):
    """Supported LLM providers."""
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class MessageRole(Enum):
    """Message roles for conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Individual message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LLMRequest:
    """LLM request configuration."""
    messages: List[LLMMessage]
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM response with metadata."""
    content: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int]
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMStats:
    """LLM usage statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    requests_by_model: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)


class LLMClient:
    """
    Centralized LLM client with support for multiple providers.
    
    Features:
    - Multiple LLM provider support (Google, OpenAI, Anthropic)
    - Response caching for efficiency
    - Rate limiting and retry logic
    - Usage tracking and cost monitoring
    - Error handling and fallback providers
    - Token usage optimization
    """

    def __init__(self, settings):
        """
        Initialize the LLM client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Client instances
        self._clients: Dict[LLMProvider, Any] = {}
        
        # Configuration
        self._default_provider = LLMProvider.GOOGLE
        self._fallback_providers = [LLMProvider.GOOGLE, LLMProvider.OPENAI]
        
        # Caching
        self._cache: Dict[str, LLMResponse] = {}
        self._cache_ttl = 3600  # 1 hour
        self._cache_enabled = True
        
        # Rate limiting
        self._rate_limits: Dict[LLMProvider, Dict[str, Any]] = {
            LLMProvider.GOOGLE: {"requests_per_minute": 60, "tokens_per_minute": 60000},
            LLMProvider.OPENAI: {"requests_per_minute": 60, "tokens_per_minute": 60000},
            LLMProvider.ANTHROPIC: {"requests_per_minute": 50, "tokens_per_minute": 50000}
        }
        self._request_times: Dict[LLMProvider, List[datetime]] = {
            provider: [] for provider in LLMProvider
        }
        
        # Statistics
        self._stats = LLMStats()
        
        # Initialize clients
        self._initialize_clients()
        
        self.logger.info("LLM Client initialized")

    def _initialize_clients(self):
        """Initialize LLM provider clients."""
        try:
            # Initialize Google client (Gemini)
            try:
                import google.generativeai as genai
                
                api_key = self.settings.get_setting("GOOGLE_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                    self._clients[LLMProvider.GOOGLE] = genai
                    self.logger.info("Google Gemini client initialized")
            except ImportError:
                self.logger.warning("Google GenerativeAI library not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google client: {e}")
            
            # Initialize OpenAI client
            try:
                import openai
                
                api_key = self.settings.get_setting("OPENAI_API_KEY")
                if api_key:
                    openai.api_key = api_key
                    self._clients[LLMProvider.OPENAI] = openai
                    self.logger.info("OpenAI client initialized")
            except ImportError:
                self.logger.warning("OpenAI library not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
            
            # Initialize Anthropic client
            try:
                import anthropic
                
                api_key = self.settings.get_setting("ANTHROPIC_API_KEY")
                if api_key:
                    client = anthropic.Anthropic(api_key=api_key)
                    self._clients[LLMProvider.ANTHROPIC] = client
                    self.logger.info("Anthropic client initialized")
            except ImportError:
                self.logger.warning("Anthropic library not available")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic client: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM clients: {e}")

    async def chat_completion(
        self,
        messages: List[Union[LLMMessage, Dict[str, str]]],
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True,
        **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion using specified provider and model.
        
        Args:
            messages: Conversation messages
            model: Model name to use
            provider: LLM provider to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_cache: Whether to use response caching
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response
            
        Raises:
            LLMError: If request fails across all providers
        """
        start_time = time.time()
        
        try:
            # Normalize messages
            normalized_messages = self._normalize_messages(messages)
            
            # Set defaults
            provider = provider or self._default_provider
            model = model or self._get_default_model(provider)
            
            # Create request
            request = LLMRequest(
                messages=normalized_messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Check cache first
            if use_cache and self._cache_enabled:
                cached_response = self._get_cached_response(request)
                if cached_response:
                    self._stats.cached_requests += 1
                    return cached_response
            
            # Check rate limits
            if not self._check_rate_limit(provider):
                # Try fallback providers
                for fallback_provider in self._fallback_providers:
                    if fallback_provider != provider and self._check_rate_limit(fallback_provider):
                        provider = fallback_provider
                        model = self._get_default_model(provider)
                        request.model = model
                        break
                else:
                    raise LLMError("Rate limit exceeded for all providers")
            
            # Make request
            response = await self._make_request(provider, request)
            
            # Update statistics
            response_time = time.time() - start_time
            response.response_time = response_time
            self._update_stats(True, response_time, response.usage, model)
            
            # Cache response
            if use_cache and self._cache_enabled:
                self._cache_response(request, response)
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(False, response_time, {}, model or "unknown")
            self.logger.error(f"LLM request failed: {str(e)}")
            raise LLMError(f"Chat completion failed: {str(e)}")

    def _normalize_messages(self, messages: List[Union[LLMMessage, Dict[str, str]]]) -> List[LLMMessage]:
        """Normalize messages to LLMMessage objects."""
        normalized = []
        
        for msg in messages:
            if isinstance(msg, LLMMessage):
                normalized.append(msg)
            elif isinstance(msg, dict):
                role = MessageRole(msg.get("role", "user"))
                content = msg.get("content", "")
                normalized.append(LLMMessage(role=role, content=content))
            else:
                raise LLMError(f"Invalid message format: {type(msg)}")
        
        return normalized

    def _get_default_model(self, provider: LLMProvider) -> str:
        """Get default model for provider."""
        defaults = {
            LLMProvider.GOOGLE: "gemini-1.5-flash",
            LLMProvider.OPENAI: "gpt-3.5-turbo",
            LLMProvider.ANTHROPIC: "claude-3-haiku-20240307"
        }
        return defaults.get(provider, "gemini-1.5-flash")

    def _check_rate_limit(self, provider: LLMProvider) -> bool:
        """Check if request is within rate limits."""
        now = datetime.now()
        limits = self._rate_limits.get(provider, {})
        
        if not limits:
            return True
        
        # Clean old requests
        cutoff = now - timedelta(minutes=1)
        provider_requests = self._request_times[provider]
        self._request_times[provider] = [
            req_time for req_time in provider_requests 
            if req_time > cutoff
        ]
        
        # Check rate limit
        requests_per_minute = limits.get("requests_per_minute", 60)
        current_requests = len(self._request_times[provider])
        
        return current_requests < requests_per_minute

    async def _make_request(self, provider: LLMProvider, request: LLMRequest) -> LLMResponse:
        """Make request to specific provider."""
        # Record request time for rate limiting
        self._request_times[provider].append(datetime.now())
        
        if provider == LLMProvider.GOOGLE:
            return await self._make_google_request(request)
        elif provider == LLMProvider.OPENAI:
            return await self._make_openai_request(request)
        elif provider == LLMProvider.ANTHROPIC:
            return await self._make_anthropic_request(request)
        else:
            raise LLMError(f"Unsupported provider: {provider}")

    async def _make_google_request(self, request: LLMRequest) -> LLMResponse:
        """Make request to Google Gemini."""
        try:
            client = self._clients.get(LLMProvider.GOOGLE)
            if not client:
                raise LLMError("Google client not initialized")
            
            # Convert messages to Google format
            conversation_text = ""
            for msg in request.messages:
                if msg.role == MessageRole.SYSTEM:
                    conversation_text += f"System: {msg.content}\n\n"
                elif msg.role == MessageRole.USER:
                    conversation_text += f"User: {msg.content}\n\n"
                elif msg.role == MessageRole.ASSISTANT:
                    conversation_text += f"Assistant: {msg.content}\n\n"
            
            # Remove last newlines and add final prompt
            conversation_text = conversation_text.strip() + "\n\nAssistant: "
            
            # Configure model
            model = client.GenerativeModel(request.model)
            
            # Generate response
            response = await asyncio.to_thread(
                model.generate_content,
                conversation_text,
                generation_config={
                    "max_output_tokens": request.max_tokens or 2048,
                    "temperature": request.temperature or 0.7,
                    "top_p": request.top_p or 0.95,
                }
            )
            
            # Extract content
            content = response.text if response.text else ""
            
            # Calculate usage (approximate for Google)
            usage = {
                "prompt_tokens": len(conversation_text.split()) * 1.3,  # Rough estimate
                "completion_tokens": len(content.split()) * 1.3,
                "total_tokens": 0
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider=LLMProvider.GOOGLE,
                usage=usage,
                response_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            self.logger.error(f"Google API request failed: {str(e)}")
            raise LLMError(f"Google API error: {str(e)}")

    async def _make_openai_request(self, request: LLMRequest) -> LLMResponse:
        """Make request to OpenAI."""
        try:
            client = self._clients.get(LLMProvider.OPENAI)
            if not client:
                raise LLMError("OpenAI client not initialized")
            
            # Convert messages to OpenAI format
            openai_messages = []
            for msg in request.messages:
                openai_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
            
            # Make request
            response = await asyncio.to_thread(
                client.ChatCompletion.create,
                model=request.model,
                messages=openai_messages,
                max_tokens=request.max_tokens or 2048,
                temperature=request.temperature or 0.7,
                top_p=request.top_p or 1.0,
                frequency_penalty=request.frequency_penalty or 0.0,
                presence_penalty=request.presence_penalty or 0.0,
                stop=request.stop_sequences
            )
            
            # Extract content
            content = response.choices[0].message.content
            
            # Get usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider=LLMProvider.OPENAI,
                usage=usage,
                response_time=0.0
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI API request failed: {str(e)}")
            raise LLMError(f"OpenAI API error: {str(e)}")

    async def _make_anthropic_request(self, request: LLMRequest) -> LLMResponse:
        """Make request to Anthropic Claude."""
        try:
            client = self._clients.get(LLMProvider.ANTHROPIC)
            if not client:
                raise LLMError("Anthropic client not initialized")
            
            # Convert messages to Anthropic format
            system_message = ""
            anthropic_messages = []
            
            for msg in request.messages:
                if msg.role == MessageRole.SYSTEM:
                    system_message += msg.content + "\n"
                else:
                    anthropic_messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            # Make request
            response = await asyncio.to_thread(
                client.messages.create,
                model=request.model,
                max_tokens=request.max_tokens or 2048,
                temperature=request.temperature or 0.7,
                system=system_message.strip() if system_message else None,
                messages=anthropic_messages
            )
            
            # Extract content
            content = ""
            for content_block in response.content:
                if content_block.type == "text":
                    content += content_block.text
            
            # Get usage
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider=LLMProvider.ANTHROPIC,
                usage=usage,
                response_time=0.0
            )
            
        except Exception as e:
            self.logger.error(f"Anthropic API request failed: {str(e)}")
            raise LLMError(f"Anthropic API error: {str(e)}")

    def _get_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request."""
        # Create hash of request content
        request_data = {
            "messages": [(msg.role.value, msg.content) for msg in request.messages],
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()

    def _get_cached_response(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Get cached response if available and not expired."""
        cache_key = self._get_cache_key(request)
        
        if cache_key in self._cache:
            cached_response = self._cache[cache_key]
            
            # Check if expired
            age = datetime.now() - cached_response.timestamp
            if age.total_seconds() < self._cache_ttl:
                cached_response.cached = True
                return cached_response
            else:
                # Remove expired entry
                del self._cache[cache_key]
        
        return None

    def _cache_response(self, request: LLMRequest, response: LLMResponse):
        """Cache response for future use."""
        cache_key = self._get_cache_key(request)
        
        # Limit cache size
        if len(self._cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(
                self._cache.items(),
                key=lambda x: x[1].timestamp
            )
            for key, _ in sorted_cache[:100]:  # Remove 100 oldest
                del self._cache[key]
        
        self._cache[cache_key] = response

    def _update_stats(self, success: bool, response_time: float, usage: Dict[str, int], model: str):
        """Update usage statistics."""
        self._stats.total_requests += 1
        
        if success:
            self._stats.successful_requests += 1
        else:
            self._stats.failed_requests += 1
        
        # Update response time average
        if self._stats.total_requests == 1:
            self._stats.average_response_time = response_time
        else:
            current_avg = self._stats.average_response_time
            self._stats.average_response_time = (
                (current_avg * (self._stats.total_requests - 1) + response_time) / 
                self._stats.total_requests
            )
        
        # Update token usage
        if "total_tokens" in usage:
            self._stats.total_tokens_used += usage["total_tokens"]
        
        # Update model usage
        if model in self._stats.requests_by_model:
            self._stats.requests_by_model[model] += 1
        else:
            self._stats.requests_by_model[model] = 1

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self._stats.total_requests,
            "successful_requests": self._stats.successful_requests,
            "failed_requests": self._stats.failed_requests,
            "cached_requests": self._stats.cached_requests,
            "success_rate": (
                self._stats.successful_requests / self._stats.total_requests * 100
                if self._stats.total_requests > 0 else 0
            ),
            "cache_hit_rate": (
                self._stats.cached_requests / self._stats.total_requests * 100
                if self._stats.total_requests > 0 else 0
            ),
            "total_tokens_used": self._stats.total_tokens_used,
            "average_response_time": self._stats.average_response_time,
            "requests_by_model": dict(self._stats.requests_by_model),
            "cache_size": len(self._cache),
            "available_providers": list(self._clients.keys())
        }

    def clear_cache(self):
        """Clear response cache."""
        self._cache.clear()
        self.logger.info("LLM response cache cleared")

    def set_cache_enabled(self, enabled: bool):
        """Enable or disable response caching."""
        self._cache_enabled = enabled
        self.logger.info(f"LLM response caching {'enabled' if enabled else 'disabled'}")

    async def simple_completion(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Simple completion for single prompt.
        
        Args:
            prompt: Input prompt
            model: Model to use
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        messages = [LLMMessage(role=MessageRole.USER, content=prompt)]
        response = await self.chat_completion(messages, model=model, **kwargs)
        return response.content

    def get_llm(self, model: str = "gemini-1.5-flash"):
        """
        Get a basic LLM interface for backward compatibility.
        This method provides a simple interface for agents that expect an LLM object.
        """
        class SimpleLLMWrapper:
            """Simple wrapper to provide LLM-like interface."""
            
            def __init__(self, llm_client, model):
                self.llm_client = llm_client
                self.model = model
            
            def invoke(self, messages):
                """Invoke the LLM with messages."""
                try:
                    if isinstance(messages, str):
                        # Simple string input
                        from integrations.llm_client import LLMMessage, MessageRole
                        message_objs = [LLMMessage(role=MessageRole.USER, content=messages)]
                    elif isinstance(messages, list):
                        # List of message objects or dicts
                        from integrations.llm_client import LLMMessage, MessageRole
                        message_objs = []
                        for msg in messages:
                            if isinstance(msg, dict):
                                role = MessageRole(msg.get("role", "user"))
                                content = msg.get("content", "")
                                message_objs.append(LLMMessage(role=role, content=content))
                            else:
                                message_objs.append(msg)
                    else:
                        # Assume it's already in the right format
                        message_objs = messages
                    
                    # Make async call synchronously
                    import asyncio
                    try:
                        # Try to get the current event loop
                        try:
                            loop = asyncio.get_running_loop()
                            # If there's a running loop, we need to handle this differently
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(self.llm_client._sync_chat_completion, message_objs, self.model)
                                response = future.result()
                        except RuntimeError:
                            # No running loop, safe to create one
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                response = loop.run_until_complete(
                                    self.llm_client.chat_completion(message_objs, model=self.model)
                                )
                            finally:
                                loop.close()
                    except Exception as e:
                        self.llm_client.logger.error(f"LLM call failed: {e}")
                        raise e
                    
                    # Return simple response object
                    class SimpleResponse:
                        def __init__(self, content):
                            self.content = content
                    
                    return SimpleResponse(response.content)
                    
                except Exception as e:
                    # Return error response
                    class ErrorResponse:
                        def __init__(self, error):
                            self.content = f"Error: {str(error)}"
                    
                    return ErrorResponse(e)
        
        return SimpleLLMWrapper(self, model)

    def get_statistics(self) -> Dict[str, Any]:
        """Get LLM usage statistics."""
        return self.get_stats()

    def _sync_chat_completion(self, messages, model):
        """
        Helper method to run chat completion synchronously in a separate thread.
        This avoids event loop conflicts when called from within an existing loop.
        """
        import asyncio
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async chat completion
            response = loop.run_until_complete(
                self.chat_completion(messages, model=model)
            )
            return response
        finally:
            # Clean up the event loop
            loop.close()
