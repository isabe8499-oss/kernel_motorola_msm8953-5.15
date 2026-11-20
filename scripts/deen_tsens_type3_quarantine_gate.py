#!/usr/bin/env python3
"""Fail-closed Deen PVT1/PVT2 TSENS quarantine test on COMPILED DTBs.

Not a thermal driver port, not validation of temperature/calibration, and
NOT permission to boot or flash. Uses fdtget from device-tree-compiler.
"""
import argparse
import json
from pathlib import Path
import subprocess

NODE = "/soc@0/thermal-sensor@4a9000"
EXPECTED_COMPAT = ["qcom,msm8953-tsens", "qcom,tsens-v2"]
BOARD = {"pvt1": [0x4D, 0xC100], "pvt2": [0x4D, 0xC200]}


def fdtget(dtb, node, prop, kind="s"):
    proc = subprocess.run(
        ["fdtget", "-t", kind, str(dtb), node, prop],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise ValueError(f"{dtb}: {node}:{prop}: {proc.stderr.strip()}")
    return proc.stdout.strip().split()


def inspect_dtb(path):
    return {
        "status": fdtget(path, NODE, "status"),
        "compatible": fdtget(path, NODE, "compatible"),
        "sensor_count": [int(x, 16) for x in fdtget(path, NODE, "#qcom,sensors", "x")],
        "board_id": [int(x, 16) for x in fdtget(path, "/", "qcom,board-id", "x")],
    }


def validate(board, actual):
    errors = []
    if actual["status"] != ["disabled"]:
        errors.append("TSENS_UNVALIDATED_DRIVER_NOT_DISABLED")
    if actual["compatible"] != EXPECTED_COMPAT:
        errors.append("TSENS_COMPAT_CHANGED_WITHOUT_NEW_EVIDENCE")
    # This check intentionally retains the WRONG inherited count: changing
    # the count to 15 does not establish the proper TYPE3 register map.
    if actual["sensor_count"] != [16]:
        errors.append("TSENS_COUNT_CHANGED_WITHOUT_TYPE3_DRIVER")
    if actual["board_id"] != BOARD[board]:
        errors.append("BOARD_ID_MISMATCH")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pvt1", type=Path, required=True)
    parser.add_argument("--pvt2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = {
        "gate": "DEEN_PVT_TSENS_TYPE3_QUARANTINE",
        "stock_verified_sensor_ids": list(range(1, 16)),
        "candidate_v2_sensor_count": 16,
        "stock_type3_register_equivalence": "HOLD",
        "tsens_runtime_and_thermal_protection": "HOLD",
        "full_kernel_boot_and_flash": "HOLD",
        "safe_for_flash": False,
        "checks": {},
        "errors": [],
    }
    for board, dtb in (("pvt1", args.pvt1), ("pvt2", args.pvt2)):
        try:
            observed = inspect_dtb(dtb)
            failures = validate(board, observed)
            result["checks"][board] = {"observed": observed, "errors": failures}
            result["errors"].extend(f"{board}:{issue}" for issue in failures)
        except (ValueError, OSError) as exc:
            result["errors"].append(f"{board}:{exc}")

    result["result"] = "PASS_QUARANTINE_ONLY_RUNTIME_HOLD" if not result["errors"] else "FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["result"], result["errors"])
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
