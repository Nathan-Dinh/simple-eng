import json
import unittest

from helpers import ProjectCase
from simple_eng import projectmap


def statuses(root, workflow=None):
    report = projectmap.status_report(root, workflow=workflow)
    return {a['id']: a['status'] for a in report['areas']}, report


class ProjectMapTests(ProjectCase):
    def test_fresh_project_is_all_missing(self):
        found, _ = statuses(self.root)
        self.assertEqual(set(found.values()), {'missing'})
        self.assertIn('stack', found)

    def test_filled_section_is_present(self):
        text = self.read('docs/PROJECT.md').replace('## Stack\n', '## Stack\n\n- Python 3.12, Django 5 (verified: pyproject.toml)\n')
        self.write('docs/PROJECT.md', text)
        self.assertEqual(statuses(self.root)[0]['stack'], 'present')

    def test_placeholder_only_content_is_missing(self):
        template = (projectmap.PLUGIN_ROOT / 'reference/templates/prd.md').read_text()
        self.write('docs/product/PRD.md', template)
        self.assertEqual(statuses(self.root)[0]['requirements'], 'missing')
        self.write('docs/product/PRD.md', template.replace(
            '|---|---|---|---|---|---|\n', '|---|---|---|---|---|---|\n| REQ-0001 | functional | Search under 1s | user-provided | open | user, 2026-10-25 |\n', 1))
        self.assertEqual(statuses(self.root)[0]['requirements'], 'present')

    def test_not_applicable_in_record(self):
        self.write('docs/design/ui-ux-brief.md', '## Users and design goals\n\nNot applicable: CLI tool with no UI (verified: no frontend code).\n')
        found, report = statuses(self.root)
        self.assertEqual(found['ui'], 'not applicable')
        self.assertIn('CLI tool', next(a['detail'] for a in report['areas'] if a['id'] == 'ui'))

    def test_overrides(self):
        self.write('ARCHITECTURE.md', '# Overview\n\nTwo services and a queue.\n')
        config = json.loads(self.read('.simple-eng/config.json'))
        config['areas'] = {'architecture': {'record': 'ARCHITECTURE.md#Overview'},
                           'data-model': {'record': 'docs/missing.md#Entities'},
                           'ui': {'not_applicable': 'library with no interface'}}
        self.write('.simple-eng/config.json', json.dumps(config))
        found, _ = statuses(self.root)
        self.assertEqual(found['architecture'], 'present')
        self.assertEqual(found['data-model'], 'broken')
        self.assertEqual(found['ui'], 'not applicable')

    def test_workflow_blocking(self):
        _, report = statuses(self.root, 'architecture-design')
        self.assertEqual(set(report['blocking']), {'problem-users', 'requirements', 'quality-priorities', 'constraints'})
        self.assertIn('Missing areas that block architecture-design', projectmap.render_status(report))
        with self.assertRaises(ValueError):
            projectmap.status_report(self.root, workflow='no-such-skill')

    def documents(self):
        return {d['id']: d for d in projectmap.status_report(self.root)['documents']}

    def test_documents_missing_draft_reviewed(self):
        self.assertEqual({d['status'] for d in self.documents().values()}, {'missing'})
        template = (projectmap.PLUGIN_ROOT / 'reference/templates/trd.md').read_text()
        self.write('docs/architecture/TRD.md', template)
        self.assertEqual(self.documents()['trd']['status'], 'draft')
        self.write('docs/architecture/TRD.md', template.replace('- Status: draft', '- Status: Reviewed'))
        self.assertEqual(self.documents()['trd']['status'], 'reviewed')
        self.write('docs/architecture/TRD.md', template.replace('- Status: draft', '- Status: done'))
        self.assertEqual(self.documents()['trd']['status'], 'broken')
        self.assertIn('Project documents', projectmap.render_status(projectmap.status_report(self.root)))

    def test_documents_follow_not_applicable_area_and_flag_legacy(self):
        config = json.loads(self.read('.simple-eng/config.json'))
        config['areas'] = {'ui': {'not_applicable': 'library with no interface'}}
        self.write('.simple-eng/config.json', json.dumps(config))
        self.write('docs/product/requirements.md', '## Requirements\n')
        docs = self.documents()
        self.assertEqual(docs['ui-ux-brief']['status'], 'not applicable')
        self.assertEqual(docs['prd']['status'], 'missing')
        self.assertIn('legacy file docs/product/requirements.md', docs['prd']['detail'])
        self.assertIn('missing: prd', projectmap.documents_line(projectmap.status_report(self.root)))

    def test_summary_groups_by_source(self):
        summary = projectmap.summary_line(statuses(self.root)[1])
        self.assertIn('missing (investigate): stack', summary)
        self.assertIn('missing (ask): problem-users', summary)


if __name__ == '__main__':
    unittest.main()
