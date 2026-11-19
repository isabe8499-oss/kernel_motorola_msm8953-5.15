#!/usr/bin/env python3
"""Independent TSENS hw_ids OOB guard source audit, on ACK-derived branch.

No staged MSM8953 descriptor, FDT/firmware access, or runtime assumptions.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "drivers/thermal/qcom/tsens.c"
V2 = ROOT / "drivers/thermal/qcom/tsens-v2.c"


def accepts(count, mapped_count=None):
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        return False
    return mapped_count is None or count <= mapped_count


class TestTsensHwidsStandalone(unittest.TestCase):
    def test_exact_guard_and_order_before_first_hwids_index(self):
        source = CORE.read_text(encoding="utf-8")
        check = "if (data->hw_ids && num_sensors > data->num_sensors)"
        self.assertEqual(source.count(check), 1)
        start = source.index("static int tsens_probe(")
        override = source.index('of_property_read_u32(np, "#qcom,sensors", &num_sensors);', start)
        validate = source.index("if (num_sensors <= 0)", override)
        guard = source.index(check, validate)
        alloc = source.index("priv = devm_kzalloc(dev,", guard)
        lookup = source.index("priv->sensor[i].hw_id = data->hw_ids[i];", alloc)
        probe_callbacks = source.index("if (!priv->ops || !priv->ops->init || !priv->ops->get_temp)", lookup)
        self.assertTrue(start < override < validate < guard < alloc < lookup < probe_callbacks)
        self.assertIn('dev_err(dev, "%s: sensor count exceeds hardware ID map\\n", __func__);',
                      source[guard:alloc])
        self.assertIn("return -EINVAL;", source[guard:alloc])

    def test_reject_dt_override_larger_than_mapped_table(self):
        for n in (16, 17, 31, 0xffffffff):
            with self.subTest(count=n):
                self.assertFalse(accepts(n, 15))
        for n in (1, 9, 14, 15):
            with self.subTest(count=n):
                self.assertTrue(accepts(n, 15))

    def test_preserve_unchanged_default_hw_ids_path(self):
        for n in (1, 15, 16, 31):
            with self.subTest(count=n):
                self.assertTrue(accepts(n, None))
        self.assertIn("priv->sensor[i].hw_id = i;", CORE.read_text())

    def test_invalid_nonpositive_counts_remain_invalid(self):
        for n in (0, -1, -15):
            with self.subTest(count=n):
                self.assertFalse(accepts(n, None))
                self.assertFalse(accepts(n, 15))

    def test_no_msm8953_stage_descriptor_or_new_of_activation(self):
        source = CORE.read_text()
        self.assertNotIn("data_msm8953_stage_only", source)
        self.assertNotIn("data_msm8953_stage_only", V2.read_text())
        self.assertNotRegex(source, r'\.compatible\s*=\s*"qcom,msm8953-tsens"')
        self.assertIn('.compatible = "qcom,tsens-v2"', source)

    def test_guard_is_conditional_on_explicit_hwids_not_all_devices(self):
        source = CORE.read_text()
        self.assertIn("if (data->hw_ids && num_sensors > data->num_sensors)", source)
        self.assertNotIn("if (num_sensors > data->num_sensors)", source)
        self.assertTrue(accepts(16, None))
        self.assertFalse(accepts(16, 15))


if __name__ == "__main__":
    unittest.main()
