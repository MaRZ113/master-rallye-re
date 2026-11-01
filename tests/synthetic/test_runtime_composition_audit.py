import unittest
from unittest.mock import patch

from tools import audit_runtime_composition as audit


class CompositionAuditTests(unittest.TestCase):
    def setUp(self):
        self.image = b'0123456789'
        self.j2 = {'source': {'sha256': audit.RETAIL}, 'operations': [
            {'name': 'change', 'rva': 4, 'file_offset': 4,
             'expected_original_bytes': b'45'.hex(), 'replacement_bytes': b'xy'.hex()},
            {'name': 'header', 'rva': None}]}
        self.rmod = {'source_executable': {'sha256': audit.RETAIL}, 'operations': [
            {'id': 'hook', 'rva': 3, 'file_offset': 3, 'feature_mask': 1,
             'expected_original_hex': b'3456'.hex(), 'replacement_hex': b'abcd'.hex()}]}

    def run_audit(self):
        sections = [{'rva': 0, 'raw_offset': 0, 'raw_size': len(self.image)}]
        with patch.object(audit.addon_runtime, '_pe_sections', return_value=(
                {'machine': 0x14c, 'image_base': 0x400000}, sections)):
            return audit.audit(self.image, self.j2, self.rmod)

    def test_partial_overlap_and_masks_are_reported(self):
        result = self.run_audit()
        self.assertEqual(result['status'], 'CONFLICT')
        row = result['overlaps'][0]
        self.assertEqual((row['rva_start'], row['rva_end_exclusive']), (4, 6))
        self.assertEqual((row['retail_hex'], row['j2_hex'], row['randomizer_hex']), ('3435', '7879', '6263'))
        self.assertEqual(row['feature_mask'], 1)
        self.assertEqual(result['j2_file_only_operations'], 1)

    def test_touching_ranges_do_not_overlap(self):
        self.rmod['operations'][0].update(rva=6, file_offset=6, expected_original_hex=b'6789'.hex())
        self.assertEqual(self.run_audit()['status'], 'NO_OVERLAP_OBSERVED')

    def test_wrong_preimage_and_lengths_fail_closed(self):
        self.rmod['operations'][0]['expected_original_hex'] = b'abcd'.hex()
        with self.assertRaisesRegex(ValueError, 'preimage'): self.run_audit()
        self.rmod['operations'][0]['expected_original_hex'] = b'3456'.hex()
        self.rmod['operations'][0]['replacement_hex'] = '00'
        with self.assertRaisesRegex(ValueError, 'length'): self.run_audit()

    def test_different_hash_with_matching_required_bytes_is_accepted(self):
        self.image = b'X123456789'
        self.assertEqual(self.run_audit()['examined_executable_sha256'], audit.digest(self.image))

    def test_plan_source_disagreement_is_rejected(self):
        self.j2['source']['sha256'] = 'not-the-plan-reference'
        with self.assertRaisesRegex(ValueError, 'plan source identity'):
            self.run_audit()

    def test_empty_plan_and_ambiguous_mapping_are_rejected(self):
        self.rmod['operations'] = []
        with self.assertRaisesRegex(ValueError, 'both plans'):
            self.run_audit()
        sections = [{'rva': 10, 'raw_offset': 0, 'raw_size': 20},
                    {'rva': 10, 'raw_offset': 40, 'raw_size': 20}]
        with self.assertRaisesRegex(ValueError, 'unique'):
            audit.file_offset_for_rva(sections, 12, 1)

    def test_rva_maps_to_new_file_offset_when_section_moves(self):
        sections = [{'rva': 0x1000, 'raw_offset': 0x600, 'raw_size': 0x200}]
        self.assertEqual(audit.file_offset_for_rva(sections, 0x1010, 2), 0x610)


if __name__ == '__main__': unittest.main()
