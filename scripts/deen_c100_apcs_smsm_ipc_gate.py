#!/usr/bin/env python3
"""Host-only Deen C100/PVT1 and C200/PVT2 APCS/SMSM/SMD IPC audit.

The qcom,ipc triples below are a syscon phandle, register offset and bit
index, NOT a 3-cell mailbox specifier. This tool never sends an interrupt,
starts firmware or decides that the device is safe to boot.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from deen_fdt_memory_ledger import decode_reg, parse_fdt, resolve_cells, strings, words
from deen_c100_ipc_contract_audit import phandles
from deen_c100_spmi_schema_gate import KNOWN_NON_SPMI, parse_diagnostics
from deen_gki_smem_rpm_config_gate import HOST_ONLY, MINIMAL, NO_NEW_ENABLEMENT, fragment_symbols, read_config

APCS = "/soc@0/mailbox@b011000"
LOCK = "/soc@0/hwlock@1905000"
SMD = "/smd/rpm"
SMSM = "/smsm"
SMEM = "/smem"
EXPECTED_IPC = {"smd-rpm": (SMD, "qcom,ipc", 8, 0),
                "smsm-host1": (SMSM, "qcom,ipc-1", 8, 13),
                "smsm-host3": (SMSM, "qcom,ipc-3", 8, 19)}
DTB_SHA = {
    "pvt1": "fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a",
    "pvt2": "9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05",
}
NEW = ("QCOM_APCS_IPC", "QCOM_SMSM")


def must_have(nodes, path, name, expected, errors):
    got = words(nodes.get(path, {}).get(name, b""))
    if got != expected:
        errors.append(f"{path}:{name} expected {expected}, got {got}")
    return got


def one_reg(nodes, path):
    parent = path.rsplit("/", 1)[0] or "/"
    cells = resolve_cells(nodes, parent)
    return decode_reg(nodes.get(path, {}), *cells) if cells else []


def inspect_nodes(nodes, board):
    errors, endpoints = [], {}
    root_board = [0x4d, 0xc100 if board == "pvt1" else 0xc200]
    must_have(nodes, "/", "qcom,board-id", root_board, errors)
    maps = phandles(nodes)

    apcs = nodes.get(APCS, {})
    if strings(apcs.get("compatible", b"")) != ["qcom,msm8953-apcs-kpss-global", "syscon"]:
        errors.append("APCS syscon compatible changed")
    must_have(nodes, APCS, "#mbox-cells", [1], errors)
    regs = one_reg(nodes, APCS)
    if [(x["start"], x["size"]) for x in regs] != [(0x0b011000, 0x1000)]:
        errors.append("APCS MMIO window changed")
    apcs_handle = words(apcs.get("phandle", b""))
    if len(apcs_handle or []) != 1 or maps.get(apcs_handle[0]) != APCS:
        errors.append("APCS provider phandle absent/ambiguous")
    if not apcs_handle or len(apcs_handle) != 1:
        return errors + ["cannot resolve IPC phandle"], endpoints

    for label, (path, key, offset, bit) in EXPECTED_IPC.items():
        got = must_have(nodes, path, key, [apcs_handle[0], offset, bit], errors)
        provider = maps.get(got[0]) if got else None
        if provider != APCS:
            errors.append(f"{label} IPC provider must resolve to APCS syscon")
        if got and len(got) == 3 and (got[1] % 4 or got[1] + 4 > 0x1000 or got[2] >= 32):
            errors.append(f"{label} invalid regmap IPC offset or bit")
        endpoints[label] = {"provider": provider, "cells": got,
                            "protocol": "legacy-syscon-offset-bit (not mailbox cells)"}

    if strings(nodes.get("/smd", {}).get("compatible", b"")) != ["qcom,smd"]:
        errors.append("SMD parent compatible changed")
    must_have(nodes, SMD, "qcom,smd-edge", [15], errors)
    must_have(nodes, SMD, "interrupts", [0, 168, 1], errors)
    if "mboxes" in nodes.get(SMD, {}):
        errors.append("SMD unexpectedly switched from legacy qcom,ipc to mboxes")
    if strings(nodes.get("/smd/rpm/rpm-requests", {}).get("compatible", b"")) != ["qcom,rpm-msm8953"]:
        errors.append("RPM child compatible changed")

    if strings(nodes.get(SMSM, {}).get("compatible", b"")) != ["qcom,smsm"]:
        errors.append("SMSM compatible changed")
    must_have(nodes, "/smsm/apps@0", "reg", [0], errors)
    must_have(nodes, "/smsm/apps@0", "#qcom,smem-state-cells", [1], errors)
    if "interrupt-controller" in nodes.get("/smsm/apps@0", {}):
        errors.append("apps SMSM state incorrectly converted into remote interrupt controller")
    smem = nodes.get(SMEM, {})
    if strings(smem.get("compatible", b"")) != ["qcom,smem"]:
        errors.append("SMEM platform device missing")
    for key, target, extra in (
        ("memory-region", "/reserved-memory/memory@86300000", []),
        ("qcom,rpm-msg-ram", "/soc@0/sram@60000", []),
        ("hwlocks", LOCK, [3]),
    ):
        got = words(smem.get(key, b""))
        provider = maps.get(got[0]) if got else None
        if provider != target or not got or got[1:] != extra:
            errors.append(f"SMEM {key} provider/index changed")
    if strings(nodes.get(LOCK, {}).get("compatible", b"")) != ["qcom,tcsr-mutex"]:
        errors.append("TCSR hwlock OF compatible changed")
    must_have(nodes, LOCK, "#hwlock-cells", [1], errors)
    return errors, endpoints


def source_audit(root):
    failures = []
    files = {
        "smd": "drivers/rpmsg/qcom_smd.c",
        "smsm": "drivers/soc/qcom/smsm.c",
        "apcs": "drivers/mailbox/qcom-apcs-ipc-mailbox.c",
        "hwspin": "drivers/hwspinlock/qcom_hwspinlock.c",
        "rpm": "drivers/soc/qcom/smd-rpm.c",
        "mbox_kconfig": "drivers/mailbox/Kconfig",
        "soc_kconfig": "drivers/soc/qcom/Kconfig",
    }
    sources = {k: (root / f).read_text(encoding="utf-8") for k, f in files.items()}
    expected = {
        "smd": ['.compatible = "qcom,smd"', 'mbox_request_channel(&edge->mbox_client, 0)',
                'of_parse_phandle(node, "qcom,ipc", 0)',
                'syscon_node_to_regmap(syscon_np)',
                'of_property_read_u32_index(node, key, 1, &edge->ipc_offset)',
                'of_property_read_u32_index(node, key, 2, &edge->ipc_bit)',
                'irq_of_parse_and_map(node, 0)'],
        "smsm": ['.compatible = "qcom,smsm"', 'snprintf(key, sizeof(key), "qcom,ipc-%d", host_id)',
                 'syscon_node_to_regmap(syscon)', 'of_property_read_u32_index(node, key, 1, &host->ipc_offset)',
                 'of_property_read_u32_index(node, key, 2, &host->ipc_bit)',
                 'SMEM_SMSM_SIZE_INFO', 'SMEM_SMSM_SHARED_STATE', 'SMEM_SMSM_CPU_INTR_MASK'],
        "apcs": ['.compatible = "qcom,msm8953-apcs-kpss-global", .data = &msm8994_apcs_data',
                 'static const struct qcom_apcs_ipc_data msm8994_apcs_data',
                 '.offset = 8, .clk_name = NULL',
                 'devm_mbox_controller_register', 'regmap_write(apcs->regmap, apcs->offset, BIT(idx))'],
        "hwspin": ['.compatible = "qcom,tcsr-mutex"'],
        "rpm": ['.compatible = "qcom,rpm-msm8953"'],
        "mbox_kconfig": ['config QCOM_APCS_IPC'],
        "soc_kconfig": ['config QCOM_SMSM', 'depends on QCOM_SMEM',
                        'select QCOM_SMEM_STATE'],
    }
    for name, terms in expected.items():
        for term in terms:
            if term not in sources[name]:
                failures.append(f"driver/source contract disappeared: {name}: {term}")
    # The current DTB uses the legacy syscon IPC path. Do not claim the
    # APCS mailbox platform device is necessary for qcom,ipc to be delivered.
    return {"sources": files, "source_sha256": {
        k: hashlib.sha256(sources[k].encode()).hexdigest() for k in files
    }, "mode": "SMD and SMSM legacy syscon regmap; APCS mailbox optional/unproven",
        "errors": failures}


def config_audit(base_file, after_file, fragment):
    before = read_config(base_file)
    after = read_config(after_file)
    errors = []
    if fragment_symbols(fragment) != set(NEW):
        errors.append("host-only APCS/SMSM fragment must contain exactly two built-in symbols")
    for k in MINIMAL + HOST_ONLY:
        if before.get(k) != "y" or after.get(k) != "y":
            errors.append(f"Deen20/host5 dependency not built in: {k}")
    for k in NEW:
        if before.get(k, "n") != "n" or after.get(k, "n") != "y":
            errors.append(f"new APCS/SMSM symbol not exclusively enabled by this fragment: {k}")
    delta = {k: {"before": before.get(k, "n"), "after": after.get(k, "n")}
             for k in sorted(set(before) | set(after))
             if before.get(k, "n") != after.get(k, "n")}
    if set(delta) != set(NEW):
        errors.append(f"unexpected Kconfig changes outside APCS/SMSM: {sorted(delta)}")
    for name in NO_NEW_ENABLEMENT:
        # The PR #13 guard bans SMSM, appropriately for its host5 scope.
        # This stage explicitly permits only the two exact delta keys in NEW;
        # all other originally forbidden subsystems remain blocked.
        if name in NEW:
            continue
        if before.get(name, "n") not in ("y", "m") and after.get(name, "n") in ("y", "m"):
            errors.append(f"forbidden new subsystem enablement: {name}")
    for name in ("LTO_CLANG_FULL", "CFI_CLANG"):
        if before.get(name) != "y" or after.get(name) != "y":
            errors.append(f"required GKI toolchain setting not preserved: {name}")
    if before.get("QCOM_SMEM_STATE") != "y" or after.get("QCOM_SMEM_STATE") != "y":
        errors.append("QCOM_SMEM_STATE unexpectedly absent")
    return {"delta": delta, "expected_new": list(NEW),
            "old_smem_state": before.get("QCOM_SMEM_STATE"),
            "new_smem_state": after.get("QCOM_SMEM_STATE"),
            "errors": errors, "scope_gate": "PASS_HOST_CONFIG_ONLY" if not errors else "FAIL"}


def dtb_audit(path, board, log):
    raw = path.read_bytes()
    nodes, _ = parse_fdt(raw)
    errors, endpoints = inspect_nodes(nodes, board)
    sha = hashlib.sha256(raw).hexdigest()
    if sha != DTB_SHA[board]:
        errors.append("candidate DTB hash changed from PR #13")
    counts = Counter(item["node"] for item in parse_diagnostics(
        log.read_text(encoding="utf-8", errors="replace")))
    if counts != KNOWN_NON_SPMI:
        errors.append(f"schema baseline changed: {dict(counts)}")
    return {"sha256": sha, "board": board, "node_count": len(nodes),
            "endpoints": endpoints, "diagnostics_by_node": dict(sorted(counts.items())),
            "diagnostics_total": sum(counts.values()),
            "firmware_rpm_ipc_runtime": "HOLD",
            "stock_fdt_direct_comparison": "HOLD",
            "errors": errors, "scope_gate": "PASS_DTB_STRUCTURE_ONLY" if not errors else "FAIL"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kernel-root", required=True, type=Path)
    p.add_argument("--host5-config", required=True, type=Path)
    p.add_argument("--host7-config", required=True, type=Path)
    p.add_argument("--fragment", required=True, type=Path)
    for board in ("pvt1", "pvt2"):
        p.add_argument(f"--{board}-dtb", required=True, type=Path)
        p.add_argument(f"--{board}-schema-log", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    result = {
        "config": config_audit(a.host5_config, a.host7_config, a.fragment),
        "source": source_audit(a.kernel_root),
        "pvt1": dtb_audit(a.pvt1_dtb, "pvt1", a.pvt1_schema_log),
        "pvt2": dtb_audit(a.pvt2_dtb, "pvt2", a.pvt2_schema_log),
        "firmware_remoteproc": "HOLD",
        "smem_ipc_rpm_runtime": "HOLD",
        "global_schema": "REVIEW_REQUIRED",
        "full_kernel_boot_flash_merge": "HOLD",
    }
    result["overall"] = "PASS_HOST_ONLY_WITH_RUNTIME_HOLD" if (
        result["config"]["scope_gate"] == "PASS_HOST_CONFIG_ONLY"
        and not result["source"]["errors"]
        and all(result[k]["scope_gate"] == "PASS_DTB_STRUCTURE_ONLY"
                for k in ("pvt1", "pvt2"))
    ) else "FAIL"
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(result["overall"])
    print("APCS/SMSM Kconfig delta:", result["config"]["delta"])
    for board in ("pvt1", "pvt2"):
        print(board, "IPC endpoints:", result[board]["endpoints"],
              "schema diagnostics:", result[board]["diagnostics_total"])
    for e in result["config"]["errors"] + result["source"]["errors"] + \
             result["pvt1"]["errors"] + result["pvt2"]["errors"]:
        print("ERROR:", e, file=sys.stderr)
    return 0 if result["overall"] == "PASS_HOST_ONLY_WITH_RUNTIME_HOLD" else 3


if __name__ == "__main__":
    sys.exit(main())
