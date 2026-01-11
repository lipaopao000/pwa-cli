# PWA-CLI Session 和箭头键导航设计

## 📋 设计目标

1. **箭头键导航** - 使用上下箭头键选择菜单项，提升交互体验
2. **Session 管理** - 保持用户工作会话，记录历史和上下文

---

## 🎯 功能需求

### 1. 箭头键导航

#### 当前问题
- 只能输入数字选择菜单项
- 不够直观和友好

#### 改进方案
- 支持 **↑/↓ 箭头键** 移动选择
- 支持 **Enter** 确认选择
- 支持 **数字键** 快速跳转（保留原有功能）
- 高亮显示当前选中项
- 支持 **q** 退出当前菜单

#### 技术实现
- 使用 `readchar` 或 `pynput` 库捕获键盘输入
- 或使用 `curses` 库（Unix/Linux）
- 或使用 `prompt_toolkit` 库（跨平台，功能强大）

**推荐**: `prompt_toolkit` - 功能强大，跨平台，易于使用

### 2. Session 管理

#### Session 概念

**Session** 是用户的一次工作会话，包含：
- 会话 ID（唯一标识）
- 创建时间
- 最后活动时间
- 工作目录
- 操作历史
- 上下文数据（如当前处理的文件、配置等）
- 会话状态（活跃/暂停/完成）

#### 功能需求

1. **自动创建 Session**
   - 启动 CLI 时自动创建新 Session
   - 或恢复上次未完成的 Session

2. **Session 持久化**
   - 保存到 `~/.config/pwa/sessions/` 目录
   - JSON 格式存储

3. **Session 管理命令**
   - 查看当前 Session
   - 列出所有 Session
   - 恢复历史 Session
   - 删除旧 Session

4. **操作历史记录**
   - 记录每个命令的执行
   - 包含时间戳、命令名、参数、结果

5. **上下文保持**
   - 记住最后使用的文件路径
   - 记住最后的配置选择
   - 支持"继续上次操作"

#### Session 数据结构

```json
{
  "session_id": "pwa_20260111_143052_a1b2c3",
  "created_at": "2026-01-11T14:30:52",
  "last_active_at": "2026-01-11T15:45:30",
  "status": "active",
  "working_directory": "/home/user/papers",
  "context": {
    "last_md_file": "/home/user/papers/paper.md",
    "last_bib_file": "/home/user/papers/refs.bib",
    "last_command": "verify_statements",
    "last_config": {
      "use_ragflow": true,
      "use_pubmed": true
    }
  },
  "history": [
    {
      "timestamp": "2026-01-11T14:35:20",
      "command": "references_extract",
      "params": {
        "md_file": "/home/user/papers/paper.md"
      },
      "result": {
        "status": "success",
        "count": 45
      }
    },
    {
      "timestamp": "2026-01-11T14:40:15",
      "command": "citations_replace",
      "params": {
        "md_file": "/home/user/papers/paper.md"
      },
      "result": {
        "status": "success",
        "replaced": 120
      }
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

## 🏗️ 架构设计

### 目录结构

```
pwa/
├── ui/
│   ├── colors.py           # 现有
│   ├── menu.py             # 现有（需要重构）
│   ├── interactive.py      # 新增：箭头键导航
│   └── __init__.py
├── session/
│   ├── __init__.py         # 新增
│   ├── manager.py          # 新增：Session 管理器
│   ├── models.py           # 新增：Session 数据模型
│   └── storage.py          # 新增：Session 存储
└── cli.py                  # 需要更新
```

### 核心类设计

#### 1. InteractiveMenu (箭头键导航)

```python
class InteractiveMenu:
    """交互式菜单，支持箭头键导航"""
    
    def __init__(self, title: str, options: List[MenuOption]):
        self.title = title
        self.options = options
        self.selected_index = 0
    
    def show(self) -> Optional[MenuOption]:
        """显示菜单并返回选中的选项"""
        # 使用 prompt_toolkit 实现
        pass
    
    def render(self):
        """渲染菜单"""
        pass
```

#### 2. SessionManager (Session 管理)

```python
class SessionManager:
    """Session 管理器"""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.current_session: Optional[Session] = None
    
    def create_session(self) -> Session:
        """创建新 Session"""
        pass
    
    def load_session(self, session_id: str) -> Session:
        """加载 Session"""
        pass
    
    def save_session(self):
        """保存当前 Session"""
        pass
    
    def list_sessions(self) -> List[Session]:
        """列出所有 Session"""
        pass
    
    def delete_session(self, session_id: str):
        """删除 Session"""
        pass
    
    def add_history(self, command: str, params: Dict, result: Dict):
        """添加操作历史"""
        pass
    
    def get_context(self, key: str) -> Any:
        """获取上下文数据"""
        pass
    
    def set_context(self, key: str, value: Any):
        """设置上下文数据"""
        pass
```

#### 3. Session (数据模型)

```python
@dataclass
class Session:
    """Session 数据模型"""
    
    session_id: str
    created_at: datetime
    last_active_at: datetime
    status: str  # active, paused, completed
    working_directory: str
    context: Dict[str, Any]
    history: List[Dict]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        pass
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """从字典创建"""
        pass
```

---

## 🎨 用户体验设计

### 箭头键导航示例

```
╔════════════════════════════════════════════════════════════╗
║                    PWA-CLI v1.2.0                          ║
║              Paper Writing Assistant                       ║
╚════════════════════════════════════════════════════════════╝

Session: pwa_20260111_143052 | Working Dir: ~/papers

┌────────────────────────────────────────────────────────────┐
│ 主菜单                                                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   1. 参考文献管理                                          │
│ ▶ 2. 引用处理                    [当前选中]               │
│   3. 全文获取                                              │
│   4. 陈述验证                                              │
│   5. 工作流管理                                            │
│   6. 配置管理                                              │
│   7. Session 管理                                          │
│   8. 帮助                                                  │
│   0. 退出                                                  │
│                                                            │
└────────────────────────────────────────────────────────────┘

使用 ↑/↓ 选择，Enter 确认，数字快速跳转，q 退出
```

### Session 管理菜单

```
╔════════════════════════════════════════════════════════════╗
║                   Session 管理                             ║
╚════════════════════════════════════════════════════════════╝

当前 Session: pwa_20260111_143052
创建时间: 2026-01-11 14:30:52
工作目录: /home/user/papers
操作数: 5

┌────────────────────────────────────────────────────────────┐
│ Session 操作                                               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ▶ 1. 查看当前 Session 详情                                │
│   2. 查看操作历史                                          │
│   3. 列出所有 Session                                      │
│   4. 恢复历史 Session                                      │
│   5. 清理旧 Session                                        │
│   6. 导出 Session                                          │
│   0. 返回主菜单                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 操作历史示例

```
╔════════════════════════════════════════════════════════════╗
║                   操作历史                                 ║
╚════════════════════════════════════════════════════════════╝

Session: pwa_20260111_143052

┌────────────────────────────────────────────────────────────┐
│ 最近操作                                                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 1. [14:35:20] references_extract                           │
│    文件: paper.md                                          │
│    结果: ✅ 成功提取 45 条参考文献                         │
│                                                            │
│ 2. [14:40:15] citations_replace                            │
│    文件: paper.md                                          │
│    结果: ✅ 成功替换 120 处引用                            │
│                                                            │
│ 3. [14:50:30] fulltext_download                            │
│    来源: Zotero                                            │
│    结果: ✅ 下载 30 篇全文                                 │
│                                                            │
│ 4. [15:10:45] verify_statements                            │
│    文件: paper.md                                          │
│    结果: ✅ 验证 25 条陈述                                 │
│                                                            │
│ 5. [15:45:30] workflow_run_full                            │
│    文件: paper.md                                          │
│    结果: ✅ 完整工作流执行成功                             │
│                                                            │
└────────────────────────────────────────────────────────────┘

按 Enter 返回
```

---

## 🔧 技术实现细节

### 1. 箭头键导航实现

#### 使用 prompt_toolkit

```python
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog

def show_menu(title: str, options: List[Tuple[str, str]]) -> str:
    """显示交互式菜单"""
    result = radiolist_dialog(
        title=title,
        text="使用箭头键选择，Enter 确认",
        values=options,
    ).run()
    return result
```

#### 自定义实现（使用 readchar）

```python
import readchar
import sys

def show_menu(title: str, options: List[str]) -> int:
    """显示交互式菜单"""
    selected = 0
    
    while True:
        # 清屏
        print("\033[2J\033[H")
        
        # 显示标题
        print(f"\n{title}\n")
        
        # 显示选项
        for i, option in enumerate(options):
            if i == selected:
                print(f"▶ {option}")  # 高亮
            else:
                print(f"  {option}")
        
        # 读取按键
        key = readchar.readkey()
        
        if key == readchar.key.UP:
            selected = (selected - 1) % len(options)
        elif key == readchar.key.DOWN:
            selected = (selected + 1) % len(options)
        elif key == readchar.key.ENTER:
            return selected
        elif key.isdigit():
            num = int(key)
            if 0 <= num < len(options):
                return num
        elif key == 'q':
            return -1
```

### 2. Session 存储实现

```python
import json
from pathlib import Path
from datetime import datetime

class SessionStorage:
    """Session 存储"""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, session: Session):
        """保存 Session"""
        file_path = self.storage_dir / f"{session.session_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
    
    def load(self, session_id: str) -> Session:
        """加载 Session"""
        file_path = self.storage_dir / f"{session_id}.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Session.from_dict(data)
    
    def list_all(self) -> List[Session]:
        """列出所有 Session"""
        sessions = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                session = self.load(file_path.stem)
                sessions.append(session)
            except Exception:
                pass
        return sorted(sessions, key=lambda s: s.last_active_at, reverse=True)
    
    def delete(self, session_id: str):
        """删除 Session"""
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
```

---

## 📦 依赖更新

需要添加的新依赖：

```
# requirements.txt

# Interactive UI
prompt_toolkit>=3.0.0     # 推荐：功能强大的交互式 CLI 库
# 或
readchar>=4.0.0           # 备选：简单的键盘输入库
```

---

## 🎯 实现优先级

### Phase 1: 箭头键导航（高优先级）
1. 安装 `prompt_toolkit`
2. 创建 `pwa/ui/interactive.py`
3. 实现 `InteractiveMenu` 类
4. 更新 `pwa/ui/menu.py` 使用新的交互式菜单
5. 测试菜单导航

### Phase 2: Session 基础（高优先级）
1. 创建 `pwa/session/` 目录
2. 实现 `Session` 数据模型
3. 实现 `SessionStorage` 存储
4. 实现 `SessionManager` 管理器
5. 在 CLI 启动时创建/恢复 Session

### Phase 3: Session 管理命令（中优先级）
1. 创建 Session 管理命令
2. 查看当前 Session
3. 列出所有 Session
4. 恢复历史 Session
5. 清理旧 Session

### Phase 4: 上下文保持（中优先级）
1. 记录最后使用的文件
2. 记录最后的配置
3. 支持"继续上次操作"
4. 智能默认值建议

### Phase 5: 操作历史（低优先级）
1. 记录每个命令执行
2. 查看操作历史
3. 导出操作历史
4. 重放历史操作（可选）

---

## 🧪 测试计划

### 箭头键导航测试
- [ ] 上下箭头键正常工作
- [ ] Enter 键确认选择
- [ ] 数字键快速跳转
- [ ] q 键退出
- [ ] 多级菜单导航
- [ ] 跨平台兼容性（Windows/Linux/macOS）

### Session 管理测试
- [ ] Session 自动创建
- [ ] Session 持久化保存
- [ ] Session 恢复
- [ ] 操作历史记录
- [ ] 上下文数据保存
- [ ] 多 Session 管理
- [ ] Session 清理

---

## 📝 文档更新

需要更新的文档：
- [ ] README.md - 添加新功能说明
- [ ] CHANGELOG.md - 记录 v1.2.0 变更
- [ ] docs/user_guide.md - 添加使用指南
- [ ] 创建 docs/session_guide.md - Session 管理指南

---

## 🚀 发布计划

**版本**: v1.2.0  
**类型**: 功能增强版本  
**重要性**: 中等（用户体验提升）

**主要特性**:
- ✨ 箭头键导航
- ✨ Session 管理
- ✨ 操作历史
- ✨ 上下文保持

---

## 💡 未来扩展

1. **Session 分享** - 导出 Session 供他人使用
2. **Session 模板** - 预定义的工作流 Session
3. **Session 统计** - 使用时长、命令频率等
4. **Session 搜索** - 按时间、命令、文件搜索
5. **Session 备份** - 自动备份到云端

---

**设计完成时间**: 2026-01-11  
**预计实现时间**: 2-3 小时  
**目标版本**: v1.2.0
