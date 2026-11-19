#!/usr/bin/env python3
"""Host-only SPMI schema scope regression gate for Deen C100/C200.

Verifies that ONLY the existing generic SPMI maxItems=1 false positive was
resolved for Qualcomm PMIC arbiter. Preserves all other DTB diagnostics and
ensures DTBs are byte-identical to the validated PR #6 artifacts. No firmware.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from deen_fdt_memory_ledger import parse_fdt, strings, words, resolve_cells, decode_reg

SPMI_PATH = "/soc@0/spmi@200f000"
EXPECTED_REG = [
    (0x0200F000, 0x1000),
    (0x02400000, 0x800000),
    (0x02C00000, 0x800000),
    (0x03800000, 0x200000),
    (0x0200A000, 0x2100),
]
EXPECTED_NAMES = ["core", "chnls", "obsrvr", "intr", "cnfg"]
KNOWN_NON_SPMI = Counter({
    "/": 1,
    "thermal-sensor@4a9000": 1,
    "clock-controller@1800000": 1,
    "rtc@6000": 2,
    "usb@70f8800": 5,
    "mailbox@b011000": 1,
})
EXPECTED_SHA = {
    "pvt1": "fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a",
    "pvt2": "9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05",
}
RE_DIAG = re.compile(r"\.dtb:\s+([^:]+):\s+(.+)$")


def parse_diagnostics(log):
    return [
        {"node": match.group(1), "message": match.group(2)}
        for line in log.splitlines()
        if (match := RE_DIAG.search(line))
    ]


def inspect(name, dtb_path, log_path, board_id):
    errors = []
    data = dtb_path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXPECTED_SHA[name]:
        errors.append("DTB binary differs from validated PR#6 baseline")
    nodes, memreserve = parse_fdt(data)
    if words(nodes.get("/", {}).get("qcom,board-id", b"")) != [0x4D, board_id]:
        errors.append("unexpected board ID")
    prop = nodes.get(SPMI_PATH, {})
    if strings(prop.get("compatible", b"")) != ["qcom,spmi-pmic-arb"]:
        errors.append("SPMI compatible changed")
    if strings(prop.get("reg-names", b"")) != EXPECTED_NAMES:
        errors.append("SPMI reg-names/order changed")
    addr_size = resolve_cells(nodes, "/soc@0")
    regs = decode_reg(prop, *addr_size)
    tuples = [(x["start"], x["size"]) for x in regs]
    if tuples != EXPECTED_REG:
        errors.append(f"SPMI physical register windows changed: {tuples}")
    if words(prop.get("qcom,ee", b"")) != [0] or words(prop.get("qcom,channel", b"")) != [0]:
        errors.append("SPMI execution environment/channel changed")
    if strings(nodes.get("/soc@0/thermal-sensor@4a9000", {}).get("compatible", b"")) != [
        "qcom,msm8953-tsens", "qcom,tsens-v2"]:
        errors.append("TSENS candidate compatible unexpectedly changed")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    diag = parse_diagnostics(log)
    count = Counter(x["node"] for x in diag)
    if count != KNOWN_NON_SPMI:
        errors.append(f"non-target diagnostic baseline altered: {dict(count)}")
    if count.get("spmi@200f000", 0):
        errors.append("SPMI schema diagnostic still present")
    if not diag:
        errors.append("missing full schema log")
    return {
        "board": name, "board_id": f"0x{board_id:x}",
        "dtb_sha256": sha, "nodes": len(nodes),
        "memreserve_count": len(memreserve),
        "spmi_ranges": [{"start": f"0x{s:x}", "size": f"0x{n:x}"} for s,n in tuples],
        "schema_diagnostics": len(diag), "diagnostics_by_node": dict(sorted(count.items())),
        "tsens_runtime": "HOLD_TYPE3_NOT_PORTED",
        "stock_spmi_exact_binary": "NOT_AVAILABLE_IN_SUPPLIED_ZIP",
        "overall_runtime_and_flash": "HOLD",
        "errors": errors,
        "scope_gate": "PASS_SPMI_SCHEMA_ONLY" if not errors else "FAIL",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pvt1-dtb", type=Path, required=True)
    p.add_argument("--pvt2-dtb", type=Path, required=True)
    p.add_argument("--pvt1-log", type=Path, required=True)
    p.add_argument("--pvt2-log", type=Path, required=True)
    p.add_argument("--generic-invalid-log", type=Path, required=True)
    p.add_argument("--generic-valid-log", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    doc = {
        "pvt1": inspect("pvt1", a.pvt1_dtb, a.pvt1_log, 0xC100),
        "pvt2": inspect("pvt2", a.pvt2_dtb, a.pvt2_log, 0xC200),
    }
    bad = parse_diagnostics(a.generic_invalid_log.read_text(errors="replace"))
    ok = parse_diagnostics(a.generic_valid_log.read_text(errors="replace"))
    generic_errors = []
    if not any(x["node"] == "spmi@1000" and "reg" in x["message"] for x in bad):
        generic_errors.append("generic SPMI two-window negative fixture was not rejected")
    if any(x["node"] == "spmi@1000" for x in ok):
        generic_errors.append("generic SPMI one-window control was rejected")
    doc["generic_spmi_control"] = {"negative_diag": bad, "positive_diag": ok, "errors": generic_errors}
    doc["overall"] = "PASS_SPMI_SCHEMA_ONLY" if (
        not generic_errors and all(doc[x]["scope_gate"] == "PASS_SPMI_SCHEMA_ONLY"
                                   for x in ("pvt1", "pvt2"))
    ) else "FAIL"
    a.output.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SPMI scoped gate:", doc["overall"])
    for board in ("pvt1", "pvt2"):
        x = doc[board]
        print(board, "schema diagnostics:", x["schema_diagnostics"],
              "scope:", x["scope_gate"], "TSENS:", x["tsens_runtime"])
        for err in x["errors"]:
            print(board, "ERROR:", err, file=sys.stderr)
    for err in generic_errors:
        print("generic SPMI ERROR:", err, file=sys.stderr)
    return 0 if doc["overall"].startswith("PASS") else 3


if __name__ == "__main__":
    sys.exit(main())
