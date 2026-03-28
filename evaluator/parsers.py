"""File parsers for .log, .txt, .doc/.docx, and .pdf formats."""

import re
from pathlib import Path


def parse_log(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def parse_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


PARSERS = {
    ".log": parse_log,
    ".txt": parse_txt,
    ".doc": parse_docx,
    ".docx": parse_docx,
    ".pdf": parse_pdf,
}


def read_log_file(path: str) -> str:
    """Read and return text content from a supported log file."""
    p = Path(path)
    suffix = p.suffix.lower()
    parser = PARSERS.get(suffix)
    if parser is None:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Supported types: {', '.join(PARSERS)}"
        )
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return parser(p)


def extract_prompts(raw_text: str) -> list[str]:
    """
    Heuristically extract user prompts from a raw log.

    Handles common patterns from Claude Code, GitHub Copilot, Cursor, etc.
    """
    prompts: list[str] = []

    # Pattern 1: Claude Code format  →  ❯ (user input) / ⏺ (agent response)
    # User turns start with ❯, agent turns start with ⏺ — capture only user turns.
    claude_code_pattern = re.compile(
        r"(?:^|\n)❯\s*(.+?)(?=\n[❯⏺]|\Z)",
        re.DOTALL,
    )
    matches = claude_code_pattern.findall(raw_text)
    if matches:
        prompts = [m.strip() for m in matches if m.strip()]

    # Pattern 2: explicit role markers  →  Human: / User: / user:
    if not prompts:
        role_pattern = re.compile(
            r"(?:^|\n)(?:Human|User|user)\s*[:\|>]\s*(.+?)(?=\n(?:Human|User|user|Assistant|assistant|AI|System)\s*[:\|>]|\Z)",
            re.DOTALL,
        )
        prompts = [m.strip() for m in role_pattern.findall(raw_text) if m.strip()]

    # Pattern 3: timestamp-prefixed log lines  →  [2024-01-01 12:00:00] User: ...
    if not prompts:
        ts_pattern = re.compile(
            r"\[\d{4}[-/]\d{2}[-/]\d{2}[^\]]*\]\s*(?:User|Human|Prompt)\s*[:\|>]\s*(.+)",
            re.IGNORECASE,
        )
        prompts = [m.strip() for m in ts_pattern.findall(raw_text) if m.strip()]

    # Pattern 4: Copilot-style  →  // Prompt: ... or # Prompt:
    if not prompts:
        copilot_pattern = re.compile(
            r"(?://|#)\s*(?:Prompt|prompt)\s*[:\|>]\s*(.+)", re.IGNORECASE
        )
        prompts = [m.strip() for m in copilot_pattern.findall(raw_text) if m.strip()]

    # Fallback: treat the entire content as one prompt block
    if not prompts:
        prompts = [raw_text.strip()]

    return prompts
