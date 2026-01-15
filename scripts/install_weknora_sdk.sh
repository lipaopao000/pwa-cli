#!/bin/bash
# Install WeKnora SDK (Auto-generated from OpenAPI)
# This script ensures PWA-CLI uses the latest WeKnora SDK

set -e

echo "=== Installing WeKnora SDK ==="

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
# WeKnora 仓库位置 (类似于 .ragflow)
WEKNORA_REPO_DIR="$PROJECT_ROOT/.weknora"
# 自动生成的 Python SDK 源码输出位置 (符合 pwa-cli 结构)
SDK_OUTPUT_DIR="$PROJECT_ROOT/pwa/clients/weknora_sdk"

# 1. 确保 WeKnora 仓库存在并同步最新
if [ -d "$WEKNORA_REPO_DIR" ]; then
    echo "✅ WeKnora repository already exists at: $WEKNORA_REPO_DIR"
    # 如果是 git 仓库则尝试更新
    if [ -d "$WEKNORA_REPO_DIR/.git" ]; then
        echo "📥 Pulling latest changes..."
        cd "$WEKNORA_REPO_DIR"
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "   (Pull failed, using existing version)"
    fi
else
    echo "📥 Cloning WeKnora repository..."
    # 注意：这里我们尝试从相对路径克隆或从 GitHub 克隆
    # 既然之前是在根目录，我们先尝试从根目录同步过来，或者直接 clone
    ORIGIN_REPO="$(dirname "$PROJECT_ROOT")/WeKnora"
    if [ -d "$ORIGIN_REPO" ]; then
        cp -R "$ORIGIN_REPO" "$WEKNORA_REPO_DIR"
        echo "✅ Copied WeKnora from $ORIGIN_REPO to $WEKNORA_REPO_DIR"
    else
        echo "🌐 Cloning from remote..."
        git clone --depth 1 https://github.com/tencent/WeKnora.git "$WEKNORA_REPO_DIR"
    fi
fi

# 2. 检查 Swagger 文件
SWAGGER_FILE="$WEKNORA_REPO_DIR/docs/swagger.json"
if [ ! -f "$SWAGGER_FILE" ]; then
    echo "❌ Swagger file not found at: $SWAGGER_FILE"
    exit 1
fi

# 3. 使用 OpenAPI Generator 生成 SDK
echo "🏗️  Generating Python SDK from $SWAGGER_FILE..."
if command -v openapi-generator-cli >/dev/null 2>&1; then
    GENERATOR="openapi-generator-cli"
else
    GENERATOR="npx @openapitools/openapi-generator-cli"
fi

# 我们只生成源码部分，并指定 package_name
$GENERATOR generate \
    -i "$SWAGGER_FILE" \
    -g python \
    -o "$SDK_OUTPUT_DIR" \
    --package-name "weknora" \
    --additional-properties=packageName="weknora",projectName="weknora-sdk",licenseName="Apache-2.0" \
    --skip-validate-spec

# 4. 修复许可格式问题 (针对 pyproject.toml)
if grep -q "license = \"NoLicense\"" "$SDK_OUTPUT_DIR/pyproject.toml"; then
    echo "🔧 Fixing license format in pyproject.toml..."
    sed -i '' 's/license = "NoLicense"/license = {text = "NoLicense"}/' "$SDK_OUTPUT_DIR/pyproject.toml" 2>/dev/null || \
    sed -i 's/license = "NoLicense"/license = {text = "NoLicense"}/' "$SDK_OUTPUT_DIR/pyproject.toml"
fi

# 5. 安装 SDK 到可编辑模式
echo "📦 Installing WeKnora SDK in editable mode..."
cd "$SDK_OUTPUT_DIR"
pip install -e .

# 6. 验证安装
echo ""
echo "🧪 Verifying installation..."
python3 << EOF
import sys
import os

# 确保生成的 sdk 路径在 sys.path 中
sdk_path = "$SDK_OUTPUT_DIR"
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

try:
    import weknora
    from weknora.api.knowledge_api import KnowledgeApi
    print("✅ weknora sdk imported successfully")
    print(f"   Location: {weknora.__file__}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 WeKnora SDK installation completed successfully!"
    echo "📍 Location: $SDK_OUTPUT_DIR"
else
    echo "❌ Verification failed"
    exit 1
fi
