#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示脚本：运行 ZoteroClient 集成测试并显示 API 输出

这个脚本展示了如何运行集成测试并查看 Zotero API 的实际响应内容。
"""

import subprocess
import sys
import os

def run_integration_tests():
    """运行集成测试并显示输出。"""
    print("=" * 60)
    print("ZoteroClient 集成测试演示")
    print("=" * 60)
    print()

    # 检查当前工作目录
    cwd = os.getcwd()
    print(f"📁 当前工作目录: {cwd}")

    # 检查 Zotero 是否运行
    print("\n🔍 检查 Zotero 状态...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:23119/better-bibtex/cayw?probe=true", timeout=5)
        if response.text == "ready":
            print("✅ Zotero 正在运行")
            zotero_running = True
        else:
            print("❌ Zotero 未运行或 Better BibTeX 未启用")
            zotero_running = False
    except:
        print("❌ Zotero 未运行或 Better BibTeX 未启用")
        zotero_running = False

    print()
    print("🚀 运行集成测试...")
    print("-" * 40)

    if zotero_running:
        # Zotero 运行时，使用 --runxfail 运行集成测试
        cmd = [sys.executable, "-m", "pytest",
               "tests/test_clients/test_zotero_client_integration.py::TestZoteroClientIntegration::test_zotero_connection",
               "tests/test_clients/test_zotero_client_integration.py::TestZoteroClientIntegration::test_search_functionality",
               "tests/test_clients/test_zotero_client_integration.py::TestZoteroClientIntegration::test_citekey_operations",
               "tests/test_clients/test_zotero_client_integration.py::TestZoteroClientIntegration::test_bibtex_export",
               "-v", "-s", "--runxfail"]
    else:
        # Zotero 未运行时，显示跳过信息
        cmd = [sys.executable, "-m", "pytest",
               "tests/test_clients/test_zotero_client_integration.py::TestZoteroClientIntegration::test_zotero_connection",
               "-v", "-s"]

    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=False, text=True)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 运行测试时出错: {e}")
        return False

def show_usage_info():
    """显示使用说明。"""
    print()
    print("=" * 60)
    print("使用说明")
    print("=" * 60)
    print("""
📋 前置条件：
1. 安装并运行 Zotero 应用程序
2. 安装 Better BibTeX 插件 (版本 >= 6.7.0)
3. 确保 Zotero 库中有一些参考文献

🔧 运行完整测试套件：
# 运行单元测试（不需要 Zotero）
pytest tests/test_clients/test_zotero_client.py -v

# 运行集成测试（需要 Zotero + Better BibTeX）
pytest tests/test_clients/test_zotero_client_integration.py -m integration --runxfail -v -s

📁 测试文件位置：
- 单元测试: tests/test_clients/test_zotero_client.py
- 集成测试: tests/test_clients/test_zotero_client_integration.py
- 说明文档: tests/test_clients/README_Zotero_Integration_Tests.md

🎯 测试覆盖范围：
- ✅ Zotero API 连接测试
- ✅ 搜索功能（空搜索、字符串搜索、高级搜索）
- ✅ Citekey 操作（获取项目、附件、笔记）
- ✅ BibTeX/BibLaTeX 导出
- ✅ 数据结构验证
- ✅ 错误处理

💡 提示：
- 集成测试默认跳过，除非使用 --runxfail 标志
- 测试会使用您 Zotero 库中的实际数据
- 不会修改或删除任何现有数据
    """)

if __name__ == "__main__":
    success = run_integration_tests()
    show_usage_info()

    print()
    if success:
        print("✅ 演示完成！")
    else:
        print("❌ 演示过程中出现错误")

    sys.exit(0 if success else 1)
