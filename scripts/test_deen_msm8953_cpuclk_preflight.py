#!/usr/bin/env python3
"""Host regression checks for the first compile-only MSM8953 CPUCLK port slice."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "drivers/clk/qcom/clk-cpu-msm8953-preflight.c"
CONFIG = ROOT / "drivers/clk/qcom/Kconfig"
MAKEFILE = ROOT / "drivers/clk/qcom/Makefile"
REFERENCE = ROOT / "documentation/DEEN_STOCK_CPU_CLOCK_TWO_CLUSTERS_2026-11-20.json"


def decode_speed_bin(value):
    return (value >> 8) & 0x7


class TestCpuClockPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = DRIVER.read_text()
        cls.manifest = json.loads(REFERENCE.read_text())

    def test_pinned_seven_resource_names_and_min_sizes(self):
        regs = self.manifest["stock_cpu_clock"]["registers"]
        self.assertEqual(len(regs), 7)
        for entry in regs:
            with self.subTest(entry=entry["name"]):
                pattern = r'\{\s*"' + re.escape(entry["name"]) + r'",\s*0x' + format(entry["size"], "x") + r'\s*\}'
                self.assertRegex(self.source, pattern)

    def test_legacy_speed_bin_selection_is_pure_and_fixed(self):
        self.assertIn("return (efuse_value >> 8) & 0x7;", self.source)
        for v in range(8):
            self.assertEqual(decode_speed_bin(v << 8), v)
        self.assertEqual(decode_speed_bin(0xffffffff), 7)
        self.assertEqual(decode_speed_bin(0xfffff0ff), 0)

    def test_resource_overlap_is_rejected(self):
        self.assertIn("res->start <= prev->end && prev->start <= res->end", self.source)
        self.assertIn("resource_size(res) < msm8953_cpuclk_resources[i].minimum_size",
                      self.source)

    def test_voltage_frequency_pairs_require_even_number_of_cells(self):
        self.assertIn("of_property_count_u32_elems(np, name)", self.source)
        self.assertIn("if (!cells || (cells & 1))", self.source)
        self.assertIn("if (bin > 7)", self.source)

    def test_table_names_cover_both_clusters_and_cci(self):
        self.assertIn('"qcom,speed%u-bin-v0-%s"', self.source)
        self.assertIn('cci ? "cci" : "cl"', self.source)
        self.assertEqual(len(self.manifest["stock_cpu_clock"]["speed_bin_property_names"]), 8)

    def test_no_mmio_or_voltage_changes_and_no_driver_binding(self):
        forbidden = ("readl(", "readl_relaxed(", "writel(", "writel_relaxed(",
                     "clk_set_rate(", "regulator_set_voltage(",
                     "of_clk_add_hw_provider(", "module_platform_driver(",
                     "platform_driver_register(", "devm_ioremap(")
        for f in forbidden:
            with self.subTest(f=f):
                self.assertNotIn(f, self.source)
        self.assertNotIn("qcom,cpu-clock-8953", self.source)

    def test_no_enabled_clocks_in_production_kconfig(self):
        k = CONFIG.read_text()
        m = MAKEFILE.read_text()
        self.assertIn("config QCOM_MSM8953_CPUCLK_PREFLIGHT", k)
        self.assertIn("depends on ARM64 && COMPILE_TEST", k)
        self.assertIn("obj-$(CONFIG_QCOM_MSM8953_CPUCLK_PREFLIGHT)", m)
        self.assertNotIn("QCOM_MSM8953_CPUCLK_PREFLIGHT",
                         (ROOT / "arch/arm64/configs/deen-msm8953-base.fragment").read_text())

    def test_ref_is_not_runtime_validation(self):
        m = self.manifest
        self.assertFalse(m["stock_cpu_clock"]["clock_frequency_is_measured_runtime"])
        self.assertFalse(m["ack515_candidate"]["cpu_clock_provider_in_dtb"])
        self.assertIn("CPU_DVFS_DRIVER_PORT=HOLD", m["holds"])


if __name__ == "__main__":
    unittest.main()
