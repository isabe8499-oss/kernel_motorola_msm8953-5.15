#!/usr/bin/env python3
"""Host-only RPM SMD OF match contract tests. No hardware or firmware actions."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT = "qcom,rpm-msm8953"


def source(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class TestDeenC100RpmOfMatch(unittest.TestCase):
    def test_driver_of_match_table_contains_exactly_one_msm8953(self):
        driver = source("drivers/soc/qcom/smd-rpm.c")
        table = re.search(
            r"static\s+const\s+struct\s+of_device_id\s+qcom_smd_rpm_of_match\s*\[\s*\]\s*=\s*\{(.*?)\n\};",
            driver, re.S)
        self.assertIsNotNone(table, "RPM OF table not found")
        entries = re.findall(
            r'\.\s*compatible\s*=\s*"([^"]+)"', table.group(1))
        self.assertEqual(entries.count(COMPAT), 1)
        self.assertIn("MODULE_DEVICE_TABLE(of, qcom_smd_rpm_of_match);", driver)
        self.assertRegex(driver, r"\.of_match_table\s*=\s*qcom_smd_rpm_of_match")

    def test_binding_already_documents_msm8953(self):
        binding = source("Documentation/devicetree/bindings/soc/qcom/qcom,smd-rpm.yaml")
        self.assertRegex(binding, r"(?m)^\s*-\s*qcom,rpm-msm8953\s*$")
        self.assertIn("rpm_requests", binding)

    def test_device_tree_names_matching_smd_channel(self):
        dts = source("arch/arm64/boot/dts/qcom/msm8953.dtsi")
        self.assertIn('compatible = "qcom,rpm-msm8953";', dts)
        self.assertIn('qcom,smd-channels = "rpm_requests";', dts)
        self.assertIn("rpm_requests: rpm-requests {", dts)

    def test_qcom_smd_passes_of_node_to_rpmsg_device(self):
        smd = source("drivers/rpmsg/qcom_smd.c")
        self.assertRegex(
            smd,
            r"rpdev->dev\.of_node\s*=\s*qcom_smd_match_channel\(edge->of_node,\s*channel->name\)")
        self.assertIn('key = "qcom,smd-channels";', smd)
        self.assertIn("return rpmsg_register_device(rpdev);", smd)

    def test_rpmsg_bus_falls_back_to_of_match(self):
        core = source("drivers/rpmsg/rpmsg_core.c")
        match = re.search(
            r"static\s+int\s+rpmsg_dev_match\(.*?\n\}", core, re.S)
        self.assertIsNotNone(match)
        self.assertIn("return of_driver_match_device(dev, drv);", match.group(0))

    def test_rpm_driver_does_not_substitute_name_only_match(self):
        driver = source("drivers/soc/qcom/smd-rpm.c")
        self.assertIn(".of_match_table = qcom_smd_rpm_of_match", driver)
        self.assertNotIn(".id_table =", driver)


if __name__ == "__main__":
    unittest.main()
