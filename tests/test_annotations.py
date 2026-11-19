import json
import os
import subprocess
import unittest

from helpers import PLUGIN, ProjectCase
from simple_eng import annotations, hooks, scaffold

CLI = PLUGIN / 'bin/simple-eng'


class AnnotationCase(ProjectCase):
    def setUp(self):
        super().setUp()
        scaffold.annotate_scaffold(self.root)
        annotations.add_area(self.root, 'orders', 'Placing and tracking orders')
        annotations.add_area(self.root, 'billing', 'Invoices and payments')

    def add(self, rel, text, area='orders', **kw):
        self.write(rel, text)
        return annotations.annotate(self.root, rel, purpose=f'{rel} purpose', area=area, **kw)

    def kinds(self, paths=None):
        return {(p['kind'], p['path']) for p in annotations.check(self.root, paths)}


class ParserTests(AnnotationCase):
    def test_python_absolute_relative_and_package_imports(self):
        self.write('app/__init__.py', '')
        self.write('app/models.py', 'class Order: pass\n')
        self.write('app/services/__init__.py', '')
        self.write('app/services/pricing.py', 'X = 1\n')
        self.write('app/views.py', 'import json\nimport app.models\nfrom .services import pricing\nfrom . import models\n'
                                   'from app.services.pricing import X\nimport requests\n')
        self.write('app/json.py', '')
        files = set(annotations.project_files(self.root))
        self.assertEqual(annotations.imports(self.root, 'app/views.py', files),
                         ['app/models.py', 'app/services/pricing.py'])

    def test_src_layout_and_syntax_errors(self):
        self.write('src/shop/__init__.py', '')
        self.write('src/shop/cart.py', 'from shop.tax import rate\n')
        self.write('src/shop/tax.py', 'rate = 1\n')
        self.write('broken.py', 'def (:\n')
        files = set(annotations.project_files(self.root))
        self.assertEqual(annotations.imports(self.root, 'src/shop/cart.py', files), ['src/shop/tax.py'])
        self.assertEqual(annotations.imports(self.root, 'broken.py', files), [])

    def test_js_relative_imports_only(self):
        self.write('web/api.ts', 'export const get = 1\n')
        self.write('web/components/index.tsx', '')
        self.write('web/util.js', '')
        self.write('web/app.tsx', "import React from 'react'\nimport { get } from './api'\nimport './components'\n"
                                  "const u = require('./util.js')\nexport * from './api.js'\nimport('./missing')\n"
                                  "import type { T } from '../web/api'\n")
        files = set(annotations.project_files(self.root))
        self.assertEqual(annotations.imports(self.root, 'web/app.tsx', files),
                         ['web/api.ts', 'web/components/index.tsx', 'web/util.js'])

    def test_other_languages_have_no_parsed_imports(self):
        self.write('main.go', 'import "fmt"\n')
        self.assertEqual(annotations.imports(self.root, 'main.go'), [])


class IndexTests(AnnotationCase):
    def test_exclusions_and_binaries(self):
        self.write('package-lock.json', '{}')
        self.write('node_modules/x/index.js', '')
        self.write('static/app.min.js', '')
        (self.root / 'logo.png').write_bytes(b'\x89PNG\x00\x01')
        self.write('src/keep.py', '')
        files = annotations.project_files(self.root)
        self.assertIn('src/keep.py', files)
        for rel in ('package-lock.json', 'node_modules/x/index.js', 'static/app.min.js', 'logo.png',
                    '.simple-eng/config.json', '.simple-eng/annotations.jsonl'):
            self.assertNotIn(rel, files)
        with self.assertRaisesRegex(ValueError, 'excluded'):
            annotations.annotate(self.root, 'package-lock.json', purpose='p', area='orders')

    def test_sorted_one_line_per_file(self):
        self.add('z.py', '')
        self.add('a.py', 'import z\n', layer=['domain'], symbols=['A'])
        lines = self.read('.simple-eng/annotations.jsonl').splitlines()
        paths = [json.loads(line)['path'] for line in lines]
        self.assertEqual(paths, sorted(paths))
        record = json.loads(next(line for line in lines if '"a.py"' in line))
        self.assertEqual(list(record), list(annotations.FIELDS))
        self.assertEqual(record['layer'], ['Domain'])
        self.assertEqual(record['imports'], ['z.py'])

    def test_new_annotation_needs_purpose_and_known_area(self):
        self.write('x.py', '')
        with self.assertRaisesRegex(ValueError, '--purpose and --area'):
            annotations.annotate(self.root, 'x.py', area='orders')
        with self.assertRaisesRegex(ValueError, 'unknown area'):
            annotations.annotate(self.root, 'x.py', purpose='p', area='payment')
        with self.assertRaisesRegex(ValueError, 'layer'):
            annotations.annotate(self.root, 'x.py', purpose='p', area='orders', layer=['Data'])

    def test_every_check_kind(self):
        self.assertEqual(self.kinds(), set())
        self.add('b.py', '')
        self.add('a.py', 'import b\n')
        self.add('c.py', '', links=['b.py'])
        self.write('new.py', '')
        self.write('a.py', 'import b\nx = 1\n')
        os.remove(self.root / 'b.py')
        records = annotations.load(self.root)
        records['c.py']['area'] = 'shipping'
        annotations.save(self.root, records)
        self.assertEqual(self.kinds(), {('missing', 'new.py'), ('drift', 'a.py'), ('orphan', 'b.py'),
                                        ('unknown area', 'c.py'), ('broken link', 'a.py'), ('broken link', 'c.py')})
        self.assertEqual(self.kinds(['a.py']), {('drift', 'a.py'), ('broken link', 'a.py')})

    def test_confirm_refreshes_hash_and_imports(self):
        self.add('a.py', '')
        self.add('b.py', '')
        self.write('a.py', 'import b\n')
        self.assertIn(('drift', 'a.py'), self.kinds())
        record = annotations.annotate(self.root, 'a.py')
        self.assertEqual(record['imports'], ['b.py'])
        self.assertEqual(record['purpose'], 'a.py purpose')
        self.assertEqual(self.kinds(), set())

    def test_area_rename_and_merge_rewrite_annotations(self):
        self.add('a.py', '', area='billing')
        self.add('b.py', '', area='orders')
        annotations.rename_area(self.root, 'billing', 'payments')
        self.assertEqual(annotations.load(self.root)['a.py']['area'], 'payments')
        self.assertIn('payments', annotations.load_areas(self.root))
        with self.assertRaisesRegex(ValueError, 'already exists'):
            annotations.rename_area(self.root, 'payments', 'orders')
        annotations.merge_areas(self.root, 'payments', 'orders')
        self.assertEqual({r['area'] for r in annotations.load(self.root).values() if r['path'].endswith('.py')}, {'orders'})
        self.assertNotIn('payments', annotations.load_areas(self.root))
        self.assertEqual(self.kinds(), set())
        with self.assertRaisesRegex(ValueError, 'lowercase'):
            annotations.add_area(self.root, 'Bad Name', 'x')

    def test_queries(self):
        self.add('orders/models.py', 'class Order: pass\n', symbols=['Order'])
        self.add('orders/views.py', 'from orders import models\n', symbols=['refund_order'])
        self.add('templates/order.html', '<p>', links=[])
        annotations.annotate(self.root, 'orders/views.py', links=['templates/order.html'])
        records = annotations.load(self.root)
        found = annotations.related(records, 'orders/models.py')
        self.assertEqual(found['used_by'], ['orders/views.py'])
        found = annotations.related(records, 'orders/views.py')
        self.assertEqual(found['imports'], ['orders/models.py'])
        self.assertEqual(found['links'], ['templates/order.html'])
        self.assertEqual([r['path'] for r in annotations.search(records, 'REFUND')], ['orders/views.py'])
        self.assertEqual(len(annotations.by_area(records, 'orders')), 3)


class HookTests(AnnotationCase):
    def payload(self, rel):
        return {'tool_name': 'Edit', 'tool_input': {'file_path': str(self.root / rel)}}

    def test_post_tool_use_reports_missing_and_drift(self):
        self.write('new.py', '')
        out = hooks.post_tool_use(self.payload('new.py'))
        self.assertIn('new.py has no annotation', out['hookSpecificOutput']['additionalContext'])
        self.add('b.py', '')
        self.add('a.py', '')
        self.write('a.py', 'import b\n')
        out = hooks.post_tool_use(self.payload('a.py'))
        self.assertIn('simple-eng annotate a.py --confirm', out['hookSpecificOutput']['additionalContext'])
        self.assertEqual(annotations.load(self.root)['a.py']['imports'], ['b.py'])
        self.assertIn(('drift', 'a.py'), self.kinds(), 'imports refresh must not hide the drift')
        self.assertIsNone(hooks.post_tool_use(self.payload('b.py')))
        self.assertIsNone(hooks.post_tool_use({'tool_input': {'file_path': '/elsewhere/x.py'}}))

    def test_stop_blocks_once_then_reports(self):
        self.assertIsNone(hooks.stop({}))
        self.add('a.py', '')
        subprocess.run(['git', '-C', str(self.root), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'commit', '-qm', 'init'], check=True)
        self.assertIsNone(hooks.stop({}))
        subprocess.run(['git', '-C', str(self.root), 'mv', 'a.py', 'moved.py'], check=True)
        out = hooks.stop({})
        self.assertEqual(out['decision'], 'block')
        self.assertIn('moved.py has no annotation', out['reason'])
        self.assertIn('annotate --remove a.py', out['reason'])
        self.assertIn('systemMessage', hooks.stop({'stop_hook_active': True}))

    def test_run_is_silent_outside_projects_and_survives_errors(self):
        self.write('.simple-eng/annotations.jsonl', '{broken\n')
        out = json.loads(hooks.run('post-tool-use', json.dumps(self.payload('x.py'))))
        self.assertIn('hook failed', out['systemMessage'])


class CliTests(AnnotationCase):
    def cli(self, *args, cwd=None, stdin=None):
        env = {**os.environ, 'CLAUDE_PROJECT_DIR': ''}
        return subprocess.run(['python3', str(CLI), *args], capture_output=True, text=True, env=env,
                              cwd=cwd or self.root, input=stdin)

    def test_paths_resolve_from_project_root_in_any_directory(self):
        self.write('pkg/a.py', '')
        self.write('pkg/b.py', '')
        out = self.cli('annotate', 'pkg/a.py', '--purpose', 'A', '--area', 'orders', cwd=self.root / 'pkg')
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.cli('annotate', 'b.py', '--purpose', 'B', '--area', 'orders', '--link', 'a.py', cwd=self.root / 'pkg')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(annotations.load(self.root)['pkg/b.py']['links'], ['pkg/a.py'])
        out = self.cli('annotations', '--related-to', 'pkg/a.py', cwd=self.root / 'pkg')
        self.assertIn('Used by:\n  pkg/b.py', out.stdout)
        self.assertIn('Validation passed', self.cli('validate', cwd=self.root / 'pkg').stdout)

    def test_batch_areas_and_validate_failures(self):
        self.write('x.py', '')
        self.write('y.py', '')
        bad = self.cli('validate')
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn('2 file(s) have no annotation: x.py, y.py', bad.stderr)
        items = json.dumps([{'path': 'x.py', 'purpose': 'X', 'area': 'orders'},
                            {'path': 'y.py', 'purpose': 'Y', 'area': 'billing', 'layer': ['Infrastructure']}])
        self.assertIn('Annotated 2', self.cli('annotate', '--from-json', '-', stdin=items).stdout)
        self.assertIn('orders (1 files)', self.cli('areas').stdout)
        self.assertEqual(self.cli('areas', 'rename', 'billing', 'payments').returncode, 0)
        self.assertIn('y.py', self.cli('annotations', '--area', 'payments').stdout)
        self.assertEqual(self.cli('validate').returncode, 0)
        self.assertEqual(self.cli('annotate', '--remove', 'y.py').returncode, 0)
        self.assertIn('y.py', self.cli('annotations', '--missing').stdout)


if __name__ == '__main__':
    unittest.main()
