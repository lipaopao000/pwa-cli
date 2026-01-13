# Mineru API 客户端使用指南

`MineruClient` 是基于 [MinerU 官方 API v4](https://mineru.net/apiManage/docs) 文档开发的客户端，提供完整的 API 功能支持和更好的错误处理。

## 核心特性

- **完整 v4 支持**：支持单文件解析、批量文件解析、文件上传和下载。
- **自动重试机制**：内置指数退避重试，处理网络波动。
- **内置缓存**：支持 GET 请求缓存，减少重复 API 调用。
- **类型提示**：提供完整的数据类和类型注解，方便 IDE 集成。
- **错误映射**：自动转换 API 错误代码为易读的中文字符串。

## 快速开始

### 初始化

```python
from pwa.clients.mineru import MineruClient

# 创建客户端
client = MineruClient(token="your_api_token")

# 禁用缓存
client = MineruClient(token="your_api_token", enable_cache=False)
```

### 单文件解析

```python
from pwa.clients.mineru import TaskOptions

# 配置解析选项
options = TaskOptions(is_ocr=True, language="ch")

# 创建任务
task_id = client.create_task(
    url="https://example.com/paper.pdf",
    options=options
)

# 等待并获取结果
result = client.wait_for_task(task_id)
print(f"解析成功，下载地址: {result['full_zip_url']}")
```

### 异常处理

```python
from pwa.clients.mineru import MineruAPIError

try:
    task_id = client.create_task("...")
except MineruAPIError as e:
    print(f"API 错误: {e.code}, 消息: {e.message}")
```

## 配置参考

### MineruClient

```python
MineruClient(
    token: str,           # API Token
    enable_cache: bool,    # 是否启用缓存 (默认 True)
    base_url: str,        # API 基础地址
    timeout: int,         # 超时时间 (默认 30s)
    max_retries: int      # 最大重试次数 (默认 3次)
)
```

## 与旧版区别

- **统一性**：所有方法名采用蛇形命名法（snake_case）。
- **健壮性**：增加会话池管理和重试逻辑。
- **易用性**：提供 `wait_for_task` 等便捷方法。
