#!/usr/bin/env python3
"""Read-only stock Deen boot-FDT and candidate DTB reconciliation.

- With --stock-boot: directly re-verifies the user's original 64 MiB image.
- Without it (GitHub CI): validates only compiled candidates against a
  derived, hash-pinned reference; NEVER claims a direct stock scan in CI.
- No flashing, firmware execution, temperature probing or device access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from deen_fdt_memory_ledger import parse_fdt, strings, words

MAGIC = b"\xd0\x0d\xfe\xed"
BOOT_SHA = "6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765"
CAND_SHA = {
    "pvt1": "fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a",
    "pvt2": "9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05",
}
STOCK_SMEM = "/soc/qcom,smem@86300000"
SOURCE_NAMES = ("smd-rpm", "smd-modem", "smsm-modem", "smd-wcnss",
                "smsm-wcnss", "smd-adsp", "smsm-adsp")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prop(nodes, path, key):
    return words(nodes.get(path, {}).get(key, b""))


def comps(nodes, path):
    return strings(nodes.get(path, {}).get("compatible", b""))


def pairs(cells):
    if cells is None or len(cells) % 2:
        raise ValueError("unexpected reg cell width")
    return [cells[i:i+2] for i in range(0, len(cells), 2)]


def all_stock_fdt(boot, reference):
    if (len(boot) != reference["provenance"]["boot_size"]
            or sha(boot) != reference["provenance"]["boot_sha256"]
            or sha(boot) != BOOT_SHA or not boot.startswith(b"ANDROID!")):
        raise ValueError("stock boot image missing expected Android magic/length/SHA")
    found = []
    offset = 0
    while True:
        pos = boot.find(MAGIC, offset)
        if pos < 0:
            break
        offset = pos + 4
        if pos + 40 > len(boot):
            continue
        length = struct.unpack_from(">I", boot, pos + 4)[0]
        if length < 80 or length > 2_000_000 or pos + length > len(boot):
            continue
        raw = boot[pos:pos+length]
        try:
            nodes, _ = parse_fdt(raw)
        except ValueError:
            continue
        found.append({"offset": pos, "size": length, "sha256": sha(raw),
                      "nodes": nodes, "count": len(nodes),
                      "board": prop(nodes, "/", "qcom,board-id"),
                      "msm": prop(nodes, "/", "qcom,msm-id")})
    if len(found) != 7 or len(found) != reference["provenance"]["fdt_count"]:
        raise ValueError("stock FDT scan did not find exactly seven valid FDTs")
    ordered = sorted(found, key=lambda x: x["offset"])
    if any(a["offset"] + a["size"] > b["offset"]
           for a, b in zip(ordered, ordered[1:])):
        raise ValueError("stock FDT intervals overlap")
    selected = {}
    for name in ("c100", "c200"):
        expected = reference["stock"][name]
        matches = [x for x in found if x["board"] == expected["board"]]
        if len(matches) != 1:
            raise ValueError(f"missing or ambiguous verified stock FDT {name}")
        value = matches[0]
        for key in ("offset", "size", "sha256"):
            if value[key] != expected[key]:
                raise ValueError(f"stock {name} {key} differs from binary reference")
        if value["count"] != expected["nodes"] or value["msm"] != expected["msm"]:
            raise ValueError(f"stock {name} unexpected node count or SoC")
        selected[name] = value
    a, b = selected["c100"]["nodes"], selected["c200"]["nodes"]
    changed = [(path, prop_name)
               for path in sorted(set(a) | set(b))
               for prop_name in sorted(set(a.get(path, {})) | set(b.get(path, {})))
               if a.get(path, {}).get(prop_name) != b.get(path, {}).get(prop_name)]
    if changed != [("/", "qcom,board-id")]:
        raise ValueError("stock C100/C200 differ outside qcom,board-id")
    return selected, [{"offset":x["offset"], "size":x["size"],
                       "sha256":x["sha256"], "board":x["board"],
                       "node_count":x["count"]} for x in ordered]


def check_stock_nodes(nodes, ref):
    stock = ref["stock"]
    smem = nodes[STOCK_SMEM]
    if (comps(nodes, STOCK_SMEM) != ["qcom,smem"]
            or strings(smem["reg-names"]) != stock["smem"]["reg_names"]
            or pairs(prop(nodes, STOCK_SMEM, "reg")) != stock["smem"]["reg_pairs"]
            or ("qcom,mpu-enabled" in smem) != stock["smem"]["mpu_enabled"]):
        raise ValueError("stock SMEM geometry/IRQ map differs")
    l2 = stock["block_at_b011000"]
    if (comps(nodes, l2["node"]) != l2["compatible"]
            or pairs(prop(nodes, l2["node"], "reg")) != [l2["reg_pair"]]):
        raise ValueError("stock L2CCC block differs")
    for name in SOURCE_NAMES:
        e = stock["endpoints"][name]
        path = f"{STOCK_SMEM}/qcom,{name}"
        kind = "smd" if name.startswith("smd-") else "smsm"
        mask = prop(nodes, path, f"qcom,{kind}-irq-bitmask")
        offset = prop(nodes, path, f"qcom,{kind}-irq-offset")
        irq = prop(nodes, path, "interrupts")
        edge = prop(nodes, path, f"qcom,{kind}-edge")
        if (not mask or mask != [e["mask"]] or offset != [e["offset"]]
                or mask[0] != 1 << e["bit"]
                or irq != [0, e["spi"], 1] or edge != [e["edge"]]):
            raise ValueError(f"stock IPC endpoint differs: {name}")
    if any(k in ("qcom,ipc", "qcom,ipc-1", "qcom,ipc-3")
           for p in nodes.values() for k in p):
        raise ValueError("stock unexpectedly has new-style qcom,ipc triples")
    ts = stock["tsens"]
    if (comps(nodes, ts["node"]) != ts["compatible"]
            or prop(nodes, ts["node"], "qcom,sensors") != [ts["count"]]
            or prop(nodes, ts["node"], "qcom,sensor-id") != ts["ids"]
            or prop(nodes, ts["node"], "qcom,client-id") != ts["ids"]
            or pairs(prop(nodes, ts["node"], "reg")) != ts["reg_pairs"]
            or len(prop(nodes, ts["node"], "qcom,slope") or []) != 15):
        raise ValueError("stock TSENS sensors/registers differ")
    expected = stock["spmi"]
    if (strings(nodes["/soc/qcom,spmi@200f000"]["reg-names"]) != expected["reg_names"]
            or pairs(prop(nodes, "/soc/qcom,spmi@200f000", "reg")) != expected["reg_pairs"]):
        raise ValueError("stock SPMI resources changed")
    return True


def candidate_nodes(raw, board, ref):
    info = ref["candidate"][board]
    if sha(raw) != info["sha256"] or sha(raw) != CAND_SHA[board]:
        raise ValueError(f"candidate {board} SHA mismatch")
    nodes, _ = parse_fdt(raw)
    if len(nodes) != info["nodes"] or prop(nodes, "/", "qcom,board-id") != info["board"]:
        raise ValueError(f"candidate {board} board/nodes changed")
    apcs = ref["candidate"]["apcs"]
    provider = nodes[apcs["node"]]
    if (comps(nodes, apcs["node"]) != apcs["compatible"]
            or pairs(prop(nodes, apcs["node"], "reg")) != [apcs["reg_pair"]]):
        raise ValueError("candidate APCS compatible/address changed")
    phandle = prop(nodes, apcs["node"], "phandle")
    if not phandle or len(phandle) != 1:
        raise ValueError("candidate APCS phandle missing")
    observed = {}
    for key, (path, prop_name, offset, bit) in ref["candidate"]["ipc"].items():
        ipc = prop(nodes, path, prop_name)
        if ipc != [phandle[0], offset, bit]:
            raise ValueError(f"{key} candidate legacy syscon triple changed")
        observed[key] = {"absolute_mmio": apcs["reg_pair"][0] + offset,
                         "bit": bit, "provider": apcs["node"]}
    if "mboxes" in nodes["/smd/rpm"]:
        raise ValueError("candidate no longer uses legacy SMD IPC")
    if (prop(nodes, "/smd/rpm", "qcom,smd-edge") != [15]
            or prop(nodes, "/smd/rpm", "interrupts") != [0, 168, 1]):
        raise ValueError("candidate RPM SMD edge/interrupt changed")
    ts = ref["candidate"]["tsens"]
    if (comps(nodes, ts["node"]) != ts["compatible"]
            or prop(nodes, ts["node"], "#qcom,sensors") != [ts["count"]]
            or pairs(prop(nodes, ts["node"], "reg")) != ts["reg_pairs"]):
        raise ValueError("candidate TSENS geometry changed")
    spmi = pairs(prop(nodes, "/soc@0/spmi@200f000", "reg"))
    if spmi != ref["stock"]["spmi"]["reg_pairs"]:
        raise ValueError("candidate SPMI geometry changed from stock five windows")
    return {"board": board, "sha256": sha(raw), "node_count": len(nodes),
            "ipc": observed, "spmi_windows_match_stock": True}


def compare_numeric(reference, candidate):
    ref = reference["stock"]
    mmio = ref["smem"]["irq_reg_mmio"]
    pairs_to_check = (
        ("smd-rpm", "smd-rpm"),
        ("smsm-modem", "smsm-modem-bit"),
        ("smsm-wcnss", "smsm-wcnss-bit"),
    )
    out = []
    for stock_key, candidate_key in pairs_to_check:
        stock = ref["endpoints"][stock_key]
        c = candidate["ipc"][candidate_key]
        match = (mmio + stock["offset"] == c["absolute_mmio"]
                 and stock["bit"] == c["bit"])
        if not match:
            raise ValueError(f"numeric MMIO/bit mismatch: {stock_key}")
        out.append({"stock": stock_key, "candidate": candidate_key,
                    "register_mmio": c["absolute_mmio"], "bit": c["bit"],
                    "numeric_match": match, "host_and_firmware_equivalence": "HOLD"})
    if ref["tsens"]["count"] != 15 or reference["candidate"]["tsens"]["count"] != 16:
        raise ValueError("TSENS 15 vs 16 evidence differs from source")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--stock-boot", type=Path, default=None)
    parser.add_argument("--candidate-pvt1", type=Path, required=True)
    parser.add_argument("--candidate-pvt2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    try:
        ref = json.loads(a.reference.read_text(encoding="utf-8"))
        if ref["provenance"]["boot_sha256"] != BOOT_SHA:
            raise ValueError("reference boot SHA mismatch")
        stock_catalog = None
        if a.stock_boot is not None:
            selected, stock_catalog = all_stock_fdt(a.stock_boot.read_bytes(), ref)
            for name in ("c100", "c200"):
                check_stock_nodes(selected[name]["nodes"], ref)
        candidates = {
            board: candidate_nodes(getattr(a, f"candidate_{board}").read_bytes(), board, ref)
            for board in ("pvt1", "pvt2")
        }
        numeric = {b:compare_numeric(ref, candidates[b]) for b in candidates}
        direct = a.stock_boot is not None
        result = {
            "result": ("PASS_STOCK_DIRECT_DIFFERENCES_RUNTIME_HOLD" if direct else
                       "PASS_REFERENCE_ONLY_STOCK_DIRECT_NOT_RECHECKED_IN_CI"),
            "stock_binary_directly_read": direct,
            "stock_fdt_catalog": stock_catalog,
            "stock_c100_fdt_sha256": ref["stock"]["c100"]["sha256"],
            "stock_c200_fdt_sha256": ref["stock"]["c200"]["sha256"],
            "stock_smd_edges": sorted(e["edge"] for n,e in ref["stock"]["endpoints"].items()
                                      if n.startswith("smd-")),
            "candidate_smd_edges": [15],
            "stock_l2ccc_compatible": ref["stock"]["block_at_b011000"]["compatible"],
            "candidate_apcs_compatible": ref["candidate"]["apcs"]["compatible"],
            "stock_smem_1mib_location": ref["stock"]["smem"]["reg_pairs"][0],
            "stock_vs_candidate_tsens_sensor_count": [15,16],
            "candidate": candidates,
            "numeric_doorbell_matches": numeric,
            "bootloader_selects_this_fdt": "NOT_PROVEN",
            "smem_ipc_firmware_irq_runtime": "HOLD",
            "tsens_thermal_runtime": "HOLD",
            "full_kernel_boot_flash_merge": "HOLD",
        }
        a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(result["result"])
        for board in ("pvt1", "pvt2"):
            print(board, "physical matches", len(numeric[board]),
                  "DTB sha", candidates[board]["sha256"])
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        print("FAIL_CLOSED:", exc, file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
