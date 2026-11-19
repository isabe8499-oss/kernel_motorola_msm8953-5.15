#!/usr/bin/env python3
"""No-APCS-mailbox candidate test: Deen SMD/SMSM legacy syscon IPC.

Checks host-only Kconfig and *candidate* DTBs. Does not validate stock C100,
SMEM initialization, RPM ACK, mailbox delivery, firmware, boot or flashing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from deen_fdt_memory_ledger import parse_fdt, strings, words
from deen_c100_ipc_contract_audit import phandles
from deen_gki_smem_rpm_config_gate import (
    MINIMAL, HOST_ONLY, NO_NEW_ENABLEMENT, read_config, fragment_symbols,
)

EXPECTED_SHA = {
    "pvt1": "fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a",
    "pvt2": "9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05",
}
APCS_PATH = "/soc@0/mailbox@b011000"
EXPECTED_IPC = {
    ("/smd/rpm", "qcom,ipc"): (8, 0),
    ("/smsm", "qcom,ipc-1"): (8, 13),
    ("/smsm", "qcom,ipc-3"): (8, 19),
}
BLOCKED_NEW = set(NO_NEW_ENABLEMENT) - {"QCOM_SMSM"}


def config_gate(before_path, after_path, fragment_path):
    before = read_config(before_path)
    after = read_config(after_path)
    errors = []
    if fragment_symbols(fragment_path) != {"QCOM_SMSM"}:
        errors.append("only QCOM_SMSM allowed in host-only experiment")
    for sym in MINIMAL + HOST_ONLY:
        if before.get(sym) != "y" or after.get(sym) != "y":
            errors.append(f"previous base/host dependency not built in: {sym}")
    delta = {
        sym: [before.get(sym, "n"), after.get(sym, "n")]
        for sym in sorted(set(before) | set(after))
        if before.get(sym, "n") != after.get(sym, "n")
    }
    if delta != {"QCOM_SMSM": ["n", "y"]}:
        errors.append(f"Kconfig delta outside one SMSM symbol: {delta}")
    if before.get("QCOM_APCS_IPC", "n") != "n" or after.get("QCOM_APCS_IPC", "n") != "n":
        errors.append("APCS mailbox must remain disabled in both configurations")
    for sym in ("QCOM_SMEM_STATE", "LTO_CLANG_FULL", "CFI_CLANG"):
        if before.get(sym) != "y" or after.get(sym) != "y":
            errors.append(f"expected existing dependency/toolchain changed: {sym}")
    for sym in BLOCKED_NEW:
        if before.get(sym, "n") not in ("y", "m") and after.get(sym, "n") in ("y", "m"):
            errors.append(f"forbidden hardware/firmware enablement: {sym}")
    return {"delta": delta, "errors": errors,
            "scope": "host-only SMSM build without APCS mailbox"}


def inspect_candidate_nodes(nodes, board):
    errors = []
    ph = phandles(nodes)
    provider = nodes.get(APCS_PATH, {})
    compat = strings(provider.get("compatible", b""))
    if compat != ["qcom,msm8953-apcs-kpss-global", "syscon"]:
        errors.append(f"unexpected APCS syscon compatible: {compat}")
    if words(provider.get("reg", b"")) != [0x0b011000, 0x1000]:
        errors.append("APCS reg address/range changed")
    for (node, key), (offset, bit) in EXPECTED_IPC.items():
        cells = words(nodes.get(node, {}).get(key, b""))
        if not cells or len(cells) != 3:
            errors.append(f"missing or invalid {node}:{key} legacy IPC triple")
            continue
        if ph.get(cells[0]) != APCS_PATH or cells[1:] != [offset, bit]:
            errors.append(f"incorrect provider/offset/bit for {node}:{key} = {cells}")
    if "mboxes" in nodes.get("/smd/rpm", {}):
        errors.append("SMD unexpectedly switched to mailbox consumer path")
    if strings(nodes.get("/smsm", {}).get("compatible", b"")) != ["qcom,smsm"]:
        errors.append("SMSM compatible absent")
    if words(nodes.get("/smd/rpm", {}).get("qcom,smd-edge", b"")) != [15]:
        errors.append("RPM SMD edge changed")
    expected_board = 0xc100 if board == "pvt1" else 0xc200
    if words(nodes.get("/", {}).get("qcom,board-id", b"")) != [0x4d, expected_board]:
        errors.append("PVT board identity changed")
    return errors


def dtb_gate(path, board):
    data = path.read_bytes()
    nodes, _ = parse_fdt(data)
    errors = inspect_candidate_nodes(nodes, board)
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA[board]:
        errors.append("candidate DTB changed from PR #13 baseline")
    return {"variant": board, "sha256": digest, "node_count": len(nodes),
            "legacy_ipc_triplets": len(EXPECTED_IPC),
            "stock_fdt_equivalence": "NOT_TESTED",
            "rpm_runtime": "HOLD", "errors": errors}


def source_gate(root):
    sources = {
        "rpmsg": (root / "drivers/rpmsg/qcom_smd.c").read_text(),
        "smsm": (root / "drivers/soc/qcom/smsm.c").read_text(),
        "soc_kconfig": (root / "drivers/soc/qcom/Kconfig").read_text(),
    }
    must = {
        "rpmsg": ('mbox_request_channel(&edge->mbox_client, 0)',
                  'of_parse_phandle(node, "qcom,ipc", 0)',
                  'syscon_node_to_regmap(syscon_np)'),
        "smsm": ('snprintf(key, sizeof(key), "qcom,ipc-%d", host_id)',
                 'syscon_node_to_regmap(syscon)'),
        "soc_kconfig": ("config QCOM_SMSM", "depends on QCOM_SMEM",
                        "select QCOM_SMEM_STATE"),
    }
    errors = [f"missing source contract {group}: {term}"
              for group, tests in must.items()
              for term in tests if term not in sources[group]]
    return {"errors": errors, "smd_path": "legacy syscon/regmap",
            "apcs_mailbox_requirement": "NOT_PROVEN"}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for arg in ("kernel-root", "host5-config", "smsm-config", "fragment",
                "pvt1-dtb", "pvt2-dtb", "output"):
        cli.add_argument("--" + arg, required=True, type=Path)
    a = cli.parse_args()
    result = {
        "config": config_gate(a.host5_config, a.smsm_config, a.fragment),
        "drivers": source_gate(a.kernel_root),
        "pvt1": dtb_gate(a.pvt1_dtb, "pvt1"),
        "pvt2": dtb_gate(a.pvt2_dtb, "pvt2"),
        "smem_rpm_thermal_firmware_runtime": "HOLD",
        "full_deen_config_boot_flash": "HOLD",
    }
    all_errors = (result["config"]["errors"] + result["drivers"]["errors"]
                  + result["pvt1"]["errors"] + result["pvt2"]["errors"])
    result["gate"] = "PASS_HOST_ONLY_WITH_RUNTIME_HOLD" if not all_errors else "FAIL"
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(result["gate"], "delta", result["config"]["delta"],
          "candidate DTBs", result["pvt1"]["sha256"], result["pvt2"]["sha256"])
    for error in all_errors:
        print("FAIL:", error, file=sys.stderr)
    return 0 if not all_errors else 2


if __name__ == "__main__":
    sys.exit(main())
