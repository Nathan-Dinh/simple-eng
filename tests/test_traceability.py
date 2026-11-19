import unittest

from helpers import ProjectCase, traceability


class TraceabilityTests(ProjectCase):
    def test_fresh_project_validates(self):
        self.assertEqual(traceability.validate_traceability(self.root), [])

    def test_dangling_requirement_reference(self):
        self.write('docs/features/FEAT-0001.md', '# FEAT-0001: Search\n\nImplements REQ-0099.\n')
        errors = traceability.validate_traceability(self.root)
        self.assertTrue(any('REQ-0099 is referenced but never defined' in e for e in errors))

    def test_table_definition_resolves_and_duplicates_fail(self):
        self.write('docs/product/PRD.md', '# PRD\n\n- Status: draft\n\n| ID | Requirement |\n|---|---|\n| REQ-0001 | Fast search |\n')
        self.write('docs/features/FEAT-0001.md', '# FEAT-0001: Search\n\nCovers REQ-0001.\n')
        self.assertEqual(traceability.validate_traceability(self.root), [])
        self.write('docs/other.md', '| REQ-0001 | Duplicate |\n')
        self.assertTrue(any('REQ-0001 is defined more than once' in e for e in traceability.validate_traceability(self.root)))

    def test_old_decision_and_evidence_ids_are_ignored(self):
        self.write('docs/notes.md', 'See DEC-0001 and EVD-0002.\n')
        self.assertEqual(traceability.validate_traceability(self.root), [])

    def test_project_document_status_is_checked(self):
        self.write('docs/product/PRD.md', '# PRD\n\n- Status: draft\n')
        self.assertEqual(traceability.validate_traceability(self.root), [])
        self.write('docs/product/PRD.md', '# PRD\n\n- Status: approved\n')
        self.assertTrue(any('PRD.md: Status must be draft or reviewed' in e for e in traceability.validate_traceability(self.root)))


if __name__ == '__main__':
    unittest.main()
