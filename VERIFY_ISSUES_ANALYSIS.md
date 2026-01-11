# PWA-CLI Verify 功能问题分析

## 📋 分析日期
2026-01-11

## 🔍 问题概述

通过深入对比原始 `05-Scientific_Statement_Verifier.py` 和当前 PWA-CLI 中的 `pwa/commands/verify.py`，发现当前实现存在**严重的功能缺失和架构问题**。

---

## ❌ 主要问题

### 1. **核心依赖模块缺失** (严重)

原始代码依赖的核心模块在当前架构中**完全缺失**：

| 模块 | 原代码 | 当前架构 | 状态 |
|------|--------|---------|------|
| `core/statement_verifier.py` | ✅ 15,916 行 | ❌ 缺失 | **严重** |
| `core/statement_verifier_utils.py` | ✅ 3,756 行 | ❌ 缺失 | **严重** |
| `core/configuration.py` | ✅ 1,453 行 | ❌ 缺失 | **严重** |
| `core/state.py` | ✅ 1,605 行 | ❌ 缺失 | **严重** |
| `core/schemas.py` | ✅ 1,337 行 | ❌ 缺失 | **严重** |
| `core/prompts.py` | ✅ 2,423 行 | ❌ 缺失 | **严重** |
| `core/base_agent.py` | ✅ 1,747 行 | ❌ 缺失 | **中等** |
| `core/citation_agent.py` | ✅ 37,824 行 | ❌ 缺失 | **中等** |

**总计缺失代码**: ~66,000 行

### 2. **LangGraph 工作流缺失** (严重)

原始实现使用 **LangGraph** 构建了复杂的状态机工作流：

```python
# 原代码使用 LangGraph StateGraph
from langgraph.graph import StateGraph, END, START

class ScientificStatementVerifier:
    def _build_graph(self):
        builder = StateGraph(AgentState, config_schema=Configuration)
        
        # 多节点状态机
        builder.add_node("initialize", self.initialize)
        builder.add_node("citation_verifier_ladder", self.citation_verifier_ladder)
        builder.add_node("factuality_verifier_global", self.factuality_verifier_global)
        builder.add_node("finalize", self.finalize_result)
        
        # 条件路由
        builder.add_conditional_edges(...)
        
        return builder.compile()
```

**当前实现**: 完全没有这个工作流逻辑！

### 3. **"阶梯式验证" (Ladder Verification) 逻辑缺失** (严重)

原代码实现了精妙的**阶梯式验证策略**：

```
Abstract → Local RAG → Fulltext → Global Factuality
```

**验证逻辑**:
1. **Abstract 层**: 先检查引用文献的摘要
2. **Local RAG 层**: 如果摘要不足，检索该文献的全文 RAG
3. **Fulltext 层**: 如果 RAG 不足，使用完整全文
4. **Global Factuality 层**: 如果本地证据不足，进行全局事实性检查

**当前实现**: 完全没有这个阶梯逻辑！

### 4. **证据评估机制缺失** (严重)

原代码使用 **结构化输出 (Structured Output)** 进行精确的证据评估：

```python
# 使用 Pydantic 模型进行结构化输出
class LocalSupportEvaluation(BaseModel):
    local_support: Literal["Full", "Partial", "None", "Contradictory"]
    reasoning: str

class GlobalFactualityEvaluation(BaseModel):
    factuality: Literal["Supported", "Partially Supported", "Unsupported", "Contradicted"]
    reasoning: str
    suggested_key: Optional[str]

# LLM 调用
llm = self.default_model.with_structured_output(LocalSupportEvaluation)
result = llm.invoke([SystemMessage(...), HumanMessage(...)])
```

**当前实现**: 没有结构化评估！

### 5. **参考文献集成缺失** (严重)

原代码会：
1. 加载参考文献库 (Zotero/BibTeX)
2. 提取每个陈述的 `citation_id`
3. 获取引用文献的元数据（标题、摘要、Journal IF、URL）
4. 使用这些信息进行验证

**当前实现**: 完全没有这个集成！

### 6. **RAGFlow 数据集交互缺失** (严重)

原代码实现了完整的 RAGFlow 交互：

```python
def select_dataset_interactively(self):
    """交互式选择 RAGFlow 数据集"""
    datasets = self.rag_client.list_datasets(page_size=100)
    # 显示数据集列表让用户选择
    ...

def sync_documents_to_rag(self, statements):
    """将全文 Markdown 同步到 RAGFlow"""
    existing_docs = self.rag_client.list_documents(self.dataset_id)
    # 上传缺失的文档
    ...
```

**当前实现**: 没有数据集选择和文档同步！

### 7. **Markdown 注释功能缺失** (中等)

原代码会生成带注释的 Markdown：

```python
def annotate_markdown(self, md_path, results):
    """在原文中添加验证结果注释"""
    # 在每个陈述后添加 emoji 和验证结果
    # ✅ Supported / ❌ Contradicted / ⚠️ Partially Supported
    ...
```

**当前实现**: 没有这个功能！

### 8. **并发处理不完整** (中等)

原代码使用 ThreadPoolExecutor 进行多层并发：
- 陈述级并发（多个陈述同时验证）
- 证据收集并发（Library RAG + Web Search 并行）

**当前实现**: 只有陈述级并发，没有证据收集并发！

### 9. **审计历史 (Audit History) 缺失** (中等)

原代码记录每一步的验证历史：

```python
audit_entry = {
    "level": "local_abstract",
    "evidence_count": 5,
    "local_support": "Partial",
    "reasoning": "..."
}
state['audit_history'].append(audit_entry)
```

**当前实现**: 没有审计历史！

### 10. **Journal IF (影响因子) 考虑缺失** (中等)

原代码会根据期刊影响因子调整验证策略：

```python
current_if = state.get('ref_journal_if', 0.0) or 0.0
is_definitive = (ls_val == "Full" and 
                (level != "abstract" or current_if >= config.high_if_threshold))
```

**高影响因子期刊的摘要可以直接作为充分证据！**

**当前实现**: 完全没有考虑 Journal IF！

---

## 📊 功能对比表

| 功能 | 原代码 | 当前实现 | 完成度 |
|------|--------|---------|--------|
| LangGraph 状态机 | ✅ | ❌ | 0% |
| 阶梯式验证 | ✅ | ❌ | 0% |
| 结构化输出评估 | ✅ | ❌ | 0% |
| 参考文献集成 | ✅ | ❌ | 0% |
| RAGFlow 数据集选择 | ✅ | ❌ | 0% |
| 文档同步到 RAG | ✅ | ❌ | 0% |
| Markdown 注释 | ✅ | ❌ | 0% |
| 审计历史 | ✅ | ❌ | 0% |
| Journal IF 考虑 | ✅ | ❌ | 0% |
| 证据收集并发 | ✅ | ⚠️ | 50% |
| 陈述提取 | ✅ | ⚠️ | 50% |
| PubMed 集成 | ✅ | ⚠️ | 50% |
| RAGFlow 基础调用 | ✅ | ⚠️ | 50% |
| **总体完成度** | **100%** | **~15%** | **15%** |

---

## 🔧 当前实现的问题

### 问题 1: 过度简化

当前的 `pwa/commands/verify.py` 只是一个**空壳**，试图直接调用核心模块：

```python
from ..core.statement_verifier import ScientificStatementVerifier
from ..core.statement_verifier_utils import parse_markdown_to_statements
```

但这些模块**根本不存在**！

### 问题 2: 缺少依赖

当前 `requirements.txt` 缺少关键依赖：
- ❌ `langgraph` - 状态机工作流
- ❌ `langchain-core` - LangChain 核心
- ❌ `langchain-openai` - OpenAI 集成

### 问题 3: 架构不匹配

原代码是一个**复杂的 AI Agent 系统**，使用：
- LangGraph 状态机
- 多步推理
- 动态路由
- 结构化输出

当前实现试图用简单的函数调用来替代，这是**不可能的**！

---

## 🎯 修复方案

### 方案 A: 完整迁移 (推荐)

**工作量**: 大 (~3-5 天)

**步骤**:
1. 复制所有缺失的核心模块到 `pwa/core/`
2. 更新 `requirements.txt` 添加 LangGraph 等依赖
3. 重构 `pwa/commands/verify.py` 以正确使用核心模块
4. 添加完整的测试

**优点**:
- 功能完整
- 保持原有的精妙设计
- 可扩展性强

**缺点**:
- 工作量大
- 需要深入理解 LangGraph

### 方案 B: 简化实现

**工作量**: 中 (~1-2 天)

**步骤**:
1. 实现简化版的验证逻辑（不使用 LangGraph）
2. 保留核心功能：RAGFlow 检索、PubMed 搜索
3. 简化评估逻辑

**优点**:
- 工作量较小
- 易于维护

**缺点**:
- 失去原有的精妙设计
- 功能不完整

### 方案 C: 包装原脚本

**工作量**: 小 (~半天)

**步骤**:
1. 在 CLI 中直接调用原始脚本
2. 只做参数转换和输出格式化

**优点**:
- 工作量最小
- 功能完整

**缺点**:
- 不符合现代化 CLI 架构
- 不易扩展

---

## 💡 建议

**强烈建议采用方案 A（完整迁移）**，原因：

1. **原代码设计精妙**: LangGraph 状态机 + 阶梯式验证是非常优秀的设计
2. **功能完整性**: 只有完整迁移才能保证所有功能正常工作
3. **长期价值**: 完整的实现更易于维护和扩展
4. **学习价值**: 深入理解 LangGraph 和 AI Agent 设计

---

## 📝 下一步行动

1. ✅ 确认采用哪个方案
2. ⏳ 复制缺失的核心模块
3. ⏳ 更新依赖
4. ⏳ 重构 verify 命令
5. ⏳ 添加测试
6. ⏳ 更新文档

---

## 🔗 相关文件

- 原始脚本: `/home/ubuntu/paper-writing-assistant/05-Scientific_Statement_Verifier.py`
- 核心模块目录: `/home/ubuntu/paper-writing-assistant/core/`
- 当前实现: `/home/ubuntu/pwa-cli/pwa/commands/verify.py`
- 缺失模块列表: 见上文"核心依赖模块缺失"部分

---

**结论**: 当前的 verify 功能实现**严重不完整**，只有约 15% 的功能完成度。需要进行**完整的重构和迁移**才能达到原代码的功能水平。
