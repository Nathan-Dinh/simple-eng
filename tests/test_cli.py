"""End-to-end runs of bin/simple-eng in a temporary project."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import PLUGIN

CLI = PLUGIN / 'bin/simple-eng'


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PROJECT_DIR'}

    def cli(self, *args, stdin=None, check=True):
        result = subprocess.run(['python3', str(CLI), '--root', str(self.root), *args], input=stdin,
                                capture_output=True, text=True, env=self.env, cwd=self.root)
        if check and result.returncode != 0:
            self.fail(f'simple-eng {args} failed: {result.stderr}')
        return result

    def test_project_lifecycle(self):
        self.assertNotEqual(self.cli('validate', check=False).returncode, 0)
        self.assertIn('Dry run', self.cli('init').stdout)
        self.assertFalse((self.root / 'CLAUDE.md').exists())
        self.cli('init', '--apply')
        self.assertTrue((self.root / 'docs/STATE.md').is_file())
        self.assertIn('Validation passed', self.cli('validate').stdout)
        self.assertIn('- stack: missing', self.cli('status').stdout)
        report = json.loads(self.cli('status', '--json', '--workflow', 'feature-development').stdout)
        self.assertIn('commands', report['blocking'])
        self.assertIn('No simple-eng 0.2 leftovers', self.cli('cleanup').stdout)
        self.assertIn('Stage: prototype', self.cli('stage').stdout)
        self.cli('stage', 'production')
        self.assertIn('Stage: production', self.cli('context').stdout)
        self.assertNotEqual(self.cli('stage', 'beta', check=False).returncode, 0)

    def test_docs_command(self):
        self.assertNotEqual(self.cli('docs', check=False).returncode, 0)
        self.cli('init', '--apply')
        out = self.cli('docs').stdout
        self.assertIn('create  docs/product/PRD.md', out)
        self.assertIn('Dry run', out)
        self.assertFalse((self.root / 'docs/product/PRD.md').exists())
        self.cli('docs', '--apply')
        self.assertTrue((self.root / 'docs/backend/schema.md').is_file())
        self.assertIn('- PRD: draft', self.cli('status').stdout)
        self.assertIn('Validation passed', self.cli('validate').stdout)
        self.assertIn('unchanged  docs/product/PRD.md', self.cli('docs').stdout)

    def test_hook_entry_points(self):
        self.assertEqual(self.cli('hook', 'session-start', stdin='{}').stdout, '')
        self.cli('init', '--apply')
        self.assertIn('simple-eng project context', self.cli('hook', 'session-start', stdin='{}').stdout)

    def test_cleanup_command(self):
        self.cli('init', '--apply')
        (self.root / 'docs/evidence/records').mkdir(parents=True)
        (self.root / 'docs/evidence/records/EVD-0001.md').write_text('# EVD-0001\n')
        out = self.cli('cleanup').stdout
        self.assertIn('delete     docs/evidence/', out)
        self.assertIn('Dry run', out)
        self.assertTrue((self.root / 'docs/evidence').exists())
        self.cli('cleanup', '--apply')
        self.assertFalse((self.root / 'docs/evidence').exists())

    def test_plugin_validation_and_budget(self):
        self.assertIn('Validation passed for plugin guidance', self.cli('validate', '--plugin').stdout)
        self.assertIn('initialize-project', self.cli('budget').stdout)


if __name__ == '__main__':
    unittest.main()
