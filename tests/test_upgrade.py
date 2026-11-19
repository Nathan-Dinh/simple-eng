import json
import unittest

from helpers import ProjectCase
from simple_eng import context, markdown, upgrade

OLD_BLOCK = ('<!-- simple-eng:start version=0.2.0 -->\n## simple-eng\n\n5. Approval is recorded only when the decision owner '
             'types `/simple-eng:approve DEC-####`.\n<!-- simple-eng:end -->')


class UpgradeTests(ProjectCase):
    def make_old_project(self):
        self.write('CLAUDE.md', f'# Mine\n\nKeep this.\n\n{OLD_BLOCK}\n\nAnd this.\n')
        self.write('decision-log/events.jsonl', '{}\n')
        self.write('docs/decisions/records/DEC-0001.md', '# DEC-0001\n')
        self.write('docs/resources/postgres.md', '# Postgres pricing\n')
        self.write('docs/STATE.md', self.read('docs/STATE.md').replace(
            '## Recent changes', '## Pending decisions\n\n<!-- DEC IDs -->\n- DEC-0001\n\n## Recent changes'))
        self.write('docs/PROJECT.md', self.read('docs/PROJECT.md').replace('## Stack', '## Decision owners\n\n- Ana\n\n## Stack'))

    def test_fresh_project_has_no_leftovers(self):
        self.assertFalse(upgrade.has_leftovers(upgrade.leftovers(self.root)))
        self.assertNotIn('0.2', context.build_context(self.root))

    def test_detects_and_offers_cleanup(self):
        self.make_old_project()
        found = upgrade.leftovers(self.root)
        self.assertEqual(found['folders'], ['decision-log', 'docs/decisions', 'docs/resources'])
        self.assertEqual(found['sections'], ['docs/STATE.md#Pending decisions', 'docs/PROJECT.md#Decision owners'])
        self.assertTrue(found['block'])
        self.assertEqual(found['notes'], ['docs/resources/postgres.md'])
        out = context.build_context(self.root)
        self.assertIn('simple-eng cleanup --apply', out)
        self.assertIn('1 note(s) under docs/resources/', out)

    def test_apply_removes_leftovers_and_keeps_user_text(self):
        self.make_old_project()
        upgrade.apply_cleanup(self.root)
        self.assertFalse(upgrade.has_leftovers(upgrade.leftovers(self.root)))
        self.assertFalse((self.root / 'decision-log').exists())
        claude = self.read('CLAUDE.md')
        self.assertTrue(claude.startswith('# Mine\n\nKeep this.\n'))
        self.assertTrue(claude.rstrip().endswith('And this.'))
        self.assertNotIn('/simple-eng:approve', claude)
        self.assertNotIn('Pending decisions', self.read('docs/STATE.md'))
        self.assertIn('## Recent changes', self.read('docs/STATE.md'))
        self.assertNotIn('Decision owners', self.read('docs/PROJECT.md'))
        self.assertIn('## Stack', self.read('docs/PROJECT.md'))
        self.assertNotIn('framework_version', json.dumps(upgrade.leftovers(self.root)))

    def test_decline_silences_offer_but_not_stale_block(self):
        self.make_old_project()
        upgrade.decline_cleanup(self.root)
        self.assertTrue(json.loads(self.read('.simple-eng/config.json'))['cleanup_declined'])
        out = context.build_context(self.root)
        self.assertNotIn('cleanup --apply', out)
        self.assertIn('still describes 0.2 commands', out)
        self.assertTrue((self.root / 'decision-log').exists())
        self.write('CLAUDE.md', '# Mine\n')
        self.assertNotIn('0.2', context.build_context(self.root))

    def test_remove_section_stops_at_same_level(self):
        text = '# T\n\n## A\n\nbody\n\n### Sub\n\nmore\n\n## B\n\nkeep\n'
        self.assertEqual(markdown.remove_section(text, 'a'), '# T\n\n## B\n\nkeep\n')
        self.assertEqual(markdown.remove_section(text, 'missing'), text)


if __name__ == '__main__':
    unittest.main()
