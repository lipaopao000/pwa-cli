"""
MarkItDown Client

This module provides a client for converting documents to Markdown using the custom markitdown library.
The markitdown library is cloned from GitHub and added to sys.path at runtime.
"""

import sys
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class MarkItDownClient:
    """Client for converting documents to Markdown using markitdown library."""
    
    def __init__(self):
        """Initialize the MarkItDown client."""
        self._ensure_markitdown_available()
        self._markitdown = None
    
    def _ensure_markitdown_available(self):
        """Ensure markitdown library is available in sys.path."""
        project_root = Path(__file__).parent.parent.parent
        markitdown_src = project_root / ".markitdown" / "packages" / "markitdown" / "src"
        
        if not markitdown_src.exists():
            raise RuntimeError(
                f"markitdown source not found at {markitdown_src}\n"
                "Please run: ./scripts/install_markitdown.sh"
            )
        
        markitdown_src_str = str(markitdown_src)
        if markitdown_src_str not in sys.path:
            sys.path.insert(0, markitdown_src_str)
            logger.debug(f"Added markitdown to sys.path: {markitdown_src_str}")
    
    def _get_markitdown(self):
        """Lazy load MarkItDown class."""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown
                self._markitdown = MarkItDown()
                logger.debug("MarkItDown instance created successfully")
            except ImportError as e:
                raise RuntimeError(
                    f"Failed to import markitdown: {e}\n"
                    "Please run: ./scripts/install_markitdown.sh"
                )
        return self._markitdown
    
    def convert_file(self, file_path: Union[str, Path]) -> str:
        """
        Convert a document file to Markdown.
        
        Args:
            file_path: Path to the document file (docx, pdf, pptx, xlsx, etc.)
        
        Returns:
            Markdown content as string
        
        Raises:
            FileNotFoundError: If the file does not exist
            RuntimeError: If conversion fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            markitdown = self._get_markitdown()
            result = markitdown.convert(str(file_path))
            
            if hasattr(result, 'text_content'):
                return result.text_content
            elif isinstance(result, str):
                return result
            else:
                raise RuntimeError(f"Unexpected result type: {type(result)}")
        
        except Exception as e:
            logger.error(f"Failed to convert {file_path}: {e}")
            raise RuntimeError(f"Failed to convert {file_path}: {e}")
    
    def convert_to_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Convert a document file to Markdown and save to file.
        
        Args:
            input_path: Path to the input document file
            output_path: Path to save the output Markdown file.
                        If None, uses input filename with .md extension.
        
        Returns:
            Path to the output Markdown file
        
        Raises:
            FileNotFoundError: If the input file does not exist
            RuntimeError: If conversion fails
        """
        input_path = Path(input_path)
        
        if output_path is None:
            output_path = input_path.with_suffix('.md')
        else:
            output_path = Path(output_path)
        
        markdown_content = self.convert_file(input_path)
        
        output_path.write_text(markdown_content, encoding='utf-8')
        logger.info(f"Converted {input_path} to {output_path}")
        
        return output_path
    
    def convert_docx(self, docx_path: Union[str, Path]) -> str:
        """
        Convert a DOCX file to Markdown.
        
        Args:
            docx_path: Path to the DOCX file
        
        Returns:
            Markdown content as string
        
        Raises:
            FileNotFoundError: If the file does not exist
            RuntimeError: If conversion fails
        """
        docx_path = Path(docx_path)
        
        if docx_path.suffix.lower() != '.docx':
            raise ValueError(f"Expected .docx file, got: {docx_path.suffix}")
        
        return self.convert_file(docx_path)
    
    def convert_docx_to_file(
        self,
        docx_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Convert a DOCX file to Markdown and save to file.
        
        Args:
            docx_path: Path to the DOCX file
            output_path: Path to save the output Markdown file.
                        If None, uses input filename with .md extension.
        
        Returns:
            Path to the output Markdown file
        
        Raises:
            FileNotFoundError: If the input file does not exist
            RuntimeError: If conversion fails
        """
        return self.convert_to_file(docx_path, output_path)
    
    @staticmethod
    def get_supported_formats() -> list[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return [
            '.docx',  # Word documents
            '.pdf',   # PDF documents
            '.pptx',  # PowerPoint presentations
            '.xlsx',  # Excel spreadsheets
            '.html',  # HTML files
            '.txt',   # Text files
            '.csv',   # CSV files
            '.json',  # JSON files
            '.xml',   # XML files
        ]
    
    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file format is supported.
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if the file format is supported, False otherwise
        """
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.get_supported_formats()


# Convenience function for quick conversions
def convert_to_markdown(file_path: Union[str, Path]) -> str:
    """
    Convert a document file to Markdown (convenience function).
    
    Args:
        file_path: Path to the document file
    
    Returns:
        Markdown content as string
    """
    client = MarkItDownClient()
    return client.convert_file(file_path)
