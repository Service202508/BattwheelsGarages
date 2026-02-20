"""
Battwheels Knowledge Brain - LLM Provider Interface
Abstraction layer for swappable LLM models
"""

import os
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = None
    finish_reason: str = "complete"
    error: Optional[str] = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Implement this interface to add new LLM backends.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name"""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt/query
            system_message: System message for context
            session_id: Optional session ID for conversation tracking
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available"""
        pass


class GeminiProvider(LLMProvider):
    """
    Gemini LLM Provider using Emergent Integrations library.
    Primary provider for Battwheels Knowledge Brain.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3-flash-preview"
    ):
        self._api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        self._model = model
        self._provider = "gemini"
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    async def generate(
        self,
        prompt: str,
        system_message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="LLM service unavailable. API key not configured.",
                model=self._model,
                provider=self._provider,
                error="API key not configured"
            )
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            sid = session_id or f"kb_rag_{uuid.uuid4().hex[:8]}"
            
            chat = LlmChat(
                api_key=self._api_key,
                session_id=sid,
                system_message=system_message
            ).with_model(self._provider, self._model)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return LLMResponse(
                content=response,
                model=self._model,
                provider=self._provider,
                finish_reason="complete"
            )
            
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return LLMResponse(
                content="I encountered an error generating a response. Please try again.",
                model=self._model,
                provider=self._provider,
                error=str(e)
            )


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM Provider using Emergent Integrations library.
    Alternative provider for fallback or preference.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5.2"
    ):
        self._api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        self._model = model
        self._provider = "openai"
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    async def generate(
        self,
        prompt: str,
        system_message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="LLM service unavailable. API key not configured.",
                model=self._model,
                provider=self._provider,
                error="API key not configured"
            )
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            sid = session_id or f"kb_rag_{uuid.uuid4().hex[:8]}"
            
            chat = LlmChat(
                api_key=self._api_key,
                session_id=sid,
                system_message=system_message
            ).with_model(self._provider, self._model)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return LLMResponse(
                content=response,
                model=self._model,
                provider=self._provider,
                finish_reason="complete"
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return LLMResponse(
                content="I encountered an error generating a response. Please try again.",
                model=self._model,
                provider=self._provider,
                error=str(e)
            )


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude LLM Provider using Emergent Integrations library.
    Alternative provider for fallback or preference.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929"
    ):
        self._api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        self._model = model
        self._provider = "anthropic"
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    async def generate(
        self,
        prompt: str,
        system_message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="LLM service unavailable. API key not configured.",
                model=self._model,
                provider=self._provider,
                error="API key not configured"
            )
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            sid = session_id or f"kb_rag_{uuid.uuid4().hex[:8]}"
            
            chat = LlmChat(
                api_key=self._api_key,
                session_id=sid,
                system_message=system_message
            ).with_model(self._provider, self._model)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return LLMResponse(
                content=response,
                model=self._model,
                provider=self._provider,
                finish_reason="complete"
            )
            
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            return LLMResponse(
                content="I encountered an error generating a response. Please try again.",
                model=self._model,
                provider=self._provider,
                error=str(e)
            )


class LLMProviderFactory:
    """
    Factory for creating LLM providers.
    Use this to get the appropriate provider based on configuration.
    """
    
    _default_provider: LLMProviderType = LLMProviderType.GEMINI
    _providers: Dict[LLMProviderType, type] = {
        LLMProviderType.GEMINI: GeminiProvider,
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
    }
    
    @classmethod
    def get_provider(
        cls,
        provider_type: Optional[LLMProviderType] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> LLMProvider:
        """
        Get an LLM provider instance.
        
        Args:
            provider_type: Which provider to use (default: Gemini)
            api_key: Override API key (default: from env)
            model: Override model name
            
        Returns:
            LLMProvider instance
        """
        ptype = provider_type or cls._default_provider
        provider_class = cls._providers.get(ptype)
        
        if not provider_class:
            raise ValueError(f"Unknown provider type: {ptype}")
        
        kwargs = {}
        if api_key:
            kwargs['api_key'] = api_key
        if model:
            kwargs['model'] = model
            
        return provider_class(**kwargs)
    
    @classmethod
    def get_default_provider(cls) -> LLMProvider:
        """Get the default LLM provider (Gemini)"""
        return cls.get_provider(cls._default_provider)
    
    @classmethod
    def set_default_provider(cls, provider_type: LLMProviderType):
        """Change the default provider"""
        cls._default_provider = provider_type


# Convenience function for quick access
def get_llm_provider(
    provider: str = "gemini",
    model: Optional[str] = None
) -> LLMProvider:
    """
    Quick helper to get an LLM provider.
    
    Usage:
        provider = get_llm_provider("gemini")
        response = await provider.generate(prompt, system_message)
    """
    provider_map = {
        "gemini": LLMProviderType.GEMINI,
        "openai": LLMProviderType.OPENAI,
        "anthropic": LLMProviderType.ANTHROPIC,
        "claude": LLMProviderType.ANTHROPIC,
    }
    
    ptype = provider_map.get(provider.lower(), LLMProviderType.GEMINI)
    return LLMProviderFactory.get_provider(ptype, model=model)
