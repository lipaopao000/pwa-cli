# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAcademicAgent:
    """
    Base class for academic writing assistance agents.
    Provides common LLM initialization and communication methods.
    """
    def __init__(self, llm_settings: Dict[str, Any], name: str = "AcademicAgent"):
        self.name = name
        self.llm_settings = llm_settings
        self.logger = logging.getLogger(name)
        
        # Initialize LangChain Chat Model
        self.model = ChatOpenAI(
            model=llm_settings["model"],
            api_key=llm_settings["api_key"],
            base_url=llm_settings["base_url"],
            temperature=llm_settings.get("temperature", 0.1)
        )

    def ask_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = True) -> Any:
        """Utility to call LLM and optionally parse JSON."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            res = self.model.invoke(messages)
            content = res.content
            
            if json_mode:
                import re
                import json
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    self.logger.error(f"Failed to extract JSON from: {content[:100]}")
                    return None
            return content
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return None
