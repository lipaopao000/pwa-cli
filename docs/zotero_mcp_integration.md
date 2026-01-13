# Zotero-MCP 集成文档

## 概述

PWA-CLI 现已集成 [zotero-mcp](https://github.com/54yyyu/zotero-mcp) 的核心功能，提供增强的 Zotero 文献管理能力。

## 集成方式

采用类似 `markitdown` 和 `ragflow` 的方式：
- 通过 `scripts/install_zotero_mcp.sh` 脚本下载和安装
- 源代码存放在 `.zotero-mcp/` 目录
- 通过适配器层 (`pwa/clients/zotero_mcp_adapter.py`) 提供接口
- 不安装 MCP 服务器和语义搜索功能（使用 RAGFlow 代替）

## 安装

```bash
# 运行安装脚本
bash scripts/install_zotero_mcp.sh
```

脚本会自动：
1. 克隆 zotero-mcp 仓库到 `.zotero-mcp/`
2. 安装核心依赖（pyzotero, markitdown, python-dotenv 等）
3. 验证核心模块可以正常导入

## 功能特性

### 1. 本地 Zotero 连接

无需 API key，直接连接本地 Zotero 应用：

```python
from pwa.clients import create_zotero_mcp_client

# 创建本地客户端
client = create_zotero_mcp_client(local=True)

# 搜索文献
items = client.search_items(query="machine learning", limit=10)

# 获取单个文献
item = client.get_item("ITEM_KEY")

# 格式化元数据
markdown = client.format_item_metadata(item, include_abstract=True)
```

### 2. PDF 注释提取

直接从 PDF 文件提取注释和高亮：

```python
# 提取 PDF 注释
annotations = client.extract_pdf_annotations(
    item_key="ITEM_KEY",
    include_images=False
)

# 注释数据结构
# {
#     "item_key": "ITEM_KEY",
#     "annotations": [
#         {
#             "type": "highlight",
#             "text": "highlighted text",
#             "comment": "user comment",
#             "page": 1
#         }
#     ]
# }
```

### 3. Better BibTeX 集成

导出高质量的 BibTeX 引用：

```python
# 导出 BibTeX
bibtex = client.get_better_bibtex_export(
    item_keys=["KEY1", "KEY2"],
    translator="biblatex"  # 或 "bibtex"
)
```

### 4. 增强的元数据格式化

```python
# 格式化作者列表
creators = [
    {"creatorType": "author", "firstName": "John", "lastName": "Doe"},
    {"creatorType": "author", "firstName": "Jane", "lastName": "Smith"}
]
formatted = client.format_creators(creators)
# 输出: "John Doe, Jane Smith"
```

### 5. 集合和标签管理

```python
# 获取所有集合
collections = client.get_collections()

# 获取所有标签
tags = client.get_tags()

# 获取文献的附件
attachments = client.get_item_attachments("ITEM_KEY")
```

## 配置

### 本地模式（推荐）

使用本地 Zotero 应用，无需配置：

```python
client = create_zotero_mcp_client(local=True)
```

**要求**:
- 安装 Zotero 7+
- 启用本地 API（在 Zotero 首选项中）

### 远程 API 模式

使用 Zotero Web API：

```python
client = create_zotero_mcp_client(
    local=False,
    library_id="YOUR_LIBRARY_ID",
    api_key="YOUR_API_KEY",
    library_type="user"  # 或 "group"
)
```

**获取 API 密钥**:
1. 访问 https://www.zotero.org/settings/keys
2. 创建新的 API 密钥
3. 记录 Library ID 和 API Key

## 使用示例

### 示例 1: 搜索并格式化文献

```python
from pwa.clients import create_zotero_mcp_client

# 创建客户端
client = create_zotero_mcp_client(local=True)

# 搜索文献
items = client.search_items(
    query="deep learning",
    item_type="journalArticle",
    limit=5
)

# 格式化每个文献
for item in items:
    markdown = client.format_item_metadata(item)
    print(markdown)
    print("-" * 80)
```

### 示例 2: 提取 PDF 注释

```python
# 搜索特定文献
items = client.search_items(query="neural networks", limit=1)

if items:
    item_key = items[0]["data"]["key"]
    
    # 提取注释
    annotations = client.extract_pdf_annotations(item_key)
    
    # 打印注释
    for annot in annotations.get("annotations", []):
        print(f"Type: {annot['type']}")
        print(f"Text: {annot['text']}")
        if annot.get('comment'):
            print(f"Comment: {annot['comment']}")
        print()
```

### 示例 3: 导出 BibTeX

```python
# 搜索文献
items = client.search_items(tag="important", limit=10)

# 提取 item keys
item_keys = [item["data"]["key"] for item in items]

# 导出 BibTeX
bibtex = client.get_better_bibtex_export(item_keys, translator="biblatex")

# 保存到文件
with open("references.bib", "w") as f:
    f.write(bibtex)
```

### 示例 4: 浏览集合

```python
# 获取所有集合
collections = client.get_collections()

for collection in collections:
    name = collection["data"]["name"]
    key = collection["data"]["key"]
    print(f"Collection: {name} ({key})")
    
    # 获取集合中的文献
    items = client.search_items(collection=key, limit=5)
    print(f"  Items: {len(items)}")
```

## API 参考

### ZoteroMCPClient

#### 初始化

```python
ZoteroMCPClient(
    library_id: Optional[str] = None,
    library_type: str = "user",
    api_key: Optional[str] = None,
    local: bool = True
)
```

#### 方法

- `search_items(query, item_type, tag, limit)` - 搜索文献
- `get_item(item_key)` - 获取单个文献
- `format_item_metadata(item, include_abstract)` - 格式化元数据
- `get_item_attachments(item_key)` - 获取附件
- `get_collections()` - 获取集合列表
- `get_tags()` - 获取标签列表
- `extract_pdf_annotations(item_key, include_images)` - 提取 PDF 注释
- `get_better_bibtex_export(item_keys, translator)` - 导出 BibTeX
- `format_creators(creators)` - 格式化作者列表

## 与现有 ZoteroClient 的区别

| 特性 | ZoteroClient | ZoteroMCPClient |
|------|--------------|-----------------|
| 本地 API | ❌ | ✅ |
| 远程 API | ✅ | ✅ |
| PDF 注释提取 | ❌ | ✅ |
| Better BibTeX | ❌ | ✅ |
| 元数据格式化 | 基础 | 增强 |
| 全文提取 | ❌ | ✅ (通过 markitdown) |

## 依赖

核心依赖（自动安装）：
- `pyzotero>=1.5.0` - Zotero API 客户端
- `markitdown` - PDF 和文档处理
- `python-dotenv>=1.0.0` - 环境变量管理
- `pydantic>=2.0.0` - 数据验证
- `requests>=2.28.0` - HTTP 请求

**不包含的依赖**（不需要）：
- `fastmcp` - MCP 服务器（我们不使用）
- `chromadb` - 向量数据库（使用 RAGFlow 代替）
- `sentence-transformers` - 嵌入模型（使用 RAGFlow 代替）

## 故障排除

### 导入错误

如果遇到导入错误：

```bash
# 重新运行安装脚本
bash scripts/install_zotero_mcp.sh
```

### 本地连接失败

确保：
1. Zotero 应用正在运行
2. 本地 API 已启用（Zotero → 首选项 → 高级 → 允许其他应用访问）
3. 防火墙未阻止本地连接

### PDF 注释提取失败

可能原因：
1. PDF 文件不存在或无法访问
2. PDF 没有注释
3. 需要安装 Better BibTeX 插件（推荐）

## 更新

更新到最新版本：

```bash
# 重新运行安装脚本
bash scripts/install_zotero_mcp.sh
```

脚本会自动拉取最新代码。

## 贡献

zotero-mcp 是一个独立的开源项目。如果发现问题或想贡献：
- 项目地址: https://github.com/54yyyu/zotero-mcp
- 文档: https://stevenyuyy.us/zotero-mcp/

## 许可

zotero-mcp 使用 MIT 许可证。
