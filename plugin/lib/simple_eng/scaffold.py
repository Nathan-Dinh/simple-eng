"""Project setup for /simple-eng:init and `simple-eng docs`. Dry run by default; only the marked CLAUDE.md block is ever replaced."""
import datetime as dt
import difflib
import json
import re
from pathlib import Path

from . import PLUGIN_ROOT, plugin_version
from . import annotations
from .paths import ANNOTATIONS, AREAS, CONFIG, PROJECT, STATE, load_config
from .projectmap import MISSING, NOT_APPLICABLE, load_documents, status_report

PROJECT_AREA = 'project'
PROJECT_AREA_DESCRIPTION = 'Project-wide docs, configuration, and tooling that belong to no single business area'
PURPOSES = {'CLAUDE.md': 'Instructions Claude Code loads in every session, including the simple-eng rules block',
            PROJECT: 'Stable project facts: problem and users, scope, constraints, stack, commands, environments',
            STATE: 'Working state for the next session: current focus, checkpoints, open questions, recent changes'}

START = '<!-- simple-eng:start version={version} -->'
END = '<!-- simple-eng:end -->'
BLOCK = re.compile(r'<!-- simple-eng:start[^>]*-->.*?<!-- simple-eng:end -->', re.DOTALL)


def claude_md_block(plugin_root=PLUGIN_ROOT):
    body = (Path(plugin_root) / 'reference/templates/claude-md-block.md').read_text(encoding='utf-8').strip()
    return f'{START.format(version=plugin_version(plugin_root))}\n{body}\n{END}'


def _with_block(existing, block):
    if existing is None:
        return block + '\n'
    if BLOCK.search(existing):
        return BLOCK.sub(lambda _: block, existing, count=1)
    if '<!-- simple-eng:start' in existing:
        raise ValueError('CLAUDE.md has a simple-eng start marker but no end marker; restore '
                         f'"{END}" after the block (or delete the partial block), then run init again')
    return existing.rstrip('\n') + ('\n\n' if existing.strip() else '') + block + '\n'


def _plan(root, rel, new):
    path = Path(root) / rel
    old = path.read_text(encoding='utf-8') if path.is_file() else None
    if old == new:
        return {'path': rel, 'action': 'unchanged', 'content': new, 'diff': ''}
    diff = ''.join(difflib.unified_diff((old or '').splitlines(True), new.splitlines(True),
                                        fromfile=f'a/{rel}' if old is not None else '/dev/null', tofile=f'b/{rel}'))
    return {'path': rel, 'action': 'update' if old is not None else 'create', 'content': new, 'diff': diff}


def _template(plugin_root, name):
    return (Path(plugin_root) / 'reference' / 'templates' / name).read_text(encoding='utf-8')


def planned_changes(root, plugin_root=PLUGIN_ROOT):
    root = Path(root)
    changes = []

    def plan(rel, new):
        changes.append(_plan(root, rel, new))

    config = load_config(root)
    config.setdefault('initialized', dt.date.today().isoformat())
    config['framework_version'] = plugin_version(plugin_root)
    config.setdefault('areas', {})
    config.setdefault('stage', 'prototype')
    config.setdefault('agent_threshold', 15)
    config.setdefault('annotation_exclude', list(annotations.DEFAULT_EXCLUDE))
    plan(CONFIG, json.dumps(config, indent=2) + '\n')
    for rel, empty in ((ANNOTATIONS, ''), (AREAS, json.dumps({'areas': {PROJECT_AREA: PROJECT_AREA_DESCRIPTION}}, indent=2) + '\n')):
        if not (root / rel).exists():
            plan(rel, empty)
    claude = root / 'CLAUDE.md'
    plan('CLAUDE.md', _with_block(claude.read_text(encoding='utf-8') if claude.is_file() else None, claude_md_block(plugin_root)))
    for rel, template in ((PROJECT, 'project.md'), (STATE, 'state.md')):
        if not (root / rel).exists():
            plan(rel, _template(plugin_root, template))
    return changes


def planned_docs(root, plugin_root=PLUGIN_ROOT):
    """Create the project documents that are missing, from their templates. An existing document is never touched,
    and a document is skipped while its legacy record still exists (migrate that first) or its area does not apply."""
    root = Path(root)
    report = {d['id']: d for d in status_report(root, plugin_root)['documents']}
    today = dt.date.today().isoformat()
    changes = []
    for doc in load_documents(plugin_root):
        found = report[doc['id']]
        if found['status'] == NOT_APPLICABLE:
            changes.append({'path': doc['path'], 'action': 'skip', 'content': '', 'diff': '',
                            'reason': f'not applicable: {found["detail"]}'})
        elif found['status'] != MISSING:
            changes.append({'path': doc['path'], 'action': 'unchanged', 'content': '', 'diff': ''})
        elif 'legacy file' in found['detail']:
            changes.append({'path': doc['path'], 'action': 'skip', 'content': '', 'diff': '', 'reason': found['detail']})
        else:
            text = _template(plugin_root, doc['template']).replace('- Last updated:', f'- Last updated: {today}', 1)
            changes.append(_plan(root, doc['path'], text))
    return changes


def apply_changes(root, changes):
    for change in changes:
        if change['action'] in ('unchanged', 'skip'):
            continue
        path = Path(root) / change['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(change['content'], encoding='utf-8')


def annotate_scaffold(root, plugin_root=PLUGIN_ROOT):
    """Annotate the files simple-eng creates (CLAUDE.md, PROJECT.md, STATE.md, project documents) when they have no
    annotation yet, so a fresh setup leaves the index complete. Skipped if the project area was removed."""
    root = Path(root)
    if PROJECT_AREA not in annotations.load_areas(root):
        return []
    purposes = dict(PURPOSES)
    for doc in load_documents(plugin_root):
        purposes[doc['path']] = f'Project document: the {doc["title"]}'
    records = annotations.load(root)
    items = [{'path': rel, 'purpose': purpose, 'area': PROJECT_AREA} for rel, purpose in purposes.items()
             if rel not in records and (root / rel).is_file()]
    return annotations.annotate_many(root, items) if items else []
