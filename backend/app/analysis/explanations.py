"""Deterministic Explanation Generator.

Produces fact-based, transparent explanations from parsed symbols,
line changes, and statically resolved callers without LLMs.
"""

from typing import Dict, List
from app.models.schemas import Explanation, Relationship, Symbol


def generate_explanations(
    changed_symbols: List[Symbol],
    affected_symbols: List[Symbol],
    relationships: List[Relationship],
) -> List[Explanation]:
    """Generate structured explanations for changed symbols."""
    explanations: List[Explanation] = []

    # Map relationships by target
    callers_by_target: Dict[str, List[str]] = {}
    for rel in relationships:
        callers_by_target.setdefault(rel.target, []).append(rel.source)

    for sym in changed_symbols:
        callers = callers_by_target.get(sym.qualified_name, [])
        caller_count = len(callers)

        lines_str = f"{sym.start_line}-{sym.end_line}"
        if sym.start_line == sym.end_line:
            lines_str = str(sym.start_line)

        lines = [
            f"Changed symbol: {sym.name} ({sym.qualified_name})",
            f"File: {sym.file_path}",
            f"Lines: {lines_str}",
            f"Type: {sym.type}",
            "",
            "This symbol changed in the supplied unified diff.",
        ]

        if caller_count == 0:
            lines.append("It has 0 statically detectable direct caller(s) in this repository.")
        else:
            lines.append(f"It has {caller_count} statically detectable direct caller(s): {', '.join(sorted(callers))}.")
            lines.append(f"Potential impact includes: {', '.join(sorted(callers))}.")

        text = "\n".join(lines)

        explanations.append(
            Explanation(
                symbol=sym.qualified_name,
                file=sym.file_path,
                lines=lines_str,
                caller_count=caller_count,
                affected_symbols=sorted(callers),
                text=text,
            )
        )

    explanations.sort(key=lambda exp: (exp.file, exp.symbol))
    return explanations
