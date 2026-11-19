"""Traceability IDs (REQ, QA, FEAT, TEST) in project documents, and the fact labels claims carry.

An ID is defined once, at a definition site (first table cell, heading, or `- ID:` line), and every other mention is a
reference that must resolve to a definition.
"""
import re
from pathlib import Path

from . import PLUGIN_ROOT
from .paths import DOCS
from .projectmap import BROKEN, document_status, load_documents

FACT_LABELS = ('verified', 'user-provided', 'inferred', 'proposed', 'unknown')

ANY_ID = re.compile(r'\b(?:REQ|QA|FEAT|TEST)-\d{4,}\b')
DEFINITION_SITES = (
    re.compile(r'^\s*\|\s*((?:REQ|QA|FEAT|TEST)-\d{4,})\s*\|'),
    re.compile(r'^\s*#{1,6}\s+((?:REQ|QA|FEAT|TEST)-\d{4,})\b'),
    re.compile(r'^\s*[-*]\s*ID:\s*((?:REQ|QA|FEAT|TEST)-\d{4,})\b', re.IGNORECASE),
)


def _markdown_files(root, extra=()):
    root = Path(root)
    files = sorted((root / DOCS).rglob('*.md')) if (root / DOCS).is_dir() else []
    for rel in extra:
        path = root / rel
        if path.is_file() and path not in files:
            files.append(path)
    return files


def scan_ids(root, extra_files=()):
    """Return (definitions, references), each mapping an ID to a list of 'path:line' locations."""
    root = Path(root)
    definitions, references = {}, {}
    for path in _markdown_files(root, extra_files):
        rel = path.relative_to(root).as_posix()
        for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            defined_here = set()
            for pattern in DEFINITION_SITES:
                m = pattern.match(line)
                if m:
                    definitions.setdefault(m.group(1), []).append(f'{rel}:{n}')
                    defined_here.add(m.group(1))
            for ref in ANY_ID.findall(line):
                if ref not in defined_here:
                    references.setdefault(ref, []).append(f'{rel}:{n}')
    return definitions, references


def validate_traceability(root, extra_files=(), plugin_root=PLUGIN_ROOT):
    root = Path(root)
    errors = []
    definitions, references = scan_ids(root, extra_files)
    for ident, sites in sorted(definitions.items()):
        if len(sites) > 1:
            errors.append(f'{ident} is defined more than once: {", ".join(sites)}')
    for ident, sites in sorted(references.items()):
        if ident not in definitions:
            errors.append(f'{ident} is referenced but never defined ({", ".join(sites[:3])})')
    for doc in load_documents(plugin_root):
        found = document_status(root, doc)
        if found['status'] == BROKEN:
            errors.append(found['detail'])
    return errors
