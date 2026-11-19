#!/usr/bin/env python3
"""Host-only gate for Deen C100/C200 RPM SMD and RPMPD DTB schema repairs.

This gate covers ONLY two known RPM schema diagnostics. It deliberately
retains, reports and fingerprints all other known schema diagnostics.
It never asserts that the kernel boots, SMEM works or firmware is compatible.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

from deen_fdt_memory_ledger import parse_fdt, strings, words


RPM_NODE = "/smd/rpm/rpm-requests"
POWER_NODE = RPM_NODE + "/power-controller"
CLOCK_NODE = RPM_NODE + "/rpmcc"
REG_NODE = RPM_NODE + "/regulators"
EXPECTED_CHILDREN = {"power-controller", "rpmcc", "regulators"}

# Exact node multiplicities in the user's original 2026-11-19 PVT1/PVT2
# pinned dtschema=2024.2 logs, excluding the two targeted RPM diagnostics.
# The rest remain REVIEW_REQUIRED, not magically resolved.
KNOWN_NON_RPM = Counter({
    "/": 1,
    "thermal-sensor@4a9000": 1,
    "clock-controller@1800000": 1,
    "spmi@200f000": 1,
    "rtc@6000": 2,
    "usb@70f8800": 5,
    "mailbox@b011000": 1,
})
DIAGNOSTIC_RE = re.compile(r"\.dtb:\s+([^:]+):\s+(.+)$")


def diagnostics(text):
    """Read top-level dt-validate diagnostic lines, excluding continuations."""
    result = []
    for line in text.splitlines():
        match = DIAGNOSTIC_RE.search(line)
        if match:
            result.append({"node": match.group(1), "message": match.group(2)})
    return result


def audit_variant(dtb_path, log_path, board_id):
    problems = []
    nodes, _ = parse_fdt(dtb_path.read_bytes())
    root = nodes.get("/", {})
    identity = words(root.get("qcom,board-id", b""))
    if identity != [0x4D, board_id]:
        problems.append(f"wrong board ID: {identity} != [77, {board_id}]")
    rpm_node = nodes.get(RPM_NODE, {})
    if strings(rpm_node.get("compatible", b"")) != ["qcom,rpm-msm8953"]:
        problems.append("RPM SMD compatible missing or changed")
    if strings(rpm_node.get("qcom,smd-channels", b"")) != ["rpm_requests"]:
        problems.append("RPM SMD channel name missing or changed")
    actual_children = {
        path[len(RPM_NODE) + 1:] for path in nodes
        if path.startswith(RPM_NODE + "/")
        and "/" not in path[len(RPM_NODE) + 1:]
    }
    if actual_children != EXPECTED_CHILDREN:
        problems.append(f"RPM child nodes changed: {sorted(actual_children)}")
    pd = nodes.get(POWER_NODE, {})
    if strings(pd.get("compatible", b"")) != ["qcom,msm8953-rpmpd"]:
        problems.append("RPMPD compatible missing or changed")
    if "clocks" in pd or "clock-names" in pd:
        problems.append("RPMPD inherited unused clock properties remain")
    if words(pd.get("#power-domain-cells", b"")) != [1]:
        problems.append("RPMPD #power-domain-cells changed")
    if not words(pd.get("operating-points-v2", b"")):
        problems.append("RPMPD operating-points-v2 removed")
    if RPM_NODE + "/power-controller/opp-table" not in nodes:
        problems.append("RPMPD OPP table removed")
    clock = nodes.get(CLOCK_NODE, {})
    if "qcom,rpmcc-msm8953" not in strings(clock.get("compatible", b"")):
        problems.append("RPM clock child compatible missing")
    if "clocks" not in clock or strings(clock.get("clock-names", b"")) != ["xo"]:
        problems.append("RPMCC clock properties unexpectedly removed")
    if "qcom,rpm-pm8953-regulators" not in strings(
            nodes.get(REG_NODE, {}).get("compatible", b"")):
        problems.append("PM8953 regulator child compatible missing")

    log = log_path.read_text(encoding="utf-8", errors="replace")
    diag = diagnostics(log)
    count = Counter(item["node"] for item in diag)
    if not diag:
        problems.append("no DTB schema diagnostics collected; cannot verify gate")
    if count.get("rpm-requests", 0):
        problems.append("RPM parent schema diagnostic persists")
    if count.get("power-controller", 0):
        problems.append("RPMPD schema diagnostic persists")
    if count != KNOWN_NON_RPM:
        problems.append(
            f"non-target baseline changed: observed={dict(count)}, "
            f"expected={dict(KNOWN_NON_RPM)}")
    return {
        "dtb": str(dtb_path), "schema_log": str(log_path),
        "board_id": f"0x{board_id:x}", "diagnostics_total": len(diag),
        "diagnostics_by_node": dict(sorted(count.items())),
        "expected_remaining_diagnostics": sum(KNOWN_NON_RPM.values()),
        "rpm_parent_diagnostic_removed": count.get("rpm-requests", 0) == 0,
        "rpmpd_diagnostic_removed": count.get("power-controller", 0) == 0,
        "other_schema_diagnostics_still_review_required": True,
        "runtime_smem_rpm_firmware_boot": "HOLD",
        "problems": problems,
        "scope_gate": "PASS_RPM_SCHEMA_ONLY" if not problems else "FAIL",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pvt1-dtb", type=Path, required=True)
    p.add_argument("--pvt2-dtb", type=Path, required=True)
    p.add_argument("--pvt1-schema-log", type=Path, required=True)
    p.add_argument("--pvt2-schema-log", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = {
        "scope": "Deen RPM-only DTB schema repair; NOT a full DTB pass",
        "pvt1": audit_variant(a.pvt1_dtb, a.pvt1_schema_log, 0xC100),
        "pvt2": audit_variant(a.pvt2_dtb, a.pvt2_schema_log, 0xC200),
    }
    result["overall"] = ("PASS_RPM_SCHEMA_ONLY" if all(
        result[k]["scope_gate"] == "PASS_RPM_SCHEMA_ONLY"
        for k in ("pvt1", "pvt2")) else "FAIL")
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("RPM targeted schema gate:", result["overall"])
    for k in ("pvt1", "pvt2"):
        print(k, "diagnostics:", result[k]["diagnostics_total"],
              "gate:", result[k]["scope_gate"],
              "runtime:", result[k]["runtime_smem_rpm_firmware_boot"])
        for problem in result[k]["problems"]:
            print("  -", problem, file=sys.stderr)
    return 0 if result["overall"] == "PASS_RPM_SCHEMA_ONLY" else 3


if __name__ == "__main__":
    sys.exit(main())
