# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Modern `pyproject.toml` configuration
- Pydantic models for configuration validation
- Custom exception hierarchy for better error handling
- Type annotations throughout the codebase
- GitHub Actions CI/CD workflow
- Makefile for common development tasks
- CONTRIBUTING.md with development guidelines
- Configuration validation with detailed error messages
- Improved logging with proper levels

### Changed
- Upgraded to modern Python packaging standards
- Improved code formatting with Black and isort
- Enhanced ConfigManager with validation support
- Better error handling in BaseAcademicAgent
- Improved type safety across modules

### Fixed
- Import ordering inconsistencies
- Missing type annotations in core modules

## [1.2.2] - 2024-01-XX

### Added
- Session management functionality
- Workflow management commands
- Citation verification with LangGraph agents
- RAGFlow integration for statement verification
- PubMed API client for medical literature search

### Changed
- Refactored command structure to plugin-based architecture
- Improved interactive menu system

### Fixed
- Reference matching accuracy improvements
- Zotero API authentication issues

## [1.0.0] - 2023-XX-XX

### Added
- Initial release
- Reference matching from Markdown documents
- Zotero integration
- Citation format conversion
- Full-text download with Mineru OCR
- Interactive CLI interface
- Configuration management system

[Unreleased]: https://github.com/lipaopao000/pwa-cli/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/lipaopao000/pwa-cli/releases/tag/v1.2.2
[1.0.0]: https://github.com/lipaopao000/pwa-cli/releases/tag/v1.0.0
