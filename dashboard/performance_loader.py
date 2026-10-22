"""Read recorded Markdown benchmark results without running benchmarks."""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any


@dataclass
class PerformanceData:
    available: bool
    reason: str = ""
    table: Any = None
    environment: str = ""
    observations: str = ""
    marked_rows: list[int] = field(default_factory=list)


def _section(text: str, title: str) -> str:
    """Return section body verbatim, retaining its original whitespace."""
    match = re.search(rf"(?m)^([#]{{1,6}})[ \t]+{re.escape(title)}[ \t]*\r?\n", text)
    if not match:
        return ""
    remaining = text[match.end():]
    end = re.search(rf"(?m)^[#]{{1,{len(match[1])}}}[ \t]+", remaining)
    return remaining[:end.start()] if end else remaining


def load_performance(path: str | Path) -> PerformanceData:
    try:
        # newline='' keeps section bodies verbatim, including CRLF in reports.
        with Path(path).open(encoding="utf-8", newline="") as handle:
            text = handle.read()
    except (OSError, UnicodeError) as exc:
        return PerformanceData(False, f"Could not read benchmark report: {exc}")
    try:
        import pandas as pd

        lines = text.splitlines()
        for i in range(len(lines) - 1):
            if "|" not in lines[i]:
                continue
            headers = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            separator = [c.strip() for c in lines[i + 1].strip().strip("|").split("|")]
            if len(headers) < 2 or len(set(headers)) != len(headers) or not all(headers):
                continue
            if len(separator) != len(headers) or not all(re.fullmatch(r":?-{3,}:?", c) for c in separator):
                continue
            # Ignore unrelated prose tables; a benchmark table has Statements.
            if "Statements" not in headers:
                continue
            rows = []
            for line in lines[i + 2:]:
                if "|" not in line or not line.strip():
                    break
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) != len(headers):
                    return PerformanceData(False, "The benchmark table contains a malformed row.")
                rows.append(cells)
            if not rows:
                continue
            table = pd.DataFrame(rows, columns=headers)
            marked = []
            if "Status" in table:
                marked = table.index[table["Status"].str.contains(r"skipp|reduc", case=False, regex=True)].tolist()
            for column in table.columns:
                if column != "Status":
                    table[column] = pd.to_numeric(table[column].str.removesuffix("%"), errors="coerce")
            return PerformanceData(True, table=table, environment=_section(text, "Environment"),
                                   observations=_section(text, "Observations"), marked_rows=marked)
        return PerformanceData(False, "No readable benchmark results table was found.")
    except Exception as exc:
        return PerformanceData(False, f"Could not parse benchmark results: {exc}")
