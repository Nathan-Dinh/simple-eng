"""The annotation index: one JSON line per project file in .simple-eng/annotations.jsonl, sorted by path.

Each annotation holds the file's purpose, area, layer, key symbols, dependencies, and content hash. Imports come from a
parser (Python through `ast`, JS/TS through a regex over relative specifiers), so they are exact and free; other links
(a route to its view, code that reads a table) are written by a model. "Used by" is derived by reversing both.
"""
import ast
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from .paths import ANNOTATIONS, AREAS, load_config

FIELDS = ('path', 'purpose', 'area', 'layer', 'symbols', 'imports', 'links', 'hash')
LAYERS = ('Presentation', 'Application', 'Domain', 'Infrastructure')
AREA_NAME = re.compile(r'^[a-z0-9][a-z0-9-]*$')
DEFAULT_EXCLUDE = [
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'Pipfile.lock', 'uv.lock', 'Cargo.lock',
    'Gemfile.lock', 'composer.lock', 'go.sum', '*.min.js', '*.min.css', '*.map',
    'node_modules', 'vendor', 'dist', 'build', '__pycache__',
]
ALWAYS_EXCLUDE = ('.simple-eng/', '.git/')
MISSING, ORPHAN, DRIFT, UNKNOWN_AREA, BROKEN_LINK = 'missing', 'orphan', 'drift', 'unknown area', 'broken link'
KIND_LABELS = {MISSING: 'have no annotation', ORPHAN: 'are annotated but no longer exist',
               DRIFT: 'changed since they were annotated', UNKNOWN_AREA: 'use an area not in .simple-eng/areas.json',
               BROKEN_LINK: 'link to files that do not exist'}
JS_SUFFIXES = ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')
JS_SPECIFIER = re.compile(r'''(?:\bimport\s+(?:[\w*{}\s,$]+?\s+from\s+)?|\bexport\s+[\w*{}\s,$]+?\s+from\s+|'''
                          r'''\bimport\s*\(\s*|\brequire\s*\(\s*)['"]([^'"\n]+)['"]''')


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def is_binary(path):
    try:
        with open(path, 'rb') as f:
            return b'\0' in f.read(8192)
    except OSError:
        return True


def excluded(rel, patterns):
    if rel.startswith(ALWAYS_EXCLUDE):
        return True
    parts = rel.split('/')
    for pattern in patterns:
        if '/' in pattern.strip('/'):
            if fnmatch.fnmatch(rel, pattern.strip('/')) or fnmatch.fnmatch(rel, pattern.strip('/') + '/*'):
                return True
        elif any(fnmatch.fnmatch(part, pattern.strip('/')) for part in parts):
            return True
    return False


def _listed_files(root):
    try:
        out = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                             capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        out = None
    if out is not None and out.returncode == 0:
        return [p for p in out.stdout.decode('utf-8', 'surrogateescape').split('\0') if p]
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != '.git']
        found += [Path(dirpath, name).relative_to(root).as_posix() for name in filenames]
    return found


def exclusions(root):
    patterns = load_config(root).get('annotation_exclude')
    return list(DEFAULT_EXCLUDE if patterns is None else patterns)


def project_files(root):
    """Files that should carry an annotation: tracked or untracked-but-not-ignored, minus exclusions and binaries."""
    root = Path(root)
    patterns = exclusions(root)
    return sorted({rel for rel in _listed_files(root)
                   if not excluded(rel, patterns) and (root / rel).is_file() and not is_binary(root / rel)})


def annotatable(root, rel):
    path = Path(root) / rel
    return path.is_file() and not excluded(rel, exclusions(root)) and not is_binary(path)


# --- index and areas files -------------------------------------------------------------------------------------------

def load(root):
    path = Path(root) / ANNOTATIONS
    if not path.is_file():
        return {}
    records = {}
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError as exc:
            raise ValueError(f'{ANNOTATIONS} line {n}: invalid JSON: {exc}') from exc
        if not isinstance(record, dict) or not isinstance(record.get('path'), str):
            raise ValueError(f'{ANNOTATIONS} line {n}: each line must be an object with a "path"')
        records[record['path']] = record
    return records


def _normalized(record):
    out = {key: record.get(key, [] if key in ('layer', 'symbols', 'imports', 'links') else '') for key in FIELDS}
    for key in ('imports', 'links'):
        out[key] = sorted(set(out[key]))
    return out


def save(root, records):
    path = Path(root) / ANNOTATIONS
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(_normalized(records[rel]), ensure_ascii=False) for rel in sorted(records)]
    path.write_text(''.join(line + '\n' for line in lines), encoding='utf-8')


def load_areas(root):
    path = Path(root) / AREAS
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as exc:
        raise ValueError(f'{AREAS} is not valid JSON: {exc}') from exc
    areas = data.get('areas') if isinstance(data, dict) else None
    if not isinstance(areas, dict):
        raise ValueError(f'{AREAS} must contain {{"areas": {{"name": "description", ...}}}}')
    return areas


def save_areas(root, areas):
    path = Path(root) / AREAS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'areas': dict(sorted(areas.items()))}, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')


def add_area(root, name, description):
    if not AREA_NAME.match(name):
        raise ValueError(f'area name {name!r} must be lowercase letters, digits, and hyphens (for example "payments")')
    if not description.strip():
        raise ValueError('an area needs a one-line description')
    areas = load_areas(root)
    areas[name] = ' '.join(description.split())
    save_areas(root, areas)


def _move_area(root, old, new, description=None):
    areas = load_areas(root)
    if old not in areas:
        raise ValueError(f'unknown area {old!r}')
    if not AREA_NAME.match(new):
        raise ValueError(f'area name {new!r} must be lowercase letters, digits, and hyphens')
    keep = areas.pop(old)
    areas[new] = description if description is not None else areas.get(new, keep)
    records = load(root)
    changed = [rel for rel, r in records.items() if r.get('area') == old]
    for rel in changed:
        records[rel]['area'] = new
    save(root, records)
    save_areas(root, areas)
    return changed


def rename_area(root, old, new):
    if new in load_areas(root):
        raise ValueError(f'area {new!r} already exists; use merge to combine areas')
    return _move_area(root, old, new)


def merge_areas(root, source, target):
    if target not in load_areas(root):
        raise ValueError(f'unknown area {target!r}; merge into an existing area')
    if source == target:
        raise ValueError('cannot merge an area into itself')
    return _move_area(root, source, target)


# --- import parser ---------------------------------------------------------------------------------------------------

def python_module_index(files):
    """Map dotted module names to files. A name starts at the root or at a directory that is not a package."""
    fileset = set(files)
    index = {}
    for rel in files:
        if not rel.endswith('.py'):
            continue
        parts = rel[:-3].split('/')
        if parts[-1] == '__init__':
            parts = parts[:-1]
        for i in range(len(parts)):
            if i and '/'.join(parts[:i]) + '/__init__.py' in fileset:
                continue
            index.setdefault('.'.join(parts[i:]), []).append((i, rel))
    return index


def _lookup(index, name):
    found = index.get(name, [])
    if not found:
        return None
    if name.split('.')[0] in getattr(sys, 'stdlib_module_names', ()):
        found = [f for f in found if f[0] == 0]
    best = min((f[0] for f in found), default=None)
    winners = [rel for start, rel in found if start == best]
    return winners[0] if len(winners) == 1 else None


def _python_relative(rel, level, module, fileset):
    base = rel.split('/')[:-1]
    if level > 1:
        base = base[:-(level - 1)] if level - 1 <= len(base) else None
    if base is None:
        return []
    stem = '/'.join(base + (module.split('.') if module else []))
    return [c for c in (stem + '.py', stem + '/__init__.py') if c.strip('/') in fileset]


def python_imports(root, rel, fileset, index=None):
    index = index if index is not None else python_module_index(fileset)
    try:
        tree = ast.parse((Path(root) / rel).read_bytes())
    except (SyntaxError, ValueError):
        return []
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = _lookup(index, alias.name)
                if hit:
                    found.add(hit)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                for alias in node.names:
                    sub = '.'.join(filter(None, [node.module, alias.name]))
                    hits = _python_relative(rel, node.level, sub, fileset) if alias.name != '*' else []
                    found.update(hits or _python_relative(rel, node.level, node.module or '', fileset))
            elif node.module:
                for alias in node.names:
                    hit = _lookup(index, f'{node.module}.{alias.name}') or _lookup(index, node.module)
                    if hit:
                        found.add(hit)
    found.discard(rel)
    return sorted(p.strip('/') for p in found)


def _js_candidates(stem):
    yield stem
    for suffix in JS_SUFFIXES:
        yield stem + suffix
    for suffix in JS_SUFFIXES:
        yield f'{stem}/index{suffix}'
    for js, ts in (('.js', '.ts'), ('.js', '.tsx'), ('.jsx', '.tsx'), ('.mjs', '.mts'), ('.cjs', '.cts')):
        if stem.endswith(js):
            yield stem[:-len(js)] + ts


def js_imports(root, rel, fileset):
    try:
        text = (Path(root) / rel).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return []
    base = rel.split('/')[:-1]
    found = set()
    for spec in JS_SPECIFIER.findall(text):
        if not spec.startswith(('./', '../')):
            continue
        parts = list(base)
        for piece in spec.split('/'):
            if piece in ('', '.'):
                continue
            if piece == '..':
                if not parts:
                    parts = None
                    break
                parts.pop()
            else:
                parts.append(piece)
        if parts is None:
            continue
        for candidate in _js_candidates('/'.join(parts)):
            if candidate in fileset:
                found.add(candidate)
                break
    found.discard(rel)
    return sorted(found)


def imports(root, rel, fileset=None, index=None):
    """Project files that `rel` imports, from the parser. Empty for languages the parser does not cover."""
    fileset = set(project_files(root)) if fileset is None else fileset
    if rel.endswith('.py'):
        return python_imports(root, rel, fileset, index)
    if rel.endswith(JS_SUFFIXES):
        return js_imports(root, rel, fileset)
    return []


# --- writing annotations ---------------------------------------------------------------------------------------------

def resolve_path(root, given, cwd=None):
    """A path argument as a project-relative path. Relative arguments are tried against the project root first, then
    against the current directory, so commands work from any directory inside the project."""
    root = Path(root).resolve()
    raw = Path(given)
    options = [raw] if raw.is_absolute() else [root / raw, Path(cwd or os.getcwd()) / raw]
    rels = []
    for option in options:
        try:
            rels.append(option.resolve().relative_to(root).as_posix())
        except ValueError:
            continue
    if not rels:
        raise ValueError(f'{given} is outside the project {root}')
    records = load(root)
    return next((rel for rel in rels if (root / rel).exists() or rel in records), rels[0])


def _layers(values):
    out = []
    for value in values or ():
        match = next((layer for layer in LAYERS if layer.lower() == str(value).strip().lower()), None)
        if not match:
            raise ValueError(f'layer {value!r} must be one of {", ".join(LAYERS)}')
        if match not in out:
            out.append(match)
    return out


def annotate(root, rel, *, purpose=None, area=None, layer=None, symbols=None, links=None, records=None,
             files=None, index=None):
    """Create or update one annotation. Imports and the hash are recomputed from the current file, because writing an
    annotation means the file was just read. Fields left as None keep their current value."""
    root = Path(root)
    save_now = records is None
    records = load(root) if records is None else records
    files = set(project_files(root)) if files is None else files
    if rel not in files:
        if not (root / rel).is_file():
            raise ValueError(f'{rel} does not exist')
        raise ValueError(f'{rel} is excluded from the index (generated, vendored, lockfile, build output, or binary)')
    current = dict(records.get(rel, {'path': rel}))
    if purpose is not None:
        current['purpose'] = ' '.join(purpose.split())
    if area is not None:
        current['area'] = area
    if layer is not None:
        current['layer'] = _layers(layer)
    if symbols is not None:
        current['symbols'] = [s.strip() for s in symbols if s.strip()]
    if links is not None:
        missing = [link for link in links if link not in files]
        if missing:
            raise ValueError(f'links to files that are not in the index: {", ".join(missing)}')
        current['links'] = sorted(set(links) - {rel})
    if not current.get('purpose') or not current.get('area'):
        raise ValueError(f'{rel} has no annotation yet; give it --purpose and --area')
    areas = load_areas(root)
    if current['area'] not in areas:
        raise ValueError(f'unknown area {current["area"]!r}; add it first with `simple-eng areas add NAME "description"`'
                         + (f' (areas: {", ".join(sorted(areas))})' if areas else ''))
    current['imports'] = imports(root, rel, files, index)
    current['hash'] = file_hash(root / rel)
    records[rel] = _normalized(current)
    if save_now:
        save(root, records)
    return records[rel]


def annotate_many(root, items):
    """Apply a list of {path, purpose, area, layer, symbols, links} objects in one write."""
    records, files = load(Path(root)), set(project_files(root))
    index = python_module_index(files)
    done = []
    for item in items:
        if not isinstance(item, dict) or 'path' not in item:
            raise ValueError('each item needs a "path"')
        done.append(annotate(root, item['path'], purpose=item.get('purpose'), area=item.get('area'),
                             layer=item.get('layer'), symbols=item.get('symbols'), links=item.get('links'),
                             records=records, files=files, index=index))
    save(root, records)
    return done


def remove(root, rel):
    records = load(root)
    if rel not in records:
        raise ValueError(f'{rel} has no annotation')
    del records[rel]
    save(root, records)


def refresh_imports(root, rel):
    """Update a drifted file's parser-derived imports, leaving its hash so the drift stays visible until reviewed."""
    records = load(root)
    if rel not in records or not (Path(root) / rel).is_file():
        return False
    new = imports(root, rel)
    if new == records[rel].get('imports'):
        return False
    records[rel]['imports'] = new
    save(root, records)
    return True


# --- checks and queries ----------------------------------------------------------------------------------------------

def check(root, paths=None):
    """Problems for the given project-relative paths, or for every file and annotation."""
    root = Path(root)
    records, areas = load(root), load_areas(root)
    if paths is None:
        files = set(project_files(root))
        targets = sorted(files | set(records))
    else:
        patterns = exclusions(root)
        targets = sorted(set(paths))
        files = {rel for rel in targets if (root / rel).is_file() and not excluded(rel, patterns)
                 and not is_binary(root / rel)}
    problems = []
    for rel in targets:
        record = records.get(rel)
        if record is None:
            if rel in files:
                problems.append({'kind': MISSING, 'path': rel, 'detail': ''})
            continue
        if not (root / rel).is_file():
            problems.append({'kind': ORPHAN, 'path': rel, 'detail': 'file no longer exists'})
            continue
        if rel not in files:
            problems.append({'kind': ORPHAN, 'path': rel, 'detail': 'file is excluded from the index'})
            continue
        if record.get('hash') != file_hash(root / rel):
            problems.append({'kind': DRIFT, 'path': rel, 'detail': ''})
        if record.get('area') not in areas:
            problems.append({'kind': UNKNOWN_AREA, 'path': rel, 'detail': str(record.get('area') or '(none)')})
        broken = [dep for dep in record.get('imports', []) + record.get('links', []) if not (root / dep).is_file()]
        if broken:
            problems.append({'kind': BROKEN_LINK, 'path': rel, 'detail': ', '.join(broken)})
    return problems


def summarize(problems, shown=5):
    lines = []
    for kind in (MISSING, ORPHAN, DRIFT, UNKNOWN_AREA, BROKEN_LINK):
        hits = [p for p in problems if p['kind'] == kind]
        if hits:
            sample = ', '.join(p['path'] + (f' ({p["detail"]})' if p['detail'] else '') for p in hits[:shown])
            more = f', and {len(hits) - shown} more' if len(hits) > shown else ''
            lines.append(f'{len(hits)} file(s) {KIND_LABELS[kind]}: {sample}{more}')
    return lines


def by_area(records, area):
    return [records[rel] for rel in sorted(records) if records[rel].get('area') == area]


def related(records, rel):
    record = records.get(rel)
    used_by = sorted(p for p, r in records.items() if p != rel and (rel in r.get('imports', []) or rel in r.get('links', [])))
    return {'path': rel, 'annotation': record, 'imports': (record or {}).get('imports', []),
            'links': (record or {}).get('links', []), 'used_by': used_by}


def search(records, query):
    words = query.lower().split()
    hits = []
    for rel in sorted(records):
        r = records[rel]
        text = ' '.join([rel, r.get('purpose', ''), *r.get('symbols', [])]).lower()
        if words and all(word in text for word in words):
            hits.append(r)
    return hits


def render(record):
    layer = ', '.join(record.get('layer') or []) or 'no layer'
    line = f'{record["path"]}  [{record.get("area") or "no area"}; {layer}]  {record.get("purpose", "")}'
    if record.get('symbols'):
        line += f'\n    symbols: {", ".join(record["symbols"])}'
    return line
