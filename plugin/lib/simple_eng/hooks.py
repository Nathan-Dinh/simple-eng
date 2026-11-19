"""Claude Code hook entry points. Each reads the hook's JSON from stdin and prints the hook's output.

- session-start: prints the project context (plain text is added to Claude's context).

Plugin hooks fire in every repository where the plugin is enabled, so `run` skips projects that never ran init.
"""
import json
import os

from .context import build_context
from .paths import is_initialized, project_root


def _root(payload):
    return project_root(os.environ.get('CLAUDE_PROJECT_DIR') or payload.get('cwd'))


def session_start(payload):
    try:
        return build_context(_root(payload))
    except Exception as exc:  # a broken project must never break session start
        return f'simple-eng: could not build project context ({exc}). Run `simple-eng validate` for details.'


HANDLERS = {'session-start': session_start}


def run(name, stdin):
    try:
        payload = json.loads(stdin or '{}')
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    if not is_initialized(_root(payload)):
        return ''
    result = HANDLERS[name](payload)
    if result is None:
        return ''
    return result if isinstance(result, str) else json.dumps(result)
