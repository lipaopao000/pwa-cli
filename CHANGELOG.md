# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-11

### Added

- **全文获取功能** - 使用 Mineru API 批量下载论文全文 Markdown
  - 支持从 Zotero 和 BibTeX 加载参考文献
  - 并发下载，提高效率
  - 任务状态管理和断点续传
  - 支持查看下载状态和重试失败任务
- **陈述验证功能** - 验证论文中的科学陈述
  - 集成 RAGFlow 知识库进行语义检索
  - 集成 PubMed 数据库验证
  - 多线程并发验证
  - 生成详细验证报告
  - 支持查看验证结果和导出报告
- **工作流管理** - 自动化多步骤处理
  - 完整工作流：参考文献匹配 → 引用替换 → 全文获取 → 陈述验证
  - 自定义工作流：选择特定步骤执行
  - 工作流历史记录
- **Mineru 客户端** - 封装 Mineru OCR API
  - 支持 URL 和本地文件上传
  - 批量处理支持
  - 请求重试和缓存机制
- **测试覆盖** - 新增测试模块
  - 全文获取命令测试
  - 陈述验证命令测试
  - 工作流管理测试

### Changed

- 更新版本号到 v1.1.0
- 完善 CLI 主程序，集成所有新命令
- 优化命令模块结构

### Technical Details

- 新增 `pwa.commands.fulltext` 模块（3 个命令）
- 新增 `pwa.commands.verify` 模块（3 个命令）
- 新增 `pwa.commands.workflow` 模块（3 个命令）
- 新增 `pwa.clients.mineru` 模块
- 总计新增代码约 1,500 行

## [1.0.0] - 2026-01-11

### Added

- **交互式菜单系统** - 友好的用户界面，支持多级菜单导航
- **参考文献管理**
  - 从 Markdown 文档提取参考文献
  - 与 Zotero/BibTeX 库智能匹配
  - 支持 DOI 精确匹配和标题相似度匹配
  - 输出完美匹配和模糊匹配结果
- **引用处理**
  - 将上标引用 (^1^) 替换为 Pandoc BibTeX 格式 ([@key])
  - 支持单个、多个和范围引用
  - 只处理 Abstract 之后的内容
- **配置管理系统**
  - 支持多级配置（项目级、用户级、系统级）
  - 统一的 YAML 配置文件格式
  - 配置文件自动发现和创建
- **核心功能模块**
  - 从 paper-writing-assistant 迁移所有核心功能
  - 保持向后兼容性
  - 模块化设计，易于扩展
- **命令基类**
  - 统一的命令接口
  - 交互式参数获取
  - 参数验证
  - 日志记录
- **测试框架**
  - 单元测试
  - 集成测试
  - 测试脚本
  - Pytest 配置
- **文档**
  - README.md - 项目说明和快速开始
  - ARCHITECTURE.md - 详细架构设计
  - CHANGELOG.md - 变更日志

### Technical Details

- **架构**: 模块化、插件式架构
- **Python 版本**: 3.8+
- **依赖管理**: requirements.txt 和 setup.py
- **测试框架**: pytest
- **配置格式**: YAML
- **日志系统**: Python logging

### Migration Notes

从 paper-writing-assistant 迁移到 pwa-cli:

1. 所有核心功能已迁移到 `pwa/core/` 目录
2. 原有的独立脚本已重构为命令模块
3. 配置文件格式保持不变
4. 支持原有的工作流程

## [Unreleased]

### Planned Features

- **命令行模式** - 支持非交互式命令行操作
- **插件系统** - 支持第三方插件
- **Web 界面** - 基于 Web 的图形界面
- **云同步** - 配置和数据云同步
- **更多测试** - 提高测试覆盖率到 80%+

---

[1.1.0]: https://github.com/lipaopao000/pwa-cli/releases/tag/v1.1.0
[1.0.0]: https://github.com/lipaopao000/pwa-cli/releases/tag/v1.0.0
[Unreleased]: https://github.com/lipaopao000/pwa-cli/compare/v1.1.0...HEAD
