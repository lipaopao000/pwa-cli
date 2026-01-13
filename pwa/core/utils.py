# -*- coding: utf-8 -*-
"""
utils.py

Shared utility functions for PWA core modules.
Includes file I/O, text processing, and data parsing.

Note: Configuration and logging management has been moved to pwa.config and Python's logging module.
      Colors have been moved to pwa.ui.colors.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

# Try to import bibtexparser, handle if missing
try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    from bibtexparser.customization import convert_to_unicode

    BIBTEXPARSER_AVAILABLE = True
except ImportError:
    BIBTEXPARSER_AVAILABLE = False

# Get logger for this module
logger = logging.getLogger(__name__)


def load_markdown_content(file_path: str) -> str:
    """
    Loads content from a Markdown file.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        Content of the file as a string, or empty string on error.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load Markdown file {file_path}: {e}")
        return ""


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculates Jaccard similarity between two strings.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Jaccard similarity score (0.0 to 1.0).
    """
    set1 = set(re.findall(r"\w+", text1.lower()))
    set2 = set(re.findall(r"\w+", text2.lower()))
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


def extract_doi(text: str) -> Optional[str]:
    """
    Extracts DOI from text.

    Args:
        text: Text to search for DOI.

    Returns:
        DOI string if found, None otherwise.
    """
    if not text:
        return None
    
    # Pattern for DOI: 10.xxxx/xxxxx
    doi_pattern = r'10\.\d{4,}(?:\.\d+)*\/(?:(?!["&\'<>])\S)+'
    match = re.search(doi_pattern, text)
    if match:
        return match.group(0)
    return None


def normalize_title(title: str) -> str:
    """
    Normalizes a title for comparison.

    Args:
        title: Title string to normalize.

    Returns:
        Normalized title (lowercase, no punctuation, single spaces).
    """
    if not title:
        return ""
    
    # Convert to lowercase
    title = title.lower()
    
    # Remove punctuation
    title = re.sub(r'[^\w\s]', ' ', title)
    
    # Normalize whitespace
    title = ' '.join(title.split())
    
    return title.strip()


def normalize_doi(doi: str) -> str:
    """
    Normalizes a DOI string by removing prefixes.

    Args:
        doi: DOI string (may include https://doi.org/ prefix).

    Returns:
        Normalized DOI string.
    """
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://doi\.org/", "", doi)
    doi = re.sub(r"^doi\.org/", "", doi)
    doi = re.sub(r"^doi:", "", doi)
    return doi.strip()


def parse_biblatex_content(biblatex_content: str) -> List[Dict[str, Any]]:
    """
    Parses BibLaTeX content into a list of dictionaries.

    Standardizes keys: ID, title, abstract, doi, url, file_paths.

    Args:
        biblatex_content: BibLaTeX content as a string.

    Returns:
        List of parsed entry dictionaries.
    """
    if not BIBTEXPARSER_AVAILABLE:
        logger.warning("bibtexparser not found. Using regex fallback (less reliable).")
        return _parse_biblatex_regex(biblatex_content)

    try:
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.loads(biblatex_content, parser=parser)

        parsed_entries = []
        for entry in bib_database.entries:
            # Normalize fields
            entry_id = entry.get("ID", "")
            title = entry.get("title", "").replace("\n", " ").strip()
            # Remove brace protection often found in BibTeX titles ({Title})
            title = re.sub(r"^{(.*)}$", r"\1", title)

            abstract = entry.get("abstract", "").replace("\n", " ").replace("\\", "").strip()
            # Clean TLDR
            tldr_match = re.search(r"TLDR:\s*(.*)", abstract)
            if tldr_match:
                abstract = tldr_match.group(1).strip()

            doi = entry.get("doi", "")
            url = entry.get("url", "")

            # Parse file paths from 'file' field (Zotero format: Title:path:type;Title:path:type)
            file_paths = []
            file_field = entry.get("file", "")
            if file_field:
                for f_part in file_field.split(";"):
                    f_part = f_part.strip()
                    if not f_part:
                        continue
                    # Logic to extract path. Usually it's between two colons or at the end.
                    # Zotero: Name:Path:Type
                    # But sometimes just Path if manual.
                    # Simple heuristic: look for .pdf
                    if ".pdf" in f_part.lower():
                        # split by :
                        parts = f_part.split(":")
                        for p in parts:
                            if p.lower().endswith(".pdf"):
                                # Check if absolute or relative
                                clean_path = p.strip()
                                # Handle Zotero storage location expansion if needed (simplistic here)
                                if os.path.exists(clean_path):
                                    file_paths.append(clean_path)
                                elif clean_path.startswith("storage/"):
                                    # Fallback for Zotero relative paths
                                    zotero_base = os.path.expanduser("~/Zotero/")
                                    full_p = os.path.join(zotero_base, clean_path)
                                    if os.path.exists(full_p):
                                        file_paths.append(full_p)
                                break

            parsed_entries.append(
                {
                    "ID": entry_id,
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "file_paths": file_paths,
                    "raw": entry,  # Keep raw just in case
                }
            )

        return parsed_entries
    except Exception as e:
        logger.error(f"BibLaTeX parsing failed: {e}")
        return []


def _parse_biblatex_regex(content: str) -> List[Dict[str, Any]]:
    """
    Fallback Regex parser for BibLaTeX.

    Args:
        content: BibLaTeX content as a string.

    Returns:
        List of parsed entry dictionaries.
    """
    entries = []
    # Split by @type{
    raw_entries = re.split(r"@\w+\s*\{", content)

    for raw in raw_entries[1:]:  # Skip preamble
        # Extract ID (first string before comma)
        id_match = re.match(r"([^,]+),", raw)
        if not id_match:
            continue
        entry_id = id_match.group(1).strip()

        # Simple extractors
        title = _extract_field_regex(raw, "title")
        abstract = _extract_field_regex(raw, "abstract")
        doi = _extract_field_regex(raw, "doi")
        url = _extract_field_regex(raw, "url")
        file_field = _extract_field_regex(raw, "file")

        file_paths = []
        if file_field:
            if ".pdf" in file_field.lower():
                # Very basic extraction
                parts = file_field.split(":")
                for p in parts:
                    if p.lower().endswith(".pdf"):
                        if os.path.exists(p.strip()):
                            file_paths.append(p.strip())

        entries.append(
            {
                "ID": entry_id,
                "title": title,
                "abstract": abstract,
                "doi": doi,
                "url": url,
                "file_paths": file_paths,
            }
        )
    return entries


def _extract_field_regex(text: str, field: str) -> str:
    """
    Helper to extract field value using regex.

    Args:
        text: Text to search in.
        field: Field name to extract.

    Returns:
        Extracted field value or empty string.
    """
    # Matches field = {value} or field = "value"
    pattern = re.compile(rf'{field}\s*=\s*[\{{"](.*?)(?<!\\)[\}}"]', re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    if match:
        val = match.group(1)
        return val.replace("\n", " ").strip()
    return ""


def parse_json_content(json_content: str) -> List[Dict[str, Any]]:
    """
    Parses CSL JSON content into a list of dictionaries.

    Standardizes keys: ID, title, abstract, doi, url.

    Args:
        json_content: JSON content as a string.

    Returns:
        List of parsed entry dictionaries.
    """
    try:
        data = json.loads(json_content)
        parsed_entries = []
        for item in data:
            entry_id = str(item.get("id", "")) or str(item.get("ID", ""))
            if not entry_id:
                continue

            title = item.get("title", "")
            abstract = item.get("abstract", "")
            doi = item.get("DOI") or item.get("doi", "")
            url = item.get("URL") or item.get("url", "")

            parsed_entries.append(
                {
                    "ID": entry_id,
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "url": url,
                    "file_paths": [],  # JSON export usually doesn't include local file paths in the same way
                }
            )
        return parsed_entries
    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        return []
