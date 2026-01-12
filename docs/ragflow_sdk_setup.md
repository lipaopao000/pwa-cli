# RAGFlow SDK Setup Guide

PWA-CLI uses the RAGFlow SDK for statement verification. This document explains how to install and update the SDK.

## Why Not Use PyPI?

RAGFlow SDK is not available on PyPI, and even if it were, we want to ensure PWA-CLI always uses the **latest version** from GitHub. This approach provides:

- ✅ **Always up-to-date** - Get the latest features and bug fixes
- ✅ **No version conflicts** - Direct from source
- ✅ **Easy updates** - Just run the install script again

## Installation

### Automatic Installation (Recommended)

Run the installation script:

```bash
cd pwa-cli
./scripts/install_ragflow_sdk.sh
```

This script will:
1. Clone the RAGFlow repository to `.ragflow/` (if not exists)
2. Pull the latest changes (if already exists)
3. Install SDK dependencies
4. Verify the installation

### Manual Installation

If you prefer to install manually:

```bash
# 1. Clone RAGFlow repository
cd pwa-cli
git clone --depth 1 https://github.com/infiniflow/ragflow.git .ragflow

# 2. Install dependencies
pip install requests pydantic

# 3. Verify installation
python3 -c "import sys; sys.path.insert(0, '.ragflow/sdk/python'); from ragflow_sdk import RAGFlow; print('✅ OK')"
```

## How It Works

PWA-CLI uses a custom path resolution to load the RAGFlow SDK:

```python
# pwa/clients/ragflow.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ragflow_sdk_path = os.path.join(project_root, ".ragflow/sdk/python")

if os.path.exists(ragflow_sdk_path):
    sys.path.insert(0, ragflow_sdk_path)

from ragflow_sdk import RAGFlow
```

**Key points**:
- SDK is **not installed via pip**
- SDK path is added to `sys.path` at runtime
- This ensures you always use the version in `.ragflow/`

## Updating the SDK

To update to the latest version:

```bash
cd pwa-cli
./scripts/install_ragflow_sdk.sh
```

The script will automatically pull the latest changes from GitHub.

## Troubleshooting

### Import Error: No module named 'ragflow_sdk'

**Cause**: RAGFlow SDK not installed

**Solution**:
```bash
./scripts/install_ragflow_sdk.sh
```

### SDK Directory Not Found

**Cause**: `.ragflow/` directory missing or incomplete

**Solution**:
```bash
# Remove and reinstall
rm -rf .ragflow
./scripts/install_ragflow_sdk.sh
```

### Git Clone Failed

**Cause**: Network issues or GitHub access problems

**Solution**:
```bash
# Try manual clone
git clone https://github.com/infiniflow/ragflow.git .ragflow

# Or use SSH
git clone git@github.com:infiniflow/ragflow.git .ragflow
```

### Python Version Compatibility

**Note**: RAGFlow SDK requires Python 3.12+, but PWA-CLI uses Python 3.11.

**Solution**: We bypass the pip installation and directly add the SDK to Python path, which works fine for most use cases. If you encounter compatibility issues, consider:

1. Using Python 3.12+ environment
2. Reporting the issue to RAGFlow repository
3. Using an alternative verification method

## Directory Structure

```
pwa-cli/
├── .ragflow/                    # RAGFlow repository (git ignored)
│   └── sdk/
│       └── python/
│           └── ragflow_sdk/     # SDK package
│               ├── __init__.py
│               ├── ragflow.py
│               └── ...
├── pwa/
│   └── clients/
│       └── ragflow.py           # RAGFlow client wrapper
└── scripts/
    └── install_ragflow_sdk.sh   # Installation script
```

## Configuration

After installing the SDK, configure RAGFlow in `configs/RAGFlow.yaml`:

```yaml
# RAGFlow Configuration
api_key: "your-ragflow-api-key"
base_url: "https://your-ragflow-instance.com"
default_dataset_id: ""
timeout: 30
```

See `configs/RAGFlow.yaml.example` for a template.

## API Usage

Once installed, you can use the RAGFlow client:

```python
from pwa.clients import RAGFlowClient

# Initialize client
client = RAGFlowClient(
    base_url="https://your-ragflow-instance.com",
    api_key="your-api-key"
)

# Check connection
if client.check_connection():
    print("✅ Connected to RAGFlow")

# Create dataset
dataset_id = client.get_or_create_dataset("my_dataset")

# Upload document
doc_id = client.upload_document(dataset_id, "paper.pdf")

# Retrieve relevant chunks
results = client.retrieve(dataset_id, "What is the main finding?", top_k=5)
```

## Contributing

If you find issues with the RAGFlow SDK:

1. Check if it's a PWA-CLI integration issue → Open issue in pwa-cli repo
2. Check if it's a RAGFlow SDK issue → Open issue in [RAGFlow repo](https://github.com/infiniflow/ragflow)

## References

- [RAGFlow GitHub Repository](https://github.com/infiniflow/ragflow)
- [RAGFlow SDK Documentation](https://github.com/infiniflow/ragflow/tree/main/sdk/python)
- [PWA-CLI Documentation](../README.md)
