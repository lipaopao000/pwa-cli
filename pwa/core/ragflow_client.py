# -*- coding: utf-8 -*-
import os
import logging
import sys

# Ensure SDK is in path if not installed
sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../ragflow/sdk/python"))
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

from ragflow_sdk import RAGFlow

class RagFlowClient:
    """
    Wrapper for RAGFlow Python SDK.
    Uses official SDK but extends it where API coverage is incomplete.
    """
    def __init__(self, base_url, api_key):
        # SDK expects base_url without /api/v1
        self.base_url = base_url.rstrip('/')
        if self.base_url.endswith('/api/v1'):
             self.base_url = self.base_url[:-7].rstrip('/')
             
        self.api_key = api_key
        self.logger = logging.getLogger("RagFlowClient")
        
        # Initialize official SDK
        self.sdk = RAGFlow(api_key=self.api_key, base_url=self.base_url)

    def check_connection(self):
        """Verify if RAGFlow is accessible."""
        try:
            # list_datasets is a good connectivity check
            self.sdk.list_datasets(page=1, page_size=1)
            return True
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return False

    # ----------------------------------------------------------------------
    # Dataset Management
    # ----------------------------------------------------------------------

    def get_or_create_dataset(self, name):
        """Get dataset ID by name, or create if not exists."""
        try:
            # SDK's get_dataset raises Exception if not found, but let's list to be safer
            datasets = self.sdk.list_datasets(name=name, page_size=100)
            for ds in datasets:
                if ds.name == name:
                    return ds.id
            
            # Create if not found
            self.logger.info(f"Dataset '{name}' not found, creating...")
            new_ds = self.sdk.create_dataset(name=name, permission="me", chunk_method="naive")
            return new_ds.id
        except Exception as e:
            self.logger.error(f"Failed to get/create dataset {name}: {e}")
            return None

    def list_datasets(self, page=1, page_size=30, name=None):
        """List datasets."""
        try:
            return self.sdk.list_datasets(page=page, page_size=page_size, name=name)
        except Exception as e:
            self.logger.error(f"Failed to list datasets: {e}")
            return None

    def delete_dataset(self, ids):
        """Delete datasets by IDs."""
        try:
            if isinstance(ids, str):
                ids = [ids]
            self.sdk.delete_datasets(ids=ids)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete datasets {ids}: {e}")
            return False

    # ----------------------------------------------------------------------
    # Document Management
    # ----------------------------------------------------------------------

    def upload_document(self, dataset_id, file_path, display_name=None):
        """Upload a file and trigger parsing."""
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False

        try:
            # Get dataset object
            datasets = self.sdk.list_datasets(id=dataset_id)
            if not datasets:
                self.logger.error(f"Dataset {dataset_id} not found")
                return False
            ds = datasets[0]

            filename = display_name if display_name else os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                blob = f.read()
            
            # Upload via SDK
            uploaded_docs = ds.upload_documents([{"display_name": filename, "blob": blob}])
            
            if uploaded_docs:
                doc = uploaded_docs[0]
                # SDK async_parse_documents uses /api/v1/datasets/{dataset_id}/chunks
                ds.async_parse_documents([doc.id])
                self.logger.info(f"Uploaded and triggered parsing for {filename} ({doc.id})")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error uploading file {file_path}: {e}")
            return False

    def parse_documents(self, dataset_id, document_ids):
        """Trigger parsing for documents."""
        try:
            datasets = self.sdk.list_datasets(id=dataset_id)
            if datasets:
                datasets[0].async_parse_documents(document_ids)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to parse documents {document_ids}: {e}")
            return False

    def list_documents(self, dataset_id, page=1, page_size=1000, keywords=None, doc_id=None):
        """List documents in a dataset with auto-pagination."""
        try:
            datasets = self.sdk.list_datasets(id=dataset_id)
            if not datasets:
                return []
            
            ds = datasets[0]
            all_docs = []
            current_page = page
            
            while True:
                docs = ds.list_documents(page=current_page, page_size=page_size, keywords=keywords, id=doc_id)
                if not docs:
                    break
                all_docs.extend(docs)
                if len(docs) < page_size:
                    break
                current_page += 1
                
            return all_docs
        except Exception as e:
            self.logger.error(f"Failed to list documents in {dataset_id}: {e}")
            return []

    def delete_documents(self, dataset_id, document_ids):
        """Delete documents."""
        try:
            datasets = self.sdk.list_datasets(id=dataset_id)
            if datasets:
                datasets[0].delete_documents(ids=document_ids)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete documents {document_ids}: {e}")
            return False

    def get_document_status(self, dataset_id, document_id):
        """Get status of a specific document."""
        docs = self.list_documents(dataset_id, page=1, page_size=1, doc_id=document_id)
        if docs:
            return docs[0]
        return None

    # ----------------------------------------------------------------------
    # Retrieval
    # ----------------------------------------------------------------------

    def retrieve(self, dataset_id, query, document_ids=None, similarity_threshold=0.1, top_k=5, 
                 vector_similarity_weight=0.3, keyword=False):
        """Retrieve chunks relevant to the query."""
        try:
            # SDK's retrieve method
            # vector_similarity_weight: 1.0 for pure vector, 0.0 for pure keyword
            chunks = self.sdk.retrieve(
                dataset_ids=[dataset_id],
                document_ids=document_ids,
                question=query,
                similarity_threshold=similarity_threshold,
                vector_similarity_weight=vector_similarity_weight,
                top_k=top_k,
                keyword=keyword
            )
            
            # Map SDK Chunk objects to simple dicts for backward compatibility
            results = []
            doc_cache = {} # Cache document names to avoid redundant lookups

            for chunk in chunks:
                doc_name = getattr(chunk, 'document_name', None)
                doc_id = getattr(chunk, 'document_id', None)
                
                # If document_name is missing but document_id exists, try to look it up
                if (not doc_name or doc_name == "") and doc_id:
                    if doc_id in doc_cache:
                        doc_name = doc_cache[doc_id]
                    else:
                        try:
                            docs = self.list_documents(dataset_id, doc_id=doc_id)
                            if docs:
                                doc_name = docs[0].name
                                doc_cache[doc_id] = doc_name
                        except Exception as e:
                            self.logger.warning(f"Could not lookup document name for {doc_id}: {e}")
                
                results.append({
                    'content': chunk.content,
                    'similarity': getattr(chunk, 'similarity', None),
                    'document_name': doc_name
                })
            return results
        except Exception as e:
            msg = str(e)
            if "Model Not Exist" in msg:
                 self.logger.error("RAGFlow Error: Model Not Exist. Please ensure an Embedding Model is configured for this dataset in RAGFlow Web UI.")
            else:
                 self.logger.error(f"Retrieval failed: {e}")
            return []

    # ----------------------------------------------------------------------
    # Chat Assistant Management
    # ----------------------------------------------------------------------

    def create_chat_assistant(self, name, dataset_ids, llm=None, prompt=None):
        """Create a chat assistant."""
        try:
            # Map simple dicts to SDK objects if provided
            sdk_llm = None
            if llm:
                # Note: SDK Chat.LLM expects certain keys, might need careful mapping
                # For now let's try direct dict update if LLM creation is complex
                # SDK create_chat handles default LLM if None
                pass 
                
            return self.sdk.create_chat(name=name, dataset_ids=dataset_ids)
        except Exception as e:
            self.logger.error(f"Failed to create chat assistant: {e}")
            return None

    def list_chat_assistants(self, page=1, page_size=30, name=None):
        """List chat assistants."""
        try:
            return self.sdk.list_chats(page=page, page_size=page_size, name=name)
        except Exception as e:
            self.logger.error(f"Failed to list chat assistants: {e}")
            return None

    def delete_chat_assistants(self, ids):
        """Delete chat assistants."""
        try:
            self.sdk.delete_chats(ids=ids)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete chat assistants {ids}: {e}")
            return False

    # ----------------------------------------------------------------------
    # Session Management
    # ----------------------------------------------------------------------

    def create_session(self, chat_id, name="New Session", user_id=None):
        """Create a session for a chat assistant."""
        try:
            chats = self.sdk.list_chats(id=chat_id)
            if chats:
                # SDK Session creation doesn't currently take user_id in create_session
                # We can use底层 post if needed, but let's try standard SDK first
                return chats[0].create_session(name=name)
            return None
        except Exception as e:
            self.logger.error(f"Failed to create session for chat {chat_id}: {e}")
            return None

    def list_sessions(self, chat_id, page=1, page_size=30):
        """List sessions for a chat assistant."""
        try:
            chats = self.sdk.list_chats(id=chat_id)
            if chats:
                return chats[0].list_sessions(page=page, page_size=page_size)
            return []
        except Exception as e:
            self.logger.error(f"Failed to list sessions for chat {chat_id}: {e}")
            return []

    # ----------------------------------------------------------------------
    # File Management (Note: Backend /api/v1/file/* currently has implementation bugs)
    # ----------------------------------------------------------------------

    def _handle_response(self, res):
        """Helper to parse SDK response objects."""
        try:
            res_json = res.json()
            if res_json.get("code") == 0:
                return res_json.get("data")
            else:
                self.logger.error(f"API Error: {res_json.get('message')} (Code: {res_json.get('code')})")
                return None
        except Exception as e:
            self.logger.error(f"Failed to parse response: {e}")
            return None

    def get_root_folder(self):
        """Get root folder information. (Working)"""
        res = self.sdk.get("/file/root_folder")
        return self._handle_response(res)

    def list_files(self, parent_id=None, keywords=None, page=1, page_size=15):
        """List files and folders. (Working)"""
        params = {"page": page, "page_size": page_size}
        if parent_id:
            params["parent_id"] = parent_id
        if keywords:
            params["keywords"] = keywords
        res = self.sdk.get("/file/list", params=params)
        return self._handle_response(res)

    # ----------------------------------------------------------------------
    # WARNING: The following interfaces may fail due to RAGFlow backend bugs 
    # in asynchronous request handling (AttributeError).
    # It is recommended to use DataSet Management instead.
    # ----------------------------------------------------------------------

    def create_directory(self, name, parent_id=None):
        """Create a directory. (WARNING: Backend Bug)"""
        payload = {"name": name, "type": "folder"}
        if parent_id:
            payload["parent_id"] = parent_id
        res = self.sdk.post("/file/create", json=payload)
        return self._handle_response(res)

    def upload_file(self, file_path, parent_id=None):
        """Upload a file to a folder. (WARNING: Backend Bug if creating paths)"""
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return None
        files = [('file', (os.path.basename(file_path), open(file_path, 'rb')))]
        res = self.sdk.post("/file/upload", files=files, json={"parent_id": parent_id} if parent_id else None)
        return self._handle_response(res)

    def delete_files(self, file_ids):
        """Delete files or folders."""
        if isinstance(file_ids, str):
            file_ids = [file_ids]
        res = self.sdk.post("/file/rm", json={"file_ids": file_ids})
        return self._handle_response(res)

    # ----------------------------------------------------------------------
    # Conversation
    # ----------------------------------------------------------------------

    def chat(self, chat_id, question, session_id=None, stream=True):
        """
        Chat with the assistant.
        Returns a generator yielding content strings if stream=True.
        Returns the final Message object if stream=False.
        """
        try:
            # 1. Find session
            chats = self.sdk.list_chats(id=chat_id)
            if not chats:
                return None
            chat_obj = chats[0]
            
            session = None
            if session_id:
                sessions = chat_obj.list_sessions(id=session_id)
                if sessions:
                    session = sessions[0]
            
            if not session:
                session = chat_obj.create_session()
            
            # 2. Ask
            if stream:
                return self._stream_response_generator(session.ask(question, stream=True))
            else:
                # ask(stream=False) returns a generator with one element in current SDK implementation?
                # Actually looking at SDK session.py: yield self._structure_answer(json_data["data"])
                # So it's always a generator.
                responses = list(session.ask(question, stream=False))
                return responses[0] if responses else None
                
        except Exception as e:
            self.logger.error(f"Chat failed: {e}")
            return None

    def _stream_response_generator(self, sdk_generator):
        """Adapt SDK generator to yield plain text strings."""
        last_content = ""
        try:
            for message in sdk_generator:
                if message and message.content:
                    # SDK seems to yield cumulative content in some versions or chunks?
                    # Based on session.py: yields Message object.
                    # We need to see if it's incremental.
                    new_text = message.content[len(last_content):]
                    if new_text:
                        yield new_text
                        last_content = message.content
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
