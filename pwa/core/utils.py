# -*- coding: utf-8 -*-
"""
utils.py

Shared utility functions for the paper-writing-assistant skill.
Includes logging, configuration management, file I/O, text processing, and data parsing.
"""

import os
import sys
import logging
import yaml
import json
import re
import shutil
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union

# Try to import bibtexparser, handle if missing
try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    from bibtexparser.customization import convert_to_unicode, author
    BIBTEXPARSER_AVAILABLE = True
except ImportError:
    BIBTEXPARSER_AVAILABLE = False

# ANSI Color Codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def setup_logging(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with both console and file handlers.
    
    Args:
        name: Logger name.
        log_file: Path to the log file. If None, only console logging is enabled.
        level: Logging level (default: logging.INFO).
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers to prevent duplicates

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING if level == logging.DEBUG else level) # Keep console clean usually
    console_handler.setFormatter(logging.Formatter('%(message)s')) # Simple format for console
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"{Colors.YELLOW}[Warning] Could not setup file logging to {log_file}: {e}{Colors.RESET}", file=sys.stderr)

    return logger

def load_yaml_config(config_path: str) -> Optional[Dict[str, Any]]:
    """Loads a YAML configuration file."""
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"{Colors.RED}[Error] Failed to load config {config_path}: {e}{Colors.RESET}", file=sys.stderr)
        return None

def load_markdown_content(file_path: str) -> str:
    """Loads content from a Markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"{Colors.RED}[Error] Failed to load Markdown file {file_path}: {e}{Colors.RESET}", file=sys.stderr)
        return ""

def get_or_create_config_cache_dir(md_path: str) -> str:
    """
    Gets or creates the 'config-and-cache' directory relative to the Markdown file.
    If md_path is in CWD, creates it in CWD.
    """
    md_dir = os.path.dirname(os.path.abspath(md_path))
    cache_dir = os.path.join(md_dir, 'config-and-cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def ensure_config_in_cache(config_name: str, cache_dir: str, source_dir: str = None) -> str:
    """
    Ensures a configuration file exists in the cache directory by copying it from the source directory.
    
    Args:
        config_name: Name of the config file (e.g., 'zotero_config.yaml').
        cache_dir: Destination directory.
        source_dir: Source directory (default: current working directory).
        
    Returns:
        Path to the cached config file.
    """
    if source_dir is None:
        source_dir = os.getcwd()
        
    cached_config_path = os.path.join(cache_dir, config_name)
    source_config_path = os.path.join(source_dir, config_name)

    if not os.path.exists(cached_config_path):
        if os.path.exists(source_config_path):
            try:
                shutil.copy(source_config_path, cached_config_path)
                # Using print here as logger might not be set up yet
                # print(f"Copied {config_name} to {cache_dir}", file=sys.stderr)
            except Exception as e:
                print(f"{Colors.YELLOW}[Warning] Failed to copy {config_name}: {e}{Colors.RESET}", file=sys.stderr)
        else:
            # print(f"{Colors.YELLOW}[Warning] {config_name} not found in {source_dir}.{Colors.RESET}", file=sys.stderr)
            pass
            
    return cached_config_path

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculates Jaccard similarity between two strings."""
    set1 = set(re.findall(r'\w+', text1.lower()))
    set2 = set(re.findall(r'\w+', text2.lower()))
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

def normalize_doi(doi: str) -> str:
    """Normalizes a DOI string by removing prefixes."""
    if not doi:
        return ''
    doi = doi.strip().lower()
    doi = re.sub(r'^https?://doi\.org/', '', doi)
    doi = re.sub(r'^doi\.org/', '', doi)
    doi = re.sub(r'^doi:', '', doi)
    return doi.strip()

def parse_biblatex_content(biblatex_content: str) -> List[Dict[str, Any]]:
    """
    Parses BibLaTeX content into a list of dictionaries.
    Standardizes keys: ID, title, abstract, doi, url, file_paths.
    """
    if not BIBTEXPARSER_AVAILABLE:
        print(f"{Colors.YELLOW}[Warning] bibtexparser not found. Using regex fallback (less reliable).{Colors.RESET}", file=sys.stderr)
        return _parse_biblatex_regex(biblatex_content)

    try:
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.loads(biblatex_content, parser=parser)
        
        parsed_entries = []
        for entry in bib_database.entries:
            # Normalize fields
            entry_id = entry.get('ID', '')
            title = entry.get('title', '').replace('\n', ' ').strip()
            # Remove brace protection often found in BibTeX titles ({Title})
            title = re.sub(r'^{(.*)}$', r'\1', title) 
            
            abstract = entry.get('abstract', '').replace('\n', ' ').replace('\\', '').strip()
            # Clean TLDR
            tldr_match = re.search(r'TLDR:\s*(.*)', abstract)
            if tldr_match:
                abstract = tldr_match.group(1).strip()
                
            doi = entry.get('doi', '')
            url = entry.get('url', '')
            
            # Parse file paths from 'file' field (Zotero format: Title:path:type;Title:path:type)
            file_paths = []
            file_field = entry.get('file', '')
            if file_field:
                for f_part in file_field.split(';'):
                    f_part = f_part.strip()
                    if not f_part: continue
                    # Logic to extract path. Usually it's between two colons or at the end.
                    # Zotero: Name:Path:Type
                    # But sometimes just Path if manual.
                    # Simple heuristic: look for .pdf
                    if '.pdf' in f_part.lower():
                        # split by :
                        parts = f_part.split(':')
                        for p in parts:
                            if p.lower().endswith('.pdf'):
                                # Check if absolute or relative
                                clean_path = p.strip()
                                # Handle Zotero storage location expansion if needed (simplistic here)
                                if os.path.exists(clean_path):
                                    file_paths.append(clean_path)
                                elif clean_path.startswith('storage/'):
                                    # Fallback for Zotero relative paths
                                    zotero_base = os.path.expanduser('~/Zotero/')
                                    full_p = os.path.join(zotero_base, clean_path)
                                    if os.path.exists(full_p):
                                        file_paths.append(full_p)
                                break
            
            parsed_entries.append({
                'ID': entry_id,
                'title': title,
                'abstract': abstract,
                'doi': doi,
                'url': url,
                'file_paths': file_paths,
                'raw': entry # Keep raw just in case
            })
            
        return parsed_entries
    except Exception as e:
        print(f"{Colors.RED}[Error] BibLaTeX parsing failed: {e}{Colors.RESET}", file=sys.stderr)
        return []

def _parse_biblatex_regex(content: str) -> List[Dict[str, Any]]:
    """Fallback Regex parser for BibLaTeX."""
    entries = []
    # Split by @type{
    raw_entries = re.split(r'@\w+\s*\{', content)
    
    for raw in raw_entries[1:]: # Skip preamble
        # Extract ID (first string before comma)
        id_match = re.match(r'([^,]+),', raw)
        if not id_match: continue
        entry_id = id_match.group(1).strip()
        
        # Simple extractors
        title = _extract_field_regex(raw, 'title')
        abstract = _extract_field_regex(raw, 'abstract')
        doi = _extract_field_regex(raw, 'doi')
        url = _extract_field_regex(raw, 'url')
        file_field = _extract_field_regex(raw, 'file')
        
        file_paths = []
        if file_field:
             if '.pdf' in file_field.lower():
                 # Very basic extraction
                 parts = file_field.split(':')
                 for p in parts:
                     if p.lower().endswith('.pdf'):
                         if os.path.exists(p.strip()):
                             file_paths.append(p.strip())
        
        entries.append({
            'ID': entry_id,
            'title': title,
            'abstract': abstract,
            'doi': doi,
            'url': url,
            'file_paths': file_paths
        })
    return entries

def _extract_field_regex(text: str, field: str) -> str:
    """Helper to extract field value using regex."""
    # Matches field = {value} or field = "value"
    pattern = re.compile(rf'{field}\s*=\s*[\{{"](.*?)(?<!\\)[\}}"]', re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    if match:
        val = match.group(1)
        return val.replace('\n', ' ').strip()
    return ""

def parse_json_content(json_content: str) -> List[Dict[str, Any]]:
    """
    Parses CSL JSON content into a list of dictionaries.
    Standardizes keys: ID, title, abstract, doi, url.
    """
    try:
        data = json.loads(json_content)
        parsed_entries = []
        for item in data:
            entry_id = str(item.get('id', '')) or str(item.get('ID', ''))
            if not entry_id: continue
            
            title = item.get('title', '')
            abstract = item.get('abstract', '')
            doi = item.get('DOI') or item.get('doi', '')
            url = item.get('URL') or item.get('url', '')
            
            parsed_entries.append({
                'ID': entry_id,
                'title': title,
                'abstract': abstract,
                'doi': doi,
                'url': url,
                'file_paths': [] # JSON export usually doesn't include local file paths in the same way
            })
        return parsed_entries
    except Exception as e:
        print(f"{Colors.RED}[Error] JSON parsing failed: {e}{Colors.RESET}", file=sys.stderr)
        return []
