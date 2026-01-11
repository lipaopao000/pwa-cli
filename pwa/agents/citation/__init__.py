"""
Citation Agent - 引用和陈述验证

This agent handles:
- Citation verification
- Statement verification  
- Factuality checking
"""

from .agent import CitationVerificationAgent as CitationAgent
from .verifier import ScientificStatementVerifier as StatementVerifier
from .configuration import Configuration
from .state import AgentState, Evidence
from .schemas import *

__all__ = [
    'CitationAgent',
    'StatementVerifier',
    'Configuration',
    'AgentState',
    'Evidence',
]
