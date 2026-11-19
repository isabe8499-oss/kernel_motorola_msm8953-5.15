#!/usr/bin/env python3
"""Source-contract tests for TSENS hw_ids count bounds (no device access).

This checks the actual driver's guard and its ordering, plus a pure model of
count acceptance. The model is not evidence of physical thermal operation.
"""
from pathlib import Path
import re
import unittest

from test_deen_msm8953_tsens_stage_only import stage_ids

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "drivers/thermal/qcom/tsens.c"
SOC = ROOT / "arch/arm64/boot/dts/qcom/msm8953.dtsi"
STAGE = ROOT / "drivers/thermal/qcom/tsens-v2.c"


def count_allowed(num_sensors, map_length=None):
    """Host model of existing <=0 check plus new mapped-count guard."""
    if not isinstance(num_sensors, int) or num_sensors <= 0:
        return False
    return map_length is None or num_sensors <= map_length


class TestTsensHwIdsCountGuard(unittest.TestCase):
    def test_guard_is_before_allocation_and_every_hw_id_read(self):
        source = CORE.read_text(encoding="utf-8")
        marker = "if (data->hw_ids && num_sensors > data->num_sensors)"
        self.assertEqual(source.count(marker), 1)
        probe = source.index("static int tsens_probe(")
        override = source.index('of_property_read_u32(np, "#qcom,sensors", &num_sensors);', probe)
        old_check = source.index("if (num_sensors <= 0)", override)
        guard = source.index(marker, old_check)
        allocation = source.index("priv = devm_kzalloc(dev,", guard)
        mapping = source.index("priv->sensor[i].hw_id = data->hw_ids[i];", allocation)
        self.assertTrue(probe < override < old_check < guard < allocation < mapping)
        self.assertIn("sensor count exceeds hardware ID map", source[guard:allocation])
        self.assertRegex(source[guard:allocation], r"return -EINVAL;")

    def test_count_guard_is_conditional_on_hw_ids_table(self):
        source = CORE.read_text()
        self.assertIn("if (data->hw_ids && num_sensors > data->num_sensors)", source)
        self.assertNotIn("if (num_sensors > data->num_sensors)", source)
        self.assertTrue(count_allowed(16, None), "Unmapped default path unchanged")
        self.assertFalse(count_allowed(16, 15), "Mapped 15-entry path must reject 16")
        self.assertTrue(count_allowed(15, 15), "Exact mapping count remains valid")
        self.assertTrue(count_allowed(1, 15), "Smaller override remains valid")

    def test_invalid_and_boundary_counts(self):
        for bad in (-3, -1, 0):
            with self.subTest(value=bad):
                self.assertFalse(count_allowed(bad, 15))
        for valid in (1, 2, 14, 15):
            with self.subTest(value=valid):
                self.assertTrue(count_allowed(valid, 15))
        for invalid in (16, 17, 0xffffffff):
            with self.subTest(value=invalid):
                self.assertFalse(count_allowed(invalid, 15))

    def test_staged_ms8953_mapping_still_unbound_and_exposes_risk(self):
        ids = stage_ids()
        source = CORE.read_text()
        self.assertEqual(ids, list(range(1, 16)))
        self.assertIn("#qcom,sensors = <16>;", SOC.read_text())
        self.assertNotRegex(source, r'\.compatible\s*=\s*"qcom,msm8953-tsens"')
        self.assertNotIn("data_msm8953_stage_only", source)
        staged = STAGE.read_text()
        self.assertIn("struct tsens_plat_data data_msm8953_stage_only", staged)
        self.assertNotIn(".ops\t\t= &ops_generic_v2", staged.split("data_msm8953_stage_only = {",1)[1].split("};",1)[0])
        self.assertFalse(count_allowed(16, len(ids)))

    def test_fallback_dtb_and_all_probe_callbacks_are_unchanged(self):
        core = CORE.read_text()
        self.assertIn('.compatible = "qcom,tsens-v2"', core)
        self.assertIn("if (!priv->ops || !priv->ops->init || !priv->ops->get_temp)", core)
        self.assertIn("return tsens_register(priv);", core)
        self.assertIn('compatible = "qcom,msm8953-tsens", "qcom,tsens-v2";', SOC.read_text())

    def test_rejects_any_late_guard_placed_after_first_index(self):
        source = CORE.read_text()
        marker = "if (data->hw_ids && num_sensors > data->num_sensors)"
        guard = source.index(marker)
        first_map = source.index("priv->sensor[i].hw_id = data->hw_ids[i];")
        self.assertLess(guard, first_map)
        # The guard is not dependent on callbacks; NULL ops cannot bypass safety.
        callback_check = source.index("if (!priv->ops || !priv->ops->init || !priv->ops->get_temp)")
        self.assertLess(guard, callback_check)


if __name__ == "__main__":
    unittest.main()
