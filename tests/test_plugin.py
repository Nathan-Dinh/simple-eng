"""Structural tests of the plugin's own guidance. They check text and layout, not live agent behavior."""
import json
import re
import unittest

from helpers import PLUGIN, plugin_copy, traceability
from simple_eng import guidance, markdown, projectmap

CONSEQUENTIAL = 'changing a database schema'
USER_ONLY = ('init',)


class PluginStructureTests(unittest.TestCase):
    def test_plugin_checks_pass(self):
        self.assertEqual(guidance.check_plugin(PLUGIN), [])

    def test_manifests(self):
        manifest = json.loads((PLUGIN / '.claude-plugin/plugin.json').read_text())
        market = json.loads((PLUGIN.parent / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(manifest['name'], 'simple-eng')
        self.assertRegex(manifest['version'], r'^\d+\.\d+\.\d+$')
        self.assertEqual(market['plugins'][0]['name'], manifest['name'])
        self.assertFalse((PLUGIN / 'CLAUDE.md').exists(), 'a CLAUDE.md at the plugin root is not loaded and fails --strict validation')

    def test_hooks_cover_each_handler(self):
        hooks = json.loads((PLUGIN / 'hooks/hooks.json').read_text())['hooks']
        self.assertEqual(set(hooks), {'SessionStart', 'PostToolUse', 'Stop'})
        self.assertIn('compact', hooks['SessionStart'][0]['matcher'])
        commands = json.dumps(hooks)
        for name in ('session-start', 'post-tool-use', 'stop'):
            self.assertIn(name, commands)

    def test_user_only_skills(self):
        skills = guidance.skills(PLUGIN)
        for name in USER_ONLY:
            self.assertIs(skills[name]['meta'].get('disable-model-invocation'), True, name)
        for name, skill in skills.items():
            if name not in USER_ONLY:
                self.assertNotIn('disable-model-invocation', skill['meta'], name)

    def test_consequential_list_stated_once(self):
        holders = [p.relative_to(PLUGIN).as_posix() for p in PLUGIN.glob('**/*.md')
                   if 'tests' not in p.parts and CONSEQUENTIAL in p.read_text()]
        self.assertEqual(holders, ['reference/templates/claude-md-block.md'])

    def test_claim_labels_agree(self):
        block = (PLUGIN / 'reference/templates/claude-md-block.md').read_text()
        policy = (PLUGIN / 'reference/policies/working-rules.md').read_text()
        policy_labels = tuple(re.findall(r'^\| ([a-z-]+) \|', policy, re.MULTILINE))
        self.assertEqual(policy_labels, traceability.FACT_LABELS)
        for label in traceability.FACT_LABELS:
            self.assertIn(label, block)

    def test_checkpoints_present(self):
        skill = (PLUGIN / 'skills/checkpoints/SKILL.md').read_text()
        state = (PLUGIN / 'reference/templates/state.md').read_text()
        for letter in 'ABCDEFG':
            self.assertIn(f'**{letter} —', skill)
            self.assertIn(f'| {letter} —', state)

    def test_project_docs_guidance_ordered_and_loaded_lazily(self):
        skill = (PLUGIN / 'skills/project-docs/SKILL.md').read_text()
        documents = projectmap.load_documents(PLUGIN)
        guidance_files = re.findall(r'\$\{CLAUDE_SKILL_DIR\}/([\w-]+\.md)', skill)
        self.assertEqual(guidance_files, [d['template'] for d in documents])
        for doc in documents:
            self.assertIn(doc['path'], skill)
            self.assertTrue((PLUGIN / 'skills/project-docs' / doc['template']).is_file(), doc['template'])
            template = (PLUGIN / 'reference/templates' / doc['template']).read_text()
            self.assertIn('- Status: draft\n', template, doc['template'])

    def test_block_and_state_template_have_no_real_ids(self):
        documents = [f'reference/templates/{d["template"]}' for d in projectmap.load_documents(PLUGIN)]
        for rel in ('reference/templates/claude-md-block.md', 'reference/templates/state.md', *documents):
            self.assertEqual(traceability.ANY_ID.findall((PLUGIN / rel).read_text()), [], rel)

    def test_tier_agents(self):
        found = {name: a['meta']['model'] for name, a in guidance.agents(PLUGIN).items()}
        self.assertEqual(found, {'labor': 'haiku', 'implementer': 'sonnet', 'reviewer': 'opus'})
        for name, agent in guidance.agents(PLUGIN).items():
            self.assertIn('Open questions', agent['body'], name)

    def test_lead_routes_to_every_agency_skill(self):
        lead = (PLUGIN / 'skills/lead/SKILL.md').read_text()
        for name in ('initialize-project', 'analyze-existing-project', 'architecture-design', 'database-engineering',
                     'ui-ux-design', 'feature-development', 'maintain-project', 'research-management'):
            self.assertIn(f'`simple-eng:{name}`', lead)
        for name in guidance.agents(PLUGIN):
            self.assertIn(f'`simple-eng:{name}`', lead)

    def test_frontmatter_parser(self):
        meta, body = markdown.parse_frontmatter('---\ndescription: a: b\nneeds: [x, y]\nflag: true\n---\n\nBody\n')
        self.assertEqual(meta, {'description': 'a: b', 'needs': ['x', 'y'], 'flag': True})
        self.assertEqual(body.strip(), 'Body')


class BrokenPluginTests(unittest.TestCase):
    def test_each_check_fails_on_a_broken_copy(self):
        breakages = {
            'unknown area': ('skills/status/SKILL.md', lambda t: t.replace('description:', 'needs: [nope]\ndescription:', 1), 'unknown area'),
            'missing reference': ('skills/maintain-project/SKILL.md', lambda t: t + '\nSee ${CLAUDE_PLUGIN_ROOT}/policies/gone.md\n', 'missing file'),
            'long description': ('skills/status/SKILL.md', lambda t: t.replace('description: ', 'description: ' + 'x' * 1600, 1), 'limit 1536'),
            'over budget': ('reference/policies/working-rules.md', lambda t: t + 'y' * 13000, 'budget'),
            'map heading': ('reference/templates/project.md', lambda t: t.replace('## Stack', '## Tech'), 'heading "Stack"'),
            'agent model': ('agents/labor.md', lambda t: t.replace('model: haiku', 'model: gpt'), 'model must be one of'),
            'agent name': ('agents/labor.md', lambda t: t.replace('name: labor', 'name: worker'), 'name must match'),
            'stage tag': ('reference/standards/design.md', lambda t: t.replace('- [all]', '- [beta]', 1), 'unknown stage tag [beta]'),
            'yaml colon': ('skills/status/SKILL.md', lambda t: t.replace('description: ', 'description: Status: ', 1), 'must not contain'),
            'document template': ('reference/project-map.json', lambda t: t.replace('"template": "app-flow.md", "area"', '"template": "gone.md", "area"')
                                  .replace('"template": "app-flow.md",\n      "area"', '"template": "gone.md",\n      "area"'), 'template gone.md not found'),
        }
        for label, (rel, change, expected) in breakages.items():
            with self.subTest(label):
                root = plugin_copy(self)
                path = root / rel
                path.write_text(change(path.read_text()))
                errors = guidance.check_plugin(root)
                self.assertTrue(any(expected in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
