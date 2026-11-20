#!/usr/bin/env python3
"""Host-only C100/C200 stock CPU clocks versus ACK 5.15 DTB gate.

CI checks only two compiled candidate DTBs against a derived SHA-pinned stock
manifest. Direct re-reading of the user's original stock boot is NOT claimed
by this script and is NOT supported inside this workflow.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

CPU_REGS = [0, 1, 2, 3, 0x100, 0x101, 0x102, 0x103]
STOCK_SHA = "6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765"
DTB_SHA = {
    "PVT1": "2c5fb810fdfcae65768167327bdb4ac4ba824aea6cfa2dc4b5117838aa9ae442",
    "PVT2": "5998d09cae4ebb4b65ebc2e7085ae83ae61ac5a7b8ae6adf3c725f753f20ecff",
}
EXPECTED_REGS = [
    ("rcgwr-c0-base", 0x0b114000, 0x68),
    ("rcgwr-c1-base", 0x0b014000, 0x68),
    ("c0-pll", 0x0b116000, 0x400),
    ("c0-mux", 0x0b111050, 0x8),
    ("c1-mux", 0x0b011050, 0x8),
    ("cci-mux", 0x0b1d1050, 0x8),
    ("efuse", 0x000a4124, 0x8),
]
L2 = [
    ("/soc/clock-controller@b011000", 0x0b011000, 0x1000),
    ("/soc/clock-controller@b111000", 0x0b111000, 0x1000),
]


def validate_manifest(man):
    if man["provenance"]["boot_sha256"] != STOCK_SHA:
        raise ValueError("stock boot SHA differs from pinned source")
    if man["provenance"]["stock_binary_committed"] is not False:
        raise ValueError("stock binary must not be in repo")
    seen = man["provenance"]["stock_fdt"]
    if sorted(seen) != ["C100", "C200"]:
        raise ValueError("missing stock C100/C200 evidence")
    if (seen["C100"]["sha256"] !=
            "537dc8c3f0a75fbe0b27d8d32b067c7efa8472dccd86b33698700e7e4022408a"
            or seen["C200"]["sha256"] !=
            "f1bd9bb41f203ebb443b79bfd38564e6203fb858be3d53d8ad132792952c9a16"):
        raise ValueError("unexpected stock FDT hashes")
    stock = man["stock_cpu_clock"]
    if stock["node"] != "/soc/qcom,cpu-clock-8953@b116000":
        raise ValueError("stock clock node mismatch")
    if stock["compatible"] != ["qcom,cpu-clock-8953"]:
        raise ValueError("unexpected stock CPU clock binding")
    if stock["num_clusters"] != 2 or stock["clock_cells"] != 1:
        raise ValueError("expected two clusters and single clock selector")
    regs = [(x["name"], x["address"], x["size"]) for x in stock["registers"]]
    if regs != EXPECTED_REGS:
        raise ValueError("stock clock's seven named MMIO windows differ")
    for name, addr, length in regs:
        if length <= 0 or any(addr < other + size and other < addr + length
                              for other_name, other, size in regs
                              if other_name != name):
            raise ValueError("stock clock resources overlap unexpectedly")
    windows = [(x["node"], x["address"], x["size"])
               for x in man["stock_l2ccc"]]
    if windows != L2:
        raise ValueError("two stock L2CCC bases differ")
    if regs[3][1] != L2[1][1] + 0x50 or regs[4][1] != L2[0][1] + 0x50:
        raise ValueError("stock A53 cluster mux offsets differ")
    if stock["cpu_node_regs"] != CPU_REGS:
        raise ValueError("eight stock CPU identifiers differ")
    if stock["cpu_advertised_clock_frequency_hz"] != 2016000000:
        raise ValueError("stock DT declared CPU clock frequency differs")
    if stock["clock_frequency_is_measured_runtime"] is not False:
        raise ValueError("DT clock-frequency is not runtime evidence")
    if stock["supplies"] != ["vdd-mx-supply", "vdd-cl-supply"]:
        raise ValueError("stock CPU voltage supply names differ")
    if stock["clock_names"] != ["xo_a"]:
        raise ValueError("stock CPU clock input name differs")
    if stock["speed_bin_property_names"] != [
        f"qcom,speed{v}-bin-v0-{label}"
        for v in (0, 2, 6, 7) for label in ("cl", "cci")
    ]:
        raise ValueError("stock CPU/CCI speed-bin property names differ")
    cand = man["ack515_candidate"]
    if (cand["cpus"] != 8 or
            cand["cpu_clock_provider_in_dtb"] is not False or
            cand["cpu_opp_reference_in_dtb"] is not False or
            cand["cpu_supply_in_dtb"] is not False or
            cand["dtb_sha256"] != DTB_SHA):
        raise ValueError("candidate CPU DVFS source assumptions differ")
    a = cand["apcs"]
    if (a["address"], a["size"], a["node"], a["compatible"]) != (
            0x0b011000, 0x1000, "/soc@0/mailbox@b011000",
            ["qcom,msm8953-apcs-kpss-global", "syscon"]):
        raise ValueError("candidate APCS geometry differs")
    return True


def invoke(*args):
    p = subprocess.run(args, text=True, capture_output=True, check=False)
    if p.returncode != 0:
        raise ValueError(f"{args[0]} failed: {p.stderr.strip()[:250]}")
    return p.stdout.strip()


def cells(dtb, path, prop):
    return [int(v, 16) for v in invoke("fdtget", "-t", "x", str(dtb),
                                       path, prop).split()]


def properties(dtb, path):
    return set(invoke("fdtget", "-p", str(dtb), path).split())


def verify_candidate(board, dtb, ref):
    expected = ref["ack515_candidate"]
    digest = hashlib.sha256(dtb.read_bytes()).hexdigest()
    if digest != DTB_SHA[board] or digest != expected["dtb_sha256"][board]:
        raise ValueError(f"{board} DTB hash differs from audited baseline")
    if cells(dtb, "/", "qcom,board-id") != expected["board_id"][board]:
        raise ValueError(f"{board} board-id mismatch")
    absent = {"clocks", "cpu-supply", "operating-points-v2"}
    for cpu in CPU_REGS:
        path = f"/cpus/cpu@{cpu:x}"
        if cells(dtb, path, "reg") != [cpu]:
            raise ValueError(f"{board} CPU reg mismatch: {path}")
        if invoke("fdtget", str(dtb), path, "compatible") != "arm,cortex-a53":
            raise ValueError(f"{board} unexpected CPU compatible")
        if invoke("fdtget", str(dtb), path, "enable-method") != "psci":
            raise ValueError(f"{board} CPU power-on method differs")
        if properties(dtb, path) & absent:
            raise ValueError(f"{board} unreviewed CPU clock/OPP/supply in {path}")
    a = expected["apcs"]
    if cells(dtb, a["node"], "reg") != [a["address"], a["size"]]:
        raise ValueError(f"{board} APCS register range differs")
    if invoke("fdtget", str(dtb), a["node"], "compatible").split() != a["compatible"]:
        raise ValueError(f"{board} APCS compatible differs")
    dts = invoke("dtc", "-I", "dtb", "-O", "dts", str(dtb))
    if '"qcom,cpu-clock-8953"' in dts:
        raise ValueError(f"{board} CPU clock driver now bound: review required")
    return {
        "board": board,
        "dtb_sha256": digest,
        "cpus_checked": len(CPU_REGS),
        "clock_provider_in_candidate": False,
        "cpu_opp_supply_bindings_found": False,
        "apcs_mmio": hex(a["address"]),
        "cpu_dvfs_runtime": "HOLD",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--pvt1", required=True, type=Path)
    p.add_argument("--pvt2", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    try:
        ref = json.loads(a.reference.read_text(encoding="utf-8"))
        validate_manifest(ref)
        result = {
            "gate": "PASS_REFERENCE_ONLY_CPU_DVFS_PORT_HOLD",
            "original_stock_boot_directly_read_in_CI": False,
            "stock_cpu_clock_two_clusters": True,
            "stock_cpu_clock_mmio_resources": len(EXPECTED_REGS),
            "stock_l2ccc_windows": len(L2),
            "stock_cpu_advertised_mhz_not_measured": 2016,
            "candidate": {
                name: verify_candidate(name, dtb, ref)
                for name, dtb in (("PVT1", a.pvt1), ("PVT2", a.pvt2))
            },
            "cpu_dvfs_driver": "HOLD",
            "cpu_voltages_cci_thermal": "HOLD",
            "firmware_boot_flash": "HOLD",
        }
        a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(result["gate"])
        return 0
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"FAIL_CLOSED: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
