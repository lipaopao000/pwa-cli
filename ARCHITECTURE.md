# PWA-CLI 架构设计文档

## 项目概述

Paper Writing Assistant CLI (pwa-cli) 是一个现代化的命令行工具，旨在帮助研究人员和学术写作者管理参考文献、验证科学陈述、获取全文等学术写作相关任务。

## 设计原则

1. **模块化**: 每个功能独立封装，易于维护和扩展
2. **可扩展性**: 插件式架构，方便添加新功能
3. **用户友好**: 交互式菜单和清晰的命令行界面
4. **配置驱动**: 集中化配置管理
5. **测试覆盖**: 完整的单元测试和集成测试

## 目录结构

```
pwa-cli/
├── pwa/                          # 主包目录
│   ├── __init__.py              # 包初始化
│   ├── __main__.py              # 入口点 (python -m pwa)
│   ├── cli.py                   # CLI 主程序和交互式菜单
│   ├── config.py                # 配置管理
│   ├── version.py               # 版本信息
│   │
│   ├── core/                    # 核心功能模块
│   │   ├── __init__.py
│   │   ├── base_agent.py       # 基础代理类
│   │   ├── configuration.py    # 配置管理
│   │   ├── prompts.py          # LLM 提示词
│   │   ├── schemas.py          # 数据模式
│   │   ├── state.py            # 状态管理
│   │   └── utils.py            # 工具函数
│   │
│   ├── commands/                # 命令模块（插件式）
│   │   ├── __init__.py
│   │   ├── base.py             # 命令基类
│   │   ├── references.py       # 参考文献管理
│   │   ├── citations.py        # 引用处理
│   │   ├── fulltext.py         # 全文获取
│   │   ├── verify.py           # 陈述验证
│   │   └── workflow.py         # 工作流管理
│   │
│   ├── clients/                 # 外部服务客户端
│   │   ├── __init__.py
│   │   ├── zotero.py           # Zotero API
│   │   ├── pubmed.py           # PubMed API
│   │   ├── ragflow.py          # RAGFlow API
│   │   └── mineru.py           # Mineru OCR API
│   │
│   └── ui/                      # 用户界面
│       ├── __init__.py
│       ├── menu.py             # 交互式菜单
│       ├── progress.py         # 进度显示
│       └── colors.py           # 颜色和样式
│
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_commands/          # 命令测试
│   ├── test_clients/           # 客户端测试
│   ├── test_core/              # 核心功能测试
│   └── fixtures/               # 测试数据
│
├── configs/                     # 默认配置文件
│   ├── llm_config.yaml
│   ├── zotero_config.yaml
│   ├── ocr_api.yaml
│   └── ragflow.yaml
│
├── docs/                        # 文档
│   ├── user_guide.md
│   ├── api_reference.md
│   └── development.md
│
├── scripts/                     # 辅助脚本
│   ├── install.sh
│   └── test.sh
│
├── setup.py                     # 安装配置
├── pyproject.toml              # 项目元数据
├── requirements.txt            # 依赖列表
├── README.md                   # 项目说明
├── CHANGELOG.md                # 变更日志
└── LICENSE                     # 许可证
```

## 核心架构

### 1. CLI 入口层

**文件**: `pwa/cli.py`

- 使用 `click` 或 `typer` 框架构建 CLI
- 提供交互式菜单和命令行参数两种模式
- 统一的错误处理和日志记录

### 2. 命令层（插件式）

**目录**: `pwa/commands/`

每个命令模块继承自 `BaseCommand`，实现标准接口：

```python
class BaseCommand:
    def __init__(self, config):
        self.config = config
    
    def execute(self, **kwargs):
        """执行命令的主逻辑"""
        raise NotImplementedError
    
    def validate(self, **kwargs):
        """验证输入参数"""
        pass
    
    def get_help(self):
        """返回帮助信息"""
        pass
```

### 3. 核心功能层

**目录**: `pwa/core/`

- 从原 `core/` 目录迁移，保持功能完整性
- 提供通用工具函数和基础类
- 独立于命令层，可被多个命令复用

### 4. 客户端层

**目录**: `pwa/clients/`

- 封装所有外部 API 调用
- 统一的错误处理和重试机制
- 支持异步操作

### 5. 配置管理

**文件**: `pwa/config.py`

```python
class ConfigManager:
    def __init__(self, config_dir=None):
        self.config_dir = config_dir or self.get_default_config_dir()
    
    def load_config(self, name):
        """加载指定配置文件"""
        pass
    
    def save_config(self, name, data):
        """保存配置"""
        pass
    
    def get_config_path(self, name):
        """获取配置文件路径"""
        pass
```

## 交互式菜单设计

### 主菜单

```
╔════════════════════════════════════════════════════════╗
║     Paper Writing Assistant (PWA) - v1.0.0            ║
╠════════════════════════════════════════════════════════╣
║  1. 参考文献管理                                       ║
║  2. 引用处理                                          ║
║  3. 全文获取                                          ║
║  4. 陈述验证                                          ║
║  5. 工作流管理                                        ║
║  6. 配置管理                                          ║
║  7. 帮助与文档                                        ║
║  0. 退出                                              ║
╚════════════════════════════════════════════════════════╝
请选择功能 [0-7]:
```

### 子菜单示例：参考文献管理

```
╔════════════════════════════════════════════════════════╗
║     参考文献管理                                       ║
╠════════════════════════════════════════════════════════╣
║  1. 匹配参考文献                                       ║
║  2. 查看匹配结果                                       ║
║  3. 导出参考文献                                       ║
║  4. 同步 Zotero 库                                     ║
║  0. 返回主菜单                                         ║
╚════════════════════════════════════════════════════════╝
请选择操作 [0-4]:
```

## 命令行接口设计

### 基本命令结构

```bash
# 交互式模式
pwa

# 直接执行命令
pwa references match <markdown_file> [options]
pwa citations replace <markdown_file> [options]
pwa fulltext download <references_file> [options]
pwa verify statements <markdown_file> [options]

# 工作流模式
pwa workflow run <workflow_name> <markdown_file>

# 配置管理
pwa config list
pwa config set <key> <value>
pwa config get <key>

# 帮助
pwa --help
pwa references --help
```

### 全局选项

```bash
--config-dir PATH    # 配置目录
--log-level LEVEL    # 日志级别
--quiet              # 静默模式
--verbose            # 详细输出
--version            # 版本信息
```

## 功能模块映射

| 原脚本 | 新命令 | 模块路径 |
|--------|--------|----------|
| 01-References-Match.py | `pwa references match` | `pwa.commands.references.MatchCommand` |
| 02-Citation-Replace.py | `pwa citations replace` | `pwa.commands.citations.ReplaceCommand` |
| 03-Get-FullText-MD.py | `pwa fulltext download` | `pwa.commands.fulltext.DownloadCommand` |
| 05-Scientific_Statement_Verifier.py | `pwa verify statements` | `pwa.commands.verify.VerifyCommand` |

## 扩展机制

### 插件系统

支持通过插件扩展功能：

```python
# pwa/plugins/base.py
class Plugin:
    name = "plugin_name"
    version = "1.0.0"
    
    def register(self, app):
        """注册插件到应用"""
        pass
    
    def get_commands(self):
        """返回插件提供的命令"""
        return []
```

### 钩子系统

支持在关键点注入自定义逻辑：

```python
# 支持的钩子
- before_command_execute
- after_command_execute
- on_error
- on_config_load
```

## 测试策略

### 单元测试

- 每个模块独立测试
- 使用 `pytest` 框架
- Mock 外部 API 调用

### 集成测试

- 测试完整工作流
- 使用测试数据集
- 验证输出正确性

### 测试脚本

```bash
# 运行所有测试
./scripts/test.sh

# 运行特定模块测试
pytest tests/test_commands/test_references.py

# 生成覆盖率报告
pytest --cov=pwa --cov-report=html
```

## 配置管理

### 配置文件位置

1. 系统级: `/etc/pwa/`
2. 用户级: `~/.config/pwa/`
3. 项目级: `./config-and-cache/`

优先级: 项目级 > 用户级 > 系统级

### 配置文件格式

统一使用 YAML 格式，支持环境变量替换：

```yaml
llm:
  provider: ${LLM_PROVIDER:-deepseek}
  api_key: ${LLM_API_KEY}
```

## 依赖管理

### 核心依赖

- `click` / `typer`: CLI 框架
- `rich`: 终端美化
- `pyyaml`: YAML 解析
- `requests`: HTTP 客户端
- `bibtexparser`: BibTeX 解析

### 可选依赖

- `aiohttp`: 异步 HTTP
- `tqdm`: 进度条
- `pytest`: 测试框架

## 版本管理

使用语义化版本 (Semantic Versioning):

- 主版本号: 不兼容的 API 变更
- 次版本号: 向后兼容的功能新增
- 修订号: 向后兼容的问题修正

## 发布流程

1. 更新 `CHANGELOG.md`
2. 更新版本号 (`pwa/version.py`)
3. 运行测试套件
4. 构建分发包
5. 推送到 GitHub
6. 创建 Release
7. 发布到 PyPI (可选)

## 文档

### 用户文档

- 安装指南
- 快速开始
- 命令参考
- 配置说明
- 常见问题

### 开发者文档

- 架构说明
- API 参考
- 插件开发
- 贡献指南

## 后续扩展方向

1. **Web 界面**: 提供基于 Web 的图形界面
2. **云同步**: 支持配置和数据云同步
3. **协作功能**: 支持团队协作
4. **AI 增强**: 更多 AI 辅助功能
5. **多语言支持**: 国际化和本地化
