#!/usr/bin/env python3
"""Read-only Deen C100 TSENS register, IRQ, and CPU-zone contract gate.

The pinned Linux 3.18 donor is used solely as source evidence. This program
does not provide a driver, initialize sensors, or authorize boot or flash.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from deen_fdt_memory_ledger import parse_fdt, words, strings, decode_reg, resolve_cells
from deen_c100_spmi_schema_gate import KNOWN_NON_SPMI, parse_diagnostics

NODE = "/soc@0/thermal-sensor@4a9000"
CPU_ZONES = {"cpu0-thermal": 9, "cpu1-thermal": 10,
             "cpu2-thermal": 11, "cpu3-thermal": 12,
             "cpu4-thermal": 4, "cpu5-thermal": 5,
             "cpu6-thermal": 6, "cpu7-thermal": 7}
DTB_SHA = {
    "pvt1": "fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a",
    "pvt2": "9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05",
}
# Legacy vendor has a contiguous 0x4a8000/0x2000 TSENS window. Generic
# 5.15 splits that into SROT 0x4a8000/0x1000 + TM 0x4a9000/0x1000.
LEGACY_BASE = 0x4a8000
TM_BASE = 0x4a9000
TM_SIZE = 0x1000
STOCK_IDS_REPORTED = tuple(range(1, 16))  # From prior stock-FDT report, not extracted here.
# (legacy source register macro, modern source macro, old offset, TM offset)
REGISTER_PAIRS = (
    ("TSENS_TM_INT_EN", "TM_INT_EN_OFF", 0x1004, 0x0004),
    ("TSENS_TM_UPPER_LOWER_INT_STATUS", "TM_UPPER_LOWER_INT_STATUS_OFF", 0x1008, 0x0008),
    ("TSENS_TM_UPPER_LOWER_INT_CLEAR", "TM_UPPER_LOWER_INT_CLEAR_OFF", 0x100c, 0x000c),
    ("TSENS_TM_UPPER_LOWER_INT_MASK", "TM_UPPER_LOWER_INT_MASK_OFF", 0x1010, 0x0010),
    ("TSENS_TM_CRITICAL_INT_STATUS", "TM_CRITICAL_INT_STATUS_OFF", 0x1014, 0x0014),
    ("TSENS_TM_CRITICAL_INT_CLEAR", "TM_CRITICAL_INT_CLEAR_OFF", 0x1018, 0x0018),
    ("TSENS_TM_CRITICAL_INT_MASK", "TM_CRITICAL_INT_MASK_OFF", 0x101c, 0x001c),
    ("TSENS_TM_UPPER_LOWER_THRESHOLD", "TM_Sn_UPPER_LOWER_THRESHOLD_OFF", 0x1020, 0x0020),
    ("TSENS_TM_SN_CRITICAL_THRESHOLD", "TM_Sn_CRITICAL_THRESHOLD_OFF", 0x1060, 0x0060),
    ("TSENS_TM_SN_STATUS", "TM_Sn_STATUS_OFF", 0x10a0, 0x00a0),
    ("TSENS_TM_TRDY", "TM_TRDY_OFF", 0x10e4, 0x00e4),
)


def sensor_registers(hw_id):
    """Pure register/interrupt arithmetic; never access mapped hardware."""
    if not isinstance(hw_id, int) or isinstance(hw_id, bool) or hw_id not in STOCK_IDS_REPORTED:
        raise ValueError("C100 stock-reported sensor ID must be in 1..15")
    result = {
        "sensor_id": hw_id,
        "threshold_low_upper": TM_BASE + 0x20 + 4 * hw_id,
        "threshold_critical": TM_BASE + 0x60 + 4 * hw_id,
        "status": TM_BASE + 0xa0 + 4 * hw_id,
        "lower_irq_bit": hw_id,
        "upper_irq_bit": hw_id + 16,
        "critical_irq_bit": hw_id,
    }
    for field in ("threshold_low_upper", "threshold_critical", "status"):
        if not TM_BASE <= result[field] <= TM_BASE + TM_SIZE - 4:
            raise ValueError("register outside verified candidate TM resource")
    return result


def check_donor_and_modern_sources(vendor_file, kernel_root):
    old = vendor_file.read_text(encoding="utf-8")
    new = (kernel_root / "drivers/thermal/qcom/tsens-v2.c").read_text(encoding="utf-8")
    tsens = (kernel_root / "drivers/thermal/qcom/tsens.c").read_text(encoding="utf-8")
    hdr = (kernel_root / "drivers/thermal/qcom/tsens.h").read_text(encoding="utf-8")
    errors = []
    matches = []
    for legacy, modern, old_offset, new_offset in REGISTER_PAIRS:
        pat_old = re.compile(r"#define\s+" + re.escape(legacy) +
                             r"\s*\(n\)\s*\(\(n\)\s*\+\s*(0x[0-9a-fA-F]+)\)")
        pat_new = re.compile(r"#define\s+" + re.escape(modern) +
                             r"\s+(0x[0-9a-fA-F]+)\b")
        a, b = pat_old.search(old), pat_new.search(new)
        if not a or not b:
            errors.append("register macro absent: " + legacy + " / " + modern)
            continue
        lhs, rhs = int(a.group(1), 16), int(b.group(1), 16)
        if (lhs, rhs) != (old_offset, new_offset) or LEGACY_BASE + lhs != TM_BASE + rhs:
            errors.append("register offset mismatch: " + legacy)
        matches.append({"register": modern,
                        "old_address": f"0x{LEGACY_BASE + lhs:x}",
                        "new_address": f"0x{TM_BASE + rhs:x}"})
    must_old = [
        'compatible = "qcom,msm8953-tsens"',
        "tmdev->tsens_type = TSENS_TYPE3",
        "TSENS_CALIB_FUSE_MAP_NONE",
        "TSENS_TM_CODE_SIGN_BIT",
        "TSENS_TM_SN_STATUS_VALID_BIT",
        "platform_get_irq_byname(pdev,",
        '"tsens-upper-lower"',
        '"tsens-critical"',
        "TSENS_TM_UPPER_INT_SET",
        "sensor[i].sensor_hw_num",
        "tsens_num_sensors",
    ]
    must_new = [
        "REG_FIELD_FOR_EACH_SENSOR16(LAST_TEMP",
        "REG_FIELD_SPLIT_BITS_16_31(UP_INT_MASK",
        "REG_FIELD_SPLIT_BITS_0_15(LOW_INT_MASK",
        "REG_FIELD_SPLIT_BITS_0_15(CRIT_INT_MASK",
        "[VALID] =",
    ]
    for value in must_old:
        if value not in old:
            errors.append("vendor source contract absent: " + value)
    for value in must_new[:-1]:
        if value not in new:
            errors.append("modern v2 source contract absent: " + value)
    if "return sign_extend32(temp, resolution) * 100;" not in tsens:
        errors.append("modern signed temperature conversion changed")
    if "priv->sensor[i].hw_id = data->hw_ids[i];" not in tsens:
        errors.append("modern platform hw_ids mapping changed")
    if "priv->sensor[i].hw_id = i;" not in tsens:
        errors.append("modern default sequential IDs changed")
    if "REG_FIELD_FOR_EACH_SENSOR16" not in hdr:
        errors.append("modern reg_field macro missing")
    # The actual driver remains generic and MUST NOT claim a dedicated MSM8953 binding.
    if '.compatible = "qcom,msm8953-tsens"' in tsens:
        errors.append("dedicated MSM8953 match appeared: review driver before proceeding")
    return {"paired_registers": matches, "problems": errors,
            "legacy_donor": str(vendor_file), "modern_driver": "unchanged 5.15"}


def audit_variant(board, path, log):
    errors = []
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != DTB_SHA[board]:
        errors.append("DTB byte hash differs from approved PR #9")
    nodes, _ = parse_fdt(raw)
    target = nodes.get(NODE, {})
    if words(nodes.get("/", {}).get("qcom,board-id", b"")) != [0x4d, 0xc100 if board == "pvt1" else 0xc200]:
        errors.append("board identity changed")
    if strings(target.get("compatible", b"")) != ["qcom,msm8953-tsens", "qcom,tsens-v2"]:
        errors.append("candidate TSENS compatible changed")
    if words(target.get("#qcom,sensors", b"")) != [16]:
        errors.append("candidate 16-sensor count changed unexpectedly")
    regs = decode_reg(target, *resolve_cells(nodes, "/soc@0"))
    if [(r["start"], r["size"]) for r in regs] != [(0x4a9000, 0x1000), (0x4a8000, 0x1000)]:
        errors.append("candidate TM/SROT window layout changed")
    if words(target.get("interrupts", b"")) != [0, 184, 4, 0, 314, 4]:
        errors.append("candidate two GIC IRQ tuples changed")
    if strings(target.get("interrupt-names", b"")) != ["uplow", "critical"]:
        errors.append("candidate 5.15 IRQ names changed")
    handle = words(target.get("phandle", b""))
    if len(handle) != 1:
        errors.append("TSENS provider phandle missing or duplicate")
    resolved_zones = {}
    for zone, ident in CPU_ZONES.items():
        zp = "/thermal-zones/" + zone
        prop = nodes.get(zp, {})
        link = words(prop.get("thermal-sensors", b""))
        if link != (handle + [ident]):
            errors.append("thermal zone reference invalid: " + zone)
        for child, temperature in (("trip-point0", 80000), ("crit", 100000)):
            tp = nodes.get(zp + "/trips/" + child, {})
            if words(tp.get("temperature", b"")) != [temperature]:
                errors.append("CPU thermal trip value changed: " + zone + "/" + child)
            if words(tp.get("hysteresis", b"")) != [2000]:
                errors.append("CPU thermal hysteresis changed: " + zone + "/" + child)
        resolved_zones[zone] = {"phandle": link[0] if link else None,
                                "sensor_id": link[1] if len(link) > 1 else None}
    all_zones = {p.rsplit("/", 1)[-1] for p, props in nodes.items()
                 if p.startswith("/thermal-zones/") and p.count("/") == 2}
    if all_zones != set(CPU_ZONES):
        errors.append("CPU thermal zone count/identity changed")
    log_counts = Counter(x["node"] for x in parse_diagnostics(log.read_text(errors="replace")))
    if log_counts != KNOWN_NON_SPMI or log_counts["thermal-sensor@4a9000"] != 1:
        errors.append("global schema baseline changed or TYPE3 diagnostic concealed")
    if not set(CPU_ZONES.values()).issubset(STOCK_IDS_REPORTED):
        errors.append("CPU zone sensor outside documented C100 stock IDs")
    return {
        "dtb_sha256": digest, "board": board, "nodes": len(nodes),
        "tsens_provider_phandle": handle, "cpu_thermal_zones": resolved_zones,
        "schema_diagnostics": sum(log_counts.values()),
        "tsens_schema_diagnostic_still_present": log_counts["thermal-sensor@4a9000"] == 1,
        "stock_fdt_binary": "NOT_AVAILABLE",
        "thermal_sensor_runtime": "HOLD",
        "errors": errors, "gate": "PASS_HOST_ONLY" if not errors else "FAIL"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vendor-tsens", type=Path, required=True)
    p.add_argument("--kernel-root", type=Path, required=True)
    for name in ("pvt1", "pvt2"):
        p.add_argument("--" + name + "-dtb", type=Path, required=True)
        p.add_argument("--" + name + "-schema-log", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    source = check_donor_and_modern_sources(a.vendor_tsens, a.kernel_root)
    geometry = [sensor_registers(x) for x in STOCK_IDS_REPORTED]
    report = {
        "type": "TSENS TYPE3 register and thermal-zone source audit, NOT an enabled port",
        "base": {"stock_reported_sensor_ids": list(STOCK_IDS_REPORTED),
                 "candidate_sensor_count": 16, "stock_binary": "NOT_AVAILABLE"},
        "source": source, "sensor_geometry": geometry,
        "pvt1": audit_variant("pvt1", a.pvt1_dtb, a.pvt1_schema_log),
        "pvt2": audit_variant("pvt2", a.pvt2_dtb, a.pvt2_schema_log),
        "thermal_type3_functional_port": "HOLD",
        "stock_fdt_direct_comparison": "HOLD",
        "firmware_boot_flash_merge": "HOLD",
    }
    report["result"] = "PASS_HOST_SOURCE_CONTRACT_ONLY" if (
        not source["problems"] and len(source["paired_registers"]) == len(REGISTER_PAIRS)
        and all(report[x]["gate"] == "PASS_HOST_ONLY" for x in ("pvt1", "pvt2"))
    ) else "FAIL"
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["result"], "register pairs:", len(source["paired_registers"]))
    for x in ("pvt1", "pvt2"):
        print(x, "zones:", len(report[x]["cpu_thermal_zones"]),
              "remaining errors:", report[x]["schema_diagnostics"],
              "TSENS:", report[x]["thermal_sensor_runtime"])
        for e in report[x]["errors"]:
            print(x, "ERROR:", e, file=sys.stderr)
    for e in source["problems"]:
        print("SOURCE ERROR:", e, file=sys.stderr)
    return 0 if report["result"] == "PASS_HOST_SOURCE_CONTRACT_ONLY" else 3


if __name__ == "__main__":
    sys.exit(main())
