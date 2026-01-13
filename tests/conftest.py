"""
Pytest configuration and fixtures
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Mock ragflow_sdk if not installed
try:
    import ragflow_sdk
except ImportError:
    sys.modules["ragflow_sdk"] = MagicMock()


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_llm_config():
    """Sample LLM configuration."""
    return {
        "active_provider": "openai",
        "providers": {
            "openai": {
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 4096,
            }
        },
    }


@pytest.fixture
def sample_zotero_config():
    """Sample Zotero configuration."""
    return {
        "library_id": "12345",
        "library_type": "user",
        "api_key": "test-zotero-key",
    }


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file with references."""
    md_file = tmp_path / "paper.md"
    content = """# Test Paper

## Abstract
This is a test paper.

## Introduction
Some introduction text with citation^1^.

## References
[1] Smith, J. (2023). Test Paper. Journal of Testing, 10(1), 1-10.
[2] Doe, J. (2023). Another Paper. Testing Review, 5(2), 20-30.
"""
    md_file.write_text(content)
    return md_file


@pytest.fixture
def sample_bib_file(tmp_path):
    """Create a sample BibTeX file."""
    bib_file = tmp_path / "references.bib"
    content = """@article{smith2023test,
  title={Test Paper},
  author={Smith, John},
  journal={Journal of Testing},
  volume={10},
  number={1},
  pages={1--10},
  year={2023},
  doi={10.1234/test.2023.001}
}

@article{doe2023another,
  title={Another Paper},
  author={Doe, Jane},
  journal={Testing Review},
  volume={5},
  number={2},
  pages={20--30},
  year={2023}
}
"""
    bib_file.write_text(content)
    return bib_file
