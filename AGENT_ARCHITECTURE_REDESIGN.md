# PWA-CLI Agent 架构重新设计

**日期**: 2026-01-11  
**目的**: 将 Verifier 整合到 Citation Agent，设计可扩展的 Agent 架构

---

## 🎯 设计原则

### 核心理念

1. **每个 Agent 是一个独立的功能模块**
2. **Agent 内部可以包含多个子功能**
3. **Agent 之间相互独立，易于添加和删除**
4. **统一的 Agent 基类和接口**

---

## 📋 当前问题

### 问题 1: Verifier 独立存在

**当前结构**:
```
pwa/
├── agents/
│   ├── base.py
│   └── citation.py
└── verifier/          # ❌ 独立的 verifier
    ├── statement_verifier.py
    ├── configuration.py
    ├── state.py
    └── ...
```

**问题**: 
- Verifier 实际上是 Citation Agent 的核心功能
- 分离后职责不清晰
- 难以理解两者的关系

### 问题 2: 未来扩展性不足

**未来可能的 Agent**:
- **Reference Agent** - 参考文献管理
- **Writing Agent** - 写作辅助
- **Review Agent** - 论文审阅
- **Translation Agent** - 学术翻译
- **Summary Agent** - 文献摘要

**需求**: 清晰的目录结构，方便添加新 Agent

---

## 🎨 新的 Agent 架构

### 目标结构

```
pwa/
└── agents/
    ├── __init__.py              # Agent 包入口
    ├── base.py                  # Agent 基类
    │
    ├── citation/                # 🆕 Citation Agent 模块
    │   ├── __init__.py          # 导出 CitationAgent
    │   ├── agent.py             # CitationAgent 主类
    │   ├── verifier.py          # 陈述验证器 (原 statement_verifier.py)
    │   ├── configuration.py     # 配置模式
    │   ├── state.py             # 状态定义
    │   ├── schemas.py           # Pydantic 模型
    │   ├── prompts.py           # LLM 提示词
    │   └── utils.py             # 工具函数
    │
    ├── reference/               # 🔮 未来: Reference Agent
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── matcher.py
    │   └── utils.py
    │
    ├── writing/                 # 🔮 未来: Writing Agent
    │   ├── __init__.py
    │   ├── agent.py
    │   └── ...
    │
    └── ...                      # 更多 Agent
```

---

## 📦 详细设计

### 1. Agent 基类 (`agents/base.py`)

```python
"""
Base class for all agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseAgent(ABC):
    """Base class for all PWA agents"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute the agent's main functionality"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict:
        """Get agent status"""
        pass
```

### 2. Citation Agent 模块 (`agents/citation/`)

#### 目录结构

```
agents/citation/
├── __init__.py          # 导出 CitationAgent
├── agent.py             # CitationAgent 主类
├── verifier.py          # 陈述验证器
├── configuration.py     # 配置模式
├── state.py             # 状态定义
├── schemas.py           # Pydantic 模型
├── prompts.py           # LLM 提示词
└── utils.py             # 工具函数
```

#### `__init__.py`

```python
"""
Citation Agent - 引用和陈述验证

This agent handles:
- Citation verification
- Statement verification
- Factuality checking
"""

from .agent import CitationAgent
from .verifier import StatementVerifier

__all__ = [
    'CitationAgent',
    'StatementVerifier',
]
```

#### `agent.py`

```python
"""
Citation Agent main class
"""
from ..base import BaseAgent
from .verifier import StatementVerifier

class CitationAgent(BaseAgent):
    """
    Citation Agent for citation and statement verification
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        self.verifier = StatementVerifier(config)
    
    def verify_statements(self, markdown_file: str):
        """Verify statements in markdown file"""
        return self.verifier.verify(markdown_file)
    
    def verify_citations(self, markdown_file: str):
        """Verify citations in markdown file"""
        # 实现引用验证逻辑
        pass
    
    def run(self, task: str, *args, **kwargs):
        """Execute agent task"""
        if task == 'verify_statements':
            return self.verify_statements(*args, **kwargs)
        elif task == 'verify_citations':
            return self.verify_citations(*args, **kwargs)
        else:
            raise ValueError(f"Unknown task: {task}")
    
    def get_status(self):
        """Get agent status"""
        return {
            'agent': 'CitationAgent',
            'status': 'ready',
            'verifier_status': self.verifier.get_status()
        }
```

### 3. 未来的 Agent 示例

#### Reference Agent (`agents/reference/`)

```
agents/reference/
├── __init__.py          # 导出 ReferenceAgent
├── agent.py             # ReferenceAgent 主类
├── matcher.py           # 参考文献匹配
├── extractor.py         # 参考文献提取
└── utils.py             # 工具函数
```

#### Writing Agent (`agents/writing/`)

```
agents/writing/
├── __init__.py          # 导出 WritingAgent
├── agent.py             # WritingAgent 主类
├── grammar_checker.py   # 语法检查
├── style_improver.py    # 风格改进
└── utils.py             # 工具函数
```

---

## 🔄 文件移动计划

### 阶段 1: 创建 Citation Agent 目录

```bash
mkdir -p pwa/agents/citation
```

### 阶段 2: 移动文件

| 源文件 | 目标文件 | 说明 |
|--------|---------|------|
| `pwa/agents/citation.py` | `pwa/agents/citation/agent.py` | Citation Agent 主类 |
| `pwa/verifier/statement_verifier.py` | `pwa/agents/citation/verifier.py` | 陈述验证器 |
| `pwa/verifier/configuration.py` | `pwa/agents/citation/configuration.py` | 配置模式 |
| `pwa/verifier/state.py` | `pwa/agents/citation/state.py` | 状态定义 |
| `pwa/verifier/schemas.py` | `pwa/agents/citation/schemas.py` | Pydantic 模型 |
| `pwa/verifier/prompts.py` | `pwa/agents/citation/prompts.py` | LLM 提示词 |
| `pwa/verifier/utils.py` | `pwa/agents/citation/utils.py` | 工具函数 |

### 阶段 3: 删除旧目录

```bash
rm -rf pwa/verifier/
```

---

## 📝 导入路径更新

### Citation Agent 导入

```python
# 旧路径
from pwa.agents import CitationAgent
from pwa.verifier import StatementVerifier

# 新路径
from pwa.agents.citation import CitationAgent, StatementVerifier
```

### 命令模块更新

```python
# pwa/commands/verify.py

# 旧导入
from pwa.verifier import StatementVerifier, Configuration, State

# 新导入
from pwa.agents.citation import StatementVerifier
from pwa.agents.citation.configuration import Configuration
from pwa.agents.citation.state import State
```

---

## 🎯 架构优势

### 1. **职责清晰**

- `agents/base.py` - Agent 基类
- `agents/citation/` - Citation Agent 及其所有子功能
- `agents/reference/` - Reference Agent（未来）
- `agents/writing/` - Writing Agent（未来）

### 2. **易于扩展**

添加新 Agent 的步骤：
1. 在 `agents/` 下创建新目录，如 `agents/new_agent/`
2. 实现 `agent.py` 继承 `BaseAgent`
3. 添加子功能模块
4. 在 `agents/new_agent/__init__.py` 中导出
5. 在 `agents/__init__.py` 中注册

### 3. **模块化**

每个 Agent 是独立的模块：
- 可以单独测试
- 可以单独部署
- 可以单独维护

### 4. **统一接口**

所有 Agent 继承 `BaseAgent`：
- 统一的 `run()` 方法
- 统一的 `get_status()` 方法
- 易于管理和调用

---

## 📊 对比分析

### 当前结构 vs 新结构

| 方面 | 当前结构 | 新结构 |
|------|---------|--------|
| Verifier 位置 | 独立的 `verifier/` 目录 | `agents/citation/` 内部 |
| Citation Agent | 单文件 `citation.py` | 完整的 `citation/` 模块 |
| 职责清晰度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 扩展性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可维护性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🚀 实施计划

### 步骤 1: 创建新目录结构

```bash
mkdir -p pwa/agents/citation
```

### 步骤 2: 移动和重构文件

1. 将 `agents/citation.py` 重构为 `agents/citation/agent.py`
2. 将 `verifier/` 下所有文件移到 `agents/citation/`
3. 创建 `agents/citation/__init__.py`

### 步骤 3: 更新导入路径

1. 更新 `pwa/commands/verify.py`
2. 更新 `pwa/agents/__init__.py`
3. 更新所有相关测试

### 步骤 4: 测试

1. 测试所有导入
2. 测试 Citation Agent 功能
3. 测试命令模块

### 步骤 5: 删除旧目录

```bash
rm -rf pwa/verifier/
```

---

## 🔮 未来扩展示例

### 添加 Reference Agent

```bash
# 1. 创建目录
mkdir -p pwa/agents/reference

# 2. 创建文件
touch pwa/agents/reference/__init__.py
touch pwa/agents/reference/agent.py
touch pwa/agents/reference/matcher.py
touch pwa/agents/reference/extractor.py

# 3. 实现 ReferenceAgent
# 4. 在 agents/__init__.py 中注册
```

### 添加 Writing Agent

```bash
# 1. 创建目录
mkdir -p pwa/agents/writing

# 2. 创建文件
touch pwa/agents/writing/__init__.py
touch pwa/agents/writing/agent.py
touch pwa/agents/writing/grammar_checker.py
touch pwa/agents/writing/style_improver.py

# 3. 实现 WritingAgent
# 4. 在 agents/__init__.py 中注册
```

---

## 📋 检查清单

### 重构前检查

- [ ] 理解当前 Citation Agent 的功能
- [ ] 理解 Verifier 的功能
- [ ] 确认两者的关系
- [ ] 规划新的目录结构

### 重构中检查

- [ ] 创建新目录
- [ ] 移动所有文件
- [ ] 更新所有导入路径
- [ ] 创建 __init__.py 文件
- [ ] 更新命令模块

### 重构后检查

- [ ] 所有模块可以正常导入
- [ ] Citation Agent 功能正常
- [ ] Verifier 功能正常
- [ ] 命令模块正常工作
- [ ] 测试通过

---

## 🎊 预期成果

### 架构清晰度

- ✅ Citation Agent 包含 Verifier
- ✅ 每个 Agent 是独立模块
- ✅ 易于理解和维护

### 扩展性

- ✅ 添加新 Agent 非常简单
- ✅ 统一的 Agent 接口
- ✅ 模块化设计

### 代码质量

- ✅ 职责清晰
- ✅ 高内聚低耦合
- ✅ 符合 SOLID 原则

---

**设计完成时间**: 2026-01-11  
**预计实施时间**: 30-45 分钟  
**风险级别**: 低
