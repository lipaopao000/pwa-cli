from __future__ import annotations
import operator
from typing import TypedDict, List, Dict, Any, Optional, Union
from typing_extensions import Annotated

class Evidence(TypedDict):
    citation_key: str
    content: str
    source: str  # 'abstract', 'Local RAG', 'fulltext', 'Library RAG', 'web'
    journal_if: Optional[float]
    title: Optional[str]
    url: Optional[str]

class AgentState(TypedDict):
    # Input
    citation_id: Optional[str]
    context: str
    ref_title: Optional[str]
    ref_abstract: Optional[str]
    ref_journal_if: Optional[float]
    ref_url: Optional[str]
    doc_id: Optional[str]
    dataset_id: Optional[str]
    
    # Internal State
    query: str
    subflow: str  # 'citation' or 'factuality'
    ladder_level: str  # 'abstract', 'Local RAG', 'fulltext', 'done'
    
    # Using operator.add for automatic list merging
    evidences: Annotated[List[Evidence], operator.add]
    audit_history: Annotated[List[Dict[str, Any]], operator.add]
    
    fulltext_md: Optional[str]
    
    # Results
    local_support: str  # 'Full', 'Partial', 'Not Mentioned', 'Contradictory', 'N/A'
    factuality: str    # 'Well-established', 'Supported by Evidence', etc.
    verification_result: Dict[str, Any]
    suggested_key: Optional[str]
    
    # Control
    status: str  # 'Definitive' or 'In-Progress'
    
    # Clients (Passed in via initialize or available in scope)
    # Note: In LangGraph, it's better to keep large objects out of state 
    # and use a wrapper or provider if possible, but for simplicity here
    # we'll assume they are available to the nodes.
