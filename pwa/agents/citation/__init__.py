"""
Citation Agent - 引用和陈述验证

This agent handles:
- Citation verification
- Statement verification
- Factuality checking
"""

from .agent import CitationVerificationAgent as CitationAgent
from .configuration import Configuration
from .schemas import *
from .state import AgentState, Evidence
from .verifier import ScientificStatementVerifier as StatementVerifier

__all__ = [
    "CitationAgent",
    "StatementVerifier",
    "Configuration",
    "AgentState",
    "Evidence",
]
