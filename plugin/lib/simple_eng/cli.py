"""`simple-eng`: the simple-eng command line. Claude runs it through the Bash tool; hooks run it with `hook <name>`."""
import argparse
import json
import sys
from pathlib import Path

from . import PLUGIN_ROOT, plugin_version
from .context import DEFAULT_LIMIT, build_context, record_files
from .guidance import budget_report, check_plugin
from .hooks import HANDLERS, run as run_hook
from .paths import is_initialized, project_root
from .projectmap import render_status, status_report
from .traceability import validate_traceability
from .upgrade import apply_cleanup, decline_cleanup, describe, has_leftovers, leftovers
from .scaffold import apply_changes, planned_changes, planned_docs


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
        label = 'project records'
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
        print(f'\nApplied to {root}. Existing documents were not touched.')
    else:
        print('\nDry run. Re-run with --apply to create the missing documents from their templates.')
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
