#!/bin/bash
# Install RAGFlow SDK from GitHub
# This script ensures PWA-CLI always uses the latest RAGFlow SDK

set -e

echo "=== Installing RAGFlow SDK from GitHub ==="

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RAGFLOW_DIR="$PROJECT_ROOT/.ragflow"
SDK_DIR="$RAGFLOW_DIR/sdk/python"

# Check if ragflow directory exists
if [ -d "$RAGFLOW_DIR" ]; then
    echo "✅ RAGFlow repository already exists at: $RAGFLOW_DIR"
    echo "📥 Pulling latest changes..."
    cd "$RAGFLOW_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "   (Pull failed, using existing version)"
else
    echo "📥 Cloning RAGFlow repository..."
    git clone --depth 1 https://github.com/infiniflow/ragflow.git "$RAGFLOW_DIR"
fi

# Check if SDK directory exists
if [ ! -d "$SDK_DIR" ]; then
    echo "❌ SDK directory not found at: $SDK_DIR"
    echo "   Expected path: ragflow/sdk/python"
    exit 1
fi

echo "✅ RAGFlow SDK directory found: $SDK_DIR"

# Install SDK in editable mode
echo "📦 Installing SDK in editable mode..."
cd "$SDK_DIR"

# Install SDK and its dependencies
pip install -e . 2>/dev/null || pip install requests pydantic beartype && pip install -e .

# Verify installation
echo ""
echo "🧪 Verifying installation..."
python3 << EOF
import sys
import os

# Add SDK to path
sdk_path = "$SDK_DIR"
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

try:
    import ragflow_sdk
    print("✅ ragflow_sdk imported successfully")
    print(f"   Location: {ragflow_sdk.__file__}")
    
    from ragflow_sdk import RAGFlow
    print("✅ RAGFlow class imported successfully")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"   SDK path: {sdk_path}")
    print(f"   sys.path: {sys.path[:3]}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 RAGFlow SDK installation completed successfully!"
    echo ""
    echo "📍 SDK Location: $SDK_DIR"
    echo "📝 To update SDK: run this script again"
    echo ""
    echo "ℹ️  Note: SDK is not installed via pip, but added to Python path at runtime"
    echo "   This ensures you always use the latest version from GitHub"
else
    echo ""
    echo "❌ Installation verification failed"
    exit 1
fi
