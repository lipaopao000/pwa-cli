# Zotero-MCP 集成方案

## 项目背景

**zotero-mcp** 是一个功能强大的 Model Context Protocol (MCP) 服务器，提供了与 Zotero 文献管理工具的深度集成。它的核心功能包括语义搜索、PDF 注释提取、Better BibTeX 支持等。

**pwa-cli** 是一个现代化的学术论文写作辅助 CLI 工具，已经具备基础的 Zotero 集成和 LLM 功能。

## 集成目标

将 zotero-mcp 的核心功能整合到 pwa-cli 中，增强其文献管理和搜索能力，同时保持 pwa-cli 的 CLI 工具定位。

## 功能对比分析

### zotero-mcp 核心功能

| 功能 | 描述 | 技术栈 |
|------|------|--------|
| 语义搜索 | 基于向量嵌入的相似度搜索 | ChromaDB + sentence-transformers |
| 本地/远程 API | 支持本地 Zotero 和 Web API | pyzotero |
| PDF 注释提取 | 直接从 PDF 提取注释和高亮 | markitdown + pdfannots |
| Better BibTeX | BibTeX 导出和管理 | Better BibTeX plugin |
| 全文搜索 | 元数据和全文内容搜索 | SQLite + 全文提取 |
| MCP 服务器 | 作为 MCP 服务器运行 | fastmcp |

### pwa-cli 现有功能

| 功能 | 描述 | 技术栈 |
|------|------|--------|
| Zotero 集成 | 基础的文献检索和管理 | pyzotero |
| LLM 集成 | 多 LLM 支持（OpenAI 等） | langchain + openai |
| 参考文献管理 | 文献引用和格式化 | bibtexparser |
| Session 管理 | 会话和上下文管理 | 自定义实现 |
| Agent 系统 | 学术写作 Agent | langchain + langgraph |

## 集成方案

### 方案 A: 完全集成（推荐）

**描述**: 将 zotero-mcp 的核心功能模块直接集成到 pwa-cli 中，作为增强的 Zotero 客户端。

**优点**:
- 功能完全可控，可以深度定制
- 不依赖外部 MCP 服务器
- 统一的配置和错误处理
- 更好的性能（无需跨进程通信）

**缺点**:
- 需要添加较多依赖（ChromaDB、sentence-transformers 等）
- 增加项目复杂度
- 需要维护更多代码

**实施步骤**:
1. 添加依赖到 pyproject.toml
2. 创建 `pwa/clients/zotero_enhanced.py` - 增强的 Zotero 客户端
3. 创建 `pwa/search/semantic.py` - 语义搜索模块
4. 创建 `pwa/pdf/annotations.py` - PDF 注释提取
5. 创建新的 CLI 命令支持这些功能
6. 编写测试和文档

### 方案 B: MCP 客户端集成

**描述**: pwa-cli 作为 MCP 客户端，通过 MCP 协议调用 zotero-mcp 服务器。

**优点**:
- 依赖较少，项目更轻量
- 可以利用 zotero-mcp 的所有功能
- 解耦，易于维护

**缺点**:
- 需要用户单独安装和配置 zotero-mcp
- 跨进程通信有性能开销
- 依赖外部服务的可用性

**实施步骤**:
1. 添加 MCP 客户端依赖
2. 创建 `pwa/clients/mcp_client.py` - MCP 客户端封装
3. 创建命令调用 MCP 工具
4. 编写集成测试

### 方案 C: 混合方案（最佳平衡）

**描述**: 核心功能完全集成，可选功能通过 MCP 调用。

**核心集成功能**:
- 增强的 Zotero 客户端（本地/远程 API）
- 语义搜索（ChromaDB + 向量嵌入）
- PDF 注释提取

**可选 MCP 功能**:
- Better BibTeX 高级功能
- 其他扩展功能

**优点**:
- 平衡了功能完整性和项目复杂度
- 核心功能可控，扩展功能灵活
- 用户可以选择是否启用 MCP 功能

## 推荐方案: 方案 A（完全集成）

考虑到 pwa-cli 的定位是一个独立的 CLI 工具，建议采用完全集成方案，原因如下：

1. **用户体验**: 用户只需安装一个工具，无需配置多个服务
2. **功能一致性**: 所有功能使用统一的配置和错误处理
3. **性能**: 无跨进程通信开销
4. **可维护性**: 虽然代码量增加，但功能完全可控

## 详细实施计划

### 阶段 1: 依赖和基础设施

1. **更新 pyproject.toml**
   ```toml
   dependencies = [
       # 现有依赖...
       "chromadb>=0.4.0",
       "sentence-transformers>=2.2.0",
       "markitdown[pdf]",
   ]
   ```

2. **创建配置模型**
   - 扩展 `pwa/config_models.py` 添加语义搜索配置
   - 添加嵌入模型配置（default/openai/gemini）

### 阶段 2: 增强 Zotero 客户端

1. **创建 `pwa/clients/zotero_enhanced.py`**
   - 继承或包装现有 Zotero 客户端
   - 添加本地 API 支持
   - 添加全文提取功能
   - 添加 PDF 注释提取

2. **重构现有 Zotero 集成**
   - 迁移到新的增强客户端
   - 保持向后兼容

### 阶段 3: 语义搜索

1. **创建 `pwa/search/semantic.py`**
   - ChromaDB 集成
   - 向量嵌入生成
   - 相似度搜索
   - 数据库更新和管理

2. **创建 `pwa/search/embeddings.py`**
   - 多种嵌入模型支持
   - 模型管理和缓存

### 阶段 4: PDF 处理

1. **创建 `pwa/pdf/annotations.py`**
   - PDF 注释提取
   - 高亮和评论处理
   - 图片注释支持

2. **创建 `pwa/pdf/fulltext.py`**
   - 全文提取
   - 文本清理和格式化

### 阶段 5: CLI 命令

1. **新增命令**
   ```
   pwa semantic-search "query"           # 语义搜索
   pwa update-search-db                  # 更新搜索数据库
   pwa extract-annotations <item-key>    # 提取 PDF 注释
   pwa search-annotations "query"        # 搜索注释
   ```

2. **增强现有命令**
   - `pwa search` 添加 `--semantic` 选项
   - `pwa references` 添加语义搜索支持

### 阶段 6: 测试和文档

1. **单元测试**
   - 语义搜索测试
   - PDF 处理测试
   - 集成测试

2. **文档更新**
   - README 添加新功能说明
   - 使用示例和最佳实践
   - 配置指南

## 技术细节

### 语义搜索架构

```
┌─────────────────────────────────────────────────────────┐
│                     pwa-cli                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │  CLI Commands    │─────▶│  Semantic Search │        │
│  └──────────────────┘      └──────────────────┘        │
│                                     │                    │
│                                     ▼                    │
│                            ┌──────────────────┐         │
│                            │  ChromaDB Client │         │
│                            └──────────────────┘         │
│                                     │                    │
│                                     ▼                    │
│                            ┌──────────────────┐         │
│                            │  Embedding Model │         │
│                            │  - default       │         │
│                            │  - openai        │         │
│                            │  - gemini        │         │
│                            └──────────────────┘         │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │  Zotero Enhanced │◀────▶│  Local/Remote API│        │
│  └──────────────────┘      └──────────────────┘        │
│           │                                              │
│           ▼                                              │
│  ┌──────────────────┐                                   │
│  │  PDF Processor   │                                   │
│  │  - Annotations   │                                   │
│  │  - Full Text     │                                   │
│  └──────────────────┘                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 数据流

1. **索引构建**:
   ```
   Zotero Items → Extract Metadata/Fulltext → Generate Embeddings → Store in ChromaDB
   ```

2. **语义搜索**:
   ```
   User Query → Generate Query Embedding → ChromaDB Similarity Search → Return Ranked Results
   ```

3. **PDF 注释**:
   ```
   PDF File → Extract Annotations → Parse and Format → Return Structured Data
   ```

## 配置示例

```yaml
# configs/zotero_enhanced.yaml
zotero:
  # 基础配置
  api_key: "your_api_key"
  user_id: "your_user_id"
  library_type: "user"
  
  # 本地 API（可选）
  local_mode: true
  local_db_path: "/path/to/zotero.sqlite"

# configs/semantic_search.yaml
semantic_search:
  # 嵌入模型
  embedding_model: "default"  # default, openai, gemini
  
  # OpenAI 配置（如果使用 openai）
  openai:
    api_key: "your_openai_key"
    model: "text-embedding-3-small"
    base_url: "https://api.openai.com/v1"  # 可选
  
  # Gemini 配置（如果使用 gemini）
  gemini:
    api_key: "your_gemini_key"
    model: "models/text-embedding-004"
  
  # 更新配置
  update_config:
    auto_update: false
    update_frequency: "manual"  # manual, startup, daily, custom
    update_days: 7  # 如果是 custom
  
  # ChromaDB 配置
  chroma:
    persist_directory: "~/.pwa/chroma_db"
    collection_name: "zotero_items"
```

## 迁移路径

为了保持向后兼容，现有功能将继续工作：

1. **现有 Zotero 客户端**: 保留为 `pwa/clients/zotero_client.py`
2. **新增强客户端**: `pwa/clients/zotero_enhanced.py`
3. **配置**: 用户可以选择使用哪个客户端
4. **命令**: 新命令使用增强客户端，旧命令保持不变

## 时间估算

| 阶段 | 工作量 | 时间估算 |
|------|--------|----------|
| 依赖和基础设施 | 小 | 1-2 小时 |
| 增强 Zotero 客户端 | 中 | 3-4 小时 |
| 语义搜索 | 大 | 4-6 小时 |
| PDF 处理 | 中 | 2-3 小时 |
| CLI 命令 | 中 | 2-3 小时 |
| 测试和文档 | 中 | 2-3 小时 |
| **总计** | | **14-21 小时** |

## 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 依赖冲突 | 高 | 仔细测试依赖兼容性 |
| 性能问题 | 中 | 优化嵌入生成和搜索 |
| 存储空间 | 中 | 提供清理和压缩选项 |
| 学习曲线 | 低 | 提供详细文档和示例 |

## 下一步

1. ✅ 完成集成方案设计
2. ⏳ 实施阶段 1: 依赖和基础设施
3. ⏳ 实施阶段 2: 增强 Zotero 客户端
4. ⏳ 实施阶段 3: 语义搜索
5. ⏳ 实施阶段 4: PDF 处理
6. ⏳ 实施阶段 5: CLI 命令
7. ⏳ 实施阶段 6: 测试和文档
