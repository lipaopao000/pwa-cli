"""
Setup script for PWA CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from version.py
version = {}
with open("pwa/version.py") as f:
    exec(f.read(), version)

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="pwa-cli",
    version=version['__version__'],
    author=version['__author__'],
    description=version['__description__'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=version['__url__'],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "bibtexparser>=1.4.0",
        "openai>=1.0.0",
    ],
    extras_require={
        "async": ["aiohttp>=3.8.0"],
        "progress": ["tqdm>=4.65.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pwa=pwa.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pwa": ["py.typed"],
    },
)
