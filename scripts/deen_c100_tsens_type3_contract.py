#!/usr/bin/env python3
"""Deen TSENS TYPE3 provenance/geometry audit, not a thermal driver.

Reads existing PVT1/PVT2 DTBs and ACK 5.15 sources without touching hardware.
A passing audit explicitly preserves TSENS runtime/schema/boot as HOLD.
Stock C100 facts below are transcribed from the repo's *prior* stock FDT audit,
NOT a fresh comparison against an original stock FDT binary.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from deen_fdt_memory_ledger import parse_fdt, strings, words, decode_reg, resolve_cells
from deen_c100_spmi_schema_gate import KNOWN_NON_SPMI, parse_diagnostics

NODE = "/soc@0/thermal-sensor@4a9000"
EXPECTED_SHA = {
    "pvt1": "fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a",
    "pvt2": "9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05",
}
# See main/documentation/DEEN_C100_TSENS_AND_PINCTRL_AUDIT.md
STOCK_REPORTED = {
    "compatible": ["qcom,msm8953-tsens"],
    "sensor_count": 15,
    "sensor_ids": list(range(1, 16)),
    "client_ids": list(range(1, 16)),
    "slopes": [0xc80] * 15,
    "reg": [(0x4a8000, 0x2000), (0x0a4000, 0x1000)],
    "interrupt_ids": [184, 314],
    "interrupt_names": ["tsens-upper-lower", "tsens-critical"],
}
CANDIDATE = {
    "compatible": ["qcom,msm8953-tsens", "qcom,tsens-v2"],
    "sensor_count": 16,
    "reg": [(0x4a9000, 0x1000), (0x4a8000, 0x1000)],
    "interrupt_ids": [184, 314],
    "interrupt_names": ["uplow", "critical"],
}
PHYSICAL_REGISTER_CORRESPONDENCE = {
    "tm_sensor_status": [0x4a8000 + 0x10a0, 0x4a9000 + 0x00a0],
    "tm_ready": [0x4a8000 + 0x10e4, 0x4a9000 + 0x00e4],
}
# WARNING: only an ACK 5.15 generic-v2 numeric reference model, NOT
# an assertion about the legacy thermal framework units or C100 accuracy.
def generic_v2_raw12_to_millicelsius(raw):
    if not isinstance(raw, int) or raw < 0 or raw > 0xfff:
        raise ValueError("generic v2 hardware field must be an unsigned 12-bit value")
    signed = raw - 0x1000 if raw & 0x800 else raw
    return signed * 100


def audit_source(root):
    issues = []
    modern = (root / "drivers/thermal/qcom/tsens.c").read_text(encoding="utf-8")
    version2 = (root / "drivers/thermal/qcom/tsens-v2.c").read_text(encoding="utf-8")
    dtsi = (root / "arch/arm64/boot/dts/qcom/msm8953.dtsi").read_text(encoding="utf-8")
    required = [
        ("modern signed 12-bit conversion", "return sign_extend32(temp, resolution) * 100;", modern),
        ("modern sequential default hw IDs", "priv->sensor[i].hw_id = i;", modern),
        ("modern generic v2 OF match", '.compatible = "qcom,tsens-v2"', modern),
        ("modern TM status offset", "#define TM_Sn_STATUS_OFF", version2),
        ("modern TM ready offset", "#define TM_TRDY_OFF", version2),
        ("modern max 16 sensors", ".max_sensors\t= 16", version2),
        ("candidate 16-sensor DTS contract", "#qcom,sensors = <16>;", dtsi),
    ]
    for label, token, source in required:
        if token not in source:
            issues.append("source mismatch: " + label)
    if "qcom,msm8953-tsens" in modern:
        issues.append("unexpected dedicated msm8953 TSENS driver match; audit required")
    if not all(a == b for a, b in PHYSICAL_REGISTER_CORRESPONDENCE.values()):
        issues.append("legacy and modern TM offsets are not physically aligned")
    return {"provenance": "ACK 5.15 sources in checkout", "issues": issues}


def audit_variant(name, board, dtb, log):
    data = dtb.read_bytes()
    nodes, _ = parse_fdt(data)
    errors = []
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXPECTED_SHA[name]:
        errors.append("candidate DTB differs from PR#7 baseline")
    if words(nodes.get("/", {}).get("qcom,board-id", b"")) != [0x4d, board]:
        errors.append("board ID mismatched")
    node = nodes.get(NODE, {})
    found_compatible = strings(node.get("compatible", b""))
    if found_compatible != CANDIDATE["compatible"]:
        errors.append("candidate TSENS compatible changed")
    ac = resolve_cells(nodes, "/soc@0")
    reg = [(x["start"], x["size"]) for x in decode_reg(node, *ac)] if ac else []
    if reg != CANDIDATE["reg"]:
        errors.append("candidate TSENS register windows changed")
    count = words(node.get("#qcom,sensors", b""))
    if count != [16]:
        errors.append("candidate TSENS count unexpectedly changed")
    irqs = words(node.get("interrupts", b"")) or []
    irq_ids = [irqs[i + 1] for i in range(0, len(irqs), 3)] if len(irqs) % 3 == 0 else []
    if irq_ids != CANDIDATE["interrupt_ids"] or strings(node.get("interrupt-names", b"")) != CANDIDATE["interrupt_names"]:
        errors.append("TSENS interrupt contract unexpectedly changed")
    if words(node.get("#thermal-sensor-cells", b"")) != [1]:
        errors.append("thermal-sensor-cells unexpected")
    for legacy_key in ("qcom,sensor-id", "qcom,client-id", "qcom,slope", "reg-names"):
        if legacy_key in node:
            errors.append("unexpected legacy property introduced: " + legacy_key)
    diag = parse_diagnostics(log.read_text(encoding="utf-8", errors="replace"))
    counts = Counter(item["node"] for item in diag)
    if counts != KNOWN_NON_SPMI or counts["thermal-sensor@4a9000"] != 1:
        errors.append("remaining schema diagnostic baseline changed (TSENS must remain visible)")
    return {
        "board": name, "board_id": f"0x{board:x}", "dtb_sha256": sha,
        "candidate_node_count": len(nodes), "candidate_tsens_compatibles": found_compatible,
        "candidate_tsens_reg": [[f"0x{a:x}", f"0x{n:x}"] for a, n in reg],
        "candidate_sensors": count, "candidate_irq_ids": irq_ids,
        "diagnostics_count": sum(counts.values()),
        "diagnostics_by_node": dict(sorted(counts.items())),
        "stock_binary_comparison": "NOT_DONE_STOCK_FDT_UNAVAILABLE",
        "stock_reference": "main/documentation/DEEN_C100_TSENS_AND_PINCTRL_AUDIT.md",
        "hardware_thermal_runtime": "HOLD_TYPE3_NOT_VALIDATED",
        "errors": errors, "host_gate": "PASS_AUDIT_ONLY" if not errors else "FAIL",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("pvt1", "pvt2"):
        p.add_argument("--" + name + "-dtb", type=Path, required=True)
        p.add_argument("--" + name + "-schema-log", type=Path, required=True)
    p.add_argument("--kernel-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    report = {
        "stock_reference": STOCK_REPORTED,
        "register_correspondence": PHYSICAL_REGISTER_CORRESPONDENCE,
        "source": audit_source(a.kernel_root),
        "pvt1": audit_variant("pvt1", 0xc100, a.pvt1_dtb, a.pvt1_schema_log),
        "pvt2": audit_variant("pvt2", 0xc200, a.pvt2_dtb, a.pvt2_schema_log),
        "legacy_driver_port": "HOLD",
        "thermal_sensor_mapping": "HOLD_1_TO_15_VS_0_TO_15",
        "firmware_boot_flash_merge": "HOLD",
    }
    report["overall"] = (
        "PASS_HOST_AUDIT_ONLY_WITH_THERMAL_HOLD"
        if not report["source"]["issues"] and all(
            report[key]["host_gate"] == "PASS_AUDIT_ONLY" for key in ("pvt1", "pvt2"))
        else "FAIL")
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(report["overall"])
    for key in ("pvt1", "pvt2"):
        print(key, "schema diagnostics:", report[key]["diagnostics_count"],
              "TSENS runtime:", report[key]["hardware_thermal_runtime"])
        for err in report[key]["errors"]:
            print(key, "ERROR:", err, file=sys.stderr)
    for err in report["source"]["issues"]:
        print("ERROR:", err, file=sys.stderr)
    return 0 if report["overall"].startswith("PASS_HOST_AUDIT_ONLY") else 3


if __name__ == "__main__":
    sys.exit(main())
