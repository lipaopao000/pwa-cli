# PWA-CLI 目录重组计划

**日期**: 2026-01-11  
**目的**: 重新组织目录结构，使架构更清晰合理

---

## 📋 当前目录结构问题

### 问题 1: Agent 文件混在 core/ 中

**当前位置**: `pwa/core/`
- `base_agent.py` - Agent 基类
- `citation_agent.py` - 引用 Agent

**问题**: Agent 是独立的功能模块，不应该放在 core 中。

### 问题 2: Client 文件分散

**当前位置**:
- `pwa/core/pubmed_client.py` - PubMed 客户端
- `pwa/core/ragflow_client.py` - RAGFlow 客户端
- `pwa/core/zotero_client.py` - Zotero 客户端
- `pwa/clients/mineru.py` - Mineru 客户端

**问题**: Client 文件分散在 core 和 clients 两个目录中，不统一。

### 问题 3: Statement Verifier 相关文件

**当前位置**: `pwa/core/`
- `statement_verifier.py` - 陈述验证器
- `statement_verifier_utils.py` - 验证器工具
- `configuration.py` - 配置模式
- `state.py` - 状态定义
- `schemas.py` - Pydantic 模型
- `prompts.py` - LLM 提示词

**问题**: 这些文件是陈述验证功能的一部分，应该组织在一起。

---

## 🎯 新的目录结构

### 目标结构

```
pwa/
├── __init__.py
├── __main__.py
├── cli.py
├── config.py
├── version.py
│
├── agents/                    # 🆕 Agent 模块
│   ├── __init__.py
│   ├── base.py               # base_agent.py → base.py
│   └── citation.py           # citation_agent.py → citation.py
│
├── clients/                   # ✅ 统一所有客户端
│   ├── __init__.py
│   ├── mineru.py             # ✅ 已存在
│   ├── pubmed.py             # pubmed_client.py → pubmed.py
│   ├── ragflow.py            # ragflow_client.py → ragflow.py
│   └── zotero.py             # zotero_client.py → zotero.py
│
├── commands/                  # ✅ 命令模块
│   ├── __init__.py
│   ├── base.py
│   ├── citations.py
│   ├── fulltext.py
│   ├── references.py
│   ├── session.py
│   ├── verify.py
│   └── workflow.py
│
├── core/                      # ✅ 核心工具函数
│   ├── __init__.py
│   └── utils.py              # 只保留纯工具函数
│
├── session/                   # ✅ Session 管理
│   ├── __init__.py
│   ├── manager.py
│   ├── models.py
│   └── storage.py
│
├── ui/                        # ✅ UI 组件
│   ├── __init__.py
│   ├── colors.py
│   ├── interactive.py
│   └── menu.py
│
└── verifier/                  # 🆕 陈述验证模块
    ├── __init__.py
    ├── configuration.py
    ├── prompts.py
    ├── schemas.py
    ├── state.py
    ├── statement_verifier.py
    └── utils.py              # statement_verifier_utils.py → utils.py
```

---

## 📦 文件移动计划

### 阶段 1: 创建新目录

```bash
mkdir -p pwa/agents
mkdir -p pwa/verifier
```

### 阶段 2: 移动 Agent 文件

| 源文件 | 目标文件 | 说明 |
|--------|---------|------|
| `pwa/core/base_agent.py` | `pwa/agents/base.py` | Agent 基类 |
| `pwa/core/citation_agent.py` | `pwa/agents/citation.py` | 引用 Agent |

### 阶段 3: 移动 Client 文件

| 源文件 | 目标文件 | 说明 |
|--------|---------|------|
| `pwa/core/pubmed_client.py` | `pwa/clients/pubmed.py` | PubMed 客户端 |
| `pwa/core/ragflow_client.py` | `pwa/clients/ragflow.py` | RAGFlow 客户端 |
| `pwa/core/zotero_client.py` | `pwa/clients/zotero.py` | Zotero 客户端 |

### 阶段 4: 移动 Verifier 文件

| 源文件 | 目标文件 | 说明 |
|--------|---------|------|
| `pwa/core/statement_verifier.py` | `pwa/verifier/statement_verifier.py` | 陈述验证器 |
| `pwa/core/statement_verifier_utils.py` | `pwa/verifier/utils.py` | 验证器工具 |
| `pwa/core/configuration.py` | `pwa/verifier/configuration.py` | 配置模式 |
| `pwa/core/state.py` | `pwa/verifier/state.py` | 状态定义 |
| `pwa/core/schemas.py` | `pwa/verifier/schemas.py` | Pydantic 模型 |
| `pwa/core/prompts.py` | `pwa/verifier/prompts.py` | LLM 提示词 |

### 阶段 5: 保留在 core/ 中的文件

| 文件 | 说明 |
|------|------|
| `pwa/core/__init__.py` | 包初始化 |
| `pwa/core/utils.py` | 纯工具函数 |

---

## 🔄 导入路径更新

### Agent 导入路径

```python
# 旧路径
from pwa.core.base_agent import BaseAgent
from pwa.core.citation_agent import CitationAgent

# 新路径
from pwa.agents.base import BaseAgent
from pwa.agents.citation import CitationAgent
```

### Client 导入路径

```python
# 旧路径
from pwa.core.pubmed_client import PubMedClient
from pwa.core.ragflow_client import RAGFlowClient
from pwa.core.zotero_client import ZoteroClient

# 新路径
from pwa.clients.pubmed import PubMedClient
from pwa.clients.ragflow import RAGFlowClient
from pwa.clients.zotero import ZoteroClient
```

### Verifier 导入路径

```python
# 旧路径
from pwa.core.statement_verifier import StatementVerifier
from pwa.core.statement_verifier_utils import parse_markdown_to_statements
from pwa.core.configuration import Configuration
from pwa.core.state import State
from pwa.core.schemas import Schema
from pwa.core.prompts import PROMPTS

# 新路径
from pwa.verifier.statement_verifier import StatementVerifier
from pwa.verifier.utils import parse_markdown_to_statements
from pwa.verifier.configuration import Configuration
from pwa.verifier.state import State
from pwa.verifier.schemas import Schema
from pwa.verifier.prompts import PROMPTS
```

---

## 📝 需要更新的文件

### Commands 模块

- `pwa/commands/references.py` - 使用 ZoteroClient
- `pwa/commands/verify.py` - 使用 StatementVerifier, RAGFlowClient, PubMedClient
- `pwa/commands/fulltext.py` - 可能使用 Client

### Core 模块

- `pwa/core/__init__.py` - 更新导出

---

## ✅ 重组后的优势

### 1. **职责清晰**

- `agents/` - 所有 Agent 相关代码
- `clients/` - 所有外部服务客户端
- `verifier/` - 陈述验证功能模块
- `core/` - 纯工具函数

### 2. **易于维护**

- 相关文件组织在一起
- 更容易找到需要修改的代码
- 减少文件间的耦合

### 3. **易于扩展**

- 添加新 Agent：在 `agents/` 目录添加
- 添加新 Client：在 `clients/` 目录添加
- 添加新功能：创建新的功能目录

### 4. **符合最佳实践**

- 按功能模块组织代码
- 清晰的命名空间
- 易于理解的项目结构

---

## 🧪 测试计划

### 测试步骤

1. 移动所有文件
2. 更新所有导入路径
3. 运行导入测试
4. 运行功能测试
5. 确保所有功能正常工作

### 测试检查清单

- [ ] 所有模块可以正常导入
- [ ] ReferencesMatchCommand 正常工作
- [ ] CitationsReplaceCommand 正常工作
- [ ] FulltextDownloadCommand 正常工作
- [ ] VerifyStatementsCommand 正常工作
- [ ] Session 管理正常工作
- [ ] CLI 主程序正常运行

---

## 📊 影响评估

### 影响范围

| 模块 | 影响程度 | 需要更新的文件数 |
|------|---------|-----------------|
| agents/ | 新建 | 2 |
| clients/ | 中等 | 4 |
| verifier/ | 新建 | 6 |
| core/ | 低 | 1 |
| commands/ | 中等 | 3 |

### 风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 导入路径错误 | 中 | 全面测试所有导入 |
| 功能失效 | 低 | 逐步移动，每步测试 |
| 向后兼容性 | 低 | 在 core/__init__.py 保留兼容导出 |

---

## 🚀 执行计划

### 保守策略（推荐）

1. 创建新目录
2. 复制文件到新位置（不删除旧文件）
3. 更新导入路径
4. 测试所有功能
5. 确认无误后删除旧文件
6. 提交到 Git

### 回滚计划

如果出现问题：
1. 恢复旧的导入路径
2. 删除新目录
3. 使用 Git 回滚

---

**计划制定时间**: 2026-01-11  
**预计执行时间**: 30-60 分钟  
**风险级别**: 低-中
