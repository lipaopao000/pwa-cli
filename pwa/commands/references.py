"""
References management commands
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from .base import BaseCommand
from ..core.utils import (
    calculate_jaccard_similarity,
    parse_biblatex_content,
    parse_json_content,
    load_markdown_content,
    normalize_doi,
)
from ..core.zotero_client import fetch_preferred_references
from ..ui import print_success, print_error, print_warning, print_info, Colors


class ReferencesMatchCommand(BaseCommand):
    """Match references from Markdown with Zotero/BibTeX library"""
    
    name = "references_match"
    description = "匹配参考文献"
    help_text = """
    从 Markdown 文档的 References 部分提取参考文献，
    并与 Zotero 库或 BibTeX 文件进行智能匹配。
    
    支持的匹配方法：
    1. DOI 精确匹配
    2. 标题 Jaccard 相似度匹配
    
    输出结果包括：
    - 完美匹配（相似度 >= 0.90）
    - 模糊匹配（提供候选项）
    """
    
    def get_interactive_params(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get parameters interactively"""
        print_info("\n=== 参考文献匹配 ===\n")
        
        # Get markdown file
        md_file = self.prompt_file("请输入 Markdown 文件路径", must_exist=True)
        if not md_file:
            raise ValueError("必须提供 Markdown 文件")
        
        # Get references file (optional)
        print_info("\n参考文献来源（留空使用 Zotero API）:")
        ref_file = self.prompt_file("BibTeX/JSON 文件路径（可选）", must_exist=False)
        
        # Get output options
        top_n = int(self.prompt_input("模糊匹配候选数量", "3"))
        
        return {
            'md_file': md_file,
            'ref_file': ref_file,
            'top_n': top_n
        }
    
    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        md_file = kwargs.get('md_file')
        if not md_file or not Path(md_file).exists():
            print_error("Markdown 文件不存在")
            return False
        
        ref_file = kwargs.get('ref_file')
        if ref_file and not Path(ref_file).exists():
            print_error("参考文献文件不存在")
            return False
        
        return True
    
    def execute(self, md_file: Path, ref_file: Optional[Path] = None, top_n: int = 3, **kwargs) -> Dict[str, Any]:
        """Execute reference matching"""
        md_file = Path(md_file)
        ref_file = Path(ref_file) if ref_file else None
        
        self.logger.info(f"开始匹配参考文献: {md_file}")
        
        # Setup cache directory
        cache_dir = self.config_manager.get_cache_dir(md_file)
        
        # Ensure Zotero config
        zotero_cfg_path = self.config_manager.ensure_config(
            'zotero',
            self.config_manager.config_dir.parent / 'configs' / 'zotero_config.yaml'
        )
        
        # Fetch references
        print_info("正在获取参考文献库...")
        references_content, references_type = fetch_preferred_references(
            str(ref_file) if ref_file else None,
            zotero_config_path=str(zotero_cfg_path)
        )
        
        if not references_content:
            print_error("无法获取参考文献库")
            return None
        
        # Parse references
        bib_data = []
        if references_type == 'biblatex':
            bib_data = parse_biblatex_content(references_content)
            print_success(f"已加载 BibLaTeX 参考文献: {len(bib_data)} 条")
        elif references_type == 'csljson':
            bib_data = parse_json_content(references_content)
            print_success(f"已加载 CSL JSON 参考文献: {len(bib_data)} 条")
        else:
            print_error(f"不支持的参考文献格式: {references_type}")
            return None
        
        if not bib_data:
            print_error("参考文献库为空")
            return None
        
        # Extract references from Markdown
        print_info("正在从 Markdown 提取参考文献...")
        md_content = load_markdown_content(str(md_file))
        md_refs, md_ref_details = self.extract_references_from_md(md_content)
        
        if not md_refs:
            print_error("未从 Markdown 中提取到参考文献")
            return None
        
        print_success(f"已提取参考文献: {len(md_refs)} 条")
        
        # Analyze matches
        print_info("正在分析匹配结果...")
        perfect, nonperfect = self.analyze_references(md_refs, bib_data, md_ref_details, top_n)
        
        # Display results
        self._display_results(perfect, nonperfect)
        
        # Save results
        output_file = cache_dir / "references_match.json"
        self._save_results(output_file, perfect, nonperfect, md_refs)
        
        print_success(f"\n结果已保存到: {output_file}")
        
        return {
            'perfect_matches': perfect,
            'nonperfect_matches': nonperfect,
            'output_file': output_file
        }
    
    def extract_references_from_md(self, md_content: str) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
        """Extract references from Markdown content"""
        # Find References section
        references_section_match = re.search(
            r'^\s*(?:\*{2}References\*{2}|##\s*References|####\s*Reference|##\s*参考文献|####\s*引用的著作)\s*$',
            md_content,
            re.IGNORECASE | re.MULTILINE
        )
        
        if not references_section_match:
            return {}, {}
        
        # Extract References text
        references_text_start_index = references_section_match.end()
        references_text = md_content[references_text_start_index:]
        
        # Find first reference entry
        first_ref_match = re.search(
            r'^\s*(?:(\[\d+\])|(\d+\.)|(\d+\))|(\(\d+\)))\s+',
            references_text,
            re.MULTILINE
        )
        
        if first_ref_match:
            references_text = references_text[first_ref_match.start():]
        else:
            return {}, {}
        
        # Find next section or end
        next_section_match = re.search(r'^\s*(?:#+\s*[^#\n]+|```)', references_text, re.MULTILINE)
        if next_section_match:
            references_text = references_text[:next_section_match.start()]
        
        # Extract individual references
        ref_pattern = re.compile(r'^\s*(?:(\[\d+\])|(\d+\.)|(\d+\))|(\(\d+\)))\s+(.*)$', re.MULTILINE)
        
        references = {}
        ref_details = {}
        
        for match in ref_pattern.finditer(references_text):
            ref_num = next((g for g in match.groups()[:-1] if g is not None), None)
            full_line_content = match.groups()[-1].strip()
            
            if not ref_num:
                continue
            
            ref_num = re.sub(r'[()\[\]\.]', '', ref_num)
            
            # Extract title
            title = self._extract_title(full_line_content)
            references[ref_num] = {'title': title.strip(), 'full_line': full_line_content}
            
            # Extract DOI and URL
            doi, url = self._extract_doi_url(full_line_content)
            ref_details[ref_num] = {'doi': doi, 'url': url}
        
        return references, ref_details
    
    def _extract_title(self, line: str) -> str:
        """Extract title from reference line"""
        # Try quoted title first
        quoted_match = re.search(r'"([^"]+?)"', line)
        if quoted_match:
            return quoted_match.group(1).strip()
        
        # Try split logic (Authors. Title. Journal.)
        parts = re.split(r'\.\s+', line)
        if len(parts) >= 2:
            title_candidate = parts[1].strip()
            if len(title_candidate) > 5 and not re.match(r'^[-–—]', title_candidate):
                return title_candidate
        
        # Cleanup logic
        title_main = line
        title_main = re.sub(r'^\s*\(PDF\)\s*', '', title_main, flags=re.IGNORECASE)
        title_main = re.sub(r'^\s*\[.*?\]\s*', '', title_main)
        
        # Remove common patterns after title
        patterns_to_remove = [
            r'\s*-\s*(?:PMC|PubMed|NIH|ResearchGate|Wiley|Frontiers|Oxford|MDPI|BMJ)\b',
            r'\s*,?\s*(?:Published|vol|issue|pages|doi|PMID)\b.*',
            r'\s*\d{4}(?:;\d{1,2}\().*',
            r'\s*:(?:\d+-\d+).*',
            r'\s*\|\s*.*',
            r'<\s*https?://.*',
            r'\s*https?://.*',
            r'\s*doi:.*',
        ]
        
        min_start = len(title_main)
        found_match = False
        
        for pattern in patterns_to_remove:
            match = re.search(pattern, title_main, flags=re.IGNORECASE)
            if match and match.start() < min_start:
                min_start = match.start()
                found_match = True
        
        if found_match:
            title_main = title_main[:min_start].strip()
        
        if " - " in title_main:
            parts = title_main.split(" - ", 1)
            return parts[0].strip()
        
        return title_main.strip()
    
    def _extract_doi_url(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DOI and URL from reference line"""
        doi = None
        url = None
        
        # Extract DOI
        doi_match = re.search(r'doi:([\w./\-]+)', line, re.IGNORECASE)
        if doi_match:
            doi = f'https://doi.org/{doi_match.group(1)}'
        
        # Extract URL (non-DOI)
        urls_found = re.findall(r'(https?://[^\s>]+)', line)
        for u in urls_found:
            u = u.rstrip('.,;)')
            if 'doi.org' not in u:
                url = u
                break
        
        if not url:
            url_match = re.search(r'<(https?://[^>]+)>', line)
            if url_match:
                u = url_match.group(1)
                if 'doi.org' not in u:
                    url = u
        
        return doi, url
    
    def analyze_references(
        self,
        md_refs: Dict,
        bib_data: List[Dict],
        md_ref_details: Dict,
        top_n: int = 3
    ) -> Tuple[Dict, List]:
        """Analyze references to find matches"""
        perfect_matches = {}
        nonperfect_matches = []
        
        # Build DOI and title maps
        bib_doi_map = {
            normalize_doi(item.get('doi', '')): item['ID']
            for item in bib_data
            if item.get('doi')
        }
        
        bib_titles_map = {
            item['ID']: item.get('title', '')
            for item in bib_data
            if item.get('ID') and item.get('title')
        }
        
        if not bib_titles_map:
            return None, None
        
        for ref_num, ref_info in md_refs.items():
            md_title = ref_info['title']
            md_doi = md_ref_details.get(ref_num, {}).get('doi', '')
            md_doi_norm = normalize_doi(md_doi)
            
            # Try DOI match first
            if md_doi_norm and md_doi_norm in bib_doi_map:
                matched_id = bib_doi_map[md_doi_norm]
                perfect_matches[ref_num] = {
                    'id': matched_id,
                    'method': 'doi',
                    'score': 1.0
                }
                continue
            
            # Try title match
            all_scores = []
            for bib_id, bib_title in bib_titles_map.items():
                jaccard_score = calculate_jaccard_similarity(md_title, bib_title)
                
                # Weight by length ratio
                len_ratio = min(
                    len(md_title) / len(bib_title),
                    len(bib_title) / len(md_title)
                ) if len(md_title) > 0 and len(bib_title) > 0 else 0
                
                final_score = jaccard_score * len_ratio
                
                all_scores.append({
                    'id': bib_id,
                    'title': bib_title,
                    'score': final_score,
                    'method': 'jaccard_len_weighted'
                })
            
            all_scores.sort(key=lambda x: x['score'], reverse=True)
            best_match = all_scores[0] if all_scores else {'score': -1}
            
            if best_match['score'] >= 0.90:
                perfect_matches[ref_num] = best_match
            else:
                candidates = all_scores[:top_n]
                nonperfect_matches.append({
                    'ref_num': ref_num,
                    'md_title': md_title,
                    'candidates': candidates
                })
        
        return perfect_matches, nonperfect_matches
    
    def _display_results(self, perfect: Dict, nonperfect: List):
        """Display matching results"""
        print("\n" + "=" * 60)
        print(Colors.highlight("匹配结果"))
        print("=" * 60 + "\n")
        
        if perfect:
            print(Colors.success(f"✓ 完美匹配: {len(perfect)} 条"))
            for ref_num, match in perfect.items():
                print(f"  [{ref_num}] → {match['id']} (方法: {match['method']}, 分数: {match['score']:.2f})")
        
        if nonperfect:
            print(f"\n{Colors.warning(f'⚠ 模糊匹配: {len(nonperfect)} 条')}")
            for item in nonperfect[:5]:  # Show first 5
                print(f"\n  [{item['ref_num']}] {item['md_title'][:60]}...")
                for i, cand in enumerate(item['candidates'], 1):
                    print(f"    {i}. {cand['id']} (分数: {cand['score']:.2f})")
            
            if len(nonperfect) > 5:
                print(f"\n  ... 还有 {len(nonperfect) - 5} 条模糊匹配")
    
    def _save_results(self, output_file: Path, perfect: Dict, nonperfect: List, md_refs: Dict):
        """Save results to JSON file"""
        results = {
            'perfect_matches': perfect,
            'nonperfect_matches': nonperfect,
            'total_refs': len(md_refs),
            'perfect_count': len(perfect),
            'nonperfect_count': len(nonperfect)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
