"""Leftovers from simple-eng 0.2 (decision records, evidence, the event log, research notes) and their cleanup."""
import json
import shutil
from pathlib import Path

from . import PLUGIN_ROOT, plugin_version
from .markdown import remove_section, section
from .paths import CONFIG, PROJECT, STATE, load_config
from .scaffold import BLOCK, _with_block, claude_md_block

FOLDERS = ('decision-log', 'docs/decisions', 'docs/evidence', 'docs/resources')
OLD_SECTIONS = ((STATE, 'Pending decisions'), (PROJECT, 'Decision owners'))
OLD_BLOCK_MARKERS = ('/simple-eng:approve', 'simple-eng add-decision', 'decision-log/events.jsonl')


def stale_block(root):
    """True when the CLAUDE.md simple-eng block still tells agents to use 0.2 commands."""
    path = Path(root) / 'CLAUDE.md'
    if not path.is_file():
        return False
    m = BLOCK.search(path.read_text(encoding='utf-8'))
    return bool(m) and any(marker in m.group(0) for marker in OLD_BLOCK_MARKERS)


def resource_notes(root):
    folder = Path(root) / 'docs/resources'
    return sorted(p.relative_to(root).as_posix() for p in folder.rglob('*') if p.is_file()) if folder.is_dir() else []


def leftovers(root):
    root = Path(root)
    found = {'folders': [f for f in FOLDERS if (root / f).exists()], 'sections': [], 'block': stale_block(root),
             'notes': resource_notes(root)}
    for rel, heading in OLD_SECTIONS:
        path = root / rel
        if path.is_file() and section(path.read_text(encoding='utf-8'), heading) is not None:
            found['sections'].append(f'{rel}#{heading}')
    return found


def has_leftovers(found):
    return bool(found['folders'] or found['sections'] or found['block'])


def describe(found):
    lines = [f'delete     {folder}/' for folder in found['folders']]
    lines += [f'remove     {where}' for where in found['sections']]
    if found['block']:
        lines.append('rewrite    CLAUDE.md simple-eng block (text outside the markers is kept)')
    return lines


def apply_cleanup(root, plugin_root=PLUGIN_ROOT):
    root = Path(root)
    found = leftovers(root)
    for folder in found['folders']:
        target = root / folder
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    for where in found['sections']:
        rel, heading = where.split('#', 1)
        path = root / rel
        path.write_text(remove_section(path.read_text(encoding='utf-8'), heading), encoding='utf-8')
    if found['block']:
        path = root / 'CLAUDE.md'
        path.write_text(_with_block(path.read_text(encoding='utf-8'), claude_md_block(plugin_root)), encoding='utf-8')
        config = load_config(root)
        config['framework_version'] = plugin_version(plugin_root)
        (root / CONFIG).write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    return found


def decline_cleanup(root):
    config = load_config(root)
    config['cleanup_declined'] = True
    (Path(root) / CONFIG).write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')


def context_lines(root, config):
    """Lines for the SessionStart context: the one-time cleanup offer, and the stale-block flag that outlives a decline."""
    found = leftovers(root)
    if not has_leftovers(found):
        return []
    if config.get('cleanup_declined'):
        if not found['block']:
            return []
        return ['The CLAUDE.md simple-eng block still describes 0.2 commands that no longer exist (approve, reject, '
                'add-decision, add-evidence). Ignore those instructions, and offer to refresh the block with '
                '`simple-eng init` (dry run, then --apply after the user agrees); it changes only the marked block.']
    where = ', '.join(found['folders'] + found['sections'] + (['the CLAUDE.md block'] if found['block'] else []))
    notes = (f' First move the findings in each of the {len(found["notes"])} note(s) under docs/resources/ into the '
             'project doc it supports, with its source link and checked date; list notes that fit no document in '
             'the ask.' if found['notes'] else '')
    return [f'simple-eng 0.3 removed decision records, evidence records, the event log, and research notes. Leftovers '
            f'here: {where}. Offer the user the cleanup once, in a single ask (`simple-eng cleanup` shows the plan).'
            f'{notes} After the go-ahead run `simple-eng cleanup --apply`; if they decline, run '
            '`simple-eng cleanup --decline` and do not ask again.']
