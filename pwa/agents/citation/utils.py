# -*- coding: utf-8 -*-
import re
from typing import Any, Dict, List


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
