# MarkItDown 集成文档

## 概述

pwa-cli 集成了自定义的 [markitdown](https://github.com/lipaopao000/markitdown) 库，用于将各种文档格式转换为 Markdown 格式。这个库支持多种文档类型，包括 Word 文档、PDF、PowerPoint 演示文稿、Excel 表格等。

## 安装

markitdown 库通过自动化脚本从 GitHub 克隆到项目目录，确保始终使用最新版本。

### 首次安装

运行安装脚本：

```bash
./scripts/install_markitdown.sh
```

该脚本会：
1. 克隆 markitdown 仓库到 `.markitdown/` 目录
2. 安装所有必需的依赖
3. 验证安装是否成功

### 更新

要更新到最新版本，只需重新运行安装脚本：

```bash
./scripts/install_markitdown.sh
```

脚本会自动拉取最新的代码。

## 支持的文件格式

markitdown 支持以下文件格式：

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| Word 文档 | `.docx` | Microsoft Word 文档 |
| PDF 文档 | `.pdf` | 便携式文档格式 |
| PowerPoint | `.pptx` | Microsoft PowerPoint 演示文稿 |
| Excel | `.xlsx` | Microsoft Excel 表格 |
| HTML | `.html` | 网页文件 |
| 文本 | `.txt` | 纯文本文件 |
| CSV | `.csv` | 逗号分隔值文件 |
| JSON | `.json` | JSON 数据文件 |
| XML | `.xml` | XML 数据文件 |

## 使用方法

### 基本用法

```python
from pwa.clients import MarkItDownClient

# 创建客户端实例
client = MarkItDownClient()

# 转换文件并获取 Markdown 字符串
markdown_content = client.convert_file('path/to/document.docx')
print(markdown_content)
```

### 转换并保存到文件

```python
from pwa.clients import MarkItDownClient

client = MarkItDownClient()

# 转换并保存到指定文件
output_path = client.convert_to_file(
    'path/to/document.docx',
    'path/to/output.md'
)
print(f"已保存到: {output_path}")

# 如果不指定输出路径，会自动使用输入文件名加 .md 扩展名
output_path = client.convert_to_file('path/to/document.docx')
# 输出: path/to/document.md
```

### 专门转换 DOCX 文件

```python
from pwa.clients import MarkItDownClient

client = MarkItDownClient()

# 转换 DOCX 文件
markdown_content = client.convert_docx('path/to/document.docx')

# 转换 DOCX 并保存
output_path = client.convert_docx_to_file(
    'path/to/document.docx',
    'path/to/output.md'
)
```

### 便捷函数

对于快速转换，可以使用便捷函数：

```python
from pwa.clients import convert_to_markdown

# 直接转换文件
markdown_content = convert_to_markdown('path/to/document.docx')
```

### 检查文件格式支持

```python
from pwa.clients import MarkItDownClient

client = MarkItDownClient()

# 获取所有支持的格式
formats = client.get_supported_formats()
print(f"支持的格式: {formats}")

# 检查特定文件是否支持
if client.is_supported('document.docx'):
    print("支持此文件格式")
else:
    print("不支持此文件格式")
```

## API 参考

### MarkItDownClient

#### `__init__()`

创建 MarkItDown 客户端实例。

#### `convert_file(file_path: Union[str, Path]) -> str`

转换文档文件为 Markdown 字符串。

**参数：**
- `file_path`: 文档文件路径

**返回：**
- Markdown 内容字符串

**异常：**
- `FileNotFoundError`: 文件不存在
- `RuntimeError`: 转换失败

#### `convert_to_file(input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path`

转换文档文件为 Markdown 并保存到文件。

**参数：**
- `input_path`: 输入文档文件路径
- `output_path`: 输出 Markdown 文件路径（可选，默认使用输入文件名加 .md 扩展名）

**返回：**
- 输出文件的 Path 对象

**异常：**
- `FileNotFoundError`: 输入文件不存在
- `RuntimeError`: 转换失败

#### `convert_docx(docx_path: Union[str, Path]) -> str`

转换 DOCX 文件为 Markdown 字符串。

**参数：**
- `docx_path`: DOCX 文件路径

**返回：**
- Markdown 内容字符串

**异常：**
- `FileNotFoundError`: 文件不存在
- `ValueError`: 文件不是 .docx 格式
- `RuntimeError`: 转换失败

#### `convert_docx_to_file(docx_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path`

转换 DOCX 文件为 Markdown 并保存到文件。

**参数：**
- `docx_path`: DOCX 文件路径
- `output_path`: 输出 Markdown 文件路径（可选）

**返回：**
- 输出文件的 Path 对象

**异常：**
- `FileNotFoundError`: 输入文件不存在
- `RuntimeError`: 转换失败

#### `get_supported_formats() -> list[str]`

获取支持的文件格式列表。

**返回：**
- 支持的文件扩展名列表

#### `is_supported(file_path: Union[str, Path]) -> bool`

检查文件格式是否支持。

**参数：**
- `file_path`: 文件路径

**返回：**
- 如果支持返回 True，否则返回 False

### 便捷函数

#### `convert_to_markdown(file_path: Union[str, Path]) -> str`

快速转换文档为 Markdown 的便捷函数。

**参数：**
- `file_path`: 文档文件路径

**返回：**
- Markdown 内容字符串

## 实现细节

### 路径管理

markitdown 库不通过 pip 安装，而是克隆到项目的 `.markitdown/` 目录中。在运行时，客户端会自动将 markitdown 源代码路径添加到 `sys.path`，确保可以导入。

```python
# 自动添加到 sys.path
project_root / ".markitdown" / "packages" / "markitdown" / "src"
```

### 依赖管理

markitdown 需要以下依赖：
- `markdownify`: HTML 到 Markdown 转换
- `pdfplumber`: PDF 处理
- `pandas`: 数据处理
- `openpyxl`: Excel 文件处理
- `python-pptx`: PowerPoint 文件处理
- `youtube-transcript-api`: YouTube 字幕处理
- `magika`: 文件类型检测

这些依赖会在运行安装脚本时自动安装。

### 错误处理

客户端提供了完善的错误处理：
- 文件不存在时抛出 `FileNotFoundError`
- 转换失败时抛出 `RuntimeError` 并包含详细错误信息
- 格式不支持时抛出 `ValueError`

### 日志记录

客户端使用 Python 的 `logging` 模块记录调试信息和错误：

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)
```

## 与 pwa-cli 的集成

markitdown 客户端已集成到 pwa-cli 的客户端模块中，可以在任何需要文档转换的地方使用：

```python
from pwa.clients import MarkItDownClient

# 在命令中使用
class MyCommand(BaseCommand):
    def execute(self):
        client = MarkItDownClient()
        markdown = client.convert_file(self.input_file)
        # 处理 markdown 内容
```

## 故障排除

### 导入错误

如果遇到导入错误：

```
RuntimeError: markitdown source not found at ...
```

运行安装脚本：

```bash
./scripts/install_markitdown.sh
```

### 依赖缺失

如果遇到依赖缺失错误：

```
ImportError: No module named 'markdownify'
```

重新运行安装脚本，它会自动安装所有依赖：

```bash
./scripts/install_markitdown.sh
```

### 转换失败

如果转换失败，检查：
1. 文件是否存在且可读
2. 文件格式是否支持
3. 文件是否损坏

可以启用调试日志查看详细信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 最佳实践

1. **批量转换**：对于大量文件，考虑使用并行处理
2. **错误处理**：始终使用 try-except 捕获可能的异常
3. **路径处理**：使用 `pathlib.Path` 处理文件路径
4. **内存管理**：对于大文件，考虑流式处理或分块处理
5. **版本更新**：定期运行安装脚本更新到最新版本

## 示例：批量转换

```python
from pathlib import Path
from pwa.clients import MarkItDownClient

def batch_convert(input_dir: Path, output_dir: Path):
    """批量转换目录中的所有文档"""
    client = MarkItDownClient()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in input_dir.iterdir():
        if client.is_supported(file_path):
            try:
                output_path = output_dir / f"{file_path.stem}.md"
                client.convert_to_file(file_path, output_path)
                print(f"✅ 已转换: {file_path.name}")
            except Exception as e:
                print(f"❌ 转换失败 {file_path.name}: {e}")

# 使用示例
batch_convert(Path("documents"), Path("markdown_output"))
```

## 相关链接

- [markitdown GitHub 仓库](https://github.com/lipaopao000/markitdown)
- [pwa-cli 项目主页](https://github.com/lipaopao000/pwa-cli)
