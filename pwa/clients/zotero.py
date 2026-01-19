# -*- coding: utf-8 -*-
"""
zotero_client.py

Client for interacting with Zotero via Better BibTeX JSON-RPC API.
Provides direct access to Zotero's annotations without requiring PDF extraction.

Data Structure Overview:
- Item data: CSL-JSON format with citekey and library fields added by Better BibTeX
- Annotations: Enhanced with coordinates (x, y), image paths, and structured attachment info
- Notes: HTML strings (not objects) as returned by Better BibTeX API
- Attachments: Include annotation arrays with raw Zotero annotation data

API Behavior Notes:
- All methods return data structures based on Better BibTeX JSON-RPC API responses
- Search uses CSL-JSON format with BBT extensions
- Annotations include position data with pageIndex and rects coordinates
- Image annotations provide annotationImagePath when available
"""

import json
import logging
import os
import requests
from typing import Any, Dict, List, Optional, Tuple, Union, TypedDict

logger = logging.getLogger(__name__)

# Type definitions for better type safety
class CSLItem(TypedDict, total=False):
    """CSL-JSON item format with Better BibTeX extensions."""
    id: str
    type: str  # item type like 'article-journal', 'book', etc.
    title: str
    author: List[Dict[str, str]]  # [{'family': 'Smith', 'given': 'John'}]
    issued: Dict[str, List[List[int]]]  # {'date-parts': [[2023, 1, 15]]}
    publisher: str
    volume: str
    issue: str
    page: str
    DOI: str
    URL: str
    abstract: str
    # Better BibTeX extensions
    citekey: str  # BBT generated citation key
    library: str  # library name (e.g., 'My Library')
    # Note: 'container-title' is accessed via item.get('container-title')

class AttachmentInfo(TypedDict):
    key: str
    filename: str
    title: str
    path: Union[str, bool]  # path can be a string or False

class ProcessedAnnotation(TypedDict):
    id: str
    type: str
    color: str
    annotatedText: str
    comment: str
    page: int
    pageLabel: str
    x: float
    y: float
    date: str
    imagePath: str
    attachment: AttachmentInfo
    markdown: str


class ZoteroClient:
    """
    A client to interact with Zotero's local Better BibTeX JSON-RPC API.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """
        Initialize the ZoteroClient.

        Args:
            config: Zotero configuration dictionary.
            config_path: Path to the configuration file (fallback).
        """
        raw_config = config or self._load_config(config_path)
        if not raw_config:
            self.zcfg = {}
        else:
            # Handle both direct ZoteroConfig and nested config
            self.zcfg = raw_config.get("zotero") if "zotero" in raw_config else raw_config

        self.port = self.zcfg.get("port", "23119")
        database = self.zcfg.get("database", "Zotero")
        if database == "Juris-M":
            self.port = "24119"

        self.base_url = f"http://127.0.0.1:{self.port}/better-bibtex/json-rpc"
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PWA-CLI ZoteroClient/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
        }

    def _load_config(self, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Loads Zotero configuration."""
        try:
            from ..config import ConfigManager
            config_manager = ConfigManager()
            return config_manager.load_config("zotero")
        except Exception as e:
            logger.warning(f"ConfigManager not available or failed: {e}")

        if config_path and os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")

        return None

    def _make_rpc_request(self, method: str, params: List[Any]) -> Any:
        """Make a JSON-RPC request to the Zotero API."""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60 # Increased timeout for potential large library exports
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = str(data['error'].get('message', 'Unknown error'))
                error_data = data['error'].get('data', '')
                if error_data:
                    error_msg += f": {error_data}"
                raise Exception(f"API error: {error_msg}")

            return data.get("result", {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {str(e)}. Is Zotero running with Better BibTeX installed?")

    def is_zotero_running(self) -> bool:
        """Check if Zotero is running and accessible."""
        try:
            response = requests.get(
                f"http://127.0.0.1:{self.port}/better-bibtex/cayw?probe=true",
                headers=self.headers,
                timeout=5
            )
            return response.text == "ready"
        except:
            return False

    def get_groups(self, include_collections: bool = False) -> List[Dict[str, Any]]:
        """
        List the libraries (groups) the user has in Zotero.
        
        Args:
            include_collections: Whether to include a list of collections for each library.
            
        Returns:
            A list of group/library dictionaries.
        """
        try:
            return self._make_rpc_request("user.groups", [include_collections])
        except Exception as e:
            logger.warning(f"Could not get groups: {e}")
            return []

    def view_pdf(self, item_id: str, page: int = 0) -> bool:
        """
        Open the PDF associated with an entry and jump to a specific page.
        
        Args:
            item_id: The ID of the attachment item (e.g. http://zotero.org/users/123/items/ABC)
            page: Page number, counting from zero (0 is first page).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self._make_rpc_request("viewer.viewPDF", [item_id, page])
            return True
        except Exception as e:
            logger.warning(f"Could not open PDF: {e}")
            return False

    def search(self, terms: Union[str, List[Any]] = "", library: Union[str, int, None] = None) -> List[CSLItem]:
        """
        Search for items in Zotero.
        
        Args:
            terms: Search terms. 
                  - Simple string: "quick search" (e.g., "Zotero 2024")
                  - Advanced search: List of conditions (e.g., [['title', 'contains', 'Zotero']])
                  - Logic: [['joinMode', 'any'], ['creator', 'contains', 'Smith'], ['title', 'contains', 'Zotero']]
            library: Optional library name or ID to search in.
            
        Returns:
            A list of matching items.
            
        Examples:
            search("Zotero")  # Quick search
            search([['title', 'contains', 'Zotero']])  # Search by title
            search([['creator', 'contains', 'Smith'], ['date', 'contains', '2023']])  # AND search
            search([['joinMode', 'any'], ['title', 'contains', 'AI'], ['abstract', 'contains', 'AI']]) # OR search
        """
        params = [terms]
        if library is not None:
            params.append(library)
            
        try:
            return self._make_rpc_request("item.search", params)
        except Exception as e:
            logger.warning(f"Search failed for terms '{terms}': {e}")
            return []

    def get_item_by_citekey(self, citekey: str) -> CSLItem:
        """Get item data by citation key.

        Returns:
            CSL-JSON formatted item data (standardized format from Better BibTeX).
            Includes citekey and library information as per BBT API behavior.
        """
        # Use exact citekey search - BBT API supports this directly
        try:
            # Try exact citekey match first
            search_results = self.search([['citationKey', 'is', citekey]])
            if search_results:
                return search_results[0]

            # Fallback to contains search (case-insensitive behavior)
            search_results = self.search(citekey)
            item = next((item for item in search_results if item.get('citekey') == citekey), None)
            if item:
                return item

        except Exception as e:
            logger.warning(f"Could not find item with citekey {citekey}: {e}")

        raise Exception(f"No items found with citekey: {citekey}")

    def _parse_export_result(self, result: Any) -> Dict[str, Any]:
        """
        Parse the BBT export result, handling version differences.
        Newer BBT versions (6.7.143+) removed an extra layer of wrapping.
        """
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return {"raw": result}
        
        # Handle older versions where result might be a list or have different structure
        if isinstance(result, list):
            # Try to find a string that looks like JSON
            for item in result:
                if isinstance(item, str) and (item.strip().startswith('{') or item.strip().startswith('[')):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict): return parsed
                    except: continue
        
        if isinstance(result, dict):
            return result
            
        return {}

    def get_attachments(self, citekey: str, library: Union[str, int] = '*') -> List[Dict[str, Any]]:
        """
        Get all attachments for an item.
        'library' can be a libraryID or '*' for cross-library search.
        """
        try:
            return self._make_rpc_request("item.attachments", [citekey, library])
        except Exception as e:
            logger.warning(f"Could not get attachments for {citekey}: {e}")
            return []

    def get_item_notes(self, citekey: str) -> List[str]:
        """Fetch the notes for a citekey.

        Returns:
            List of HTML note strings (based on Better BibTeX API behavior).
        """
        try:
            notes_dict = self._make_rpc_request("item.notes", [[citekey]])
            return notes_dict.get(citekey, [])
        except Exception as e:
            logger.warning(f"Could not get notes for {citekey}: {e}")
            return []

    def export_bibtex(self, citekeys: List[str], library_id: Optional[int] = None) -> str:
        """Export BibTeX for a list of citekeys."""
        try:
            translator_id = "ca65189f-8815-4afe-8c8b-8c7c15f0edca" # Better BibTeX
            params = [citekeys, translator_id]
            if library_id is not None:
                params.append(library_id)
                
            export_result = self._make_rpc_request("item.export", params)
            
            if isinstance(export_result, str):
                return export_result
            elif isinstance(export_result, list) and len(export_result) > 0:
                return export_result[0] if isinstance(export_result[0], str) else str(export_result[0])
            return str(export_result)
        except Exception as e:
            logger.error(f"Error exporting BibTeX: {e}")
            return ""

    def fetch_biblatex(self) -> Optional[str]:
        """
        Fetch all regular reference items in BibLaTeX format from the library.
        Implementation: Search for every item then export.
        """
        try:
            # item.search('') returns every entry according to docs
            all_entries = self.search("")
            
            if not all_entries:
                return None
            
            # We must provide citekeys to item.export
            # BBT translator will automatically ignore items it can't export (like attachments)
            citekeys = [item['citekey'] for item in all_entries if item.get('citekey')]
            if not citekeys:
                return None
                
            # Use BibLaTeX translator
            translator_id = "f895aa0d-f28e-47fe-b924-4e9d281ef89d" # Better BibLaTeX
            return self._make_rpc_request("item.export", [citekeys, translator_id])
        except Exception as e:
            logger.warning(f"fetch_biblatex failed: {e}")
            return None


def process_annotation(annotation: Dict[str, Any], attachment: Dict[str, Any], format_type: str = 'markdown') -> ProcessedAnnotation:
    """
    Process a raw Zotero annotation into a more usable format.

    Enhanced to support coordinates and image annotations based on Better BibTeX API behavior.

    Args:
        annotation: The raw annotation data from Zotero
        attachment: The attachment this annotation belongs to
        format_type: Output format ('raw' or 'markdown')

    Returns:
        A processed annotation object with enhanced coordinate and image support.
    """
    try:
        annotation_type = annotation.get('annotationType', 'unknown')
        color = annotation.get('annotationColor', '')

        # Extract text content
        text = annotation.get('annotationText', '')
        comment = annotation.get('annotationComment', '')

        # Handle page information
        page_label = annotation.get('annotationPageLabel', '1')
        page = 1

        # Get position data and coordinates
        position = annotation.get('annotationPosition', {})
        x, y = 0, 0

        if isinstance(position, str):
            try:
                position = json.loads(position)
            except:
                position = {}

        if position:
            # Get page index if available
            if 'pageIndex' in position:
                page = position['pageIndex'] + 1

            # Get coordinates if available (rects contain bounding box coordinates)
            if 'rects' in position and position['rects'] and len(position['rects'][0]) >= 2:
                x, y = position['rects'][0][0], position['rects'][0][1]

        # Handle image annotations (BBT API provides annotationImagePath)
        image_path = annotation.get('annotationImagePath', '')

        # Extract attachment information from actual API response structure
        # API returns: {"open": "zotero://open-pdf/library/items/ITEMKEY", "path": "/path/to/file.pdf"}
        attachment_key = ''
        if 'open' in attachment and attachment['open']:
            # Extract itemKey from URL: zotero://open-pdf/library/items/ITEMKEY
            open_url = attachment['open']
            if 'items/' in open_url:
                attachment_key = open_url.split('items/')[-1]

        attachment_path = attachment.get('path', '')
        attachment_filename = ''
        attachment_title = 'PDF'  # Default title

        if attachment_path and attachment_path != False:
            attachment_filename = os.path.basename(attachment_path)
            # Use filename (without extension) as title
            attachment_title = os.path.splitext(attachment_filename)[0]
        elif attachment_key:
            attachment_title = f"PDF ({attachment_key})"

        result = {
            'id': annotation.get('key', ''),
            'type': annotation_type,
            'color': color,
            'annotatedText': text,
            'comment': comment,
            'page': page,
            'pageLabel': page_label,
            'x': x,
            'y': y,
            'date': annotation.get('dateModified', ''),
            'imagePath': image_path,  # For image annotations
            'attachment': {
                'key': attachment_key,
                'filename': attachment_filename,
                'title': attachment_title,
                'path': attachment_path,
            }
        }

        # If markdown format is requested, format the output
        if format_type == 'markdown':
            result['markdown'] = format_annotation_markdown(result)

        return result
    except Exception as e:
        logger.error(f"Error processing annotation: {e}")
        return {}


def format_annotation_markdown(annotation: Dict[str, Any]) -> str:
    """Format an annotation as markdown."""
    md = []
    if annotation['annotatedText']:
        color_str = f" ({annotation['color']})" if annotation['color'] else ""
        md.append(f"> \"{annotation['annotatedText']}\"{color_str} {annotation['type'].capitalize()} [Page {annotation['pageLabel']}]")
    if annotation['comment']:
        md.append(f"\n{annotation['comment']}")
    return "\n".join(md)


def fetch_preferred_references(
    local_ref_path: Optional[str] = None,
    zotero_config: Optional[Dict[str, Any]] = None,
    zotero_config_path: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Strategy function to fetch references.
    """
    client = ZoteroClient(config=zotero_config, config_path=zotero_config_path)

    if client.is_zotero_running():
        content = client.fetch_biblatex()
        if content:
            logger.info("Successfully fetched references from local Zotero")
            return content, "biblatex"

    if local_ref_path and os.path.exists(local_ref_path):
        ext = os.path.splitext(local_ref_path)[1].lower()
        try:
            with open(local_ref_path, "r", encoding="utf-8") as f:
                txt = f.read()
            if ext in [".bib", ".biblatex"]:
                return txt, "biblatex"
            elif ext in [".json", ".csljson"]:
                return txt, "csljson"
            return txt, ext.lstrip(".")
        except Exception as e:
            logger.error(f"Failed to read local file {local_ref_path}: {e}")

    return None, None
