#!/usr/bin/env python3
"""Host-only tests; passing never authorizes boot, thermal runtime or flashing."""
import unittest
from pathlib import Path

from deen_c100_tsens_type3_contract import (
    CANDIDATE, STOCK_REPORTED, PHYSICAL_REGISTER_CORRESPONDENCE,
    generic_v2_raw12_to_millicelsius, audit_source)
from deen_c100_spmi_schema_gate import KNOWN_NON_SPMI

ROOT = Path(__file__).resolve().parents[1]


class TestDeenTsensType3Contract(unittest.TestCase):
    def test_two_register_offsets_physically_align_but_do_not_prove_equivalence(self):
        for label, pair in PHYSICAL_REGISTER_CORRESPONDENCE.items():
            with self.subTest(label=label):
                self.assertEqual(pair[0], pair[1])
        self.assertEqual(PHYSICAL_REGISTER_CORRESPONDENCE["tm_sensor_status"][0],
                         0x4a90a0)
        self.assertEqual(PHYSICAL_REGISTER_CORRESPONDENCE["tm_ready"][0],
                         0x4a90e4)

    def test_legacy_15_sensor_mapping_is_not_candidate_16_mapping(self):
        self.assertEqual(STOCK_REPORTED["sensor_count"], 15)
        self.assertEqual(STOCK_REPORTED["sensor_ids"], list(range(1, 16)))
        self.assertEqual(STOCK_REPORTED["client_ids"], list(range(1, 16)))
        self.assertEqual(STOCK_REPORTED["slopes"], [0xc80] * 15)
        self.assertEqual(CANDIDATE["sensor_count"], 16)
        self.assertNotEqual(STOCK_REPORTED["sensor_ids"], list(range(16)))
        self.assertEqual(STOCK_REPORTED["reg"][0], (0x4a8000, 0x2000))
        self.assertEqual(STOCK_REPORTED["reg"][1], (0x0a4000, 0x1000))
        self.assertEqual(STOCK_REPORTED["interrupt_ids"], [184, 314])
        self.assertEqual(CANDIDATE["interrupt_ids"], [184, 314])
        self.assertNotEqual(STOCK_REPORTED["interrupt_names"], CANDIDATE["interrupt_names"])

    def test_v2_reference_model_signed_12bit_millicelsius(self):
        cases = {
            0x000: 0,
            0x001: 100,
            0x07ff: 204700,
            0x0800: -204800,
            0x0fff: -100,
            0x0f80: -12800,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=hex(raw)):
                self.assertEqual(generic_v2_raw12_to_millicelsius(raw), expected)

    def test_v2_model_rejects_invalid_register_field(self):
        for value in (-1, 0x1000, 0xffffffff, None, "0xfff"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    generic_v2_raw12_to_millicelsius(value)

    def test_modern_sources_are_unpatched_and_include_default_mapping(self):
        self.assertEqual(audit_source(ROOT)["issues"], [])

    def test_tsens_schema_remains_a_visible_failure(self):
        self.assertEqual(KNOWN_NON_SPMI["thermal-sensor@4a9000"], 1)
        self.assertEqual(sum(KNOWN_NON_SPMI.values()), 11)
        self.assertNotEqual(STOCK_REPORTED["sensor_count"], CANDIDATE["sensor_count"])


if __name__ == "__main__":
    unittest.main()
