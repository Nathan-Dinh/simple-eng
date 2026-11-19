import json
import tempfile
import unittest
from pathlib import Path

from helpers import ProjectCase
from simple_eng import context


class ContextTests(ProjectCase):
    def test_uninitialized_project_gets_one_line(self):
        with tempfile.TemporaryDirectory() as d:
            out = context.build_context(Path(d))
        self.assertEqual(len(out.splitlines()), 1)
        self.assertIn('/simple-eng:init', out)

    def test_includes_state_project_and_gaps(self):
        self.write('docs/STATE.md', '# Working state\n\n## Current focus\n\n- Workflow: initialize-project\n- Phase or step: 2\n')
        out = context.build_context(self.root)
        self.assertIn('--- docs/STATE.md ---', out)
        self.assertIn('Phase or step: 2', out)
        self.assertIn('--- docs/PROJECT.md ---', out)
        self.assertIn('Knowledge areas: missing (investigate)', out)
        self.assertNotIn('<!--', out)
        self.assertNotIn('decision', out.split('--- docs/STATE.md ---')[0].lower())

    def test_capped_and_keeps_newest_state(self):
        recent = '\n'.join(f'- 2026-10-{i:02d} change number {i}' for i in range(400, 0, -1))
        self.write('docs/STATE.md', '# Working state\n\n## Current focus\n\n- Next step: ship search\n\n## Recent changes\n\n' + recent + '\n')
        out = context.build_context(self.root)
        self.assertLessEqual(len(out), context.DEFAULT_LIMIT)
        self.assertIn('Next step: ship search', out)
        self.assertIn('change number 400', out)
        self.assertNotIn('change number 1\n', out + '\n')
        self.assertIn('truncated', out)
        self.assertLessEqual(len(context.build_context(self.root, limit=50000)), context.HARD_LIMIT)

    def test_compact_drops_unfilled_template_lines(self):
        out = context.compact('## Focus\n\n- Workflow:\n- Next step: ship\n\n| A | Status |\n|---|---|\n| A — scope | |\n\n'
                              '| Q | Why |\n|---|---|\n| Which DB? | blocks schema |\n<!-- hint -->\n')
        self.assertEqual(out, '## Focus\n- Next step: ship\n| Q | Why |\n|---|---|\n| Which DB? | blocks schema |')

    def test_reports_validation_problems_and_version_drift(self):
        self.write('docs/features/FEAT-0001.md', '# FEAT-0001: X\n\nNeeds REQ-0404.\n')
        config = json.loads(self.read('.simple-eng/config.json'))
        config['framework_version'] = '0.0.1'
        self.write('.simple-eng/config.json', json.dumps(config))
        out = context.build_context(self.root)
        self.assertIn('REQ-0404 is referenced but never defined', out)
        self.assertIn('initialized with simple-eng 0.0.1', out)


if __name__ == '__main__':
    unittest.main()
