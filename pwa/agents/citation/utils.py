# -*- coding: utf-8 -*-
import re
from typing import Any, Dict, List, Tuple


def parse_markdown_to_statements(content: str) -> List[Dict[str, Any]]:
    """Parses markdown and identifies both cited and potential uncited claims."""
    # Note: Regex for citations like @Key or [@Key]
    cited_pattern = r"\[?@([a-zA-Z0-9_\-:]+)\]?"

    results = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped_line = line.strip()
        # Skip headings, empty lines, and table structure lines
        if (
            not stripped_line
            or stripped_line.startswith("#")
            or (stripped_line.startswith("|") and "---" in stripped_line)
        ):
            continue

        # 1. Find cited statements
        matches = list(re.finditer(cited_pattern, line))
        if matches:
            # Split line into sentences while preserving boundaries, supporting Chinese punctuation
            sentences = re.split(r"(?<=[.!?。！？])\s*", line)
            current_pos = 0
            for sent in sentences:
                if not sent.strip():
                    continue
                sent_start = line.find(sent, current_pos)
                sent_end = sent_start + len(sent)

                # Find all citations within this specific sentence
                sent_citations = []
                for match in matches:
                    if sent_start <= match.start() < sent_end:
                        sent_citations.append(match.group(1))

                # For each unique citation in this sentence, create a statement
                if sent_citations:
                    for cid in set(sent_citations):
                        results.append(
                            {"citation_id": cid, "context": sent.strip(), "line": line_num}
                        )
                else:
                    # Heuristic for uncited statement in a cited line
                    sent_stripped = sent.strip()
                    if is_scientific_statement(sent_stripped):
                        results.append(
                            {"citation_id": None, "context": sent_stripped, "line": line_num}
                        )

                current_pos = sent_end
            continue

        # 2. Heuristic for uncited scientific statements on non-cited lines
        sentences = re.split(r"(?<=[.!?。！？])\s*", line)
        for sent in sentences:
            sent = sent.strip()
            if is_scientific_statement(sent):
                results.append({"citation_id": None, "context": sent, "line": line_num})

    return results


def is_scientific_statement(sent: str) -> bool:
    """Heuristic to check if a sentence looks like a scientific claim."""
    is_long_enough = len(sent.split()) > 10 or (
        any("\u4e00" <= char <= "\u9fff" for char in sent) and len(sent) > 15
    )
    if not is_long_enough:
        return False

    if re.search(r"@", sent) or re.match(r"^\s*[\*\-\d\.]+\s+", sent):
        return False

    scientific_patterns = [
        r"\b(show|indicate|suggest|report|observe|demonstrate|found|conclude)s?\b",
        r"\b(associated|correlated|linked|related|coupled|interact)\b",
        r"\b(significant|evidence|study|experiment|analysis|data|findings|results)\b",
        r"\b(increase|decrease|effect|impact|influence|lead to|contribute|induce)\b",
        r"\b(CO2|levels|warming|temperature|climate|global|carbon|cycle|ocean|land)\b",
        r"\b(mechanism|process|feedback|pathway|response)\b",
        r"(表明|揭示|提示|关联|显著|研究|结果|数据|增加|减少|影响|导致|机制|过程|反馈|路径|反应)",
    ]
    return any(re.search(p, sent, re.IGNORECASE) for p in scientific_patterns)


def parse_markdown_citations(markdown_content: str) -> List[Tuple[str, str, int]]:
    """
    Parses citation keys and their surrounding context from markdown.
    Returns: List of (citation_id, context, line_number)
    """
    citations = []
    citation_group_pattern = re.compile(r"(\[[^\]]*?@[^\]]*?\])")
    key_pattern = re.compile(r"@([a-zA-Z0-9_\-:]+)")

    lines = markdown_content.split("\n")
    paragraphs = []
    current_para = []
    start_line = 1

    for i, line in enumerate(lines):
        if re.match(r"^\s*\|.*\|?\s*$", line):
            continue

        if not line.strip():
            if current_para:
                paragraphs.append({"text": " ".join(current_para), "start": start_line})
                current_para = []
        else:
            if not current_para:
                start_line = i + 1
            current_para.append(line.strip())

    if current_para:
        paragraphs.append({"text": " ".join(current_para), "start": start_line})

    for para in paragraphs:
        text = para["text"]
        s_line = para["start"]
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        for j, sent in enumerate(sentences):
            groups = citation_group_pattern.findall(sent)
            if groups:
                prev = sentences[j - 1] if j > 0 else ""
                next_s = sentences[j + 1] if j < len(sentences) - 1 else ""
                context = f"{prev} {sent} {next_s}".strip()

                for group in groups:
                    keys = key_pattern.findall(group)
                    for key in keys:
                        citations.append((key, context, s_line))
    return citations


class CitationReportReader:
    """Helper to read and index citation audit reports."""

    def __init__(self, report_path: str):
        self.report_path = report_path
        self.data = {}
        self.index = {}  # Key: (line, citation_id) -> result
        self._load()

    def _load(self):
        import json
        import os

        if not os.path.exists(self.report_path):
            return
        try:
            with open(self.report_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                for r in self.data.get("results", []):
                    key = (r.get("line"), r.get("citation_id"))
                    self.index[key] = r
        except Exception as e:
            import logging
            logging.getLogger("CitationAgent").error(
                f"Failed to load report {self.report_path}: {e}"
            )

    def get_result(self, line: int, citation_id: str) -> Dict[str, Any]:
        return self.index.get((line, citation_id))

    def get_all_results(self) -> List[Dict[str, Any]]:
        return self.data.get("results", [])


def annotate_markdown_with_results(md_content: str, results: List[Dict[str, Any]]) -> str:
    """
    Annotates markdown content with citation check results using HTML comments.
    Uses high-value actionable templates for Cline.
    """
    lines = md_content.split("\n")

    # Group results by line for efficient processing
    line_map = {}
    for r in results:
        l = r.get("line")
        if l not in line_map:
            line_map[l] = []
        line_map[l].append(r)

    new_lines = []
    for i, line in enumerate(lines):
        line_num = i + 1
        current_line = line

        if line_num in line_map:
            line_results = line_map[line_num]

            for r in line_results:
                cid = r.get("citation_id")
                ai_v = r.get("ai_verification", {})
                status = ai_v.get("status", "Unknown")
                suggestion = ai_v.get("suggestion", "")  # This now contains the high-value template

                # We want to find the citation [@key] and append a comment
                pattern = rf"(@{re.escape(cid)})"

                # Check if we already have a comment for this check to avoid duplicates
                comment_marker = f"<!-- CITATION_CHECK_ID:{cid} -->"
                if comment_marker in current_line:
                    current_line = re.sub(
                        rf"<!-- CITATION_CHECK_ID:{cid} -->.*?-->", "", current_line
                    )

                # Status-based emoji for quick visual check
                emoji = (
                    "✅"
                    if status == "Supported"
                    else "⚠️" if status in ["Unclear", "Misplaced"] else "❌"
                )

                # High-value actionable comment
                new_comment = f" <!-- CITATION_CHECK_ID:{cid} --> {emoji} {suggestion} "

                # Append after the first occurrence of the citation key on this line
                current_line = re.sub(pattern, rf"\1<!--{new_comment}-->", current_line, count=1)

        new_lines.append(current_line)

    return "\n".join(new_lines)


def get_fulltext_md_path(citation_id: str) -> str:
    """Helper to find the local Markdown fulltext path for a given citation."""
    # Try multiple common locations
    import os
    search_dirs = [
        os.path.join(os.getcwd(), "FullTextMD"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FullTextMD"),
    ]
    for base_dir in search_dirs:
        md_path = os.path.join(base_dir, citation_id, f"{citation_id}.md")
        if os.path.exists(md_path):
            return md_path
    return None


def load_fulltext_md_content(citation_id: str) -> str:
    """Loads the content of the local Markdown fulltext for a given citation."""
    path = get_fulltext_md_path(citation_id)
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            import logging
            logging.getLogger("CitationAgent").warning(
                f"Could not read local MD for {citation_id}: {e}"
            )
    return None
