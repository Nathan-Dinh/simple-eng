"""Project-specific agents: `se-` agents in .claude/agents/, one per large area of the annotation index.

simple-eng only proposes, updates, merges, or retires agents named `se-*`; agents the user wrote are never touched.
This module reports; the lead creates or changes agent files only after the user agrees.
"""
from pathlib import Path

from . import annotations
from .markdown import parse_frontmatter
from .paths import load_config

AGENTS_DIR = '.claude/agents'
PREFIX = 'se-'
DEFAULT_THRESHOLD = 15
SHARED_AREAS = ('project',)


def project_agents(root):
    folder = Path(root) / AGENTS_DIR
    found = {}
    for path in sorted(folder.glob(f'{PREFIX}*.md')) if folder.is_dir() else []:
        try:
            meta, _ = parse_frontmatter(path.read_text(encoding='utf-8'))
        except ValueError:
            meta = {}
        found[path.stem] = {'path': path.relative_to(root).as_posix(), 'area': meta.get('area', '')}
    return found


def report(root):
    """Areas big enough for an agent that have none, and agents whose area is gone or has shrunk."""
    threshold = int(load_config(root).get('agent_threshold', DEFAULT_THRESHOLD))
    areas = annotations.load_areas(root)
    sizes = {name: 0 for name in areas}
    for record in annotations.load(root).values():
        if record.get('area') in sizes:
            sizes[record['area']] += 1
    agents = project_agents(root)
    covered = {a['area'] for a in agents.values()}
    out = {'threshold': threshold, 'agents': [], 'propose': [], 'retire': [], 'shrunk': []}
    for name, agent in agents.items():
        area = agent['area']
        out['agents'].append({'name': name, 'path': agent['path'], 'area': area, 'files': sizes.get(area, 0)})
        if area not in areas:
            out['retire'].append({'name': name, 'area': area, 'reason': 'its area is not in .simple-eng/areas.json '
                                  '(renamed, merged, or removed)' if area else 'it has no "area:" in its frontmatter'})
        elif sizes[area] < max(threshold // 3, 1):
            out['shrunk'].append({'name': name, 'area': area, 'files': sizes[area]})
    for name in sorted(areas):
        if name not in covered and name not in SHARED_AREAS and sizes[name] >= threshold:
            out['propose'].append({'name': PREFIX + name, 'area': name, 'files': sizes[name]})
    return out


def validation_errors(root):
    return [f'{AGENTS_DIR}/{r["name"]}.md: {r["reason"]}' for r in report(root)['retire']]


def context_line(root):
    found = report(root)
    parts = [f'propose {p["name"]} ({p["files"]} files)' for p in found['propose']]
    parts += [f'update or retire {r["name"]} ({r["reason"]})' for r in found['retire']]
    parts += [f'consider merging or retiring {s["name"]} (only {s["files"]} files)' for s in found['shrunk']]
    if not parts:
        return []
    return ['Project agents to review with the user (`simple-eng agents`; see simple-eng:lead): ' + '; '.join(parts) + '.']


def render(found):
    lines = [f'Areas with at least {found["threshold"]} annotated files get a project agent '
             '(set "agent_threshold" in .simple-eng/config.json).']
    for agent in found['agents']:
        lines.append(f'- {agent["name"]} -> area {agent["area"] or "(none)"}, {agent["files"]} files ({agent["path"]})')
    if not found['agents']:
        lines.append('- no se- agents yet')
    for p in found['propose']:
        lines.append(f'Propose {p["name"]}: area {p["area"]} has {p["files"]} files.')
    for r in found['retire']:
        lines.append(f'Update or retire {r["name"]}: {r["reason"]}.')
    for s in found['shrunk']:
        lines.append(f'Consider merging or retiring {s["name"]}: area {s["area"]} has only {s["files"]} files.')
    lines.append('This command never writes. Create, update, merge, or retire an agent only after the user agrees.')
    return '\n'.join(lines)
