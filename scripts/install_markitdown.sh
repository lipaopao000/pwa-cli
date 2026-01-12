#!/bin/bash
# Install markitdown from GitHub
# This script ensures PWA-CLI always uses the latest markitdown

set -e

echo "=== Installing markitdown from GitHub ==="

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MARKITDOWN_DIR="$PROJECT_ROOT/.markitdown"
MARKITDOWN_SRC="$MARKITDOWN_DIR/packages/markitdown/src"

# Check if markitdown directory exists
if [ -d "$MARKITDOWN_DIR" ]; then
    echo "✅ markitdown repository already exists at: $MARKITDOWN_DIR"
    echo "📥 Pulling latest changes..."
    cd "$MARKITDOWN_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "   (Pull failed, using existing version)"
else
    echo "📥 Cloning markitdown repository..."
    git clone --depth 1 https://github.com/lipaopao000/markitdown.git "$MARKITDOWN_DIR"
fi

# Check if source directory exists
if [ ! -d "$MARKITDOWN_SRC" ]; then
    echo "❌ markitdown source directory not found at: $MARKITDOWN_SRC"
    echo "   Expected path: packages/markitdown/src"
    exit 1
fi

echo "✅ markitdown source directory found: $MARKITDOWN_SRC"

# Install markitdown in editable mode
echo "📦 Installing markitdown in editable mode..."
cd "$MARKITDOWN_DIR/packages/markitdown"

# Install package and its dependencies
pip install -e . 2>/dev/null || {
    echo "   (Standard install failed, trying manual dependencies...)"
    pip install python-docx mammoth pillow beautifulsoup4 lxml pdfplumber pandas openpyxl pptx youtube-transcript-api
    pip install -e .
}

# Verify installation
echo ""
echo "🧪 Verifying installation..."
python3 << EOF
import sys
import os

# Add markitdown src to path
markitdown_src = "$MARKITDOWN_SRC"
if markitdown_src not in sys.path:
    sys.path.insert(0, markitdown_src)

try:
    import markitdown
    print("✅ markitdown imported successfully")
    print(f"   Location: {markitdown.__file__}")
    
    # Check if MarkItDown class exists
    from markitdown import MarkItDown
    print("✅ MarkItDown class imported successfully")
    
    # Check version
    if hasattr(markitdown, '__version__'):
        print(f"   Version: {markitdown.__version__}")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"   markitdown src: {markitdown_src}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 markitdown installation completed successfully!"
    echo ""
    echo "📍 Location: $MARKITDOWN_SRC"
    echo "📝 To update: run this script again"
    echo ""
    echo "ℹ️  Note: markitdown is not installed via pip, but added to Python path at runtime"
    echo "   This ensures you always use the latest version from your GitHub repository"
else
    echo ""
    echo "❌ Installation verification failed"
    exit 1
fi
