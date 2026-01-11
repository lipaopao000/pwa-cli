# PWA-CLI 用户指南

## 目录

1. [安装](#安装)
2. [快速开始](#快速开始)
3. [功能详解](#功能详解)
4. [配置说明](#配置说明)
5. [常见问题](#常见问题)

## 安装

### 系统要求

PWA-CLI 需要 Python 3.8 或更高版本。推荐使用 Python 3.10 或 3.11。

### 从源码安装

克隆仓库并安装依赖：

```bash
git clone https://github.com/lipaopao000/pwa-cli.git
cd pwa-cli
pip install -r requirements.txt
pip install -e .
```

### 验证安装

运行以下命令验证安装是否成功：

```bash
pwa --version
```

应该输出类似 `PWA v1.0.0` 的版本信息。

## 快速开始

### 启动交互式菜单

直接运行 `pwa` 命令进入交互式菜单：

```bash
pwa
```

您将看到主菜单，可以通过数字键选择不同的功能。

### 第一次使用

首次使用时，建议先配置必要的服务：

1. 选择 "6. 配置管理"
2. 配置 Zotero API（如果使用 Zotero）
3. 配置 LLM 服务（用于陈述验证）

## 功能详解

### 1. 参考文献管理

参考文献管理功能帮助您从 Markdown 文档中提取参考文献，并与 Zotero 库或 BibTeX 文件进行智能匹配。

#### 匹配参考文献

**操作步骤：**

1. 在主菜单选择 "1. 参考文献管理"
2. 选择 "1. 匹配参考文献"
3. 输入 Markdown 文件路径
4. 选择参考文献来源（Zotero API 或本地 BibTeX 文件）
5. 设置模糊匹配候选数量（默认 3）

**输入文件格式：**

Markdown 文件应包含 References 部分，支持以下格式：

```markdown
## References

[1] Smith J. "Paper title" Journal 2023;10:123-456.
[2] Jones A. Another paper. Nature. 2022;20:789-800.
```

**输出结果：**

匹配结果保存在 `config-and-cache/references_match.json`，包括：

- **完美匹配**：相似度 >= 0.90 的匹配
- **模糊匹配**：提供多个候选项供选择

**匹配方法：**

1. **DOI 匹配**：如果参考文献包含 DOI，优先使用 DOI 进行精确匹配
2. **标题匹配**：使用 Jaccard 相似度算法计算标题相似度
3. **长度加权**：考虑标题长度差异，避免短标题误匹配

### 2. 引用处理

引用处理功能将 Markdown 文档中的上标引用替换为 Pandoc BibTeX 引用格式。

#### 替换引用格式

**操作步骤：**

1. 在主菜单选择 "2. 引用处理"
2. 选择 "1. 替换引用格式"
3. 输入 Markdown 文件路径
4. 选择匹配结果文件（通常是步骤 1 的输出）
5. 指定输出文件路径

**支持的引用格式：**

| 输入格式 | 输出格式 | 说明 |
|---------|---------|------|
| `^1^` | `[@key1]` | 单个引用 |
| `^1,2,3^` | `[@key1; @key2; @key3]` | 多个引用 |
| `^1-5^` | `[@key1; @key2; @key3; @key4; @key5]` | 范围引用 |

**注意事项：**

- 只处理 Abstract 之后的内容
- 保持 Abstract 之前的内容不变
- 如果某个引用没有匹配结果，保持原格式不变

### 3. 全文获取（开发中）

使用 Mineru OCR API 批量下载论文 PDF 的全文 Markdown 版本。

**计划功能：**

- 并发下载，提高效率
- 自动重试失败任务
- 断点续传
- 输出高质量 Markdown 格式

### 4. 陈述验证（开发中）

验证论文中的科学陈述是否有充分的文献支持。

**计划功能：**

- 使用 RAGFlow 知识库进行语义检索
- 集成 PubMed 数据库验证
- 多线程并发验证
- 生成详细验证报告

### 5. 工作流管理（开发中）

支持运行完整的工作流，自动化多个步骤。

**计划工作流：**

- **完整工作流**：参考文献匹配 → 引用替换 → 全文获取 → 陈述验证
- **自定义工作流**：根据需要选择特定步骤

### 6. 配置管理

管理 PWA 的配置文件。

#### 查看配置列表

显示所有已配置的服务和配置文件路径。

#### 编辑配置

可以编辑以下配置：

- **LLM 配置**：配置 OpenAI、DeepSeek、Moonshot 等 LLM 服务
- **Zotero 配置**：配置 Zotero API 访问
- **RAGFlow 配置**：配置 RAGFlow 知识库
- **OCR API 配置**：配置 Mineru OCR 服务

## 配置说明

### 配置文件位置

PWA 支持多级配置，按优先级从高到低：

1. **项目级**：`./config-and-cache/`（当前目录）
2. **用户级**：`~/.config/pwa/`（用户主目录）
3. **系统级**：`/etc/pwa/`（系统级配置）

### LLM 配置

配置文件：`llm_config.yaml`

```yaml
active_provider: "deepseek"  # 当前使用的提供商

providers:
  deepseek:
    api_key: "sk-..."
    base_url: "https://api.deepseek.com"
    model: "deepseek-reasoner"
    temperature: 0.0
  
  openai:
    api_key: "sk-..."
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o-mini"
    temperature: 0.1
```

### Zotero 配置

配置文件：`zotero_config.yaml`

```yaml
user_id: "your_user_id"
api_key: "your_api_key"
library_type: "user"  # 或 "group"
collection_id: "optional_collection_id"
```

**获取 Zotero API Key：**

1. 访问 https://www.zotero.org/settings/keys
2. 创建新的 API Key
3. 复制 User ID 和 API Key

### RAGFlow 配置

配置文件：`RAGFlow.yaml`

```yaml
api_key: "your_ragflow_api_key"
base_url: "https://your-ragflow-instance.com"
dataset_id: "your_dataset_id"
```

### OCR API 配置

配置文件：`OCR_API.yaml`

```yaml
api_key: "your_mineru_api_key"
base_url: "https://mineru.net/api/v4"
model_version: "vlm"
```

## 常见问题

### Q: 如何更改配置文件位置？

A: 使用 `--config-dir` 参数指定自定义配置目录：

```bash
pwa --config-dir /path/to/config
```

### Q: 参考文献匹配失败怎么办？

A: 检查以下几点：

1. Markdown 文件是否包含 References 部分
2. 参考文献格式是否正确（支持 `[1]`, `1.`, `1)`, `(1)` 格式）
3. Zotero API 配置是否正确
4. 参考文献库是否为空

### Q: 引用替换后格式不对？

A: 确保：

1. 先运行参考文献匹配，生成匹配结果文件
2. 匹配结果文件包含足够的完美匹配
3. 原始引用格式正确（`^数字^` 格式）

### Q: 如何查看日志？

A: 日志文件保存在配置目录的 `logs/` 子目录中，每个命令有独立的日志文件。

### Q: 支持哪些参考文献格式？

A: 目前支持：

- BibTeX (.bib)
- CSL JSON (.json)
- Zotero API

### Q: 如何贡献代码？

A: 欢迎贡献！请参考 [CONTRIBUTING.md](../CONTRIBUTING.md)（待创建）。

## 获取帮助

- **GitHub Issues**: https://github.com/lipaopao000/pwa-cli/issues
- **文档**: https://github.com/lipaopao000/pwa-cli/docs
- **邮件**: lipaopao000@gmail.com

## 下一步

- 阅读 [架构文档](../ARCHITECTURE.md) 了解技术细节
- 查看 [API 参考](api_reference.md) 了解命令行接口
- 尝试运行测试：`./scripts/test.sh`
