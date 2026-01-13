"""
Tests for MarkItDownClient Client
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from pwa.clients.markitdown import MarkItDownClient, convert_to_markdown


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = temp_dir / "sample.txt"
    content = """This is a test document.

It has multiple paragraphs.

- Bullet 1
- Bullet 2

And some more text.
"""
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def client():
    """Create a MarkItDownClient client instance."""
    return MarkItDownClient()


class TestMarkItDownClient:
    """Test suite for MarkItDownClient."""
    
    def test_client_initialization(self, client):
        """Test that client initializes successfully."""
        assert client is not None
        assert hasattr(client, 'convert_file')
        assert hasattr(client, 'convert_to_file')
    
    def test_convert_text_file(self, client, sample_text_file):
        """Test converting a text file to markdown."""
        result = client.convert_file(sample_text_file)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "test document" in result.lower()
    
    def test_convert_to_file(self, client, sample_text_file, temp_dir):
        """Test converting and saving to file."""
        output_path = temp_dir / "output.md"
        result_path = client.convert_to_file(sample_text_file, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        
        content = output_path.read_text(encoding='utf-8')
        assert len(content) > 0
        assert "test document" in content.lower()
    
    def test_convert_to_file_auto_name(self, client, sample_text_file):
        """Test converting with automatic output filename."""
        result_path = client.convert_to_file(sample_text_file)
        
        expected_path = sample_text_file.with_suffix('.md')
        assert result_path == expected_path
        assert result_path.exists()
        
        # Clean up
        result_path.unlink()
    
    def test_convert_nonexistent_file(self, client):
        """Test converting a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            client.convert_file("nonexistent_file.txt")
    
    def test_get_supported_formats(self, client):
        """Test getting supported formats."""
        formats = client.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert '.docx' in formats
        assert '.pdf' in formats
        assert '.txt' in formats
    
    def test_is_supported(self, client):
        """Test checking if a file format is supported."""
        assert client.is_supported("document.docx")
        assert client.is_supported("document.pdf")
        assert client.is_supported("document.txt")
        assert not client.is_supported("document.unknown")
    
    def test_convert_docx_validation(self, client, sample_text_file):
        """Test that convert_docx validates file extension."""
        with pytest.raises(ValueError, match="Expected .docx file"):
            client.convert_docx(sample_text_file)


class TestConvenienceFunctions:
    """Test suite for convenience functions."""
    
    def test_convert_to_markdown(self, sample_text_file):
        """Test the convert_to_markdown convenience function."""
        result = convert_to_markdown(sample_text_file)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "test document" in result.lower()


class TestPathHandling:
    """Test suite for path handling."""
    
    def test_string_path_input(self, client, sample_text_file):
        """Test that string paths work correctly."""
        result = client.convert_file(str(sample_text_file))
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_path_object_input(self, client, sample_text_file):
        """Test that Path objects work correctly."""
        result = client.convert_file(sample_text_file)
        assert isinstance(result, str)
        assert len(result) > 0


class TestErrorHandling:
    """Test suite for error handling."""
    
    def test_missing_markitdown_source(self, monkeypatch, temp_dir):
        """Test error when markitdown source is not found."""
        # Mock the project root to point to a directory without .markitdown
        def mock_parent():
            return temp_dir
        
        # This test is tricky because we need to mock Path behavior
        # For now, we'll skip this test as it requires complex mocking
        pytest.skip("Requires complex path mocking")
    
    def test_conversion_error_handling(self, client):
        """Test that conversion errors are properly handled."""
        # Create a file with an unsupported format
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03')
            temp_path = Path(f.name)
        
        try:
            # This should not raise an exception, but may return unexpected content
            # The actual behavior depends on markitdown's handling
            result = client.convert_file(temp_path)
            assert isinstance(result, str)
        finally:
            temp_path.unlink()


class TestBatchConversion:
    """Test suite for batch conversion scenarios."""
    
    def test_multiple_files_conversion(self, client, temp_dir):
        """Test converting multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = temp_dir / f"test_{i}.txt"
            file_path.write_text(f"Test content {i}", encoding='utf-8')
            files.append(file_path)
        
        # Convert all files
        results = []
        for file_path in files:
            result = client.convert_file(file_path)
            results.append(result)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert f"Test content {i}" in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
