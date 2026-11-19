"""`simple-eng`: the simple-eng command line. Claude runs it through the Bash tool; hooks run it with `hook <name>`."""
import argparse
import json
import sys
from pathlib import Path

from . import PLUGIN_ROOT, annotations, plugin_version
from .context import DEFAULT_LIMIT, build_context, record_files
from .guidance import budget_report, check_plugin
from .hooks import HANDLERS, run as run_hook
from .paths import is_initialized, project_root
from .projectmap import render_status, status_report
from .traceability import validate_traceability
from .upgrade import apply_cleanup, decline_cleanup, describe, has_leftovers, leftovers
from .scaffold import annotate_scaffold, apply_changes, planned_changes, planned_docs


def _root(args):
    return Path(args.root).resolve() if args.root else project_root()


def cmd_validate(args):
    if args.plugin:
        errors = check_plugin(PLUGIN_ROOT)
        label = 'plugin guidance'
    else:
        root = _root(args)
        if not is_initialized(root):
            print(f'{root} is not a simple-eng project (run /simple-eng:init).', file=sys.stderr)
            return 1
        errors = validate_traceability(root, record_files(root))
        errors += annotations.summarize(annotations.check(root))
        label = 'project records and the annotation index'
    for error in errors:
        print('ERROR:', error, file=sys.stderr)
    if errors:
        return 1
    print(f'Validation passed for {label} (structure and references only; it does not prove claims are true).')
    return 0


def cmd_status(args):
    report = status_report(_root(args), PLUGIN_ROOT, args.workflow)
    print(json.dumps(report, indent=2) if args.json else render_status(report))
    return 0


def cmd_context(args):
    print(build_context(_root(args), PLUGIN_ROOT, args.limit))
    return 0


def cmd_init(args):
    root = _root(args)
    changes = planned_changes(root, PLUGIN_ROOT)
    for change in changes:
        print(f'{change["action"]:>9}  {change["path"]}')
    for change in changes:
        if change['path'] == 'CLAUDE.md' and change['diff']:
            print('\nCLAUDE.md diff (only the marked simple-eng block is managed):\n' + change['diff'])
    if args.apply:
        apply_changes(root, changes)
        annotate_scaffold(root, PLUGIN_ROOT)
        print(f'\nApplied to {root} (simple-eng {plugin_version()}).')
    else:
        print('\nDry run. Re-run with --apply to write these changes.')
    return 0


def cmd_docs(args):
    root = _root(args)
    if not is_initialized(root):
        print(f'{root} is not a simple-eng project (run /simple-eng:init).', file=sys.stderr)
        return 1
    changes = planned_docs(root, PLUGIN_ROOT)
    for change in changes:
        reason = f'  ({change["reason"]})' if change.get('reason') else ''
        print(f'{change["action"]:>9}  {change["path"]}{reason}')
    if args.apply:
        apply_changes(root, changes)
        annotate_scaffold(root, PLUGIN_ROOT)
        print(f'\nApplied to {root}. Existing documents were not touched.')
    else:
        print('\nDry run. Re-run with --apply to create the missing documents from their templates.')
    return 0


def _initialized(args):
    root = _root(args)
    if not is_initialized(root):
        raise ValueError(f'{root} is not a simple-eng project (run /simple-eng:init)')
    return root


def cmd_annotate(args):
    root = _initialized(args)
    if args.from_json:
        text = sys.stdin.read() if args.from_json == '-' else Path(args.from_json).read_text(encoding='utf-8')
        items = json.loads(text)
        if not isinstance(items, list):
            raise ValueError('--from-json expects a JSON list of {path, purpose, area, layer, symbols, links}')
        for item in items:
            if isinstance(item, dict) and 'path' in item:
                item['path'] = annotations.resolve_path(root, item['path'])
        done = annotations.annotate_many(root, items)
        print(f'Annotated {len(done)} file(s).')
        return 0
    if not args.path:
        raise ValueError('give a path, or --from-json FILE')
    rel = annotations.resolve_path(root, args.path)
    if args.remove:
        annotations.remove(root, rel)
        print(f'Removed the annotation for {rel}.')
        return 0
    links = [annotations.resolve_path(root, link) for link in args.link] if args.link is not None else None
    if args.confirm and any(v is not None for v in (args.purpose, args.area, args.layer, args.symbol, links)):
        raise ValueError('--confirm only refreshes imports and the hash; pass fields without --confirm to change them')
    if args.confirm and rel not in annotations.load(root):
        raise ValueError(f'{rel} has no annotation to confirm; give it --purpose and --area')
    record = annotations.annotate(root, rel, purpose=args.purpose, area=args.area, layer=args.layer,
                                  symbols=args.symbol, links=links)
    print(annotations.render(record))
    return 0


def cmd_annotations(args):
    root = _initialized(args)
    records = annotations.load(root)
    if args.related_to:
        found = annotations.related(records, annotations.resolve_path(root, args.related_to))
        if args.json:
            print(json.dumps(found, indent=2))
            return 0
        if found['annotation']:
            print(annotations.render(found['annotation']))
        else:
            print(f'{found["path"]} has no annotation.')
        for label, key in (('Imports', 'imports'), ('Other links', 'links'), ('Used by', 'used_by')):
            print(f'{label}:')
            for rel in found[key]:
                print('  ' + (annotations.render(records[rel]).replace('\n', '\n  ') if rel in records else rel))
            if not found[key]:
                print('  (none)')
        return 0
    if args.missing or args.drift:
        kinds = {annotations.MISSING} if args.missing else {annotations.DRIFT}
        problems = [p for p in annotations.check(root) if p['kind'] in kinds]
        print(json.dumps(problems, indent=2) if args.json else '\n'.join(p['path'] for p in problems))
        return 0
    if args.area:
        if args.area not in annotations.load_areas(root):
            raise ValueError(f'unknown area {args.area!r}; `simple-eng areas` lists them')
        found = annotations.by_area(records, args.area)
    elif args.search:
        found = annotations.search(records, args.search)
    else:
        raise ValueError('choose one of --area, --related-to, --search, --missing, or --drift')
    print(json.dumps(found, indent=2) if args.json else '\n'.join(annotations.render(r) for r in found)
          or 'No matching annotations.')
    return 0


def cmd_areas(args):
    root = _initialized(args)
    if args.action == 'add':
        annotations.add_area(root, args.name, args.description)
        print(f'Area {args.name} saved.')
    elif args.action == 'rename':
        changed = annotations.rename_area(root, args.old, args.new)
        print(f'Renamed {args.old} to {args.new}; {len(changed)} annotation(s) updated.')
    elif args.action == 'merge':
        changed = annotations.merge_areas(root, args.source, args.target)
        print(f'Merged {args.source} into {args.target}; {len(changed)} annotation(s) updated.')
    else:
        records = annotations.load(root)
        areas = annotations.load_areas(root)
        if args.json:
            print(json.dumps({name: {'description': desc, 'files': len(annotations.by_area(records, name))}
                              for name, desc in areas.items()}, indent=2))
        else:
            for name, desc in sorted(areas.items()):
                print(f'{name} ({len(annotations.by_area(records, name))} files): {desc}')
            if not areas:
                print('No areas yet. Add one with `simple-eng areas add NAME "one-line description"`.')
    return 0


def cmd_cleanup(args):
    root = _root(args)
    if not is_initialized(root):
        print(f'{root} is not a simple-eng project (run /simple-eng:init).', file=sys.stderr)
        return 1
    found = leftovers(root)
    if not has_leftovers(found):
        print('No simple-eng 0.2 leftovers found.')
        return 0
    if args.decline:
        decline_cleanup(root)
        print('Recorded that the cleanup was declined; the files stay as they are.')
        return 0
    print('\n'.join(describe(found)))
    if found['notes']:
        print('\nMove the findings from these research notes into their project documents first:\n'
              + '\n'.join(f'  {note}' for note in found['notes']))
    if args.apply:
        apply_cleanup(root, PLUGIN_ROOT)
        print(f'\nApplied to {root}.')
    else:
        print('\nDry run. Re-run with --apply after the user agrees, or --decline to keep the files.')
    return 0


def cmd_budget(args):
    print(budget_report(PLUGIN_ROOT))
    return 0


def cmd_hook(args):
    out = run_hook(args.name, sys.stdin.read())
    if out:
        print(out)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog='simple-eng', description=__doc__)
    parser.add_argument('--root', help='project root (default: CLAUDE_PROJECT_DIR, nearest .simple-eng/, or git top level)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('validate', help='check project records, or the plugin itself with --plugin')
    p.add_argument('--plugin', action='store_true')
    p.set_defaults(func=cmd_validate)
    p = sub.add_parser('status', help='report which knowledge areas are recorded')
    p.add_argument('--workflow', help='also list missing areas that block this workflow skill')
    p.add_argument('--json', action='store_true')
    p.set_defaults(func=cmd_status)
    p = sub.add_parser('context', help='print the session context the SessionStart hook injects')
    p.add_argument('--limit', type=int, default=DEFAULT_LIMIT)
    p.set_defaults(func=cmd_context)
    p = sub.add_parser('init', help='set up a project (dry run unless --apply)')
    p.add_argument('--apply', action='store_true')
    p.set_defaults(func=cmd_init)
    p = sub.add_parser('docs', help='create missing project documents from their templates (dry run unless --apply)')
    p.add_argument('--apply', action='store_true')
    p.set_defaults(func=cmd_docs)
    p = sub.add_parser('annotate', help='create, update, confirm, or remove a file annotation')
    p.add_argument('path', nargs='?', help='file path, relative to the project root')
    p.add_argument('--purpose', help='what the file does, in a sentence')
    p.add_argument('--area', help='business area, one listed by `simple-eng areas`')
    p.add_argument('--layer', action='append', help='Presentation, Application, Domain, or Infrastructure (repeatable)')
    p.add_argument('--symbol', action='append', help='a main public class or function (repeatable)')
    p.add_argument('--link', action='append', help='a project file this one depends on that the parser cannot see (repeatable)')
    p.add_argument('--confirm', action='store_true', help='the annotation still matches: refresh imports and the hash')
    p.add_argument('--remove', action='store_true', help='remove the annotation (the file was deleted or moved)')
    p.add_argument('--from-json', metavar='FILE', help='annotate many files from a JSON list ("-" reads stdin)')
    p.set_defaults(func=cmd_annotate)
    p = sub.add_parser('annotations', help='query the annotation index')
    group = p.add_mutually_exclusive_group()
    group.add_argument('--area', help='every file in an area')
    group.add_argument('--related-to', metavar='PATH', help="a file's dependencies and the files that use it")
    group.add_argument('--search', metavar='TEXT', help='files whose path, purpose, or key symbols match')
    group.add_argument('--missing', action='store_true', help='files with no annotation')
    group.add_argument('--drift', action='store_true', help='files changed since they were annotated')
    p.add_argument('--json', action='store_true')
    p.set_defaults(func=cmd_annotations)
    p = sub.add_parser('areas', help='list, add, rename, or merge areas')
    p.add_argument('--json', action='store_true')
    areas = p.add_subparsers(dest='action')
    q = areas.add_parser('add', help='add an area or change its description')
    q.add_argument('name')
    q.add_argument('description')
    q = areas.add_parser('rename', help='rename an area and every annotation that uses it')
    q.add_argument('old')
    q.add_argument('new')
    q = areas.add_parser('merge', help='move every annotation from one area into another, then drop the first')
    q.add_argument('source')
    q.add_argument('target')
    p.set_defaults(func=cmd_areas)
    p = sub.add_parser('cleanup', help='remove simple-eng 0.2 leftovers (dry run unless --apply)')
    group = p.add_mutually_exclusive_group()
    group.add_argument('--apply', action='store_true')
    group.add_argument('--decline', action='store_true', help='keep the files and stop offering the cleanup')
    p.set_defaults(func=cmd_cleanup)
    p = sub.add_parser('budget', help='print estimated token cost of the plugin guidance')
    p.set_defaults(func=cmd_budget)
    p = sub.add_parser('hook', help='hook entry point (used by hooks/hooks.json)')
    p.add_argument('name', choices=sorted(HANDLERS))
    p.set_defaults(func=cmd_hook)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        return 1
