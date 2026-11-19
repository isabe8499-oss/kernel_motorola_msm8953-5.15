#!/usr/bin/env python3
"""Host-only C100/PVT1 vs C200/PVT2 structural SMEM/RPM/firmware contract audit.

Requires deen_fdt_memory_ledger.py next to this script. Reads compiled DTB and
optionally the exact checked-out kernel driver sources. Reports, but does not
change, a missing driver OF match; never asserts firmware/boot compatibility.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from deen_fdt_memory_ledger import decode_reg, parse_fdt, resolve_cells, strings, words


MATCH_CHECKS = (
    ("rpm_transport", "/smd/rpm/rpm-requests", "qcom,rpm-msm8953", "drivers/soc/qcom/smd-rpm.c"),
    ("rpm_clocks", "/smd/rpm/rpm-requests/rpmcc", "qcom,rpmcc-msm8953", "drivers/clk/qcom/clk-smd-rpm.c"),
    ("rpm_power_domains", "/smd/rpm/rpm-requests/power-controller", "qcom,msm8953-rpmpd", "drivers/soc/qcom/rpmpd.c"),
    ("pm8953_regulators", "/smd/rpm/rpm-requests/regulators", "qcom,rpm-pm8953-regulators", "drivers/regulator/qcom_smd-regulator.c"),
)

EXPECTED_SPANS = {
    "/reserved-memory/memory@86300000": (0x86300000, 0x100000),
    "/reserved-memory/qseecom@84300000": (0x84300000, 0x2000000),
    "/reserved-memory/memory@86400000": (0x86400000, 0x400000),
    "/reserved-memory/memory@86c00000": (0x86c00000, 0x6A00000),
    "/reserved-memory/memory@8d600000": (0x8D600000, 0x1100000),
    "/reserved-memory/memory@8e700000": (0x8E700000, 0x700000),
}

FW_GROUPS = {
    "MPSS": {"qcom,msm8953-mss-pil", "qcom,pil-q6v55-mss"},
    "ADSP": {"qcom,msm8953-adsp-pil"},
    "WCNSS": {"qcom,pronto-v3-pil"},
}


def one_word(props, name):
    data = words(props.get(name, b""))
    return data[0] if data and len(data) == 1 else None


def phandles(nodes):
    result = {}
    for path, props in nodes.items():
        n = one_word(props, "phandle")
        if n is not None:
            if n in result and result[n] != path:
                raise ValueError(f"duplicate phandle {n}: {path} and {result[n]}")
            result[n] = path
    return result


def record_ref(props, name, by_handle):
    arr = words(props.get(name, b""))
    if not arr or len(arr) == 0:
        return {"value": None, "provider": None}
    return {"value": arr, "provider": by_handle.get(arr[0])}


def reg_for(nodes, path):
    if path not in nodes:
        return []
    parent = path.rsplit("/", 1)[0] or "/"
    cells = resolve_cells(nodes, parent)
    return decode_reg(nodes[path], *cells) if cells else []


def check_driver(root, relative_path, compatible):
    if root is None:
        return {"status": "NOT_CHECKED", "compatible": compatible, "source": relative_path}
    path = root / relative_path
    if not path.is_file():
        return {"status": "SOURCE_MISSING", "compatible": compatible, "source": relative_path}
    raw = path.read_bytes()
    source = raw.decode("utf-8", "replace")
    pat = r'\.compatible\s*=\s*"' + re.escape(compatible) + r'"'
    matches = [source.count("\n", 0, m.start()) + 1 for m in re.finditer(pat, source)]
    return {"status": "OF_MATCH_PRESENT" if matches else "OF_MATCH_ABSENT",
            "compatible": compatible, "source": relative_path,
            "source_sha256": hashlib.sha256(raw).hexdigest(), "matching_lines": matches}


def inspect(path, expected_board, source_root):
    raw = path.read_bytes()
    nodes, _memreserve = parse_fdt(raw)
    refmap = phandles(nodes)
    errors = []
    warn = []
    root = nodes.get("/", {})
    identity = words(root.get("qcom,board-id", b""))
    if identity != [0x4D, expected_board]:
        errors.append(f"board-id differs from expected 0x4d,0x{expected_board:x}: {identity}")
    if expected_board == 0xC100 and words(root.get("qcom,msm-id", b"")) != [0x125, 0]:
        errors.append("C100 qcom,msm-id missing/mismatched")
    smem = nodes.get("/smem", {})
    if strings(smem.get("compatible", b"")) != ["qcom,smem"]:
        errors.append("/smem compatible not qcom,smem")
    main = record_ref(smem, "memory-region", refmap)
    rpm = record_ref(smem, "qcom,rpm-msg-ram", refmap)
    lock = record_ref(smem, "hwlocks", refmap)
    if main["provider"] != "/reserved-memory/memory@86300000":
        errors.append("SMEM memory-region provider mismatch")
    if rpm["provider"] != "/soc@0/sram@60000":
        errors.append("SMEM RPM msg RAM provider mismatch")
    if (lock["provider"] != "/soc@0/hwlock@1905000" or
            not lock["value"] or len(lock["value"]) != 2 or lock["value"][1] != 3):
        errors.append("SMEM hwlocks phandle/index mismatch")
    for node, (expected_start, expected_size) in EXPECTED_SPANS.items():
        entries = reg_for(nodes, node)
        if len(entries) != 1 or (entries[0]["start"], entries[0]["size"]) != (expected_start, expected_size):
            errors.append(f"expected reservation differs: {node}")
    rpmreg = reg_for(nodes, "/soc@0/sram@60000")
    if len(rpmreg) != 1 or (rpmreg[0]["start"], rpmreg[0]["size"]) != (0x60000, 0x8000):
        errors.append("RPM message SRAM reg differs from candidate baseline")

    parts = []
    for name, node, compatible, source_path in MATCH_CHECKS:
        props = nodes.get(node, {})
        present = compatible in strings(props.get("compatible", b""))
        if not present:
            errors.append(f"required candidate RPM node/compatible missing: {node} {compatible}")
        parts.append({"name": name, "device_node": node,
                      "candidate_compatible_present": present,
                      "driver": check_driver(source_root, source_path, compatible)})
    gap = [p["name"] for p in parts if p["candidate_compatible_present"] and p["driver"]["status"] == "OF_MATCH_ABSENT"]
    if gap:
        warn.append("OF driver match gap(s) pending bus/probe-path review: " + ", ".join(gap))

    remote = {}
    for subsystem, compat_set in FW_GROUPS.items():
        exact = [p for p, v in nodes.items() if compat_set.intersection(strings(v.get("compatible", b"")))]
        remote[subsystem] = {"potential_nodes": exact, "vendor_firmware_hashes_verified": False}
        for p in exact:
            if strings(nodes[p].get("status", b"")) not in (["disabled"],):
                errors.append(f"unexpected active/present remoteproc compatible in candidate: {subsystem} {p}")
    other_ipc = {"modem": [], "adsp": [], "wcnss": []}
    for node_path, props in nodes.items():
        if "qcom,smp2p" in strings(props.get("compatible", b"")):
            if "modem" in node_path:
                other_ipc["modem"].append(node_path)
            if "adsp" in node_path:
                other_ipc["adsp"].append(node_path)
            if "wcnss" in node_path:
                other_ipc["wcnss"].append(node_path)
    if any(other_ipc.values()):
        warn.append("SMP2P endpoints exist; compare donor board-disabled overrides before activation")
    ipc = nodes.get("/smd/rpm", {})
    ipc_cells = words(ipc.get("qcom,ipc", b""))
    apcs = refmap.get(ipc_cells[0]) if ipc_cells else None
    if len(ipc_cells or []) != 3 or apcs != "/soc@0/mailbox@b011000":
        errors.append("RPM qcom,ipc tuple/provider mismatch")
    if one_word(ipc, "qcom,smd-edge") != 15:
        errors.append("RPM SMD edge not 15")

    fixed = []
    for p in nodes:
        if p.startswith("/reserved-memory/") and p.count("/") == 2:
            fixed.extend([{**reg, "path": p} for reg in reg_for(nodes, p) if reg["size"]])
    overlap = []
    for i, a in enumerate(fixed):
        for b in fixed[i+1:]:
            if a["start"] < b["end_exclusive"] and b["start"] < a["end_exclusive"]:
                overlap.append([a["path"], b["path"]])
    if overlap:
        errors.append(f"overlapping reserved memory intervals: {overlap}")
    return {
        "input": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
        "fdt_node_count": len(nodes), "board_id": identity,
        "smem": {"region_ref": main, "rpm_msg_ram_ref": rpm, "hwlocks_ref": lock,
                 "region": reg_for(nodes, "/reserved-memory/memory@86300000"),
                 "rpm_msg_ram_reg": rpmreg},
        "rpm": {"smd_edge": one_word(ipc, "qcom,smd-edge"), "ipc_cells": ipc_cells,
                "ipc_provider": apcs, "driver_compatibility": parts,
                "driver_match_gaps": gap},
        "firmware": {"remoteproc": remote, "smp2p_nodes": other_ipc,
                     "firmware_blobs_in_supplied_package": False,
                     "donor_contract_verified_on_stock": False},
        "memory": {"fixed_reserved_count": len(fixed), "overlap": overlap,
                   "other_ext_split_numerical_only": True},
        "errors": errors, "warnings": warn,
        "gate_structural": "FAIL" if errors else "PASS_SCOPE_LIMITED",
        "gate_ipc_firmware_runtime": "HOLD",
        "gate_full_schema": "REVIEW_REQUIRED",
        "gate_flash_merge": "NOT_AUTHORIZED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pvt1", type=Path)
    parser.add_argument("pvt2", type=Path)
    parser.add_argument("--kernel-root", type=Path,
                        help="checked-out source tree for exact RPM OF match-table checks")
    args = parser.parse_args()
    try:
        result = {
            "scope": "host-only static C100/PVT1 and C200/PVT2 IPC contract audit",
            "pvt1": inspect(args.pvt1, 0xC100, args.kernel_root),
            "pvt2": inspect(args.pvt2, 0xC200, args.kernel_root),
        }
        result["overall"] = ("FAIL" if any(result[p]["errors"] for p in ("pvt1", "pvt2"))
                             else "PASS_STATIC_WITH_BLOCKERS")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 3 if result["overall"] == "FAIL" else 0
    except (OSError, ValueError, IndexError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())