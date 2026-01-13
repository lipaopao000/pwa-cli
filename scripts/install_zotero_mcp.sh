#!/bin/bash
# Install Zotero-MCP from GitHub
# This script ensures PWA-CLI can use Zotero-MCP's core features

set -e

echo "=== Installing Zotero-MCP from GitHub ==="

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ZOTERO_MCP_DIR="$PROJECT_ROOT/.zotero-mcp"
SRC_DIR="$ZOTERO_MCP_DIR/src"

# Check if zotero-mcp directory exists
if [ -d "$ZOTERO_MCP_DIR" ]; then
    echo "✅ Zotero-MCP repository already exists at: $ZOTERO_MCP_DIR"
    echo "📥 Pulling latest changes..."
    cd "$ZOTERO_MCP_DIR"
    git pull origin main 2>/dev/null || echo "   (Pull failed, using existing version)"
else
    echo "📥 Cloning Zotero-MCP repository..."
    git clone --depth 1 https://github.com/54yyyu/zotero-mcp.git "$ZOTERO_MCP_DIR"
fi

# Check if src directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo "❌ Source directory not found at: $SRC_DIR"
    echo "   Expected path: zotero-mcp/src"
    exit 1
fi

echo "✅ Zotero-MCP source directory found: $SRC_DIR"

# Install core dependencies (excluding semantic search dependencies)
echo "📦 Installing core dependencies..."
pip install pyzotero>=1.5.0 markitdown python-dotenv>=1.0.0 pydantic>=2.0.0 requests>=2.28.0 2>/dev/null || {
    echo "⚠️  Some dependencies may already be installed"
}

# Verify installation
echo ""
echo "🧪 Verifying installation..."
python3 << EOF
import sys
import os

# Add src to path
src_path = "$SRC_DIR"
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    # Test core imports (excluding MCP server and semantic search)
    # Import modules directly to avoid __init__.py dependencies
    import importlib.util
    
    # Load client module
    client_path = os.path.join(src_path, 'zotero_mcp', 'client.py')
    spec = importlib.util.spec_from_file_location('zotero_mcp.client', client_path)
    client_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(client_module)
    print("✅ zotero_mcp.client imported successfully")
    
    # Load better_bibtex_client module
    bbt_path = os.path.join(src_path, 'zotero_mcp', 'better_bibtex_client.py')
    spec = importlib.util.spec_from_file_location('zotero_mcp.better_bibtex_client', bbt_path)
    bbt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bbt_module)
    print("✅ zotero_mcp.better_bibtex_client imported successfully")
    
    # Load pdfannots_downloader module
    pdf_path = os.path.join(src_path, 'zotero_mcp', 'pdfannots_downloader.py')
    spec = importlib.util.spec_from_file_location('zotero_mcp.pdfannots_downloader', pdf_path)
    pdf_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdf_module)
    print("✅ zotero_mcp.pdfannots_downloader imported successfully")
    
    # Load utils module
    utils_path = os.path.join(src_path, 'zotero_mcp', 'utils.py')
    spec = importlib.util.spec_from_file_location('zotero_mcp.utils', utils_path)
    utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utils_module)
    print("✅ zotero_mcp.utils imported successfully")
    
    print("")
    print("✅ All core modules imported successfully")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"   Source path: {src_path}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Zotero-MCP installation completed successfully!"
    echo ""
    echo "📍 Source Location: $SRC_DIR"
    echo "📝 To update: run this script again"
    echo ""
    echo "✨ Available Features:"
    echo "   - Local Zotero connection (no API key needed)"
    echo "   - PDF annotation extraction"
    echo "   - Better BibTeX integration"
    echo "   - Enhanced metadata formatting"
    echo ""
    echo "ℹ️  Note: Zotero-MCP is added to Python path at runtime"
    echo "   Semantic search features are NOT installed (using RAGFlow instead)"
else
    echo ""
    echo "❌ Installation verification failed"
    exit 1
fi
