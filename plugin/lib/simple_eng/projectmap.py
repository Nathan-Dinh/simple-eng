"""Knowledge areas a project should record, the project documents that hold them, and whether each one is recorded.

Status only checks presence and structure. Whether the recorded content is correct is for the user to confirm.
"""
import json
import re
from pathlib import Path

from . import PLUGIN_ROOT
from .markdown import meaningful_lines, not_applicable_reason, parse_frontmatter, section, strip_comments
from .paths import load_config

PRESENT, MISSING, NOT_APPLICABLE, BROKEN = 'present', 'missing', 'not applicable', 'broken'
DOC_STATUSES = ('draft', 'reviewed')
DOC_STATUS = re.compile(r'^[ \t]*[-*][ \t]*Status:[ \t]*(.*?)[ \t]*$', re.MULTILINE)


def _map(plugin_root):
    return json.loads((Path(plugin_root) / 'reference/project-map.json').read_text(encoding='utf-8'))


def load_map(plugin_root=PLUGIN_ROOT):
    return _map(plugin_root)['areas']


def load_documents(plugin_root=PLUGIN_ROOT):
    return _map(plugin_root).get('documents', [])


def split_record(record):
    path, _, heading = record.partition('#')
    return path, heading


def area_record(area, config):
    override = (config.get('areas') or {}).get(area['id'], {})
    record = override.get('record') if isinstance(override, dict) else None
    return (record or area['record']), bool(record)


def area_status(root, area, config):
    record, overridden = area_record(area, config)
    path, heading = split_record(record)
    result = {'id': area['id'], 'record': record, 'source': area['source'],
              'question': area['question'], 'applies_when': area.get('applies_when')}
    override = (config.get('areas') or {}).get(area['id'], {})
    if isinstance(override, dict) and str(override.get('not_applicable', '')).strip():
        return dict(result, status=NOT_APPLICABLE, detail=override['not_applicable'].strip())
    file = Path(root) / path
    if not file.is_file():
        return dict(result, status=BROKEN if overridden else MISSING,
                    detail=f'{path} does not exist' + (' (configured override)' if overridden else ''))
    text = file.read_text(encoding='utf-8')
    body = section(text, heading) if heading else text
    if body is None:
        return dict(result, status=MISSING, detail=f'no "{heading}" heading in {path}')
    reason = not_applicable_reason(body)
    if reason:
        return dict(result, status=NOT_APPLICABLE, detail=reason)
    if not meaningful_lines(body):
        return dict(result, status=MISSING, detail=f'"{heading or path}" has no recorded content')
    return dict(result, status=PRESENT, detail='')


def workflow_needs(workflow, plugin_root=PLUGIN_ROOT):
    skill = Path(plugin_root) / 'skills' / workflow / 'SKILL.md'
    if not skill.is_file():
        raise ValueError(f'unknown workflow {workflow!r}')
    meta, _ = parse_frontmatter(skill.read_text(encoding='utf-8'))
    return list(meta.get('needs', []))


def document_status(root, doc, area=None):
    """A project document is missing, draft, reviewed, or not applicable (when its main area is). A Status other
    than draft or reviewed is broken."""
    result = {'id': doc['id'], 'title': doc['title'], 'path': doc['path']}
    if area and area['status'] == NOT_APPLICABLE:
        return dict(result, status=NOT_APPLICABLE, detail=area['detail'])
    file = Path(root) / doc['path']
    if not file.is_file():
        legacy = [rel for rel in doc.get('legacy', []) if (Path(root) / rel).is_file()]
        detail = (f'legacy file {legacy[0]} found; migrate it with simple-eng:project-docs' if legacy
                  else f'{doc["path"]} does not exist')
        return dict(result, status=MISSING, detail=detail)
    m = DOC_STATUS.search(strip_comments(file.read_text(encoding='utf-8')))
    if not m or m.group(1).lower() not in DOC_STATUSES:
        found = repr(m.group(1)) if m else 'no "- Status:" line'
        return dict(result, status=BROKEN, detail=f'{doc["path"]}: Status must be draft or reviewed (found {found})')
    return dict(result, status=m.group(1).lower(), detail='')


def status_report(root, plugin_root=PLUGIN_ROOT, workflow=None):
    config = load_config(root)
    areas = [area_status(root, area, config) for area in load_map(plugin_root)]
    by_id = {a['id']: a for a in areas}
    documents = [document_status(root, doc, by_id.get(doc.get('area'))) for doc in load_documents(plugin_root)]
    report = {'areas': areas, 'documents': documents, 'workflow': workflow, 'blocking': []}
    if workflow:
        needs = set(workflow_needs(workflow, plugin_root))
        report['blocking'] = [a['id'] for a in areas if a['id'] in needs and a['status'] in (MISSING, BROKEN)]
    return report


def render_status(report):
    lines = ['Knowledge areas (presence and structure only; correctness is for the user to confirm):']
    for a in report['areas']:
        note = f' ({a["detail"]})' if a['detail'] and a['status'] != PRESENT else ''
        cond = f' [applies when {a["applies_when"]}]' if a.get('applies_when') and a['status'] in (MISSING, BROKEN) else ''
        lines.append(f'- {a["id"]}: {a["status"]} -> {a["record"]}{note}{cond}')
    gaps = [a for a in report['areas'] if a['status'] in (MISSING, BROKEN)]
    if gaps:
        lines.append('Missing areas to investigate in the repository first: '
                     + (', '.join(a['id'] for a in gaps if a['source'] == 'investigate') or 'none'))
        lines.append('Missing areas only a person can answer: '
                     + (', '.join(a['id'] for a in gaps if a['source'] == 'ask') or 'none'))
    if report['workflow']:
        blocking = ', '.join(report['blocking']) or 'none'
        lines.append(f'Missing areas that block {report["workflow"]}: {blocking}')
    if report.get('documents'):
        lines.append('Project documents (simple-eng:project-docs drafts and fills them):')
        for d in report['documents']:
            note = f' ({d["detail"]})' if d['detail'] else ''
            lines.append(f'- {d["title"]}: {d["status"]} -> {d["path"]}{note}')
    return '\n'.join(lines)


def summary_line(report):
    groups = {}
    for a in report['areas']:
        key = f'missing ({a["source"]})' if a['status'] == MISSING else a['status']
        groups.setdefault(key, []).append(a['id'])
    order = ('missing (investigate)', 'missing (ask)', BROKEN, NOT_APPLICABLE, PRESENT)
    return '; '.join(f'{key}: {", ".join(groups[key])}' for key in order if key in groups)


def documents_line(report):
    groups = {}
    for d in report.get('documents', []):
        groups.setdefault(d['status'], []).append(d['id'])
    order = (MISSING, BROKEN, 'draft', 'reviewed', NOT_APPLICABLE)
    return '; '.join(f'{key}: {", ".join(groups[key])}' for key in order if key in groups)
