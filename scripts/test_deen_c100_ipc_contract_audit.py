#!/usr/bin/env python3
"""Unit tests of the host-only audit utility; no device, network or kernel build."""
import tempfile
import unittest
from pathlib import Path

from deen_c100_ipc_contract_audit import check_driver


class TestC100Audit(unittest.TestCase):
    def test_of_match_present_absent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "drivers/soc/qcom/smd-rpm.c"
            path.parent.mkdir(parents=True)
            path.write_text('static const char *s = "qcom,rpm-msm8953";\n')
            self.assertEqual(check_driver(root, "drivers/soc/qcom/smd-rpm.c", "qcom,rpm-msm8953")["status"], "OF_MATCH_ABSENT")
            path.write_text('  { .compatible = "qcom,rpm-msm8953" },\n')
            self.assertEqual(check_driver(root, "drivers/soc/qcom/smd-rpm.c", "qcom,rpm-msm8953")["status"], "OF_MATCH_PRESENT")

    def test_missing_driver_is_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(check_driver(Path(d), "drivers/missing.c", "foo")["status"], "SOURCE_MISSING")


if __name__ == "__main__":
    unittest.main()
