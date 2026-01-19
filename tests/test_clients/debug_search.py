#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：检查 Zotero 搜索 API 的行为
"""

import json
from pwa.clients.zotero import ZoteroClient

def debug_search():
    """调试搜索功能"""
    print("🔍 调试 Zotero 搜索 API")
    print("=" * 50)

    # 创建客户端
    client = ZoteroClient()

    if not client.is_zotero_running():
        print("❌ Zotero 未运行")
        return

    print("✅ Zotero 正在运行")

    # 测试不同的搜索参数
    test_cases = [
        ("空字符串", ""),
        ("字符串 'test'", "test"),
        ("字符串 'zotero'", "zotero"),
        ("高级搜索 - 标题包含 'test'", [['title', 'contains', 'test']]),
        ("高级搜索 - 无效字段", [['invalid_field', 'contains', 'test']]),
    ]

    for name, query in test_cases:
        print(f"\n🔎 测试: {name}")
        print(f"查询参数: {query}")
        try:
            results = client.search(query)
            print(f"结果数量: {len(results)}")

            if results:
                print("前3个结果:")
                for i, item in enumerate(results[:3]):
                    title = item.get('title', 'No title')
                    citekey = item.get('citekey', 'No citekey')
                    item_type = item.get('type', 'unknown')
                    print(f"  {i+1}. [{item_type}] {title} (citekey: {citekey})")
                    if i == 0:  # 只显示第一个项目的完整信息
                        print(f"      完整数据: {json.dumps(item, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print("无结果")

        except Exception as e:
            print(f"❌ 错误: {e}")

    # 检查库信息
    print("\n📚 检查库信息")
    try:
        groups = client.get_groups(include_collections=True)
        print(f"库数量: {len(groups)}")
        for group in groups:
            print(f"  库: {group.get('name')} (ID: {group.get('id')})")
            collections = group.get('collections', [])
            if collections:
                print(f"    收藏夹数量: {len(collections)}")
            else:
                print("    无收藏夹")
    except Exception as e:
        print(f"❌ 获取库信息失败: {e}")

    # 检查附件数据结构 - 使用集成测试中实际使用的项目
    print("\n📎 检查附件数据结构")
    print("🔍 检查集成测试中使用的项目 'leblancImmunomodulationMesenchymalStem2007'")
    try:
        attachments = client.get_attachments("leblancImmunomodulationMesenchymalStem2007")
        print(f"附件数量: {len(attachments)}")
        if attachments:
            print("附件数据结构:")
            for i, attachment in enumerate(attachments):
                print(f"  附件 {i+1}:")
                for key, value in attachment.items():
                    print(f"    {key}: {value}")
                print(f"    显示标题: {attachment.get('title', 'No title')}")
                print()
        else:
            print("  无附件")
    except Exception as e:
        print(f"❌ 获取附件失败: {e}")

    # 也检查另一个有附件的项目
    print("🔍 查找有附件的项目...")
    test_results = client.search("a")  # 获取一些项目
    for item in test_results[:5]:  # 检查前5个
        citekey = item.get('citekey')
        if citekey:
            try:
                attachments = client.get_attachments(citekey)
                if attachments:
                    print(f"📄 找到有附件的项目: {citekey}")
                    print(f"附件数量: {len(attachments)}")
                    print("第一个附件数据结构:")
                    first_attachment = attachments[0]
                    for key, value in first_attachment.items():
                        print(f"  {key}: {value}")
                    print(f"显示标题: {first_attachment.get('title', 'No title')}")
                    break
            except Exception:
                continue

if __name__ == "__main__":
    debug_search()
