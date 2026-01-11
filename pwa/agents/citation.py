# -*- coding: utf-8 -*-
import os
import logging
import re
import json
from typing import TypedDict, List, Dict, Any, Union, Optional, Tuple
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

class CitationVerificationResult(BaseModel):
    """Result of citation verification."""
    local_support: str = Field(description="One of: 'Full', 'Partial', 'Not Mentioned', 'Contradictory', 'N/A'")
    factuality: str = Field(description="One of: 'Well-established', 'Supported by Evidence', 'Debatable / Mixed', 'Unsupported / No Evidence', 'Contradicted', 'Requires Specification', 'Pending'")
    reasoning: str = Field(description="Detailed analysis in Chinese or English.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    suggestion: str = Field(description="Actionable advice for the author.")
    suggested_key: Optional[str] = Field(None, description="Recommended CitationKey or URL.")
    status: str = Field(description="Internal status code for flow control (e.g., 'Definitive', 'Unsatisfied').")

class Evidence(TypedDict):
    citation_key: str
    content: str
    source: str # 'abstract', 'chunk', 'fulltext', 'global', 'web'

class AgentState(TypedDict):
    citation_id: Optional[str]
    context: str
    ref_title: Optional[str]
    ref_abstract: Optional[str]
    ref_journal_if: Optional[str]
    doc_id: Optional[str]
    dataset_id: Union[str, None]
    query: str
    
    # Internal flow control
    search_mode: str # 'abstract_only', 'scoped', 'fulltext', 'global', 'web'
    evidences: List[Evidence]
    audit_history: List[Dict[str, Any]]
    fulltext_md: Optional[str]
    verification_result: Dict[str, Any]
    
    local_support: str # Current best guess at support level
    factuality: str # Current best guess at factuality
    
    rag_available: bool
    pubmed_available: bool
    tavily_available: bool
    
    llm_settings: Dict[str, Any]

class CitationVerificationAgent:
    def __init__(self, rag_client, pubmed_client, llm_settings, tavily_client=None):
        self.rag_client = rag_client
        self.pubmed_client = pubmed_client
        self.tavily_client = tavily_client
        self.llm_settings = llm_settings.copy()
        self.logger = logging.getLogger("CitationAgent")
        
        # Initialize LangChain Chat Model
        self.model = ChatOpenAI(
            **self.llm_settings
        )
        
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("analyze_claim", self.analyze_claim)
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("verify", self.verify)
        workflow.add_node("fetch_fulltext", self.fetch_fulltext)
        workflow.add_node("web_search", self.web_search)
        workflow.add_node("update_mode", self.update_mode)
        workflow.add_node("finalize", self.finalize_result)

        workflow.set_entry_point("analyze_claim")
        
        workflow.add_edge("analyze_claim", "retrieve")
        workflow.add_edge("retrieve", "verify")
        
        workflow.add_conditional_edges(
            "verify",
            self._decide_next,
            {
                "done": "finalize",
                "go_fulltext": "fetch_fulltext",
                "go_web_search": "web_search",
                "next_mode": "update_mode"
            }
        )
        workflow.add_edge("fetch_fulltext", "retrieve")
        workflow.add_edge("web_search", "verify")
        workflow.add_edge("update_mode", "retrieve")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def analyze_claim(self, state: AgentState):
        """Level 1: Abstract Check starts here."""
        return {
            "query": state['context'],
            "search_mode": "abstract_only",
            "evidences": [],
            "audit_history": []
        }

    def _extract_citation_key(self, doc_name):
        if not doc_name: return "Unknown"
        return doc_name.replace(".pdf", "").replace(".PDF", "")

    def retrieve(self, state: AgentState):
        mode = state['search_mode']
        evidences = state.get('evidences', []).copy()
        new_evidences = []
        
        # Clean query: Remove common markdown citations and excessive whitespace
        raw_query = state['query']
        clean_query = re.sub(r'\[?@[a-zA-Z0-9_\-:]+\]?', '', raw_query).strip()
        
        if mode == 'scoped' and self.rag_client:
            # Scoped search: Target the specific document
            query = clean_query
            results = self.rag_client.retrieve(
                dataset_id=state['dataset_id'], 
                query=query, 
                document_ids=[state['doc_id']] if state.get('doc_id') else None,
                similarity_threshold=0.2, # Lower threshold for scoped check to catch more content
                top_k=15
            )
            for r in results:
                new_evidences.append({
                    "citation_key": self._extract_citation_key(r.get('document_name')),
                    "content": r.get('content', ''),
                    "source": "chunk"
                })

        elif mode == 'global' and self.rag_client:
            # Global search: Search across the entire dataset (Global Check)
            # Strategy: Use only the claim for global search to find the most relevant document anywhere
            # CRITICAL: document_ids must be None for global search to cover the whole dataset
            self.logger.info(f"Executing Global Dataset Search for: {clean_query[:100]}...")
            
            # Clean more aggressively for global search (remove common citation markers)
            global_query = re.sub(r'\[\d+\]', '', clean_query) # [1], [2]
            global_query = re.sub(r'\(\d{4}\)', '', global_query) # (2023)
            global_query = global_query.strip()

            results = self.rag_client.retrieve(
                dataset_id=state['dataset_id'], 
                query=global_query, 
                document_ids=None, # Explicitly search entire dataset
                similarity_threshold=0.3, # Minimum threshold for global search to find potential matches
                vector_similarity_weight=0.7, # Hybrid search (0.3 vector, 0.7 keyword) to match Web UI
                top_k=15 
            )
                
            for r in results:
                # In global mode, correctly identifying the source citation_key is crucial
                source_key = self._extract_citation_key(r.get('document_name'))
                new_evidences.append({
                    "citation_key": source_key,
                    "content": r.get('content', ''),
                    "source": "global"
                })
            
            self.logger.info(f"Global search found {len(new_evidences)} evidences.")
        
        elif mode == 'abstract_only':
            if state.get('ref_abstract'):
                new_evidences.append({
                    "citation_key": state['citation_id'],
                    "content": state['ref_abstract'],
                    "source": "abstract"
                })
        
        elif mode == 'fulltext':
            if state.get('fulltext_md'):
                new_evidences.append({
                    "citation_key": state['citation_id'],
                    "content": state['fulltext_md'],
                    "source": "fulltext"
                })
        
        elif mode == 'web':
            # Evidence is already populated by web_search node
            pass
        
        # Accumulate evidences
        return {"evidences": evidences + new_evidences}

    def web_search(self, state: AgentState):
        """Level 5: Web Search (PubMed/Tavily)."""
        audit_history = state.get('audit_history', []).copy()
        evidences = state.get('evidences', []).copy()
        
        context = state['context']
        citation_id = state['citation_id']
        
        # 1. Generate optimized search query
        gen_query_sys = (
            "You are an academic search expert. Based on the manuscript claim and the target citation, "
            "generate a precise search query for PubMed or Google Scholar to verify the claim.\n"
            "The query should be in English, focusing on key technical terms and the cited author's name if relevant.\n"
            "Return ONLY the search query string."
        )
        gen_query_user = f"Manuscript Claim: \"{context}\"\nTarget Citation: {citation_id}"
        
        try:
            res = self.model.invoke([
                SystemMessage(content=gen_query_sys),
                HumanMessage(content=gen_query_user)
            ])
            search_query = res.content.strip().strip('"')
            self.logger.info(f"Generated Web Search Query: {search_query}")
        except Exception as e:
            self.logger.error(f"Error generating search query: {e}")
            search_query = context[:100]

        new_web_evidences = []
        
        # 2. Try PubMed
        if self.pubmed_client:
            try:
                self.logger.info(f"[DEBUG] PubMed Client Email: {self.pubmed_client.email}")
                self.logger.info(f"Searching PubMed for: {search_query}")
                abstract = self.pubmed_client.search_abstract(search_query)
                if abstract and "No Abstract Found" not in abstract:
                    self.logger.info(f"[DEBUG] PubMed returned abstract (length: {len(abstract)})")
                    new_web_evidences.append({
                        "citation_key": "PubMed_Result",
                        "content": abstract,
                        "source": "web"
                    })
                else:
                    self.logger.warning(f"[DEBUG] PubMed returned NO abstract for: {search_query}")
            except Exception as e:
                self.logger.error(f"PubMed search error: {e}", exc_info=True)

        # 3. Try Tavily (if available)
        if not new_web_evidences and self.tavily_client:
            try:
                self.logger.info(f"Searching Tavily for: {search_query}")
                search_res = self.tavily_client.search(query=search_query, search_depth="advanced")
                if search_res and search_res.get('results'):
                    self.logger.info(f"[DEBUG] Tavily found {len(search_res['results'])} results.")
                    for r in search_res.get('results', [])[:3]:
                        new_web_evidences.append({
                            "citation_key": "Web_Result",
                            "content": f"Title: {r.get('title')}\nSnippet: {r.get('content')}",
                            "source": "web"
                        })
                else:
                    self.logger.warning(f"[DEBUG] Tavily returned NO results for: {search_query}")
            except Exception as e:
                self.logger.error(f"Tavily search error: {e}", exc_info=True)

        if new_web_evidences:
            audit_history.append({
                "level": "web",
                "status": "Searched",
                "reasoning": f"Performed web search with query: {search_query}",
                "evidence_count": len(new_web_evidences),
                "evidences": new_web_evidences
            })
            return {
                "search_mode": "web",
                "evidences": evidences + new_web_evidences,
                "audit_history": audit_history
            }
        else:
            # IMPORTANT: If web search fails to find anything, we set status to 'Failed'
            # to prevent verify node from re-judging based on old evidence.
            audit_history.append({
                "level": "web",
                "status": "Failed",
                "reasoning": f"Web search (PubMed/Tavily) with query '{search_query}' returned no results.",
                "evidence_count": 0,
                "evidences": []
            })
            return {
                "search_mode": "web",
                "audit_history": audit_history,
                "verification_result": {
                    "status": "Failed", 
                    "reasoning": "Web search found no evidence.",
                    "statement_factuality": "Unclear",
                    "citation_support": "Not Supported",
                    "suggestion": "Web search (PubMed/Tavily) failed to find any evidence to verify this claim."
                }
            }

    def fetch_fulltext(self, state: AgentState):
        """Level 3: 请求全文 Markdown"""
        audit_history = state.get('audit_history', []).copy()
        
        # 1. 优先使用已注入的本地 MD
        if state.get('fulltext_md'):
            self.logger.info(f"Using pre-loaded local MD for {state['citation_id']}")
            audit_history.append({
                "level": "fulltext",
                "status": "Loaded",
                "reasoning": "Using pre-loaded fulltext Markdown from local source (no chunking).",
                "evidence_count": 1,
                "evidences": [{"citation_key": state['citation_id'], "source": "fulltext", "content": "Fulltext content pre-loaded."}]
            })
            return {
                "search_mode": "fulltext",
                "audit_history": audit_history
            }

        # 2. 如果没有注入，则尝试从 RAG 检索并拼接 (兜底逻辑)
        if not self.rag_client or not state.get('doc_id'):
            reason = "RAG client unavailable" if not self.rag_client else "doc_id missing"
            audit_history.append({
                "level": "fulltext",
                "status": "Skipped",
                "reasoning": f"Fulltext retrieval skipped: {reason}.",
                "evidence_count": 0,
                "evidences": []
            })
            # If fulltext is skipped, we still need a verification result for _decide_next
            return {
                "search_mode": "fulltext", 
                "audit_history": audit_history,
                "verification_result": {"status": "Failed", "reasoning": "Fulltext skipped."}
            }
            
        try:
            self.logger.info(f"Fetching chunks from RAG to reconstruct fulltext for {state['citation_id']}...")
            results = self.rag_client.retrieve(
                dataset_id=state['dataset_id'],
                query="", 
                document_ids=[state['doc_id']],
                top_k=100 
            )
            if results:
                fulltext = "\n\n".join([c.get('content', '') for c in results])
                return {"fulltext_md": fulltext, "search_mode": "fulltext"}
            else:
                audit_history.append({
                    "level": "fulltext",
                    "status": "Failed",
                    "reasoning": "No content returned from RAG for fulltext.",
                    "evidence_count": 0,
                    "evidences": []
                })
                return {
                    "search_mode": "fulltext", 
                    "audit_history": audit_history,
                    "verification_result": {"status": "Failed", "reasoning": "Fulltext empty."}
                }
        except Exception as e:
            self.logger.error(f"Error fetching fulltext: {e}")
            audit_history.append({
                "level": "fulltext",
                "status": "Error",
                "reasoning": f"Exception during fulltext fetch: {str(e)}",
                "evidence_count": 0,
                "evidences": []
            })
            return {
                "search_mode": "fulltext", 
                "audit_history": audit_history,
                "verification_result": {"status": "Error", "reasoning": str(e)}
            }

    def verify(self, state: AgentState):
        """Level Verification."""
        all_evidences = state['evidences']
        mode = state['search_mode']
        audit_history = state.get('audit_history', []).copy()
        
        # Determine which evidences to show for the current verification mode
        if mode == 'web':
            # CRITICAL: We only proceed to LLM verify in web mode if we actually HAVE web evidence
            web_only = [e for e in all_evidences if e['source'] == 'web']
            if not web_only:
                # This should have been caught by web_search node, but as a safety:
                return {"verification_result": {"status": "Failed", "reasoning": "No web evidence available for verification."}}
            
            # ENHANCEMENT: In Web mode, merge with Global (RAG) evidences to think together
            current_evidences = [e for e in all_evidences if e['source'] in ['global', 'web']]
        else:
            current_evidences = [e for e in all_evidences if e['source'] == (
                'abstract' if mode == 'abstract_only' else 
                'chunk' if mode == 'scoped' else 
                'fulltext' if mode == 'fulltext' else 
                'global'
            )]

        if not current_evidences:
            # Special logic for global search when it returns nothing
            if mode == 'global':
                result = {"status": "Unclear", "confidence": 0.0, "reasoning": "Global search returned no relevant snippets from any document."}
            else:
                status_if_empty = "Need More" if mode == 'abstract_only' else "Chunk Unsatisfied" if mode == 'scoped' else "Not Supported"
                result = {"status": status_if_empty, "confidence": 0.0, "reasoning": f"No content found in {mode} level."}
            
            audit_history.append({
                "level": mode,
                "status": result['status'],
                "reasoning": result['reasoning'],
                "evidence_count": 0,
                "evidences": []
            })
            return {"verification_result": result, "audit_history": audit_history}

        context = state['context']
        citation_id = state['citation_id']
        title = state['ref_title']
        
        # Build marked evidence text for LLM (using current level only for judgment)
        evidence_lines = []
        for i, ev in enumerate(current_evidences):
            evidence_lines.append(f"--- Evidence {i+1} [Source: {ev['source']}, CitationKey: {ev['citation_key']}] ---\n{ev['content']}")
        
        evidence_text = "\n\n".join(evidence_lines)

        # Candidate Keys Prompt (for Global Search)
        candidate_instruction = ""
        if mode == 'global':
            candidate_instruction = "IMPORTANT: Since this is a global database search, if you find a specific document that clearly supports the claim, please identify its CitationKey and include it in your response as \"suggested_key\"."

        if mode == 'abstract_only':
            allowed_statuses = "Supported, Need More"
        elif mode == 'scoped':
            allowed_statuses = "Supported, Chunk Unsatisfied"
        elif mode == 'fulltext':
            allowed_statuses = "Supported, Not Supported"
        elif mode == 'global':
            allowed_statuses = "Supported, Unclear"
        else: # web
            allowed_statuses = "Supported, Unclear"

        is_global_audit = mode in ['global', 'web']
        
        if not is_global_audit:
            factuality_instruction = (
                "Currently in LOCAL AUDIT mode. You ONLY have evidence from the TARGET CITATION. "
                "You CANNOT judge if the statement is False. If the evidence doesn't support it, "
                "simply mark citation_support as 'Not Supported' and statement_factuality as 'Unclear'."
            )
            factuality_allowed = "\"True\" | \"Unclear\""
        else:
            factuality_instruction = (
                "Currently in GLOBAL/WEB AUDIT mode. You have searched the entire database/web. "
                "You ARE authorized to judge if the statement is True or False based on all evidence."
            )
            factuality_allowed = "\"True\" | \"False\" | \"Unclear\""

        system_msg = (
            "You are an expert academic reviewer. Verify if the user's claim is supported by the provided evidence.\n"
            f"Current Level: {mode}. Internal Allowed Statuses: {allowed_statuses}.\n\n"
            f"### {mode.upper()} AUDIT INSTRUCTION ###\n"
            f"{factuality_instruction}\n\n"
            "### CRITICAL: TWO-DIMENSIONAL EVALUATION ###\n"
            "You MUST evaluate the claim across two independent dimensions:\n"
            "1. **Statement Factuality**: Is the claim itself TRUE, FALSE, or UNCLEAR?\n"
            "2. **Citation Support**: Does the TARGET CITATION ([CITATION_ID]) specifically support this claim?\n\n"
            "### ACTION TEMPLATES for 'suggestion' ###\n"
            "- IF (True + Supported): \"This statement is True and Supported by [CITATION_ID].\"\n"
            "- IF (True + Not Supported): \"This statement is True but Not Supported by [CITATION_ID]. Needs to change to [SUGGESTED_KEY] or [URL] by Cline, because [REASON].\"\n"
            "- IF (False + Not Supported): \"This statement is False and Not Supported by any evidence. Evidences say [SUMMARY]. The statement needs to be rewritten by Cline considering the context.\"\n"
            "- IF (Unclear + Not Supported - LOCAL ONLY): \"The target citation [CITATION_ID] does not support this statement. Further global search is required to verify factuality.\"\n\n"
            "Return ONLY a valid JSON object with the following structure:\n"
            "{\n"
            "  \"statement_factuality\": " + factuality_allowed + ",\n"
            "  \"citation_support\": \"Supported\" | \"Not Supported\" | \"Contradicted\",\n"
            "  \"status\": \"Supported\" | ... (internal code for flow control),\n"
            "  \"reasoning\": \"Detailed analysis in Chinese or English.\",\n"
            "  \"confidence\": 0.0 to 1.0,\n"
            "  \"suggestion\": \"The final actionable sentence following the templates above.\",\n"
            "  \"suggested_key\": \"(Optional) The CitationKey or URL that actually supports the claim.\"\n"
            "}"
            f"\n{candidate_instruction}"
        )
        user_msg = f"**Manuscript Claim**: \"{context}\"\n**Target Citation**: {citation_id}\n**Paper Title**: {title}\n\n**Evidences**:\n{evidence_text}"

        try:
            res = self.model.invoke([
                SystemMessage(content=system_msg),
                HumanMessage(content=user_msg)
            ])
            
            content = res.content
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                except json.JSONDecodeError as e:
                    # Attempt simple repair for common escape issues
                    repaired = json_match.group(1).replace('\\', '\\\\')
                    try:
                        result = json.loads(repaired)
                    except:
                        result = {"status": "Error", "reasoning": f"JSON Decode Error: {str(e)} | Content: {content[:200]}", "confidence": 0.0}
            else:
                result = {"status": "Error", "reasoning": f"Could not parse JSON from LLM: {content[:100]}", "confidence": 0.0}
            
            # Record in history
            audit_history.append({
                "level": mode,
                "status": result.get('status'),
                "reasoning": result.get('reasoning'),
                "evidence_count": len(current_evidences),
                "evidences": current_evidences
            })
            
            return {"verification_result": result, "audit_history": audit_history}
        except Exception as e:
            self.logger.error(f"Verification error: {str(e)}")
            err_result = {"status": "Error", "reasoning": str(e), "confidence": 0.0}
            audit_history.append({
                "level": mode,
                "status": "Error",
                "reasoning": str(e),
                "evidence_count": len(current_evidences),
                "evidences": current_evidences
            })
            return {"verification_result": err_result, "audit_history": audit_history}

    def _decide_next(self, state: AgentState):
        res = state.get('verification_result', {})
        status = res.get('status')
        mode = state['search_mode']
        
        # If we reached a final definitive supported status, we are done
        if status == "Supported":
            return "done"
            
        # Intermediate level transitions
        if mode == 'abstract_only' and status == 'Need More':
            return "next_mode"
        
        if mode == 'scoped' and status == 'Chunk Unsatisfied':
            return "go_fulltext"
            
        if mode == 'fulltext' and (status == 'Not Supported' or status == 'Failed' or status == 'Error'):
            return "next_mode"
        
        # Transition to Web Search from Global if Unclear
        if mode == 'global' and status == 'Unclear':
            if state.get('pubmed_available') or state.get('tavily_available'):
                return "go_web_search"
        
        # If we are already in web mode, any result (Success/Failed/Error) means we finish
        if mode == 'web':
            return "done"

        return "done"

    def _get_next_mode(self, current_mode, state):
        audit_history = state.get('audit_history', []).copy()
        
        if current_mode == 'abstract_only':
            if state['rag_available'] and state.get('doc_id'):
                return 'scoped', audit_history
            elif state['rag_available']:
                audit_history.append({
                    "level": "scoped",
                    "status": "Skipped",
                    "reasoning": "No doc_id found for target citation, skipping scoped chunk search.",
                    "evidence_count": 0,
                    "evidences": []
                })
                audit_history.append({
                    "level": "fulltext",
                    "status": "Skipped",
                    "reasoning": "No doc_id found for target citation, skipping fulltext retrieval.",
                    "evidence_count": 0,
                    "evidences": []
                })
                return 'global', audit_history
        elif current_mode == 'scoped':
            return 'global', audit_history
        elif current_mode == 'fulltext':
            return 'global', audit_history
        return None, audit_history

    def finalize_result(self, state: AgentState):
        res = state.get('verification_result', {}).copy()
        mode = state['search_mode']
        
        # Two-dimensional mapping
        factuality = res.get('statement_factuality', 'Unclear')
        support = res.get('citation_support', 'Not Supported')
        
        status = res.get('status')
        confidence = res.get('confidence', 1.0)
        all_evidences = state.get('evidences', [])
        audit_history = state.get('audit_history', [])

        # 0. Confidence Check: Flag low confidence results for human review
        if factuality == "True" and support == "Supported" and confidence < 0.6:
            res['citation_support'] = "Unclear"
            res['reasoning'] = f"[Low Confidence {confidence}] " + res.get('reasoning', '')
            res['suggestion'] = "置信度较低，建议人工核对：Statement is True but support is questionable."
            support = "Unclear"

        # 1. Update rag_retrieved status
        has_rag_evidence = any(e['source'] in ['chunk', 'global', 'fulltext'] for e in all_evidences)
        res['rag_retrieved'] = has_rag_evidence

        # 2. Add audit trail (Keep FULL content as requested)
        display_history = []
        for entry in audit_history:
            clean_entry = entry.copy()
            if 'evidences' in clean_entry:
                # Keep FULL content and metadata
                clean_entry['evidences'] = [
                    {
                        "citation_key": e['citation_key'],
                        "source": e['source'],
                        "content": e['content']
                    } for e in clean_entry['evidences']
                ]
            display_history.append(clean_entry)
        res['audit_trail'] = display_history

        # 3. Consolidate source information
        res['final_mode'] = mode
        if mode == 'web':
            res['source'] = "Web Search (PubMed/Tavily)"
        else:
            res['source'] = f"RAG ({mode})" if mode != 'abstract_only' else "Local Abstract"
        
        # 4. Final status mapping based on the 2D logic
        if factuality == 'True' and support == 'Supported':
            if mode == 'global':
                res['status'] = 'Misplaced' # Found support elsewhere
                res['action_required'] = 'cline_move_citation'
            else:
                res['status'] = 'Supported'
                res['action_required'] = 'none'
        elif factuality == 'True' and (support == 'Not Supported' or support == 'Contradicted'):
            res['status'] = 'Misplaced' # Claim is true, citation is wrong
            res['action_required'] = 'cline_replace_citation'
        elif factuality == 'False':
            res['status'] = 'Contradicted'
            res['action_required'] = 'cline_rewrite_content'
        else:
            res['status'] = 'Unclear'
            res['action_required'] = 'cline_web_search'
            
        # 5. Synthesis Reasoning
        # If the final reasoning is very specific to the last level, try to synthesize
        if len(audit_history) > 1:
            best_entry = next((e for e in reversed(audit_history) if e['status'] == 'Supported'), None)
            if best_entry and mode == 'global':
                 res['reasoning'] = f"经过多级审计，最终在全库检索中找到支持证据。之前层级（如摘要或目标片段）未能充分支持，原因：{audit_history[0].get('reasoning', '不详')}。最终结论：{res['reasoning']}"
            elif not best_entry:
                 res['reasoning'] = f"经过四级深度审计（摘要->片段->全文->全库），均未能找到充分支持证据。最后一级结论：{res['reasoning']}"

        # 6. Format top evidences for display (Legacy support)
        # We only show evidences from the level that actually provided the result
        current_level_evidences = [e for e in all_evidences if e['source'] == (
            'abstract' if mode == 'abstract_only' else 
            'chunk' if mode == 'scoped' else 
            'fulltext' if mode == 'fulltext' else 
            'global' if mode == 'global' else
            'web'
        )]
        
        display_evidences = current_level_evidences[:3]
        if not display_evidences and all_evidences:
            display_evidences = all_evidences[:3]
            
        evidence_lines = []
        for i, ev in enumerate(display_evidences):
            # Compact format: [Source] [@CitationKey]
            evidence_lines.append(f"[{ev['source'].upper()}] [@{ev['citation_key']}]\n{ev['content']}")
        res['source_content'] = "\n\n".join(evidence_lines)
        
        return {"verification_result": res}

    def update_mode(self, state: AgentState):
        next_mode, updated_history = self._get_next_mode(state['search_mode'], state)
        return {"search_mode": next_mode, "audit_history": updated_history}

    def run(self, initial_state: AgentState):
        try:
            final_state = self.workflow.invoke(initial_state)
            return final_state
        except Exception as e:
            self.logger.error(f"Agent Workflow error: {str(e)}")
            return None

def get_fulltext_md_path(citation_id: str) -> Optional[str]:
    """Helper to find the local Markdown fulltext path for a given citation."""
    # Try multiple common locations
    search_dirs = [
        os.path.join(os.getcwd(), "FullTextMD"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FullTextMD")
    ]
    for base_dir in search_dirs:
        md_path = os.path.join(base_dir, citation_id, f"{citation_id}.md")
        if os.path.exists(md_path):
            return md_path
    return None

def load_fulltext_md_content(citation_id: str) -> Optional[str]:
    """Loads the content of the local Markdown fulltext for a given citation."""
    path = get_fulltext_md_path(citation_id)
    if path:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logging.getLogger("CitationAgent").warning(f"Could not read local MD for {citation_id}: {e}")
    return None

def parse_markdown_citations(markdown_content: str) -> List[Tuple[str, str, int]]:
    """
    Parses citation keys and their surrounding context from markdown.
    Returns: List of (citation_id, context, line_number)
    """
    citations = []
    citation_group_pattern = re.compile(r'(\[[^\]]*?@[^\]]*?\])')
    key_pattern = re.compile(r'@([a-zA-Z0-9_\-:]+)')
    
    lines = markdown_content.split('\n')
    paragraphs = []
    current_para = []
    start_line = 1
    
    for i, line in enumerate(lines):
        if re.match(r'^\s*\|.*\|?\s*$', line): continue 

        if not line.strip():
            if current_para:
                paragraphs.append({'text': ' '.join(current_para), 'start': start_line})
                current_para = []
        else:
            if not current_para: start_line = i + 1
            current_para.append(line.strip())
            
    if current_para:
        paragraphs.append({'text': ' '.join(current_para), 'start': start_line})

    for para in paragraphs:
        text = para['text']
        s_line = para['start']
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for j, sent in enumerate(sentences):
            groups = citation_group_pattern.findall(sent)
            if groups:
                prev = sentences[j-1] if j > 0 else ""
                next_s = sentences[j+1] if j < len(sentences) - 1 else ""
                context = f"{prev} {sent} {next_s}".strip()
                
                for group in groups:
                    keys = key_pattern.findall(group)
                    for key in keys:
                        citations.append((key, context, s_line))
    return citations

class CitationReportReader:
    """Helper to read and index citation audit reports."""
    def __init__(self, report_path: str):
        self.report_path = report_path
        self.data = {}
        self.index = {} # Key: (line, citation_id) -> result
        self._load()

    def _load(self):
        if not os.path.exists(self.report_path):
            return
        try:
            with open(self.report_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                for r in self.data.get('results', []):
                    key = (r.get('line'), r.get('citation_id'))
                    self.index[key] = r
        except Exception as e:
            logging.getLogger("CitationAgent").error(f"Failed to load report {self.report_path}: {e}")

    def get_result(self, line: int, citation_id: str) -> Optional[Dict[str, Any]]:
        return self.index.get((line, citation_id))

    def get_all_results(self) -> List[Dict[str, Any]]:
        return self.data.get('results', [])

def annotate_markdown_with_results(md_content: str, results: List[Dict[str, Any]]) -> str:
    """
    Annotates markdown content with citation check results using HTML comments.
    Uses high-value actionable templates for Cline.
    """
    lines = md_content.split('\n')
    
    # Group results by line for efficient processing
    line_map = {}
    for r in results:
        l = r.get('line')
        if l not in line_map:
            line_map[l] = []
        line_map[l].append(r)

    new_lines = []
    for i, line in enumerate(lines):
        line_num = i + 1
        current_line = line
        
        if line_num in line_map:
            line_results = line_map[line_num]
            
            for r in line_results:
                cid = r.get('citation_id')
                ai_v = r.get('ai_verification', {})
                status = ai_v.get('status', 'Unknown')
                suggestion = ai_v.get('suggestion', '') # This now contains the high-value template
                
                # We want to find the citation [@key] and append a comment
                pattern = rf'(@{re.escape(cid)})'
                
                # Check if we already have a comment for this check to avoid duplicates
                comment_marker = f"<!-- CITATION_CHECK_ID:{cid} -->"
                if comment_marker in current_line:
                    current_line = re.sub(rf'<!-- CITATION_CHECK_ID:{cid} -->.*?-->', '', current_line)

                # Status-based emoji for quick visual check
                emoji = "✅" if status == "Supported" else "⚠️" if status in ["Unclear", "Misplaced"] else "❌"
                
                # High-value actionable comment
                new_comment = f" <!-- CITATION_CHECK_ID:{cid} --> {emoji} {suggestion} "
                
                # Append after the first occurrence of the citation key on this line
                current_line = re.sub(pattern, rf'\1<!--{new_comment}-->', current_line, count=1)
        
        new_lines.append(current_line)
        
    return '\n'.join(new_lines)
