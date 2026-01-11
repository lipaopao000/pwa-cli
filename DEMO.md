# PWA-CLI 快速演示

## 1. 安装验证

```bash
# 进入项目目录
cd pwa-cli

# 安装依赖
pip install -r requirements.txt

# 安装 PWA
pip install -e .

# 验证安装
pwa --version
# 输出: PWA v1.0.0
```

## 2. 启动交互式菜单

```bash
pwa
```

您将看到：

```
============================================================
  Paper Writing Assistant (PWA) v1.0.0
  Paper Writing Assistant - A modern CLI tool for academic writing
============================================================

╔══════════════════════════════════════════════════════════╗
║  Paper Writing Assistant - v1.0.0                        ║
╠══════════════════════════════════════════════════════════╣
║  1. 参考文献管理                                          ║
║  2. 引用处理                                             ║
║  3. 全文获取                                             ║
║  4. 陈述验证                                             ║
║──────────────────────────────────────────────────────────║
║  5. 工作流管理                                           ║
║  6. 配置管理                                             ║
║──────────────────────────────────────────────────────────║
║  7. 帮助与文档                                           ║
║  0. 退出                                                 ║
╚══════════════════════════════════════════════════════════╝

ℹ 请选择: 
```

## 3. 功能演示

### 3.1 参考文献匹配

1. 选择 `1` - 参考文献管理
2. 选择 `1` - 匹配参考文献
3. 输入 Markdown 文件路径
4. 选择参考文献来源（Zotero 或本地文件）
5. 查看匹配结果

**示例输出**：

```
ℹ 正在获取参考文献库...
✓ 已加载 BibLaTeX 参考文献: 150 条
ℹ 正在从 Markdown 提取参考文献...
✓ 已提取参考文献: 25 条
ℹ 正在分析匹配结果...

============================================================
匹配结果
============================================================

✓ 完美匹配: 20 条
  [1] → smith2023test (方法: doi, 分数: 1.00)
  [2] → jones2022paper (方法: jaccard_len_weighted, 分数: 0.95)
  ...

⚠ 模糊匹配: 5 条

  [21] Machine learning in medical diagnosis...
    1. ml_diagnosis_2023 (分数: 0.85)
    2. ai_healthcare_2022 (分数: 0.82)
    3. deep_learning_med_2023 (分数: 0.80)
  ...

✓ 结果已保存到: ./config-and-cache/references_match.json
```

### 3.2 引用替换

1. 选择 `2` - 引用处理
2. 选择 `1` - 替换引用格式
3. 输入 Markdown 文件路径
4. 选择匹配结果文件
5. 指定输出文件路径

**示例输出**：

```
ℹ 正在加载匹配结果...
✓ 已加载 20 条匹配记录
ℹ 正在读取 Markdown 文件...
✓ 找到 Abstract 部分，只处理之后的内容
ℹ 正在替换引用...

============================================================
替换统计
============================================================

  单个引用: 15
  多个引用: 8
  范围引用: 3
  ✓ 成功替换: 26

✓ 结果已保存到: ./paper_replaced.md
```

### 3.3 配置管理

1. 选择 `6` - 配置管理
2. 选择 `1` - 查看配置列表

**示例输出**：

```
ℹ 当前配置文件列表：

  • llm: /home/user/.config/pwa/llm_config.yaml
  • zotero: /home/user/.config/pwa/zotero_config.yaml
  • ocr: /home/user/.config/pwa/OCR_API.yaml
  • ragflow: /home/user/.config/pwa/RAGFlow.yaml

配置目录: /home/user/.config/pwa
```

### 3.4 帮助与文档

1. 选择 `7` - 帮助与文档
2. 选择 `1` - 查看用户指南

## 4. 测试运行

```bash
# 运行所有测试
./scripts/test.sh

# 运行带覆盖率的测试
./scripts/test.sh coverage

# 运行详细模式
./scripts/test.sh verbose
```

**示例输出**：

```
=========================================
Running PWA CLI Test Suite
=========================================

Running all tests...
======================== test session starts =========================
platform linux -- Python 3.11.0, pytest-7.0.0
rootdir: /home/user/pwa-cli
plugins: cov-4.0.0
collected 15 items

tests/test_config.py ............                              [ 80%]
tests/test_commands/test_references.py ...                     [100%]

========================= 15 passed in 2.34s =========================

=========================================
Test suite completed!
=========================================
```

## 5. 项目结构浏览

```bash
tree -L 2 -I '__pycache__|*.pyc|.git'
```

**输出**：

```
.
├── ARCHITECTURE.md          # 架构设计文档
├── CHANGELOG.md            # 变更日志
├── README.md               # 项目说明
├── configs/                # 默认配置
│   ├── llm_config.yaml
│   ├── zotero_config.yaml
│   ├── OCR_API.yaml
│   └── RAGFlow.yaml
├── docs/                   # 文档
│   └── user_guide.md
├── pwa/                    # 主包
│   ├── cli.py             # CLI 主程序
│   ├── config.py          # 配置管理
│   ├── core/              # 核心功能（12 个模块）
│   ├── commands/          # 命令模块
│   ├── clients/           # 外部服务客户端
│   └── ui/                # 用户界面
├── tests/                  # 测试
├── scripts/               # 脚本
│   └── test.sh
├── setup.py               # 安装配置
└── requirements.txt       # 依赖列表
```

## 6. 代码示例

### 添加新命令

```python
# pwa/commands/mycommand.py
from .base import BaseCommand
from ..ui import print_success, print_info

class MyCommand(BaseCommand):
    name = "my_command"
    description = "我的命令"
    
    def get_interactive_params(self, context):
        file_path = self.prompt_file("请输入文件路径")
        return {'file_path': file_path}
    
    def execute(self, file_path, **kwargs):
        print_info(f"处理文件: {file_path}")
        # 实现逻辑
        print_success("处理完成！")
        return {'result': 'success'}
```

### 在菜单中注册

```python
# pwa/cli.py
def _init_commands(self):
    from .commands.mycommand import MyCommand
    
    self.commands = {
        'my_command': MyCommand(self.config_manager),
    }

def _my_menu(self, context):
    cmd = self.commands['my_command']
    cmd.interactive_execute(context)
```

## 7. 常用命令

```bash
# 查看版本
pwa --version

# 启动交互式模式
pwa

# 运行测试
./scripts/test.sh

# 查看帮助
pwa --help

# 检查代码风格
flake8 pwa/

# 格式化代码
black pwa/
```

## 8. 配置示例

### LLM 配置

编辑 `~/.config/pwa/llm_config.yaml`:

```yaml
active_provider: "deepseek"

providers:
  deepseek:
    api_key: "sk-your-api-key"
    base_url: "https://api.deepseek.com"
    model: "deepseek-reasoner"
    temperature: 0.0
```

### Zotero 配置

编辑 `~/.config/pwa/zotero_config.yaml`:

```yaml
user_id: "12345678"
api_key: "your_zotero_api_key"
library_type: "user"
```

## 9. 故障排除

### 问题：找不到 pwa 命令

```bash
# 确保已安装
pip install -e .

# 检查 PATH
which pwa
```

### 问题：配置文件未找到

```bash
# 创建配置目录
mkdir -p ~/.config/pwa

# 复制默认配置
cp configs/*.yaml ~/.config/pwa/
```

### 问题：测试失败

```bash
# 安装测试依赖
pip install pytest pytest-cov

# 运行单个测试
pytest tests/test_config.py -v
```

## 10. 下一步

- 阅读 [用户指南](docs/user_guide.md) 了解详细功能
- 查看 [架构文档](ARCHITECTURE.md) 了解技术细节
- 访问 [GitHub 仓库](https://github.com/lipaopao000/pwa-cli) 获取最新版本
- 提交 [Issue](https://github.com/lipaopao000/pwa-cli/issues) 报告问题或建议

---

**祝使用愉快！** 🎉
