# Changelog

All notable changes to PWA-CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] - 2026-01-11

### Changed

#### 切换到 InquirerPy 🎯
- **替换 prompt_toolkit** - 使用 InquirerPy 替代 prompt_toolkit 的 radiolist_dialog
- **更稳定的交互** - InquirerPy 提供更可靠的箭头键导航
- **更好的用户体验** - 更清晰的提示信息和分隔符支持
- **优雅降级** - 保持传统菜单作为降级方案

### Dependencies
- **替换**: `prompt_toolkit>=3.0.0` → `InquirerPy>=0.3.4`

### Fixed
- 修复 prompt_toolkit radiolist_dialog 的响应问题
- 改进菜单显示和交互体验

---

## [1.2.1] - 2026-01-11

### Fixed

#### 交互式菜单修复 🐛
- **菜单项显示数字** - 修复菜单项前面没有数字的问题
- **Enter 键响应** - 改进 radiolist_dialog 的使用，确保 Enter 键正常工作
- **错误处理增强** - 添加异常捕获，prompt_toolkit 出错时自动降级到传统菜单
- **降级模式改进** - 传统菜单也正确显示数字和描述
- **用户反馈** - 无效选择时给出明确提示

### Changed
- 重写 `pwa/ui/interactive.py` 改进菜单显示和错误处理
- 菜单选项格式：`"1. 选项名称 - 描述"`
- 增强降级模式的用户体验

### Tests
- 新增菜单测试脚本 `test_menu.py`
- 新增降级模式测试 `test_fallback_menu.py`
- 验证菜单显示和选择功能

---

## [1.2.0] - 2026-01-11

### Added

#### 箭头键导航 🎯
- **交互式菜单系统** - 使用 `prompt_toolkit` 实现箭头键导航
- **上下箭头键选择** - 使用 ↑/↓ 键在菜单中导航
- **Enter 确认** - 按 Enter 键确认选择
- **数字快速跳转** - 保留原有的数字输入功能
- **优雅降级** - 如果 `prompt_toolkit` 不可用，自动降级到传统菜单

#### Session 管理 📝
- **自动 Session 创建** - 启动时自动创建或恢复 Session
- **Session 持久化** - Session 数据保存到 `~/.config/pwa/sessions/`
- **操作历史记录** - 记录每个命令的执行历史
- **上下文保持** - 记住最后使用的文件和配置
- **Session 管理命令**:
  - `session_view` - 查看当前 Session 详情
  - `session_history` - 查看操作历史
  - `session_list` - 列出所有 Session
  - `session_resume` - 恢复历史 Session
  - `session_cleanup` - 清理旧 Session
  - `session_export` - 导出 Session
  - `session_stats` - 查看 Session 统计

#### 新增模块
- `pwa/ui/interactive.py` - 交互式菜单组件
- `pwa/session/models.py` - Session 数据模型
- `pwa/session/storage.py` - Session 存储
- `pwa/session/manager.py` - Session 管理器
- `pwa/commands/session.py` - Session 管理命令

### Changed
- **CLI 主程序重构** - 完全重写 `pwa/cli.py` 使用交互式菜单
- **菜单系统升级** - 从传统菜单升级到交互式菜单
- **用户体验提升** - 更直观的操作方式

### Dependencies
- **新增**: `prompt_toolkit>=3.0.0` - 交互式 CLI 库

### Tests
- 新增 Session 模型测试 (8 个测试用例)
- 所有测试通过 ✅

### Documentation
- 新增 `SESSION_AND_NAVIGATION_DESIGN.md` - 设计文档
- 更新 README.md 添加新功能说明

---

## [1.1.1] - 2026-01-11

### Fixed

#### Verify 功能完整重构 🚨
- **核心模块完整** - 复制 8 个核心模块，66,061 行代码
- **LangGraph 工作流** - 实现完整的状态机工作流
- **阶梯式验证** - Abstract → Local RAG → Fulltext → Global
- **结构化输出** - 使用 Pydantic 模型评估
- **参考文献集成** - Journal IF、DOI 等元数据
- **RAGFlow 交互** - 数据集选择和文档同步
- **Markdown 注释** - 验证结果注释功能
- **审计历史** - 完整的验证追踪
- **导入路径修复** - 修复所有核心模块导入

### Added
- 新增核心模块:
  - `statement_verifier.py` (15,916 行)
  - `statement_verifier_utils.py` (3,756 行)
  - `configuration.py` (1,453 行)
  - `state.py` (1,605 行)
  - `schemas.py` (1,337 行)
  - `prompts.py` (2,423 行)
  - `base_agent.py` (1,747 行)
  - `citation_agent.py` (37,824 行)

### Dependencies
- **新增**: `langchain>=0.1.0`
- **新增**: `langchain-core>=0.1.0`
- **新增**: `langchain-openai>=0.0.5`
- **新增**: `langgraph>=0.0.20`
- **新增**: `langsmith>=0.0.70`
- **新增**: `pydantic>=2.0.0`

### Tests
- 更新 verify 测试 (15 个测试用例)
- 所有测试通过 ✅

### Documentation
- 新增 `VERIFY_ISSUES_ANALYSIS.md` - 问题分析
- 新增 `RELEASE_v1.1.1.md` - 发布说明
- 新增 `VERIFY_FIX_SUMMARY.md` - 修复总结

---

## [1.1.0] - 2026-01-11

### Added

#### 全文获取功能 📥
- **Mineru API 集成** - 使用 Mineru OCR API 下载论文全文
- **批量下载** - 支持从 Zotero 和 BibTeX 批量下载
- **并发下载** - 提高下载效率
- **任务管理** - 状态管理和断点续传
- **命令**:
  - `fulltext_download` - 下载论文全文
  - `fulltext_status` - 查看下载状态
  - `fulltext_retry` - 重试失败任务

#### 陈述验证功能 ✅
- **RAGFlow 集成** - 语义检索知识库
- **PubMed 集成** - 验证科学陈述
- **多线程验证** - 并发验证提高效率
- **详细报告** - 生成验证报告
- **命令**:
  - `verify_statements` - 验证科学陈述
  - `verify_view_results` - 查看验证结果
  - `verify_export_report` - 导出验证报告

#### 工作流管理 🔄
- **完整工作流** - 一键运行完整流程
- **自定义工作流** - 选择步骤运行
- **历史记录** - 查看工作流历史
- **命令**:
  - `workflow_run_full` - 运行完整工作流
  - `workflow_run_custom` - 运行自定义工作流
  - `workflow_history` - 查看工作流历史

### Changed
- 更新 CLI 主程序集成新命令
- 更新菜单系统添加新功能模块

### Tests
- 新增全文获取测试
- 新增陈述验证测试

### Documentation
- 更新 README.md 添加新功能
- 新增 `RELEASE_v1.1.0.md` - 发布说明

---

## [1.0.0] - 2026-01-11

### Added
- 初始版本发布
- **参考文献管理** - 提取、匹配、导出
- **引用处理** - 格式替换
- **配置管理** - 多级配置系统
- **交互式菜单** - 美观的菜单界面
- **核心模块** - 12 个核心功能模块
- **测试框架** - 完整的测试覆盖

### Documentation
- README.md - 项目说明
- ARCHITECTURE.md - 架构文档
- CHANGELOG.md - 变更日志
- docs/user_guide.md - 用户指南

---

## Version History

- **v1.2.1** (2026-01-11) - 交互式菜单修复
- **v1.2.0** (2026-01-11) - 箭头键导航 + Session 管理
- **v1.1.1** (2026-01-11) - Verify 功能修复
- **v1.1.0** (2026-01-11) - 完整功能版本
- **v1.0.0** (2026-01-11) - 初始版本

---

**Note**: This project follows [Semantic Versioning](https://semver.org/).

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes
