#!/usr/bin/env python3
"""Pure host regression for the Deen TSENS TYPE3 hold-gate."""
import sys
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import deen_tsens_type3_quarantine_gate as gate


def fields(board):
    return {
        "status": ["disabled"],
        "compatible": ["qcom,msm8953-tsens", "qcom,tsens-v2"],
        "sensor_count": [16],
        "board_id": gate.BOARD[board],
    }


class TestDeenTsensQuarantine(unittest.TestCase):
    def test_pvt1_and_pvt2_expected_legacy_quarantine(self):
        for board in ("pvt1", "pvt2"):
            self.assertEqual(gate.validate(board, fields(board)), [])

    def test_missing_or_enabled_status_fails(self):
        for value in ([], ["okay"], ["ok"], ["reserved"]):
            d = fields("pvt1")
            d["status"] = value
            self.assertIn("TSENS_UNVALIDATED_DRIVER_NOT_DISABLED",
                          gate.validate("pvt1", d))

    def test_count_change_without_driver_is_not_claimed_as_fix(self):
        for number in (0, 1, 15, 17):
            d = fields("pvt1")
            d["sensor_count"] = [number]
            self.assertIn("TSENS_COUNT_CHANGED_WITHOUT_TYPE3_DRIVER",
                          gate.validate("pvt1", d))

    def test_compatible_not_silently_reinterpreted(self):
        d = fields("pvt1")
        d["compatible"] = ["qcom,msm8953-tsens"]
        self.assertIn("TSENS_COMPAT_CHANGED_WITHOUT_NEW_EVIDENCE",
                      gate.validate("pvt1", d))

    def test_hardware_board_id_can_never_swap(self):
        d = fields("pvt2")
        d["board_id"] = gate.BOARD["pvt1"]
        self.assertIn("BOARD_ID_MISMATCH", gate.validate("pvt2", d))

    def test_only_board_common_overrides_status_not_soc(self):
        common = (ROOT / "arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi").read_text()
        soc = (ROOT / "arch/arm64/boot/dts/qcom/msm8953.dtsi").read_text()
        self.assertIn('&tsens0 {\n\tstatus = "disabled";\n};', common)
        self.assertEqual(common.count('&tsens0 {'), 1)
        self.assertIn('#qcom,sensors = <16>;', soc)
        self.assertIn('compatible = "qcom,msm8953-tsens", "qcom,tsens-v2";', soc)
        for board in ("pvt1", "pvt2"):
            dts = (ROOT / f"arch/arm64/boot/dts/qcom/msm8953-motorola-deen-{board}.dts").read_text()
            self.assertIn('#include "msm8953-motorola-deen-common.dtsi"', dts)

    def test_missing_fdt_property_is_failure(self):
        with mock.patch.object(gate.subprocess, "run") as run:
            run.return_value.returncode = 1
            run.return_value.stderr = "FDT_ERR_NOTFOUND"
            with self.assertRaisesRegex(ValueError, "FDT_ERR_NOTFOUND"):
                gate.fdtget("some.dtb", gate.NODE, "status")


if __name__ == "__main__":
    unittest.main()
