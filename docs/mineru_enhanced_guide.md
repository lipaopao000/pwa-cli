# MinerU Enhanced Client 使用指南

## 概述

`MineruEnhancedClient` 是基于 [MinerU 官方 API v4](https://mineru.net/apiManage/docs) 文档开发的增强版客户端，提供完整的 API 功能支持和更好的错误处理。

## 主要特性

### 相比原版的改进

| 特性 | 原版 MineruClient | 增强版 MineruEnhancedClient |
|------|------------------|---------------------------|
| API 版本 | 部分 v4 | 完整 v4 |
| 参数支持 | 基础参数 | 全部参数 |
| 错误处理 | 返回 None | 抛出异常 + 错误码映射 |
| 批量 URL 上传 | ❌ | ✅ |
| 回调支持 | ❌ | ✅ |
| 页码范围 | ❌ | ✅ |
| 额外格式导出 | ❌ | ✅ |
| 等待任务完成 | ❌ | ✅ |
| 类型注解 | 部分 | 完整 |

### 新增功能

1. **完整参数支持**
   - `is_ocr`: 是否启动 OCR 功能
   - `enable_formula`: 是否开启公式识别
   - `enable_table`: 是否开启表格识别
   - `language`: 指定文档语言
   - `callback`: 回调 URL
   - `seed`: 回调签名种子
   - `extra_formats`: 额外导出格式（docx, html, latex）
   - `page_ranges`: 指定页码范围

2. **增强错误处理**
   - 自定义 `MineruAPIError` 异常
   - 完整的错误码映射
   - 清晰的错误信息

3. **便捷方法**
   - `wait_for_task()`: 等待单个任务完成
   - `wait_for_batch()`: 等待批量任务完成
   - `upload_file()`: 上传文件到预签名 URL

4. **批量 URL 上传**
   - `create_batch_url_tasks()`: 批量提交 URL 解析任务

---

## 安装

```bash
# 已包含在 pwa-cli 中，无需额外安装
```

---

## 快速开始

### 1. 创建客户端

```python
from pwa.clients.mineru_enhanced import MineruEnhancedClient

# 创建客户端
client = MineruEnhancedClient(token="your_api_token")

# 禁用缓存
client = MineruEnhancedClient(token="your_api_token", enable_cache=False)
```

### 2. 单文件解析

```python
from pwa.clients.mineru_enhanced import TaskOptions

# 基础用法
task_id = client.create_task("https://example.com/document.pdf")

# 使用选项
options = TaskOptions(
    is_ocr=True,
    enable_formula=True,
    data_id="doc123",
    extra_formats=["docx", "html"],
    page_ranges="1-10"
)
task_id = client.create_task("https://example.com/document.pdf", options)

# 查询结果
result = client.get_task_result(task_id)
print(result["state"])  # done/pending/running/failed

# 等待完成
result = client.wait_for_task(task_id)
print(result["full_zip_url"])
```

### 3. 批量文件上传解析

```python
# 1. 请求上传 URL
files = [
    {"name": "doc1.pdf", "data_id": "id1"},
    {"name": "doc2.pdf", "data_id": "id2"},
]
batch_id, upload_urls = client.request_batch_upload_urls(files)

# 2. 上传文件
for url, file_path in zip(upload_urls, ["doc1.pdf", "doc2.pdf"]):
    client.upload_file(url, file_path)

# 3. 等待结果
results = client.wait_for_batch(batch_id)
for result in results:
    if result["state"] == "done":
        print(f"{result['file_name']}: {result['full_zip_url']}")
```

### 4. 批量 URL 解析

```python
# 提交批量 URL 任务
files = [
    {"url": "https://example.com/doc1.pdf", "data_id": "id1"},
    {"url": "https://example.com/doc2.pdf", "data_id": "id2"},
]
batch_id = client.create_batch_url_tasks(files)

# 查询结果
results = client.get_batch_results(batch_id)

# 或等待完成
results = client.wait_for_batch(batch_id)
```

---

## 详细用法

### TaskOptions 配置

```python
from pwa.clients.mineru_enhanced import TaskOptions

options = TaskOptions(
    # OCR 设置
    is_ocr=False,              # 是否启动 OCR（默认 False）
    
    # 识别功能
    enable_formula=True,        # 公式识别（默认 True）
    enable_table=True,          # 表格识别（默认 True）
    
    # 语言设置
    language="ch",              # 文档语言（默认 "ch"）
                                # 其他选项：en, ja, korean 等
                                # 完整列表见 PaddleOCR 文档
    
    # 业务标识
    data_id="my_doc_123",       # 数据 ID（可选）
    
    # 回调设置
    callback="https://your.domain/callback",  # 回调 URL（可选）
    seed="random_string",       # 回调签名种子（可选）
    
    # 导出格式
    extra_formats=["docx", "html", "latex"],  # 额外格式（可选）
                                               # markdown 和 json 默认导出
    
    # 页码范围
    page_ranges="1-10,15,20-30",  # 页码范围（可选）
                                   # 格式：逗号分隔，支持范围和单页
    
    # 模型版本
    model_version="vlm"          # 模型版本（默认 "vlm"）
                                 # 可选：pipeline, vlm
)
```

### 错误处理

```python
from pwa.clients.mineru_enhanced import MineruAPIError

try:
    task_id = client.create_task("https://example.com/large_file.pdf")
except MineruAPIError as e:
    print(f"错误码: {e.code}")
    print(f"错误信息: {e.message}")
    
    # 根据错误码处理
    if e.code == "-60005":
        print("文件太大，请压缩后重试")
    elif e.code == "A0202":
        print("Token 错误，请检查配置")
```

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|-------|------|---------|
| A0202 | Token 错误 | 检查 Token 是否正确，是否有 Bearer 前缀 |
| A0211 | Token 过期 | 更换新 Token |
| -60005 | 文件大小超出限制 | 文件不超过 200MB |
| -60006 | 文件页数超过限制 | 页数不超过 600 页 |
| -60018 | 每日解析任务数量已达上限 | 明日再来 |

完整错误码列表见 `ERROR_CODES` 常量。

### 回调机制

```python
# 设置回调
options = TaskOptions(
    callback="https://your.domain/callback",
    seed="your_random_seed"
)
task_id = client.create_task(url, options)

# 回调接口实现（示例）
from flask import Flask, request
import hashlib

app = Flask(__name__)

@app.route('/callback', methods=['POST'])
def callback():
    data = request.json
    checksum = data['checksum']
    content = data['content']
    
    # 验证签名
    uid = "your_uid"  # 从 MinerU 个人中心获取
    seed = "your_random_seed"
    expected = hashlib.sha256(f"{uid}{seed}{content}".encode()).hexdigest()
    
    if checksum == expected:
        # 处理结果
        import json
        result = json.loads(content)
        print(result)
        return "OK", 200
    else:
        return "Invalid checksum", 400
```

### 高级用法

#### 1. 自定义配置

```python
client = MineruEnhancedClient(
    token="your_token",
    base_url="https://mineru.net/api/v4",  # 自定义 API 地址
    timeout=60,                             # 请求超时（秒）
    max_retries=5,                          # 最大重试次数
    backoff_factor=1.0,                     # 重试退避因子
    cache_ttl=600,                          # 缓存 TTL（秒）
)
```

#### 2. 批量处理进度监控

```python
import time

batch_id = client.create_batch_url_tasks(files)

while True:
    results = client.get_batch_results(batch_id)
    
    # 统计进度
    done = sum(1 for r in results if r["state"] == "done")
    running = sum(1 for r in results if r["state"] == "running")
    failed = sum(1 for r in results if r["state"] == "failed")
    
    print(f"完成: {done}, 运行中: {running}, 失败: {failed}")
    
    if done + failed == len(results):
        break
    
    time.sleep(10)
```

#### 3. 下载并解压结果

```python
import zipfile
import io

result = client.wait_for_task(task_id)
zip_content = client.download_result(result["full_zip_url"])

# 解压到内存
with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
    # 列出文件
    for name in zf.namelist():
        print(name)
    
    # 读取 markdown
    if "auto/demo.md" in zf.namelist():
        markdown = zf.read("auto/demo.md").decode("utf-8")
        print(markdown)

# 或保存到磁盘
with open("result.zip", "wb") as f:
    f.write(zip_content)
```

---

## API 参考

### MineruEnhancedClient

#### 初始化

```python
MineruEnhancedClient(
    token: str,
    enable_cache: bool = True,
    **kwargs
)
```

#### 单文件解析

- `create_task(url, options=None) -> str`
  - 创建解析任务
  - 返回：task_id

- `get_task_result(task_id) -> Dict`
  - 获取任务结果
  - 返回：结果字典

- `wait_for_task(task_id, poll_interval=5, max_wait=600) -> Dict`
  - 等待任务完成
  - 返回：最终结果

#### 批量文件上传

- `request_batch_upload_urls(files, options=None) -> Tuple[str, List[str]]`
  - 请求上传 URL
  - 返回：(batch_id, upload_urls)

- `upload_file(upload_url, file_path) -> bool`
  - 上传文件
  - 返回：是否成功

#### 批量 URL 解析

- `create_batch_url_tasks(files, options=None) -> str`
  - 创建批量任务
  - 返回：batch_id

- `get_batch_results(batch_id) -> List[Dict]`
  - 获取批量结果
  - 返回：结果列表

- `wait_for_batch(batch_id, poll_interval=10, max_wait=1800) -> List[Dict]`
  - 等待批量完成
  - 返回：最终结果列表

#### 辅助方法

- `download_result(download_url) -> bytes`
  - 下载结果文件
  - 返回：ZIP 文件字节

- `get_error_message(code) -> str`
  - 获取错误信息
  - 返回：错误描述

---

## 最佳实践

### 1. 使用 data_id 追踪任务

```python
options = TaskOptions(data_id=f"user_{user_id}_doc_{doc_id}")
task_id = client.create_task(url, options)

# 后续可通过 data_id 关联业务数据
result = client.get_task_result(task_id)
print(result["data_id"])  # user_123_doc_456
```

### 2. 合理设置页码范围

```python
# 只解析前 10 页
options = TaskOptions(page_ranges="1-10")

# 跳过封面，解析正文
options = TaskOptions(page_ranges="2--1")  # 第2页到倒数第1页

# 解析特定章节
options = TaskOptions(page_ranges="5-20,30-50")
```

### 3. 选择合适的导出格式

```python
# 学术论文：需要公式和表格
options = TaskOptions(
    enable_formula=True,
    enable_table=True,
    extra_formats=["latex"]
)

# 普通文档：需要编辑
options = TaskOptions(
    extra_formats=["docx"]
)

# 网页展示
options = TaskOptions(
    extra_formats=["html"]
)
```

### 4. 批量处理优化

```python
# 使用批量 API 而非循环调用单文件 API
# ❌ 不推荐
for url in urls:
    task_id = client.create_task(url)

# ✅ 推荐
files = [{"url": url, "data_id": f"doc_{i}"} for i, url in enumerate(urls)]
batch_id = client.create_batch_url_tasks(files)
```

---

## 注意事项

1. **文件限制**
   - 单个文件不超过 200MB
   - 页数不超过 600 页
   - 批量上传不超过 200 个文件

2. **配额限制**
   - 每个账户每天 2000 页高优先级解析
   - 超过 2000 页将降低优先级

3. **网络限制**
   - GitHub、AWS 等国外 URL 可能超时
   - 建议使用国内 CDN

4. **文件保存期限**
   - 解析结果保存 30 天
   - 建议及时下载

5. **回调要求**
   - 必须支持 POST 方法
   - 使用 UTF-8 编码
   - Content-Type: application/json
   - 返回 200 表示成功

---

## 迁移指南

### 从原版 MineruClient 迁移

```python
# 原版
from pwa.clients.mineru import MineruClient
client = MineruClient(token="your_token")
task_id = client.create_task("https://example.com/doc.pdf")
result = client.get_task_result(task_id)

# 增强版
from pwa.clients.mineru_enhanced import MineruEnhancedClient, TaskOptions
client = MineruEnhancedClient(token="your_token")

# 基础用法相同
task_id = client.create_task("https://example.com/doc.pdf")
result = client.get_task_result(task_id)

# 但现在可以使用更多功能
options = TaskOptions(
    enable_formula=True,
    extra_formats=["docx"],
    page_ranges="1-50"
)
task_id = client.create_task("https://example.com/doc.pdf", options)

# 并且可以等待完成
result = client.wait_for_task(task_id)
```

### 错误处理变化

```python
# 原版：返回 None
result = client.get_task_result(task_id)
if result is None:
    print("Error occurred")

# 增强版：抛出异常
try:
    result = client.get_task_result(task_id)
except MineruAPIError as e:
    print(f"Error: {e.code} - {e.message}")
```

---

## 故障排除

### 问题：Token 错误

```python
# 检查 Token 格式
# ❌ 错误
client = MineruEnhancedClient(token="your_token")

# ✅ 正确（如果需要 Bearer 前缀，客户端会自动添加）
client = MineruEnhancedClient(token="your_token")
```

### 问题：文件太大

```python
# 使用页码范围分批处理
for start in range(1, 600, 100):
    end = min(start + 99, 600)
    options = TaskOptions(page_ranges=f"{start}-{end}")
    task_id = client.create_task(url, options)
```

### 问题：任务超时

```python
# 增加等待时间
result = client.wait_for_task(
    task_id,
    poll_interval=10,  # 每 10 秒查询一次
    max_wait=1800      # 最多等待 30 分钟
)
```

---

## 更多资源

- [MinerU 官方文档](https://mineru.net/apiManage/docs)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [输出格式说明](https://opendatalab.github.io/MinerU/reference/output_files/)
- [PaddleOCR 多语言支持](https://www.paddleocr.ai/latest/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html)
