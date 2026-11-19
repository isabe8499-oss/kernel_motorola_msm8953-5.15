#!/usr/bin/env python3
"""Host-only unit tests of Deen SPMI binding scope and TSENS HOLD."""
import re
import unittest
from pathlib import Path
from deen_c100_spmi_schema_gate import EXPECTED_REG, EXPECTED_NAMES, KNOWN_NON_SPMI, parse_diagnostics

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class TestDeenSpmiSchemaScope(unittest.TestCase):
    def test_qcom_only_conditional_and_generic_one_window(self):
        y = read("Documentation/devicetree/bindings/spmi/spmi.yaml")
        self.assertIn("const: qcom,spmi-pmic-arb", y)
        self.assertRegex(y, r"(?m)^  reg:\n    minItems: 1\n    maxItems: 5$")
        self.assertRegex(y, r"then:\s+properties:\s+reg:\s+minItems: 3\s+maxItems: 5")
        self.assertRegex(y, r"else:\s+properties:\s+reg:\s+maxItems: 1")
        self.assertRegex(y, r"if:\s+properties:\s+compatible:\s+contains:\s+const: qcom,spmi-pmic-arb\s+required:\s+- compatible")

    def test_qualcomm_binding_and_driver_use_named_windows(self):
        doc = read("Documentation/devicetree/bindings/spmi/qcom,spmi-pmic-arb.txt")
        drv = read("drivers/spmi/spmi-pmic-arb.c")
        self.assertIn('compatible = "qcom,spmi-pmic-arb"', read("arch/arm64/boot/dts/qcom/msm8953.dtsi"))
        for name in EXPECTED_NAMES:
            self.assertIn(f'"{name}"', doc)
            self.assertRegex(drv, r'platform_get_resource_byname\s*\(')
            self.assertIn(f'"{name}"', drv)
        self.assertEqual(len(EXPECTED_REG), 5)

    def test_tsens_stays_unported_and_schema_visible(self):
        stock = read("drivers/thermal/qcom/tsens.c")
        self.assertIn('compatible = "qcom,tsens-v2"', stock)
        self.assertNotIn('compatible = "qcom,msm8953-tsens"', stock)
        self.assertEqual(KNOWN_NON_SPMI["thermal-sensor@4a9000"], 1)

    def test_log_parser_ignores_followup_indentation(self):
        s = (
            "out/pvt1.dtb: spmi@200f000: reg: [[1, 2]] is too long\n"
            "\tfrom schema $id: http://devicetree.org/schemas/spmi/spmi.yaml#\n"
            "out/pvt1.dtb: thermal-sensor@4a9000: compatible: oneOf failed\n"
        )
        self.assertEqual([e["node"] for e in parse_diagnostics(s)],
                         ["spmi@200f000", "thermal-sensor@4a9000"])
        self.assertEqual(sum(KNOWN_NON_SPMI.values()), 11)


if __name__ == "__main__":
    unittest.main()
