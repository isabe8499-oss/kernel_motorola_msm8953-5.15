#!/usr/bin/env python3
"""Strict tests of derived C100/C200 stock A53 clock-controller reference."""
import copy
import json
from pathlib import Path
import unittest

from deen_stock_cpu_clock_two_cluster_gate import (
    CPU_REGS, EXPECTED_REGS, L2, STOCK_SHA, validate_manifest,
)

REF = (Path(__file__).resolve().parents[1] / "documentation" /
       "DEEN_STOCK_CPU_CLOCK_TWO_CLUSTERS_2026-11-20.json")


class TestDeenStockCpuClockGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.man = json.loads(REF.read_text(encoding="utf-8"))

    def test_direct_stock_provenance_and_two_board_hashes(self):
        self.assertEqual(self.man["provenance"]["boot_sha256"], STOCK_SHA)
        self.assertFalse(self.man["provenance"]["stock_binary_committed"])
        self.assertEqual(set(self.man["provenance"]["stock_fdt"]), {"C100", "C200"})
        self.assertTrue(validate_manifest(self.man))

    def test_seven_resource_names_and_two_apcs_mux_offsets(self):
        cpu = self.man["stock_cpu_clock"]
        self.assertEqual(len(cpu["registers"]), 7)
        self.assertEqual(cpu["num_clusters"], 2)
        self.assertEqual(cpu["clock_cells"], 1)
        self.assertEqual(cpu["registers"][3]["address"], L2[1][1] + 0x50)
        self.assertEqual(cpu["registers"][4]["address"], L2[0][1] + 0x50)
        self.assertEqual(cpu["registers"][-1]["address"], 0xa4124)
        self.assertEqual(tuple(EXPECTED_REGS[0]), ("rcgwr-c0-base", 0xb114000, 0x68))

    def test_eight_stock_cpus_have_declarative_rate_only(self):
        cpu = self.man["stock_cpu_clock"]
        self.assertEqual(cpu["cpu_node_regs"], CPU_REGS)
        self.assertEqual(cpu["cpu_advertised_clock_frequency_hz"], 2016000000)
        self.assertIs(cpu["clock_frequency_is_measured_runtime"], False)

    def test_bad_cluster_mux_is_rejected(self):
        bad = copy.deepcopy(self.man)
        bad["stock_cpu_clock"]["registers"][4]["address"] += 4
        with self.assertRaisesRegex(ValueError, "seven named MMIO"):
            validate_manifest(bad)

    def test_missing_voltage_supply_is_rejected(self):
        bad = copy.deepcopy(self.man)
        bad["stock_cpu_clock"]["supplies"] = ["vdd-cl-supply"]
        with self.assertRaisesRegex(ValueError, "voltage"):
            validate_manifest(bad)

    def test_bad_fdt_hash_is_rejected(self):
        bad = copy.deepcopy(self.man)
        bad["provenance"]["stock_fdt"]["C200"]["sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "FDT hashes"):
            validate_manifest(bad)

    def test_candidate_clock_enablement_requires_new_audit(self):
        bad = copy.deepcopy(self.man)
        bad["ack515_candidate"]["cpu_opp_reference_in_dtb"] = True
        with self.assertRaisesRegex(ValueError, "DVFS source assumptions"):
            validate_manifest(bad)

    def test_unproven_stock_runtime_frequency_is_rejected(self):
        bad = copy.deepcopy(self.man)
        bad["stock_cpu_clock"]["clock_frequency_is_measured_runtime"] = True
        with self.assertRaisesRegex(ValueError, "runtime evidence"):
            validate_manifest(bad)


if __name__ == "__main__":
    unittest.main()
