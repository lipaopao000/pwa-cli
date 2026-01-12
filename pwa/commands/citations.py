"""
Citations processing commands
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.utils import load_markdown_content
from ..ui import Colors, print_error, print_info, print_success, print_warning
from .base import BaseCommand


class CitationsReplaceCommand(BaseCommand):
    """Replace superscript citations with Pandoc BibTeX format"""

    name = "citations_replace"
    description = "替换引用格式"
    help_text = """
    将 Markdown 文档中的上标引用（如 ^1^）替换为 Pandoc BibTeX 引用格式（如 [@key]）。
    
    支持的引用格式：
    - 单个引用: ^1^ → [@key1]
    - 多个引用: ^1,2,3^ → [@key1; @key2; @key3]
    - 范围引用: ^1-5^ → [@key1; @key2; @key3; @key4; @key5]
    
    注意：只处理 Abstract 之后的内容
    """

    def get_interactive_params(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get parameters interactively"""
        print_info("\n=== 引用格式替换 ===\n")

        # Get markdown file
        md_file = self.prompt_file("请输入 Markdown 文件路径", must_exist=True)
        if not md_file:
            raise ValueError("必须提供 Markdown 文件")

        # Get matches file
        cache_dir = self.config_manager.get_cache_dir(md_file)
        default_matches = cache_dir / "references_match.json"

        if default_matches.exists():
            print_info(f"找到匹配结果文件: {default_matches}")
            use_default = self.prompt_confirm("使用此文件？", True)
            if use_default:
                matches_file = default_matches
            else:
                matches_file = self.prompt_file("请输入匹配结果文件路径", must_exist=True)
        else:
            matches_file = self.prompt_file("请输入匹配结果文件路径", must_exist=True)

        # Get output file
        default_output = md_file.parent / f"{md_file.stem}_replaced{md_file.suffix}"
        output_file = self.prompt_input("输出文件路径", str(default_output))

        return {"md_file": md_file, "matches_file": matches_file, "output_file": Path(output_file)}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        md_file = kwargs.get("md_file")
        if not md_file or not Path(md_file).exists():
            print_error("Markdown 文件不存在")
            return False

        matches_file = kwargs.get("matches_file")
        if not matches_file or not Path(matches_file).exists():
            print_error("匹配结果文件不存在")
            return False

        return True

    def execute(
        self, md_file: Path, matches_file: Path, output_file: Optional[Path] = None, **kwargs
    ) -> Dict[str, Any]:
        """Execute citation replacement"""
        md_file = Path(md_file)
        matches_file = Path(matches_file)

        if not output_file:
            output_file = md_file.parent / f"{md_file.stem}_replaced{md_file.suffix}"
        else:
            output_file = Path(output_file)

        self.logger.info(f"开始替换引用: {md_file}")

        # Load matches
        print_info("正在加载匹配结果...")
        matches = self._load_matches(matches_file)

        if not matches:
            print_error("无法加载匹配结果")
            return None

        print_success(f"已加载 {len(matches)} 条匹配记录")

        # Load markdown content
        print_info("正在读取 Markdown 文件...")
        md_content = load_markdown_content(str(md_file))

        # Find Abstract section
        abstract_match = re.search(
            r"^\s*(?:##\s*Abstract|####\s*摘要)\s*$", md_content, re.IGNORECASE | re.MULTILINE
        )

        if abstract_match:
            content_before_abstract = md_content[: abstract_match.end()]
            content_after_abstract = md_content[abstract_match.end() :]
            print_success("找到 Abstract 部分，只处理之后的内容")
        else:
            content_before_abstract = ""
            content_after_abstract = md_content
            print_warning("未找到 Abstract 部分，处理全部内容")

        # Replace citations
        print_info("正在替换引用...")
        replaced_content, stats = self._replace_citations(content_after_abstract, matches)

        # Combine content
        final_content = content_before_abstract + replaced_content

        # Save output
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_content)

        # Display statistics
        self._display_stats(stats)

        print_success(f"\n结果已保存到: {output_file}")

        return {"output_file": output_file, "stats": stats}

    def _load_matches(self, matches_file: Path) -> Dict[str, str]:
        """Load matches from JSON file"""
        try:
            with open(matches_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract perfect matches
            matches = {}
            if "perfect_matches" in data:
                for ref_num, match_info in data["perfect_matches"].items():
                    matches[ref_num] = match_info["id"]

            return matches

        except Exception as e:
            self.logger.error(f"加载匹配结果失败: {e}")
            return {}

    def _replace_citations(self, content: str, matches: Dict[str, str]) -> tuple:
        """Replace citations in content"""
        stats = {"single": 0, "multiple": 0, "range": 0, "failed": 0}

        # Pattern for superscript citations
        citation_pattern = re.compile(r"\^([\d,\-\s]+)\^")

        def replace_func(match):
            citation_str = match.group(1).strip()

            # Parse citation numbers
            ref_nums = self._parse_citation_string(citation_str)

            if not ref_nums:
                stats["failed"] += 1
                return match.group(0)  # Keep original

            # Convert to citation keys
            keys = []
            for ref_num in ref_nums:
                if ref_num in matches:
                    keys.append(f"@{matches[ref_num]}")
                else:
                    self.logger.warning(f"未找到引用 {ref_num} 的匹配")
                    stats["failed"] += 1
                    return match.group(0)  # Keep original if any key is missing

            # Update statistics
            if len(keys) == 1:
                stats["single"] += 1
            elif "-" in citation_str:
                stats["range"] += 1
            else:
                stats["multiple"] += 1

            # Format as Pandoc citation
            if len(keys) == 1:
                return f"[{keys[0]}]"
            else:
                return f"[{'; '.join(keys)}]"

        replaced_content = citation_pattern.sub(replace_func, content)

        return replaced_content, stats

    def _parse_citation_string(self, citation_str: str) -> list:
        """Parse citation string to list of reference numbers"""
        ref_nums = []

        # Split by comma
        parts = citation_str.split(",")

        for part in parts:
            part = part.strip()

            # Check for range (e.g., "1-5")
            if "-" in part:
                try:
                    start, end = part.split("-", 1)
                    start_num = int(start.strip())
                    end_num = int(end.strip())
                    ref_nums.extend([str(i) for i in range(start_num, end_num + 1)])
                except ValueError:
                    continue
            else:
                # Single number
                try:
                    int(part)  # Validate it's a number
                    ref_nums.append(part)
                except ValueError:
                    continue

        return ref_nums

    def _display_stats(self, stats: Dict):
        """Display replacement statistics"""
        print("\n" + "=" * 60)
        print(Colors.highlight("替换统计"))
        print("=" * 60 + "\n")

        total = stats["single"] + stats["multiple"] + stats["range"]

        print(f"  单个引用: {stats['single']}")
        print(f"  多个引用: {stats['multiple']}")
        print(f"  范围引用: {stats['range']}")
        print(f"  {Colors.success(f'成功替换: {total}')}")

        if stats["failed"] > 0:
            failed_count = stats["failed"]
            print(f"  {Colors.warning(f'失败: {failed_count}')}")
