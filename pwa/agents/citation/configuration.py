import os
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig

class Configuration(BaseModel):
    """The configuration for the Scientific Statement Verifier."""

    # Models
    active_provider: str = Field(
        default="openai",
        description="The LLM provider to use."
    )
    
    model: str = Field(
        default="gpt-4o-mini",
        description="The name of the language model to use."
    )

    temperature: float = Field(
        default=0.1,
        description="The temperature for the LLM."
    )

    # Search Config
    max_web_results: int = Field(
        default=5,
        description="Maximum number of web search results to fetch."
    )

    # Verification Config
    high_if_threshold: float = Field(
        default=20.0,
        description="Impact Factor threshold for definitive support."
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        
        # In this specific paper-writing-assistant setup, settings might come from a YAML
        # but for compatibility with LangGraph patterns, we support the standard approach
        return cls(**configurable)
