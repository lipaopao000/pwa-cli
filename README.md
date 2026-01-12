# PWA-CLI - Paper Writing Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

一个现代化的命令行工具，用于辅助学术论文写作，提供参考文献管理、引用处理、全文获取、科学陈述验证等功能。

## ✨ 特性

- 🎯 **交互式菜单** - 友好的用户界面，易于使用
- 📚 **参考文献管理** - 自动匹配 Markdown 文档中的参考文献与 Zotero/BibTeX 库
- 🔗 **引用处理** - 将上标引用转换为 Pandoc BibTeX 格式
- 📄 **全文获取** - 使用 Mineru API 批量获取论文全文 Markdown
- ✅ **陈述验证** - 使用 RAGFlow 和 PubMed 验证科学陈述的准确性
- 🔧 **高扩展性** - 插件式架构，方便添加新功能
- 📦 **配置管理** - 集中化的配置管理系统
- 🧪 **完整测试** - 包含单元测试和集成测试

## 📦 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/lipaopao000/pwa-cli.git
cd pwa-cli

# 安装依赖
pip install -r requirements.txt

# 安装 PWA
pip install -e .

# 安装 RAGFlow SDK (用于陈述验证功能)
./scripts/install_ragflow_sdk.sh
```

### 使用 pip 安装（即将支持）

```bash
pip install pwa-cli
```

## 🚀 快速开始

### 交互式模式

直接运行 `pwa` 命令进入交互式菜单：

```bash
pwa
```

### 命令行模式（开发中）

```bash
# 匹配参考文献
pwa references match paper.md

# 替换引用格式
pwa citations replace paper.md

# 下载全文
pwa fulltext download references.bib

# 验证科学陈述
pwa verify statements paper.md
```

## 📖 功能说明

### 1. 参考文献管理

从 Markdown 文档的 References 部分提取参考文献，并与 Zotero 库或 BibTeX 文件进行智能匹配。

**功能特点：**
- 支持多种参考文献格式（`[1]`, `1.`, `1)`, `(1)`）
- 使用 Jaccard 相似度算法进行标题匹配
- 支持 DOI 精确匹配
- 输出完美匹配和模糊匹配结果

### 2. 引用处理

将 Markdown 文档中的上标引用（如 `^1^`）替换为 Pandoc BibTeX 引用格式（如 `[@key]`）。

**功能特点：**
- 支持单个引用：`^1^` → `[@key1]`
- 支持多个引用：`^1,2,3^` → `[@key1; @key2; @key3]`
- 支持范围引用：`^1-5^` → `[@key1; @key2; @key3; @key4; @key5]`
- 只处理 Abstract 之后的内容

### 3. 全文获取

使用 Mineru OCR API 批量获取论文 PDF 的全文 Markdown 版本。

**功能特点：**
- 支持并发下载，提高效率
- 自动重试失败任务
- 支持断点续传
- 输出高质量的 Markdown 格式

### 4. 陈述验证

验证论文中的科学陈述是否有充分的文献支持。

**功能特点：**
- 使用 RAGFlow 知识库进行语义检索
- 集成 PubMed 数据库进行医学文献验证
- 支持多线程并发验证
- 生成详细的验证报告

## ⚙️ 配置

PWA 使用 YAML 格式的配置文件，支持多级配置：

1. **项目级**：`./config-and-cache/`
2. **用户级**：`~/.config/pwa/`
3. **系统级**：`/etc/pwa/`

优先级：项目级 > 用户级 > 系统级

### 配置文件

- `llm_config.yaml` - LLM 提供商配置（OpenAI, DeepSeek, Moonshot 等）
- `zotero_config.yaml` - Zotero API 配置
- `OCR_API.yaml` - Mineru OCR API 配置
- `RAGFlow.yaml` - RAGFlow 知识库配置

### 示例：LLM 配置

```yaml
active_provider: "deepseek"

providers:
  deepseek:
    api_key: "sk-..."
    base_url: "https://api.deepseek.com"
    model: "deepseek-reasoner"
    temperature: 0.0
```

## 🏗️ 架构

PWA 采用模块化、插件式架构：

```
pwa-cli/
├── pwa/
│   ├── cli.py              # CLI 主程序
│   ├── config.py           # 配置管理
│   ├── core/               # 核心功能模块
│   ├── commands/           # 命令模块（插件式）
│   ├── clients/            # 外部服务客户端
│   └── ui/                 # 用户界面组件
├── tests/                  # 测试
├── configs/                # 默认配置
└── docs/                   # 文档
```

详细架构说明请参见 [ARCHITECTURE.md](ARCHITECTURE.md)

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_commands/

# 生成覆盖率报告
pytest --cov=pwa --cov-report=html
```

## 📝 开发

### 添加新命令

1. 在 `pwa/commands/` 创建新模块
2. 继承 `BaseCommand` 类
3. 实现 `execute()` 方法
4. 在 CLI 菜单中注册

示例：

```python
from pwa.commands.base import BaseCommand

class MyCommand(BaseCommand):
    name = "mycommand"
    description = "我的命令"
    
    def execute(self, **kwargs):
        # 实现命令逻辑
        pass
```

### 代码风格

使用 Black 格式化代码：

```bash
black pwa/
```

使用 Flake8 检查代码：

```bash
flake8 pwa/
```

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Zotero](https://www.zotero.org/) - 参考文献管理
- [Mineru](https://mineru.net/) - OCR 服务
- [RAGFlow](https://ragflow.io/) - 知识库检索
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/) - 医学文献数据库

## 📮 联系

- 作者：lipaopao000
- 仓库：https://github.com/lipaopao000/pwa-cli
- 问题反馈：https://github.com/lipaopao000/pwa-cli/issues

---

⭐ 如果这个项目对你有帮助，请给个 Star！
