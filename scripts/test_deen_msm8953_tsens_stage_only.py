#!/usr/bin/env python3
"""Tests for the intentionally UNBOUND msm8953 15-ID TSENS staging data.

This test rejects premature OF matching, probe callbacks or DTB rewrites.
Passing it does not validate 15 sensor temperatures or cooling safety.
"""
from pathlib import Path
import re
import unittest

from deen_c100_tsens_type3_register_gate import CPU_ZONES, sensor_registers
from deen_c100_tsens_type3_contract import STOCK_REPORTED

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "drivers/thermal/qcom/tsens-v2.c"
CORE = ROOT / "drivers/thermal/qcom/tsens.c"
SOC = ROOT / "arch/arm64/boot/dts/qcom/msm8953.dtsi"
BINDING = ROOT / "Documentation/devicetree/bindings/thermal/qcom-tsens.yaml"


def stage_descriptor():
    src = STAGE.read_text(encoding="utf-8")
    m = re.search(r"struct tsens_plat_data data_msm8953_stage_only\s*=\s*\{(.*?)\n\};", src, re.S)
    if not m:
        raise AssertionError("staged platform data absent or malformed")
    return m.group(1)


def stage_ids():
    src = STAGE.read_text(encoding="utf-8")
    m = re.search(r"static unsigned int tsens_msm8953_stage_hw_ids\[\]\s*=\s*\{([^}]+)\};", src, re.S)
    if not m:
        raise AssertionError("staged hardware ID table absent")
    return [int(x, 10) for x in re.findall(r"\b\d+\b", m.group(1))]


class TestMsm8953TsensStageOnly(unittest.TestCase):
    def test_exact_fifteen_hw_ids_without_duplicates_or_zero(self):
        ids = stage_ids()
        self.assertEqual(len(ids), 15)
        self.assertEqual(ids, list(range(1, 16)))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn(0, ids)
        self.assertNotIn(16, ids)
        self.assertEqual(ids, STOCK_REPORTED["sensor_ids"])

    def test_real_platform_data_type_count_and_table_reference(self):
        src = STAGE.read_text()
        core = CORE.read_text()
        hdr = (ROOT / "drivers/thermal/qcom/tsens.h").read_text()
        descriptor = stage_descriptor()
        self.assertIn("struct tsens_plat_data {", hdr)
        self.assertRegex(descriptor, r"\.num_sensors\s*=\s*15\s*,")
        self.assertRegex(descriptor, r"\.hw_ids\s*=\s*tsens_msm8953_stage_hw_ids\s*,")
        self.assertIn("priv->sensor[i].hw_id = data->hw_ids[i];", core)
        self.assertEqual(src.count("data_msm8953_stage_only = {"), 1)

    def test_staged_descriptor_cannot_pass_existing_probe_safety_check(self):
        descriptor = stage_descriptor()
        for field in ("ops", "feat", "fields"):
            self.assertNotRegex(descriptor, r"\." + field + r"\s*=")
        src = CORE.read_text()
        self.assertIn("if (!priv->ops || !priv->ops->init || !priv->ops->get_temp)", src)
        self.assertIn("return -EINVAL;", src)
        self.assertIn("data_msm8953_stage_only", STAGE.read_text())

    def test_no_new_of_match_or_driver_registration(self):
        core = CORE.read_text()
        soc = SOC.read_text()
        header = (ROOT / "drivers/thermal/qcom/tsens.h").read_text()
        self.assertNotIn("data_msm8953_stage_only", core)
        self.assertNotIn("data_msm8953_stage_only", header)
        self.assertNotRegex(core, r'\.compatible\s*=\s*"qcom,msm8953-tsens"')
        self.assertIn('.compatible = "qcom,tsens-v2"', core)
        self.assertIn('compatible = "qcom,msm8953-tsens", "qcom,tsens-v2";', soc)
        self.assertIn("#qcom,sensors = <16>;", soc)
        self.assertNotIn("data_msm8953_stage_only", soc)

    def test_cpu_sensor_references_fit_reported_stock_sensor_ids(self):
        ids = set(stage_ids())
        self.assertEqual(len(CPU_ZONES), 8)
        self.assertTrue(set(CPU_ZONES.values()).issubset(ids))
        for hw_id in ids:
            r = sensor_registers(hw_id)
            self.assertLessEqual(r["upper_irq_bit"], 31)
            self.assertLessEqual(r["status"], 0x4a9fff)

    def test_tsens_schema_remains_unmodified_and_not_fake_pass(self):
        schema = BINDING.read_text()
        self.assertIn("qcom,tsens-v2", schema)
        self.assertNotIn("qcom,msm8953-tsens", schema)
        self.assertIn("additionalProperties: false", schema)


if __name__ == "__main__":
    unittest.main()
