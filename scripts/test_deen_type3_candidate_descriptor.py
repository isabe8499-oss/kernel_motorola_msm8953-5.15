#!/usr/bin/env python3
"""Non-activating MSM8953 TYPE3 15-ID descriptor source checks."""
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestType3Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v2 = (ROOT/"drivers/thermal/qcom/tsens-v2.c").read_text()
        cls.driver = (ROOT/"drivers/thermal/qcom/tsens.c").read_text()
        cls.soc = (ROOT/"arch/arm64/boot/dts/qcom/msm8953.dtsi").read_text()

    def test_exact_15_stock_hw_ids(self):
        m = re.search(r"static unsigned int msm8953_type3_hw_ids\[\] = \{([^}]+)\};", self.v2)
        self.assertIsNotNone(m)
        self.assertEqual([int(x) for x in re.findall(r"\d+", m.group(1))], list(range(1,16)))

    def test_descriptor_no_silent_16th_sensor(self):
        m = re.search(r"struct tsens_plat_data data_msm8953_type3_candidate = \{([^}]+)\};", self.v2)
        self.assertIsNotNone(m)
        self.assertIn(".num_sensors\t= ARRAY_SIZE(msm8953_type3_hw_ids)", m.group(1))
        self.assertIn(".hw_ids\t\t= msm8953_type3_hw_ids", m.group(1))

    def test_production_of_match_remains_unchanged(self):
        m = re.search(r"static const struct of_device_id tsens_table\[\] = \{(.*?)\n\};",
                      self.driver, re.S)
        self.assertIsNotNone(m)
        self.assertNotIn("qcom,msm8953-tsens", m.group(1))
        self.assertNotIn("data_msm8953_type3_candidate", self.driver)

    def test_prior_hw_ids_guard_must_precede_copy(self):
        g = self.driver.index("if (data->hw_ids && num_sensors > data->num_sensors)")
        c = self.driver.index("priv->sensor[i].hw_id = data->hw_ids[i]", g)
        self.assertLess(g, c)

    def test_board_thermal_config_not_pretended_valid(self):
        self.assertIn('#qcom,sensors = <16>;', self.soc)
        self.assertIn('compatible = "qcom,msm8953-tsens", "qcom,tsens-v2";', self.soc)

    def test_known_type3_register_matches_are_only_offsets(self):
        expected = {
            "TM_UPPER_LOWER_INT_STATUS_OFF": "0x0008",
            "TM_UPPER_LOWER_INT_CLEAR_OFF": "0x000c",
            "TM_Sn_STATUS_OFF": "0x00a0",
            "TM_TRDY_OFF": "0x00e4",
        }
        for name, val in expected.items():
            with self.subTest(name=name):
                self.assertRegex(self.v2, re.escape(name)+r"\s+"+val)

    def test_driver_is_not_enabled_via_desc(self):
        self.assertIn("It must NOT be added", self.v2)
        self.assertNotIn("qcom,msm8953-tsens", self.driver)


if __name__ == "__main__":
    unittest.main()
