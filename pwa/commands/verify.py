"""
Scientific statement verification command for PWA CLI
"""

import os
import json
import logging
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
        
        # Get concurrency
        max_workers = self.prompt_text(
            "并发验证数 (默认: 3)",
            default="3"
        )
        
        try:
            max_workers = int(max_workers)
        except ValueError:
            max_workers = 3
        
        # Get output file
        default_output = "./verification_results.json"
        output_file = self.prompt_text(
            f"输出文件路径 (默认: {default_output})",
            default=default_output
        )
        
        return {
            'md_file': md_file,
            'use_ragflow': use_ragflow,
            'use_pubmed': use_pubmed,
            'max_workers': max_workers,
            'output_file': output_file
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
        use_pubmed = kwargs.get('use_pubmed', False)
        
        if use_ragflow:
            # Check RAGFlow config
            rag_config = self.config_manager.load_config('ragflow')
            if not rag_config or not rag_config.get('ragflow_api_key'):
                print_error("未找到 RAGFlow 配置")
                return False
        
        if use_pubmed:
            # Check email for PubMed
            email = llm_config.get('web_search', {}).get('email')
            if not email or 'example.com' in email:
                print_warning("未配置 PubMed 邮箱，将跳过 PubMed 验证")
        
        return True
    
    def execute(self, md_file: str, use_ragflow: bool = True,
                use_pubmed: bool = True, max_workers: int = 3,
                output_file: str = "./verification_results.json",
                **kwargs) -> Dict:
        """
        Execute statement verification
        
        Args:
            md_file: Path to Markdown file
            use_ragflow: Use RAGFlow for verification
            use_pubmed: Use PubMed for verification
            max_workers: Maximum concurrent verifications
            output_file: Output file path
            
        Returns:
            Dictionary with execution results
        """
        try:
            from ..core.statement_verifier import ScientificStatementVerifier
            from ..core.statement_verifier_utils import parse_markdown_to_statements
            from ..core.ragflow_client import RagFlowClient
            from ..core.pubmed_client import PubMedClient
            
            print_info("\n=== 开始科学陈述验证 ===\n")
            
            # Initialize clients
            rag_client = None
            pubmed_client = None
            
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
            
            if use_pubmed:
                print_info("正在初始化 PubMed 客户端...")
                llm_config = self.config_manager.load_config('llm')
                email = llm_config.get('web_search', {}).get('email')
                if email and 'example.com' not in email:
                    pubmed_client = PubMedClient(email)
                    print_success("PubMed 客户端已就绪")
            
            # Initialize verifier
            llm_config = self.config_manager.load_config('llm')
            llm_settings = self._get_active_llm_settings(llm_config)
            
            verifier = ScientificStatementVerifier(
                llm_settings=llm_settings,
                rag_client=rag_client,
                pubmed_client=pubmed_client,
                logger=self.logger
            )
            
            # Parse statements from Markdown
            print_info(f"\n正在解析 Markdown 文件: {md_file}")
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            statements = parse_markdown_to_statements(md_content)
            print_success(f"已提取 {len(statements)} 条陈述")
            
            if len(statements) == 0:
                print_warning("没有找到需要验证的陈述")
                return {'status': 'no_statements', 'count': 0}
            
            # Verify statements
            print_info(f"\n正在验证陈述 (并发数: {max_workers})...")
            results = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(verifier.verify_statement, stmt): stmt
                    for stmt in statements
                }
                
                completed = 0
                for future in as_completed(futures):
                    stmt = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        
                        # Show progress
                        if completed % 10 == 0:
                            print_info(f"已完成: {completed}/{len(statements)}")
                    except Exception as e:
                        self.logger.error(f"Verification failed for statement: {e}")
                        results.append({
                            'statement': stmt,
                            'status': 'error',
                            'error': str(e)
                        })
            
            print_success(f"\n验证完成！共验证 {len(results)} 条陈述")
            
            # Save results
            print_info(f"\n正在保存结果到: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print_success("结果已保存")
            
            # Show summary
            self._show_summary(results)
            
            return {
                'status': 'success',
                'total': len(statements),
                'verified': len(results),
                'output_file': output_file
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
    
    def _show_summary(self, results: List[Dict]):
        """Show verification summary"""
        print_info("\n" + "=" * 60)
        print_info("验证统计")
        print_info("=" * 60 + "\n")
        
        # Count by verification status
        status_counts = {}
        for result in results:
            status = result.get('verification_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        status_names = {
            'verified': '✓ 已验证',
            'partially_verified': '⚠ 部分验证',
            'unverified': '✗ 未验证',
            'error': '✗ 错误'
        }
        
        for status, count in status_counts.items():
            status_name = status_names.get(status, status)
            print(f"  {status_name}: {count}")
        
        print()


class VerifyViewResultsCommand(BaseCommand):
    """View verification results"""
    
    name = "verify_view_results"
    description = "查看验证结果"
    
    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        default_file = "./verification_results.json"
        results_file = self.prompt_text(
            f"结果文件路径 (默认: {default_file})",
            default=default_file
        )
        
        return {'results_file': results_file}
    
    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        results_file = kwargs.get('results_file')
        
        if not results_file or not Path(results_file).exists():
            print_error(f"结果文件不存在: {results_file}")
            return False
        
        return True
    
    def execute(self, results_file: str = "./verification_results.json",
                **kwargs) -> Dict:
        """Execute view results"""
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
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
        print_info("\n" + "=" * 60)
        print_info("验证结果")
        print_info("=" * 60 + "\n")
        
        # Group by status
        by_status = {}
        for result in results:
            status = result.get('verification_status', 'unknown')
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(result)
        
        # Show each group
        status_order = ['verified', 'partially_verified', 'unverified', 'error']
        status_icons = {
            'verified': '✓',
            'partially_verified': '⚠',
            'unverified': '✗',
            'error': '✗'
        }
        
        for status in status_order:
            if status not in by_status:
                continue
            
            items = by_status[status]
            icon = status_icons.get(status, '•')
            print(f"{icon} {Colors.highlight(status.upper())} ({len(items)} 条)\n")
            
            for i, item in enumerate(items[:5], 1):  # Show first 5
                stmt = item.get('statement', '')
                if len(stmt) > 80:
                    stmt = stmt[:77] + "..."
                print(f"  {i}. {stmt}")
                
                # Show evidence if available
                evidence = item.get('evidence', [])
                if evidence:
                    print(f"     证据: {len(evidence)} 条")
            
            if len(items) > 5:
                print(f"  ... 还有 {len(items) - 5} 条")
            
            print()


class VerifyExportReportCommand(BaseCommand):
    """Export verification report"""
    
    name = "verify_export_report"
    description = "导出验证报告"
    
    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        default_input = "./verification_results.json"
        results_file = self.prompt_text(
            f"结果文件路径 (默认: {default_input})",
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
        
        if not results_file or not Path(results_file).exists():
            print_error(f"结果文件不存在: {results_file}")
            return False
        
        return True
    
    def execute(self, results_file: str = "./verification_results.json",
                output_file: str = "./verification_report.md",
                **kwargs) -> Dict:
        """Execute export report"""
        try:
            # Load results
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            if not results:
                print_warning("结果文件为空")
                return {'status': 'empty'}
            
            # Generate report
            print_info(f"\n正在生成报告...")
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
        report.append("# 科学陈述验证报告\n")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"总计: {len(results)} 条陈述\n")
        
        # Summary
        report.append("## 验证统计\n")
        status_counts = {}
        for result in results:
            status = result.get('verification_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            report.append(f"- {status}: {count}\n")
        
        report.append("\n")
        
        # Detailed results
        report.append("## 详细结果\n")
        
        for i, result in enumerate(results, 1):
            stmt = result.get('statement', '')
            status = result.get('verification_status', 'unknown')
            evidence = result.get('evidence', [])
            
            report.append(f"### {i}. {stmt}\n")
            report.append(f"**状态**: {status}\n\n")
            
            if evidence:
                report.append("**证据**:\n\n")
                for j, ev in enumerate(evidence, 1):
                    source = ev.get('source', 'unknown')
                    content = ev.get('content', '')
                    report.append(f"{j}. [{source}] {content}\n")
                report.append("\n")
            
            report.append("---\n\n")
        
        return "".join(report)
