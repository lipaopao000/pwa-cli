# 贡献指南

感谢您对 PWA-CLI 项目的关注！我们欢迎各种形式的贡献。

## 开发环境设置

### 1. Fork 并克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/pwa-cli.git
cd pwa-cli
```

### 2. 安装开发依赖

```bash
# 使用 pip
pip install -e .[dev]

# 或使用 Makefile
make install-dev
```

### 3. 配置开发工具

项目使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查
- **pytest**: 测试框架

## 开发流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 编写代码

- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写文档字符串
- 保持函数简洁（单一职责原则）

### 3. 格式化代码

```bash
# 使用 Makefile
make format

# 或手动运行
isort pwa/ tests/
black pwa/ tests/ --line-length=100
```

### 4. 运行检查

```bash
# 使用 Makefile
make lint

# 或手动运行
flake8 pwa/ tests/ --max-line-length=100
mypy pwa/ --ignore-missing-imports
```

### 5. 编写测试

- 为新功能编写单元测试
- 确保测试覆盖率不降低
- 测试文件放在 `tests/` 目录下

```bash
# 运行测试
make test

# 运行测试并查看覆盖率
make test-cov
```

### 6. 提交代码

```bash
git add .
git commit -m "feat: add new feature"
```

#### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建或辅助工具变动

示例：
```
feat: add citation verification command
fix: resolve reference matching bug
docs: update installation guide
```

### 7. 推送并创建 Pull Request

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## Pull Request 指南

### PR 标题

使用清晰的标题描述变更：
```
feat: Add support for BibTeX export
fix: Fix Zotero API authentication issue
```

### PR 描述

包含以下内容：

1. **变更内容**: 简要说明做了什么
2. **动机**: 为什么需要这个变更
3. **测试**: 如何测试这个变更
4. **截图**: 如果是 UI 变更，提供截图
5. **相关 Issue**: 引用相关的 Issue 编号

### PR 检查清单

- [ ] 代码已格式化（black + isort）
- [ ] 通过所有 lint 检查（flake8 + mypy）
- [ ] 添加了测试
- [ ] 测试全部通过
- [ ] 更新了文档
- [ ] 提交信息符合规范

## 代码风格指南

### Python 代码风格

- 使用 Black 默认配置（行长度 100）
- 使用类型注解
- 编写完整的文档字符串

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0.0 and 1.0

    Raises:
        ValueError: If either text is empty
    """
    if not text1 or not text2:
        raise ValueError("Text cannot be empty")
    
    # Implementation here
    return 0.0
```

### 导入顺序

使用 isort 自动排序：

1. 标准库导入
2. 第三方库导入
3. 本地应用导入

```python
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel

from .config import ConfigManager
from .exceptions import ConfigurationError
```

### 命名规范

- **类名**: PascalCase (例如: `ConfigManager`)
- **函数名**: snake_case (例如: `load_config`)
- **常量**: UPPER_SNAKE_CASE (例如: `DEFAULT_TIMEOUT`)
- **私有方法**: 前缀下划线 (例如: `_validate_config`)

## 测试指南

### 测试结构

```
tests/
├── test_config.py          # 配置管理测试
├── test_commands/          # 命令测试
│   ├── test_references.py
│   └── test_citations.py
└── test_clients/           # 客户端测试
    ├── test_zotero.py
    └── test_mineru.py
```

### 测试示例

```python
import pytest
from pwa.config import ConfigManager
from pwa.exceptions import ConfigurationError


def test_load_valid_config(tmp_path):
    """Test loading a valid configuration file."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text("key: value\n")
    
    manager = ConfigManager(config_dir=tmp_path)
    config = manager.load_config("test_config")
    
    assert config is not None
    assert config["key"] == "value"


def test_load_invalid_config_raises_error(tmp_path):
    """Test that loading invalid config raises error."""
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: yaml: content:\n")
    
    manager = ConfigManager(config_dir=tmp_path)
    
    with pytest.raises(ConfigurationError):
        manager.load_config("invalid", validate=True)
```

## 添加新功能

### 添加新命令

1. 在 `pwa/commands/` 创建新模块
2. 继承 `BaseCommand` 类
3. 实现必要的方法
4. 在 `pwa/cli.py` 中注册命令
5. 添加测试

示例：

```python
# pwa/commands/my_command.py
from .base import BaseCommand


class MyCommand(BaseCommand):
    name = "my_command"
    description = "My new command"
    
    def execute(self, **kwargs):
        # Implementation
        pass
    
    def validate(self, **kwargs) -> bool:
        # Validation logic
        return True
```

### 添加新客户端

1. 在 `pwa/clients/` 创建新模块
2. 实现客户端类
3. 处理错误和重试
4. 添加测试

## 报告 Bug

使用 [GitHub Issues](https://github.com/lipaopao000/pwa-cli/issues) 报告 bug。

### Bug 报告应包含：

1. **描述**: 简要描述问题
2. **重现步骤**: 详细的重现步骤
3. **期望行为**: 应该发生什么
4. **实际行为**: 实际发生了什么
5. **环境信息**: 
   - PWA-CLI 版本
   - Python 版本
   - 操作系统
6. **日志**: 相关的错误日志

## 提出新功能

使用 [GitHub Issues](https://github.com/lipaopao000/pwa-cli/issues) 提出功能请求。

### 功能请求应包含：

1. **问题描述**: 当前的痛点
2. **建议方案**: 你的解决方案
3. **替代方案**: 其他可能的方案
4. **使用场景**: 谁会使用这个功能

## 获取帮助

- 查看 [文档](https://github.com/lipaopao000/pwa-cli/blob/main/README.md)
- 搜索 [已有 Issues](https://github.com/lipaopao000/pwa-cli/issues)
- 创建新 Issue 提问

## 许可证

贡献的代码将采用与项目相同的 [MIT License](LICENSE)。

---

再次感谢您的贡献！🎉
