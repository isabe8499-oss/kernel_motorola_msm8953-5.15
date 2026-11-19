#!/usr/bin/env python3
"""Unit tests for the limited Deen C100 RPM DTB schema gate."""
from collections import Counter
from pathlib import Path
import unittest

from deen_c100_rpm_schema_gate import diagnostics, KNOWN_NON_RPM

ROOT = Path(__file__).resolve().parents[1]


class TestRpmSchemaGate(unittest.TestCase):
    def test_dts_binding_whitelists_only_three_existing_children(self):
        binding = (ROOT / "Documentation/devicetree/bindings/soc/qcom/"
                   "qcom,smd-rpm.yaml").read_text()
        self.assertIn('"^(rpmcc|power-controller|regulators)$":', binding)
        self.assertIn("additionalProperties: false", binding)
        self.assertNotIn("additionalProperties: true", binding)

    def test_only_deen_removes_unused_rpmpd_xo(self):
        common = (ROOT / "arch/arm64/boot/dts/qcom/"
                  "msm8953-motorola-deen-common.dtsi").read_text()
        soc = (ROOT / "arch/arm64/boot/dts/qcom/msm8953.dtsi").read_text()
        driver = (ROOT / "drivers/soc/qcom/rpmpd.c").read_text()
        self.assertIn("&rpmpd {", common)
        self.assertIn("/delete-property/ clocks;", common)
        self.assertIn("/delete-property/ clock-names;", common)
        self.assertIn('clock-names = "ref";', soc)
        self.assertIn("clocks = <&xo_board>;", soc)
        self.assertNotIn("devm_clk_get", driver)
        self.assertNotIn("clk_prepare_enable", driver)
        self.assertNotIn("clk_get(", driver)

    def test_parser_counts_original_schema_diagnostics_and_keeps_context(self):
        fake = (
            "out/pvt1.dtb: rpm-requests: child nodes disallowed\n"
            "\tfrom schema $id: http://example/rpm\n"
            "out/pvt1.dtb: power-controller: clocks invalid\n"
            "out/pvt1.dtb: usb@70f8800: compatible invalid\n"
        )
        rows = diagnostics(fake)
        self.assertEqual([r["node"] for r in rows],
                         ["rpm-requests", "power-controller", "usb@70f8800"])

    def test_remaining_errors_are_explicitly_not_a_global_pass(self):
        self.assertEqual(sum(KNOWN_NON_RPM.values()), 12)
        self.assertEqual(KNOWN_NON_RPM["usb@70f8800"], 5)
        self.assertEqual(KNOWN_NON_RPM["rtc@6000"], 2)
        self.assertIn("/", KNOWN_NON_RPM)


if __name__ == "__main__":
    unittest.main()
