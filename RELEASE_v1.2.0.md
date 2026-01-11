# PWA-CLI v1.2.0 发布说明

## 🎉 用户体验大升级！

v1.2.0 是一个重要的用户体验提升版本，带来了**箭头键导航**和**Session 管理**两大核心功能，让 PWA-CLI 更加现代化和易用。

---

## 📋 发布日期

2026-01-11

---

## ✨ 新功能

### 1. 箭头键导航 🎯

告别传统的数字输入，现在您可以使用箭头键在菜单中自由导航！

#### 功能特点

**交互式菜单系统**：基于 `prompt_toolkit` 实现的现代化交互式菜单，提供流畅的用户体验。使用上下箭头键在菜单选项间移动，按 Enter 键确认选择，或者直接输入数字快速跳转到指定选项。

**优雅降级机制**：如果系统中未安装 `prompt_toolkit`，程序会自动切换到传统的数字输入模式，确保在任何环境下都能正常使用。

**多级菜单支持**：所有主菜单和子菜单都支持箭头键导航，提供一致的交互体验。

#### 使用方式

```bash
# 启动 PWA-CLI
pwa

# 使用箭头键导航
↑/↓  - 上下移动选择
Enter - 确认选择
数字  - 快速跳转
q    - 退出当前菜单
```

#### 技术实现

使用业界领先的 `prompt_toolkit` 库实现交互式界面，该库被广泛应用于 IPython、ptpython 等知名项目。提供跨平台支持（Windows/Linux/macOS），确保在不同操作系统上都有一致的体验。

---

### 2. Session 管理 📝

PWA-CLI 现在具备完整的 Session 管理能力，记录您的每一次操作，让工作更加连贯和高效。

#### Session 概念

**Session** 是您的一次工作会话，包含工作目录、操作历史、上下文数据等信息。每次启动 PWA-CLI 时，系统会自动创建新 Session 或恢复上次未完成的 Session。

#### 核心功能

**自动 Session 管理**：启动时自动创建或恢复 Session，无需手动操作。Session 数据持久化保存到 `~/.config/pwa/sessions/` 目录，即使关闭程序也不会丢失。

**操作历史记录**：记录每个命令的执行时间、参数、结果和执行时长。可以随时查看历史操作，了解之前做了什么。

**上下文保持**：自动记住最后使用的文件路径和配置选择。下次执行相同操作时，系统会智能推荐之前的选择，节省时间。

**Session 恢复**：可以恢复任何历史 Session，继续之前未完成的工作。支持在多个 Session 之间切换。

**Session 清理**：定期清理旧的 Session 文件，释放存储空间。可以设置保留天数，自动删除过期 Session。

**Session 导出**：将 Session 导出为 JSON 文件，方便分享或备份。

#### Session 管理命令

PWA-CLI 提供了完整的 Session 管理命令集：

**查看当前 Session** (`session_view`)：显示当前 Session 的详细信息，包括 Session ID、状态、创建时间、工作目录、操作数等。

**查看操作历史** (`session_history`)：查看最近的操作历史，包括命令名称、执行时间、参数、结果和执行时长。

**列出所有 Session** (`session_list`)：列出所有保存的 Session，按最后活动时间排序。显示每个 Session 的状态、操作数、持续时间等信息。

**恢复历史 Session** (`session_resume`)：从历史 Session 列表中选择一个 Session 进行恢复。恢复后，当前工作环境会切换到该 Session。

**清理旧 Session** (`session_cleanup`)：删除指定天数之前的 Session 文件。默认删除 30 天前的 Session。

**导出 Session** (`session_export`)：将 Session 导出为 JSON 文件。可以指定要导出的 Session ID 和输出路径。

**Session 统计** (`session_stats`)：查看 Session 统计信息，包括总 Session 数、活跃 Session 数、总操作数、总持续时间、存储大小等。

#### Session 数据结构

每个 Session 包含以下信息：

```json
{
  "session_id": "pwa_20260111_143052_a1b2c3",
  "created_at": "2026-01-11T14:30:52",
  "last_active_at": "2026-01-11T15:45:30",
  "status": "active",
  "working_directory": "/home/user/papers",
  "context": {
    "last_md_file": "/home/user/papers/paper.md",
    "last_bib_file": "/home/user/papers/refs.bib"
  },
  "history": [
    {
      "timestamp": "2026-01-11T14:35:20",
      "command": "references_match",
      "params": {"md_file": "paper.md"},
      "result": {"status": "success", "count": 45},
      "duration": 2.5
    }
  ],
  "metadata": {
    "pwa_version": "1.2.0",
    "python_version": "3.11.0",
    "platform": "Linux"
  }
}
```

---

## 🏗️ 架构改进

### 新增模块

**交互式 UI 模块** (`pwa/ui/interactive.py`)：实现交互式菜单、确认对话框、消息对话框等组件。提供统一的交互式界面 API。

**Session 数据模型** (`pwa/session/models.py`)：定义 Session、HistoryEntry 等数据模型。提供 Session 创建、序列化、反序列化等功能。

**Session 存储** (`pwa/session/storage.py`)：负责 Session 的持久化存储。支持保存、加载、删除、列表、导出、导入等操作。

**Session 管理器** (`pwa/session/manager.py`)：提供高级 Session 管理功能。包括 Session 生命周期管理、上下文管理、历史记录、统计等。

**Session 命令** (`pwa/commands/session.py`)：实现 7 个 Session 管理命令。提供完整的 Session 操作界面。

### CLI 重构

完全重写了 `pwa/cli.py`，采用新的交互式菜单系统。集成 SessionManager，自动管理 Session 生命周期。优化了菜单结构，增加了 Session 管理菜单。改进了命令执行流程，自动记录操作历史。

---

## 📦 依赖更新

新增依赖：`prompt_toolkit>=3.0.0` - 强大的交互式 CLI 库，提供箭头键导航、对话框、自动补全等功能。

---

## 🧪 测试

新增 Session 模型测试，包含 8 个测试用例，覆盖 Session 创建、序列化、历史记录、上下文管理、状态操作等功能。所有测试通过率 100%。

```bash
$ pytest tests/test_session/test_models.py -v
============================= test session starts ==============================
collected 8 items

tests/test_session/test_models.py::TestSession::test_create_session_id PASSED
tests/test_session/test_models.py::TestSession::test_create_new_session PASSED
tests/test_session/test_models.py::TestSession::test_session_to_dict PASSED
tests/test_session/test_models.py::TestSession::test_session_from_dict PASSED
tests/test_session/test_models.py::TestSession::test_add_history PASSED
tests/test_session/test_models.py::TestSession::test_context_operations PASSED
tests/test_session/test_models.py::TestSession::test_status_operations PASSED
tests/test_session/test_models.py::TestSession::test_get_summary PASSED

============================== 8 passed in 0.04s ===============================
```

---

## 🚀 升级指南

### 从 v1.1.1 升级

```bash
# 拉取最新代码
cd pwa-cli
git pull origin main

# 安装新依赖
pip install -r requirements.txt

# 重新安装
pip install -e .

# 验证版本
pwa --version
# 应显示: PWA-CLI v1.2.0
```

### 新依赖安装

如果您想启用箭头键导航功能，需要安装 `prompt_toolkit`：

```bash
pip install prompt_toolkit
```

如果不安装，PWA-CLI 会自动降级到传统的数字输入模式。

---

## 💡 使用示例

### 箭头键导航

```bash
$ pwa

============================================================
  Paper Writing Assistant (PWA) v1.2.0
  Paper Writing Assistant - A modern CLI tool for academic writing
============================================================

Session: pwa_20260111_143052_a1b2c3
工作目录: /home/user/papers

✅ 交互式导航已启用 (使用箭头键)

# 使用箭头键选择菜单项
# 按 Enter 确认
# 或输入数字快速跳转
```

### Session 管理

```bash
# 查看当前 Session
pwa
# 选择 "6. Session 管理"
# 选择 "1. 查看当前 Session"

# 查看操作历史
# 选择 "2. 查看操作历史"

# 列出所有 Session
# 选择 "3. 列出所有 Session"

# 恢复历史 Session
# 选择 "4. 恢复历史 Session"
# 从列表中选择要恢复的 Session

# 清理旧 Session
# 选择 "5. 清理旧 Session"
# 输入保留天数（默认 30 天）
```

---

## 📊 改进统计

| 指标 | v1.1.1 | v1.2.0 | 变化 |
|------|--------|--------|------|
| Python 文件 | 44 | 49 | +5 |
| 代码行数 | 72,618 | 78,000+ | +5,382 |
| 功能模块 | 4 | 5 | +1 (Session) |
| 命令数 | 14 | 21 | +7 (Session 命令) |
| 测试用例 | 15 | 23 | +8 |

---

## 🎯 用户体验提升

**操作效率提升**：箭头键导航比数字输入更快更直观。Session 管理让工作更加连贯，减少重复操作。

**智能推荐**：系统记住您的使用习惯，自动推荐上次使用的文件和配置。

**工作追溯**：完整的操作历史让您随时了解做过什么，方便追溯和复现。

**多任务支持**：可以在多个 Session 之间切换，同时处理多个项目。

---

## 📖 文档

**设计文档**：`SESSION_AND_NAVIGATION_DESIGN.md` - 详细的设计说明和技术实现

**变更日志**：`CHANGELOG.md` - 完整的变更记录

**用户指南**：`docs/user_guide.md` - 使用指南（待更新）

---

## 🔮 未来计划

**v1.3.0 计划**：

命令行模式支持非交互式使用，可以在脚本中调用。配置文件编辑器提供图形化配置编辑界面。进度条显示为长时间运行的任务添加进度条。批量处理支持批量处理多个文件。

**长期计划**：

插件系统允许用户开发和安装插件。Web 界面提供基于浏览器的图形界面。云同步支持 Session 和配置的云端同步。更多测试覆盖持续提升测试覆盖率。

---

## 🙏 致谢

感谢所有用户的反馈和建议，让 PWA-CLI 不断进步！

---

## 📝 相关链接

- **GitHub 仓库**: https://github.com/lipaopao000/pwa-cli
- **问题反馈**: https://github.com/lipaopao000/pwa-cli/issues
- **文档**: https://github.com/lipaopao000/pwa-cli/tree/main/docs

---

**发布时间**: 2026-01-11  
**版本**: v1.2.0  
**类型**: 功能增强版本  
**重要性**: 中等（用户体验大幅提升）

**立即升级，体验全新的 PWA-CLI！** 🚀
