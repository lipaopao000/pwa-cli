"""Base class for academic writing assistance agents."""

import json
import logging
import re
from typing import Any, Dict, Optional, Union

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


class BaseAcademicAgent:
    """
    Base class for academic writing assistance agents.
    Provides common LLM initialization and communication methods.
    """

    def __init__(self, llm_settings: Dict[str, Any], name: str = "AcademicAgent") -> None:
        """
        Initialize the academic agent.

        Args:
            llm_settings: Dictionary containing LLM configuration (model, api_key, base_url, etc.)
            name: Name of the agent for logging purposes
        """
        self.name: str = name
        self.llm_settings: Dict[str, Any] = llm_settings
        self.logger: logging.Logger = logging.getLogger(name)

        # Initialize LangChain Chat Model
        self.model: ChatOpenAI = ChatOpenAI(
            model=llm_settings["model"],
            api_key=llm_settings["api_key"],
            base_url=llm_settings["base_url"],
            temperature=llm_settings.get("temperature", 0.1),
        )

    def ask_llm(
        self, system_prompt: str, user_prompt: str, json_mode: bool = True
    ) -> Optional[Union[Dict[str, Any], str]]:
        """
        Call LLM and optionally parse JSON response.

        Args:
            system_prompt: System message to set context
            user_prompt: User message with the actual query
            json_mode: If True, attempt to extract and parse JSON from response

        Returns:
            Parsed JSON dict if json_mode=True and JSON found, otherwise raw string.
            Returns None if the call fails or JSON parsing fails.
        """
        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            res = self.model.invoke(messages)
            content = res.content

            if not isinstance(content, str):
                self.logger.error(f"Unexpected response type: {type(content)}")
                return None

            if json_mode:
                json_match = re.search(r"(\{.*\})", content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON parsing failed: {e}")
                        self.logger.debug(f"Content: {content[:200]}")
                        return None
                else:
                    self.logger.error(f"Failed to extract JSON from: {content[:100]}")
                    return None

            return content

        except KeyError as e:
            self.logger.error(f"Missing required LLM setting: {e}")
            return None
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}", exc_info=True)
            return None
