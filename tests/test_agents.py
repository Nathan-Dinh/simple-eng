import json
import unittest

from helpers import PLUGIN, ProjectCase
from simple_eng import annotations, context, project_agents, scaffold


class ProjectAgentTests(ProjectCase):
    def setUp(self):
        super().setUp()
        scaffold.annotate_scaffold(self.root)
        annotations.add_area(self.root, 'payments', 'Checkout and refunds')
        annotations.add_area(self.root, 'auth', 'Sign-in and permissions')

    def fill(self, area, count):
        items = []
        for i in range(count):
            self.write(f'{area}/m{i}.py', f'# {i}\n')
            items.append({'path': f'{area}/m{i}.py', 'purpose': f'module {i}', 'area': area})
        annotations.annotate_many(self.root, items)

    def agent(self, name, area):
        template = (PLUGIN / 'reference/templates/project-agent.md').read_text()
        self.write(f'.claude/agents/{name}.md', template.replace('AREA', area))

    def test_proposes_agent_at_threshold_only(self):
        self.fill('payments', 15)
        self.fill('auth', 14)
        found = project_agents.report(self.root)
        self.assertEqual([p['name'] for p in found['propose']], ['se-payments'])
        self.assertIn('propose se-payments (15 files)', context.build_context(self.root))

    def test_threshold_comes_from_config_and_project_area_is_shared(self):
        config = json.loads(self.read('.simple-eng/config.json'))
        config['agent_threshold'] = 2
        self.write('.simple-eng/config.json', json.dumps(config))
        self.fill('auth', 2)
        self.assertEqual([p['area'] for p in project_agents.report(self.root)['propose']], ['auth'])

    def test_existing_agent_is_not_proposed_again_and_renames_are_flagged(self):
        self.fill('payments', 15)
        self.agent('se-payments', 'payments')
        self.write('.claude/agents/reviewer-notes.md', '---\nname: mine\n---\nUser agent without area.\n')
        found = project_agents.report(self.root)
        self.assertEqual(found['propose'], [])
        self.assertEqual([a['name'] for a in found['agents']], ['se-payments'], 'user agents are ignored')
        annotations.rename_area(self.root, 'payments', 'billing')
        found = project_agents.report(self.root)
        self.assertEqual(found['retire'][0]['name'], 'se-payments')
        self.assertTrue(any('se-payments.md' in e for e in project_agents.validation_errors(self.root)))

    def test_shrunk_area(self):
        self.fill('auth', 3)
        self.agent('se-auth', 'auth')
        self.assertEqual(project_agents.report(self.root)['shrunk'][0]['name'], 'se-auth')
        self.assertIn('Consider merging or retiring se-auth', project_agents.render(project_agents.report(self.root)))


if __name__ == '__main__':
    unittest.main()
