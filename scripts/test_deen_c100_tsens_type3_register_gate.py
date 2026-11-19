#!/usr/bin/env python3
"""Pure host tests for Type3 register and thermal-zone contract (no hardware)."""
import unittest

from deen_c100_tsens_type3_register_gate import (
    REGISTER_PAIRS, LEGACY_BASE, TM_BASE, TM_SIZE, CPU_ZONES,
    STOCK_IDS_REPORTED, sensor_registers)
from deen_c100_tsens_type3_contract import generic_v2_raw12_to_millicelsius


class TestDeenType3RegisterZones(unittest.TestCase):
    def test_eleven_named_register_offsets_match_physically(self):
        self.assertEqual(len(REGISTER_PAIRS), 11)
        for legacy_name, modern_name, left, right in REGISTER_PAIRS:
            with self.subTest(legacy=legacy_name, modern=modern_name):
                self.assertEqual(LEGACY_BASE + left, TM_BASE + right)

    def test_all_fifteen_sensors_have_safe_tm_register_offsets(self):
        self.assertEqual(list(STOCK_IDS_REPORTED), list(range(1, 16)))
        for idx in STOCK_IDS_REPORTED:
            with self.subTest(sensor=idx):
                r = sensor_registers(idx)
                self.assertEqual(r["threshold_low_upper"], 0x4a9020 + idx * 4)
                self.assertEqual(r["threshold_critical"], 0x4a9060 + idx * 4)
                self.assertEqual(r["status"], 0x4a90a0 + idx * 4)
                for key in ("threshold_low_upper", "threshold_critical", "status"):
                    self.assertGreaterEqual(r[key], TM_BASE)
                    self.assertLessEqual(r[key], TM_BASE + TM_SIZE - 4)

    def test_sensor_zero_and_sixteen_are_rejected_not_assumed_present(self):
        for value in (0, 16, -1, 0xffff, None, True, "15"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    sensor_registers(value)

    def test_upper_lower_and_critical_masks_use_hardware_ids(self):
        for idx in STOCK_IDS_REPORTED:
            with self.subTest(idx=idx):
                r = sensor_registers(idx)
                upper = 1 << r["upper_irq_bit"]
                lower = 1 << r["lower_irq_bit"]
                critical = 1 << r["critical_irq_bit"]
                self.assertEqual(upper, (1 << (idx + 16)))
                self.assertEqual(critical, lower)
                self.assertLessEqual(upper, 0x80000000)
                self.assertEqual(upper & lower, 0)
        # For hw_id=15 bit 31 must be handled as unsigned 32-bit
        self.assertEqual(1 << sensor_registers(15)["upper_irq_bit"], 0x80000000)

    def test_cpu_thermal_zones_reference_only_stock_reported_ids(self):
        self.assertEqual(len(CPU_ZONES), 8)
        self.assertEqual(CPU_ZONES, {
            "cpu0-thermal": 9, "cpu1-thermal": 10,
            "cpu2-thermal": 11, "cpu3-thermal": 12,
            "cpu4-thermal": 4, "cpu5-thermal": 5,
            "cpu6-thermal": 6, "cpu7-thermal": 7,
        })
        self.assertTrue(set(CPU_ZONES.values()).issubset(STOCK_IDS_REPORTED))

    def test_reference_signed_conversion_not_mistaken_for_real_calibration(self):
        self.assertEqual(generic_v2_raw12_to_millicelsius(0), 0)
        self.assertEqual(generic_v2_raw12_to_millicelsius(0x001), 100)
        self.assertEqual(generic_v2_raw12_to_millicelsius(0x7ff), 204700)
        self.assertEqual(generic_v2_raw12_to_millicelsius(0x800), -204800)
        self.assertEqual(generic_v2_raw12_to_millicelsius(0xfff), -100)


if __name__ == "__main__":
    unittest.main()
