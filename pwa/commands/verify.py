"""
Scientific statement verification command for PWA CLI
"""

import os
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import BaseCommand
from ..ui import print_success, print_error, print_info, print_warning, Colors


class VerifyStatementsCommand(BaseCommand):
    """Verify scientific statements in paper"""
    
    name = "verify_statements"
    description = "验证科学陈述"
    
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.results_file = "verification_results.json"
        self.file_lock = threading.Lock()
    
    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        print_info("\n=== 科学陈述验证配置 ===\n")
        
        # Get input file
        md_file = self.prompt_file("请输入 Markdown 文件路径")
        
        # Get verification sources
        print("\n验证数据源:")
        print("  1. RAGFlow 知识库")
        print("  2. PubMed 数据库")
        print("  3. 两者都使用")
        
        source_choice = self.prompt_choice("请选择", ["1", "2", "3"])
        
        use_ragflow = source_choice in ["1", "3"]
        use_pubmed = source_choice in ["2", "3"]
        
        # Get reference source
        print("\n参考文献来源:")
        print("  1. Zotero API")
        print("  2. 本地 BibTeX 文件")
        print("  3. 不加载参考文献")
        
        ref_choice = self.prompt_choice("请选择", ["1", "2", "3"])
        
        ref_source = None
        ref_path = None
        if ref_choice == "1":
            ref_source = "zotero"
        elif ref_choice == "2":
            ref_path = self.prompt_file("请输入 BibTeX 文件路径")
            ref_source = "bibtex"
        
        # Get concurrency
        max_workers = self.prompt_text(
            "并发验证数 (默认: 3)",
            default="3"
        )
        
        try:
            max_workers = int(max_workers)
        except ValueError:
            max_workers = 3
        
        # Get output directory
        default_output = "./verification_output"
        output_dir = self.prompt_text(
            f"输出目录 (默认: {default_output})",
            default=default_output
        )
        
        return {
            'md_file': md_file,
            'use_ragflow': use_ragflow,
            'use_pubmed': use_pubmed,
            'ref_source': ref_source,
            'ref_path': ref_path,
            'max_workers': max_workers,
            'output_dir': output_dir
        }
    
    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        md_file = kwargs.get('md_file')
        
        if not md_file or not Path(md_file).exists():
            print_error(f"Markdown 文件不存在: {md_file}")
            return False
        
        # Check LLM config
        llm_config = self.config_manager.load_config('llm')
        if not llm_config:
            print_error("未找到 LLM 配置")
            return False
        
        use_ragflow = kwargs.get('use_ragflow', False)
        
        if use_ragflow:
            # Check RAGFlow config
            rag_config = self.config_manager.load_config('ragflow')
            if not rag_config or not rag_config.get('ragflow_api_key'):
                print_error("未找到 RAGFlow 配置")
                return False
        
        ref_source = kwargs.get('ref_source')
        ref_path = kwargs.get('ref_path')
        
        if ref_source == "bibtex":
            if not ref_path or not Path(ref_path).exists():
                print_error(f"BibTeX 文件不存在: {ref_path}")
                return False
        
        return True
    
    def execute(self, md_file: str, use_ragflow: bool = True,
                use_pubmed: bool = True, ref_source: Optional[str] = None,
                ref_path: Optional[str] = None, max_workers: int = 3,
                output_dir: str = "./verification_output",
                **kwargs) -> Dict:
        """
        Execute statement verification
        
        Args:
            md_file: Path to Markdown file
            use_ragflow: Use RAGFlow for verification
            use_pubmed: Use PubMed for verification
            ref_source: Reference source ('zotero' or 'bibtex')
            ref_path: Path to BibTeX file (if ref_source is 'bibtex')
            max_workers: Maximum concurrent verifications
            output_dir: Output directory
            
        Returns:
            Dictionary with execution results
        """
        try:
            from ..verifier.statement_verifier import ScientificStatementVerifier
            from ..verifier.utils import parse_markdown_to_statements
            from ..clients.ragflow import RagFlowClient
            from ..clients.pubmed import PubMedClient
            from ..clients.zotero import fetch_preferred_references
            from ..core.utils import parse_biblatex_content, parse_json_content
            from ..agents.citation import load_fulltext_md_content, get_fulltext_md_path
            from tqdm import tqdm
            
            print_info("\n=== 开始科学陈述验证 ===\n")
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize clients
            rag_client = None
            pubmed_client = None
            dataset_id = None
            doc_map = {}
            
            llm_config = self.config_manager.load_config('llm')
            llm_settings = self._get_active_llm_settings(llm_config)
            
            if use_ragflow:
                print_info("正在初始化 RAGFlow 客户端...")
                rag_config = self.config_manager.load_config('ragflow')
                rag_client = RagFlowClient(
                    base_url=rag_config['ragflow_base_url'],
                    api_key=rag_config['ragflow_api_key']
                )
                if not rag_client.check_connection():
                    print_warning("RAGFlow 连接失败，将跳过 RAGFlow 验证")
                    rag_client = None
                else:
                    print_success("RAGFlow 客户端已就绪")
                    
                    # Select dataset interactively
                    dataset_id = self._select_dataset_interactively(rag_client)
            
            if use_pubmed:
                print_info("正在初始化 PubMed 客户端...")
                email = llm_config.get('web_search', {}).get('email')
                if not email:
                    rag_config = self.config_manager.load_config('ragflow')
                    if rag_config:
                        email = rag_config.get('email')
                
                if email and 'example.com' not in email:
                    pubmed_client = PubMedClient(email)
                    print_success("PubMed 客户端已就绪")
                else:
                    print_warning("未配置有效的 PubMed 邮箱")
            
            # Load references
            bib_data = {}
            if ref_source:
                print_info(f"\n正在加载参考文献 (来源: {ref_source})...")
                
                zotero_config_path = None
                if ref_source == "zotero":
                    zotero_config_path = self.config_manager.get_config_path('zotero')
                
                content, rtype = fetch_preferred_references(
                    ref_path=ref_path,
                    zotero_config_path=str(zotero_config_path) if zotero_config_path else None
                )
                
                if content:
                    if rtype == 'biblatex':
                        entries = parse_biblatex_content(content)
                    else:
                        entries = parse_json_content(content)
                    
                    bib_data = {e['ID']: e for e in entries}
                    print_success(f"已加载 {len(bib_data)} 条参考文献")
                else:
                    print_warning("未能加载参考文献")
            
            # Parse statements from Markdown
            print_info(f"\n正在解析 Markdown 文件: {md_file}")
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            statements = parse_markdown_to_statements(md_content)
            print_success(f"已提取 {len(statements)} 条陈述")
            
            if len(statements) == 0:
                print_warning("没有找到需要验证的陈述")
                return {'status': 'no_statements', 'count': 0}
            
            # Sync documents to RAG if needed
            if rag_client and dataset_id:
                print_info("\n正在同步文档到 RAGFlow...")
                doc_map = self._sync_documents_to_rag(
                    rag_client, dataset_id, statements
                )
                print_success(f"文档同步完成")
            
            # Initialize verifier
            verifier = ScientificStatementVerifier(
                rag_client=rag_client,
                pubmed_client=pubmed_client,
                llm_settings=llm_settings,
                tavily_client=None,
                debug=False
            )
            
            # Verify statements
            print_info(f"\n正在验证陈述 (并发数: {max_workers})...")
            results = []
            
            md_base = os.path.splitext(os.path.basename(md_file))[0]
            out_path = output_path / f"Statement_Verifier_Report_{md_base}.json"
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._process_single_statement,
                        stmt, verifier, bib_data, dataset_id, doc_map, llm_settings
                    ): stmt
                    for stmt in statements
                }
                
                for future in tqdm(as_completed(futures), total=len(statements), desc="验证进度"):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Save incrementally
                        self._save_results(out_path, results)
                    except Exception as e:
                        self.logger.error(f"Verification failed: {e}")
                        results.append({
                            'error': str(e),
                            'claim_info': {'context': 'unknown'}
                        })
            
            print_success(f"\n验证完成！共验证 {len(results)} 条陈述")
            
            # Annotate markdown
            print_info("\n正在生成带注释的 Markdown...")
            annotated_path = self._annotate_markdown(md_file, results, output_path)
            print_success(f"已生成: {annotated_path}")
            
            # Show summary
            self._show_summary(results)
            
            return {
                'status': 'success',
                'total': len(statements),
                'verified': len(results),
                'output_dir': str(output_path),
                'results_file': str(out_path),
                'annotated_file': str(annotated_path)
            }
            
        except Exception as e:
            self.logger.error(f"Verification failed: {e}", exc_info=True)
            print_error(f"验证失败: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_active_llm_settings(self, llm_config: Dict) -> Dict:
        """Get active LLM settings from config"""
        provider = llm_config.get("active_provider", "openai")
        p_settings = llm_config.get("providers", {}).get(provider, {})
        
        return {
            "model": p_settings.get("model", "gpt-4o-mini"),
            "api_key": p_settings.get("api_key") or os.getenv("OPENAI_API_KEY"),
            "base_url": p_settings.get("base_url"),
            "temperature": p_settings.get("temperature", 0.1)
        }
    
    def _select_dataset_interactively(self, rag_client) -> Optional[str]:
        """Select RAGFlow dataset interactively"""
        try:
            print_info("\n--- RAGFlow 数据集选择 ---\n")
            datasets = rag_client.list_datasets(page_size=100)
            
            if not datasets:
                print_warning("未找到数据集")
                return None
            
            print("可用数据集:\n")
            for i, ds in enumerate(datasets):
                print(f"  {i+1:<4} | {ds.name:<25} | {ds.id}")
            
            choice = input(f"\n请选择数据集 (1-{len(datasets)}) [1]: ").strip()
            idx = int(choice) - 1 if choice else 0
            
            if 0 <= idx < len(datasets):
                selected = datasets[idx]
                print_success(f"已选择数据集: {selected.name}\n")
                return selected.id
            else:
                print_warning("无效选择，使用第一个数据集")
                return datasets[0].id
                
        except Exception as e:
            self.logger.error(f"Dataset selection failed: {e}")
            return None
    
    def _sync_documents_to_rag(self, rag_client, dataset_id: str, statements: List[Dict]) -> Dict:
        """Sync full-text documents to RAGFlow"""
        from ..agents.citation import get_fulltext_md_path
        from tqdm import tqdm
        
        try:
            # Get existing documents
            existing_docs = rag_client.list_documents(dataset_id, page_size=2000)
            doc_map = {getattr(d, 'name', ''): getattr(d, 'id', '') for d in existing_docs}
            
            # Get unique citation keys
            unique_keys = set(
                s.get('citation_id') for s in statements 
                if s.get('citation_id')
            )
            
            # Upload missing documents
            for key in tqdm([k for k in unique_keys if get_fulltext_md_path(k)], desc="同步文档"):
                target_name = f"{key}.md"
                if target_name not in doc_map:
                    md_path = get_fulltext_md_path(key)
                    if rag_client.upload_document(dataset_id, md_path, display_name=target_name):
                        doc_map[target_name] = "uploaded"
            
            return doc_map
            
        except Exception as e:
            self.logger.error(f"Document sync failed: {e}")
            return {}
    
    def _process_single_statement(self, stmt_data: Dict, verifier, bib_data: Dict,
                                   dataset_id: Optional[str], doc_map: Dict,
                                   llm_settings: Dict) -> Dict:
        """Process single statement verification"""
        from ..agents.citation import load_fulltext_md_content
        import re
        
        citation_id = stmt_data.get('citation_id')
        context = stmt_data.get('context')
        line = stmt_data.get('line')
        ref = bib_data.get(citation_id) if citation_id else None
        
        # Process Journal IF
        raw_if = ref.get('journal_if') if ref else None
        journal_if = None
        if raw_if:
            try:
                if_match = re.search(r'(\d+\.?\d*)', str(raw_if))
                if if_match:
                    journal_if = float(if_match.group(1))
            except:
                pass
        
        # Build initial state
        initial_state = {
            "citation_id": citation_id,
            "context": context,
            "ref_title": ref.get('title') if ref else None,
            "ref_abstract": ref.get('abstract') if ref else None,
            "ref_journal_if": journal_if,
            "ref_url": ref.get('url') or ref.get('doi') if ref else None,
            "dataset_id": dataset_id,
            "doc_id": doc_map.get(f"{citation_id}.md") if citation_id else None,
            "evidences": [],
            "audit_history": [],
            "fulltext_md": load_fulltext_md_content(citation_id) if citation_id else None,
        }
        
        try:
            # Create configuration
            config = {
                "configurable": {
                    "model": llm_settings["model"],
                    "temperature": llm_settings.get("temperature", 0.1)
                }
            }
            
            # Run verification workflow
            final_state = verifier.workflow.invoke(initial_state, config=config)
            result = final_state.get('verification_result', {"error": "No result"})
            result['claim_info']['line'] = line
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing claim at line {line}: {e}")
            return {
                "error": str(e),
                "claim_info": {"line": line, "context": context}
            }
    
    def _save_results(self, path: Path, results: List[Dict]):
        """Save results to file"""
        with self.file_lock:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({"results": results}, f, indent=2, ensure_ascii=False)
    
    def _annotate_markdown(self, md_path: str, results: List[Dict], output_dir: Path) -> Path:
        """Annotate markdown with verification results"""
        base = os.path.splitext(os.path.basename(md_path))[0]
        new_path = output_dir / f"{base}-Verified.md"
        
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
        
        # Sort results by line number (reverse order to avoid line number shifts)
        sorted_results = sorted(
            results,
            key=lambda x: x.get('claim_info', {}).get('line', 0),
            reverse=True
        )
        
        for r in sorted_results:
            line_idx = r.get('claim_info', {}).get('line', 0) - 1
            if line_idx < 0 or line_idx >= len(lines):
                continue
            
            decision = r.get('decision', {})
            status = decision.get('status', 'Unknown')
            
            # Choose emoji based on status
            emoji = {
                "Supported": "✅",
                "Contradicted": "❌",
                "Partially Supported": "⚠️",
                "Unsupported": "❓"
            }.get(status, "⚠️")
            
            suggestion = decision.get('suggestion', '')[:100]
            comment = f" <!-- {emoji} {status}: {suggestion}... -->"
            lines[line_idx] += comment
        
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return new_path
    
    def _show_summary(self, results: List[Dict]):
        """Show verification summary"""
        print_info("\n" + "=" * 60)
        print_info("验证统计")
        print_info("=" * 60 + "\n")
        
        # Count by verification status
        status_counts = {}
        for result in results:
            decision = result.get('decision', {})
            status = decision.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        status_icons = {
            'Supported': '✅',
            'Partially Supported': '⚠️',
            'Unsupported': '❓',
            'Contradicted': '❌'
        }
        
        for status, count in status_counts.items():
            icon = status_icons.get(status, '•')
            print(f"  {icon} {status}: {count}")
        
        print()


class VerifyViewResultsCommand(BaseCommand):
    """View verification results"""
    
    name = "verify_view_results"
    description = "查看验证结果"
    
    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        default_file = "./verification_output/Statement_Verifier_Report_*.json"
        results_file = self.prompt_text(
            f"结果文件路径 (支持通配符)",
            default=default_file
        )
        
        return {'results_file': results_file}
    
    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        results_file = kwargs.get('results_file')
        
        if not results_file:
            print_error("未指定结果文件")
            return False
        
        # Check if file exists (handle wildcards)
        import glob
        files = glob.glob(results_file)
        if not files:
            print_error(f"未找到匹配的文件: {results_file}")
            return False
        
        return True
    
    def execute(self, results_file: str, **kwargs) -> Dict:
        """Execute view results"""
        import glob
        
        try:
            # Find matching files
            files = glob.glob(results_file)
            if not files:
                print_error(f"未找到匹配的文件: {results_file}")
                return {'status': 'not_found'}
            
            # Use the most recent file
            latest_file = max(files, key=os.path.getmtime)
            print_info(f"\n读取文件: {latest_file}\n")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            
            if not results:
                print_info("结果文件为空")
                return {'status': 'empty'}
            
            self._show_results(results)
            
            return {'status': 'success', 'count': len(results)}
            
        except Exception as e:
            self.logger.error(f"Failed to read results: {e}", exc_info=True)
            print_error(f"读取结果失败: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _show_results(self, results: List[Dict]):
        """Show verification results"""
        print_info("=" * 60)
        print_info("验证结果详情")
        print_info("=" * 60 + "\n")
        
        # Group by status
        by_status = {}
        for result in results:
            decision = result.get('decision', {})
            status = decision.get('status', 'unknown')
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(result)
        
        # Show each group
        status_order = ['Supported', 'Partially Supported', 'Unsupported', 'Contradicted']
        status_icons = {
            'Supported': '✅',
            'Partially Supported': '⚠️',
            'Unsupported': '❓',
            'Contradicted': '❌'
        }
        
        for status in status_order:
            if status not in by_status:
                continue
            
            items = by_status[status]
            icon = status_icons.get(status, '•')
            print(f"{icon} {Colors.highlight(status)} ({len(items)} 条)\n")
            
            for i, item in enumerate(items[:5], 1):  # Show first 5
                claim_info = item.get('claim_info', {})
                context = claim_info.get('context', '')
                if len(context) > 80:
                    context = context[:77] + "..."
                print(f"  {i}. {context}")
                
                # Show decision reasoning
                decision = item.get('decision', {})
                reasoning = decision.get('reasoning', '')
                if reasoning:
                    print(f"     理由: {reasoning[:100]}...")
            
            if len(items) > 5:
                print(f"  ... 还有 {len(items) - 5} 条")
            
            print()


class VerifyExportReportCommand(BaseCommand):
    """Export verification report"""
    
    name = "verify_export_report"
    description = "导出验证报告"
    
    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        default_input = "./verification_output/Statement_Verifier_Report_*.json"
        results_file = self.prompt_text(
            f"结果文件路径 (支持通配符)",
            default=default_input
        )
        
        default_output = "./verification_report.md"
        output_file = self.prompt_text(
            f"报告文件路径 (默认: {default_output})",
            default=default_output
        )
        
        return {
            'results_file': results_file,
            'output_file': output_file
        }
    
    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        results_file = kwargs.get('results_file')
        
        if not results_file:
            print_error("未指定结果文件")
            return False
        
        # Check if file exists (handle wildcards)
        import glob
        files = glob.glob(results_file)
        if not files:
            print_error(f"未找到匹配的文件: {results_file}")
            return False
        
        return True
    
    def execute(self, results_file: str,
                output_file: str = "./verification_report.md",
                **kwargs) -> Dict:
        """Execute export report"""
        import glob
        
        try:
            # Find matching files
            files = glob.glob(results_file)
            if not files:
                print_error(f"未找到匹配的文件: {results_file}")
                return {'status': 'not_found'}
            
            # Use the most recent file
            latest_file = max(files, key=os.path.getmtime)
            print_info(f"\n读取文件: {latest_file}\n")
            
            # Load results
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            
            if not results:
                print_warning("结果文件为空")
                return {'status': 'empty'}
            
            # Generate report
            print_info(f"正在生成报告...")
            report = self._generate_report(results)
            
            # Save report
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print_success(f"报告已保存到: {output_file}")
            
            return {
                'status': 'success',
                'output_file': output_file,
                'count': len(results)
            }
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}", exc_info=True)
            print_error(f"导出失败: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _generate_report(self, results: List[Dict]) -> str:
        """Generate Markdown report"""
        from datetime import datetime
        
        report = []
        report.append("# 科学陈述验证报告\n\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        report.append(f"**总计**: {len(results)} 条陈述\n\n")
        
        # Summary
        report.append("## 验证统计\n\n")
        status_counts = {}
        for result in results:
            decision = result.get('decision', {})
            status = decision.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            report.append(f"- **{status}**: {count}\n")
        
        report.append("\n---\n\n")
        
        # Detailed results
        report.append("## 详细结果\n\n")
        
        for i, result in enumerate(results, 1):
            claim_info = result.get('claim_info', {})
            context = claim_info.get('context', '')
            decision = result.get('decision', {})
            status = decision.get('status', 'unknown')
            reasoning = decision.get('reasoning', '')
            
            # Choose emoji
            emoji = {
                "Supported": "✅",
                "Contradicted": "❌",
                "Partially Supported": "⚠️",
                "Unsupported": "❓"
            }.get(status, "⚠️")
            
            report.append(f"### {i}. {emoji} {context}\n\n")
            report.append(f"**状态**: {status}\n\n")
            report.append(f"**理由**: {reasoning}\n\n")
            
            # Show evidence if available
            evidences = result.get('evidences', [])
            if evidences:
                report.append("**证据**:\n\n")
                for j, ev in enumerate(evidences[:3], 1):  # Show first 3
                    source = ev.get('source', 'unknown')
                    content = ev.get('content', '')
                    if len(content) > 200:
                        content = content[:197] + "..."
                    report.append(f"{j}. [{source}] {content}\n\n")
            
            report.append("---\n\n")
        
        return "".join(report)
