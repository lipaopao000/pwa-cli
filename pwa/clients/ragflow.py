import os
import logging
import sys

# Add RAGFlow SDK to Python path
# Priority: 1. Project .ragflow dir, 2. Installed package
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ragflow_sdk_path = os.path.join(project_root, ".ragflow/sdk/python")

if os.path.exists(ragflow_sdk_path) and ragflow_sdk_path not in sys.path:
    sys.path.insert(0, ragflow_sdk_path)
    logging.debug(f"Added RAGFlow SDK to path: {ragflow_sdk_path}")

try:
    from ragflow_sdk import RAGFlow
except ImportError as e:
    raise ImportError(
        f"Failed to import ragflow_sdk: {e}\n"
        f"Please run: ./scripts/install_ragflow_sdk.sh\n"
        f"Or manually clone: git clone https://github.com/infiniflow/ragflow.git {project_root}/.ragflow"
    )


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
            # Not found, create it
            ds = self.sdk.create_dataset(name=name)
            return ds.id
        except Exception as e:
            self.logger.error(f"get_or_create_dataset failed: {e}")
            raise

    def list_datasets(self):
        """List all datasets."""
        try:
            return self.sdk.list_datasets(page_size=1000)
        except Exception as e:
            self.logger.error(f"list_datasets failed: {e}")
            raise

    def delete_dataset(self, dataset_id):
        """Delete a dataset by ID."""
        try:
            self.sdk.delete_dataset(dataset_id)
            return True
        except Exception as e:
            self.logger.error(f"delete_dataset failed: {e}")
            return False

    # ----------------------------------------------------------------------
    # Document Management
    # ----------------------------------------------------------------------

    def upload_document(self, dataset_id, file_path, name=None):
        """Upload a document to a dataset."""
        try:
            if name is None:
                name = os.path.basename(file_path)
            
            ds = self.sdk.get_dataset(dataset_id)
            doc = ds.upload_document(file_path=file_path, name=name)
            return doc.id
        except Exception as e:
            self.logger.error(f"upload_document failed: {e}")
            raise

    def list_documents(self, dataset_id):
        """List all documents in a dataset."""
        try:
            ds = self.sdk.get_dataset(dataset_id)
            return ds.list_documents(page_size=1000)
        except Exception as e:
            self.logger.error(f"list_documents failed: {e}")
            raise

    def delete_document(self, dataset_id, document_id):
        """Delete a document from a dataset."""
        try:
            ds = self.sdk.get_dataset(dataset_id)
            ds.delete_document(document_id)
            return True
        except Exception as e:
            self.logger.error(f"delete_document failed: {e}")
            return False

    def parse_document(self, dataset_id, document_id):
        """Parse a document (start chunking)."""
        try:
            ds = self.sdk.get_dataset(dataset_id)
            doc = ds.get_document(document_id)
            doc.parse()
            return True
        except Exception as e:
            self.logger.error(f"parse_document failed: {e}")
            return False

    def get_document_status(self, dataset_id, document_id):
        """Get document parsing status."""
        try:
            ds = self.sdk.get_dataset(dataset_id)
            doc = ds.get_document(document_id)
            return doc.status
        except Exception as e:
            self.logger.error(f"get_document_status failed: {e}")
            return None

    # ----------------------------------------------------------------------
    # Retrieval
    # ----------------------------------------------------------------------

    def retrieve(self, dataset_id, query, top_k=5):
        """Retrieve relevant chunks from a dataset."""
        try:
            ds = self.sdk.get_dataset(dataset_id)
            results = ds.retrieve(query=query, top_k=top_k)
            return results
        except Exception as e:
            self.logger.error(f"retrieve failed: {e}")
            raise

    # ----------------------------------------------------------------------
    # Chat (if needed)
    # ----------------------------------------------------------------------

    def create_chat(self, name, dataset_ids):
        """Create a chat session with specified datasets."""
        try:
            chat = self.sdk.create_chat(name=name, dataset_ids=dataset_ids)
            return chat.id
        except Exception as e:
            self.logger.error(f"create_chat failed: {e}")
            raise

    def ask(self, chat_id, question, stream=False):
        """Ask a question in a chat session."""
        try:
            chat = self.sdk.get_chat(chat_id)
            response = chat.ask(question=question, stream=stream)
            return response
        except Exception as e:
            self.logger.error(f"ask failed: {e}")
            raise
