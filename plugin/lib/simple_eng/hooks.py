"""Claude Code hook entry points. Each reads the hook's JSON from stdin and prints the hook's output.

- session-start: prints the project context (plain text is added to Claude's context).
- post-tool-use: after a file edit, checks that file's annotation and reports drift back to Claude.
- stop: when Claude finishes, checks every file git reports as changed (catching `git mv` and `rm`), and asks Claude
  to fix the annotations before stopping. It only reports on a second stop, so it cannot loop.

Plugin hooks fire in every repository where the plugin is enabled, so `run` skips projects that never ran init.
All paths are resolved from the project root, whatever directory the hook runs in.
"""
import json
import os
import subprocess
from pathlib import Path

from . import annotations
from .context import build_context
from .paths import is_initialized, project_root


def _root(payload):
    return project_root(os.environ.get('CLAUDE_PROJECT_DIR') or payload.get('cwd'))


def session_start(payload):
    try:
        return build_context(_root(payload))
    except Exception as exc:  # a broken project must never break session start
        return f'simple-eng: could not build project context ({exc}). Run `simple-eng validate` for details.'


def _instructions(root, problems):
    lines = []
    areas = ', '.join(sorted(annotations.load_areas(root))) or 'none yet; add one with `simple-eng areas add`'
    for p in problems:
        rel, kind = p['path'], p['kind']
        if kind == annotations.MISSING:
            lines.append(f'- {rel} has no annotation: `simple-eng annotate {rel} --purpose "..." --area <area> '
                         f'[--layer ...] [--symbol ...] [--link ...]` (areas: {areas}).')
        elif kind == annotations.DRIFT:
            lines.append(f'- {rel} changed since it was annotated; its imports were refreshed. Check its purpose, area, '
                         f'layer, symbols, and other links still match, then `simple-eng annotate {rel} --confirm` '
                         '(or pass the fields that changed).')
        elif kind == annotations.ORPHAN:
            lines.append(f'- {rel} is annotated but {p["detail"]}: if it moved, annotate the new path; then '
                         f'`simple-eng annotate --remove {rel}`.')
        elif kind == annotations.UNKNOWN_AREA:
            lines.append(f'- {rel} uses area {p["detail"]}, which is not listed: `simple-eng annotate {rel} --area <area>` '
                         f'or `simple-eng areas add {p["detail"]} "description"`.')
        elif kind == annotations.BROKEN_LINK:
            lines.append(f'- {rel} links to missing files ({p["detail"]}): update its links with '
                         f'`simple-eng annotate {rel} --link ...` or `--confirm` to refresh imports.')
    return '\n'.join(lines)


def _relative(root, path):
    if not path:
        return None
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix() if Path(path).is_absolute() \
            else Path(path).as_posix()
    except ValueError:
        return None


def post_tool_use(payload):
    root = _root(payload)
    data = payload.get('tool_input') if isinstance(payload.get('tool_input'), dict) else {}
    rel = _relative(root, data.get('file_path') or data.get('notebook_path'))
    if not rel:
        return None
    problems = annotations.check(root, [rel])
    if not problems:
        return None
    if any(p['kind'] == annotations.DRIFT for p in problems):
        annotations.refresh_imports(root, rel)
    return {'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext':
            'simple-eng annotation index: update it in this same change.\n' + _instructions(root, problems)}}


def changed_paths(root):
    """Paths git reports as changed, including both sides of a rename and untracked files."""
    try:
        out = subprocess.run(['git', '-C', str(root), 'status', '--porcelain=v1', '-z', '--untracked-files=all'],
                             capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    tokens = out.stdout.decode('utf-8', 'surrogateescape').split('\0')
    paths, i = [], 0
    while i < len(tokens):
        entry = tokens[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if entry[0] in 'RC' or entry[1] in 'RC':
            paths.append(tokens[i])
            i += 1
    return sorted({p for p in paths if p and not p.startswith(annotations.ALWAYS_EXCLUDE)})


def stop(payload):
    root = _root(payload)
    paths = changed_paths(root)
    if not paths:
        return None
    problems = annotations.check(root, paths)
    if not problems:
        return None
    for p in problems:
        if p['kind'] == annotations.DRIFT:
            annotations.refresh_imports(root, p['path'])
    if payload.get('stop_hook_active'):
        return {'systemMessage': f'simple-eng: the annotation index is still out of date for {len(problems)} '
                                 'changed file(s). Run `simple-eng validate` for details.'}
    return {'decision': 'block', 'reason': 'simple-eng: the annotation index does not match the files changed in this '
            'session. Fix it before finishing:\n' + _instructions(root, problems)}


HANDLERS = {'session-start': session_start, 'post-tool-use': post_tool_use, 'stop': stop}


def run(name, stdin):
    try:
        payload = json.loads(stdin or '{}')
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    if not is_initialized(_root(payload)):
        return ''
    try:
        result = HANDLERS[name](payload)
    except Exception as exc:  # a hook must never break the session
        return json.dumps({'systemMessage': f'simple-eng {name} hook failed: {exc}. Run `simple-eng validate`.'})
    if result is None:
        return ''
    return result if isinstance(result, str) else json.dumps(result)
