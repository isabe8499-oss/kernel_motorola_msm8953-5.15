#!/usr/bin/env python3
"""Host-only tests: derived stock facts versus candidate DTB protocols.

Synthetic fixtures do NOT claim the original boot image is present in CI.
"""
import json
from pathlib import Path
import struct
import unittest

from deen_stock_c100_c200_binary_gate import (
    BOOT_SHA, CAND_SHA, STOCK_SMEM, SOURCE_NAMES,
    all_stock_fdt, check_stock_nodes, compare_numeric,
)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = (ROOT / "documentation" /
             "DEEN_STOCK_C100_C200_BINARY_REFERENCE_2026-11-19.json")


def cells(*values):
    return struct.pack(">" + "I"*len(values), *values)


def strs(*values):
    return b"".join(v.encode("ascii") + b"\0" for v in values)


def fixture_stock(ref):
    stock = ref["stock"]
    nodes = {STOCK_SMEM: {
        "compatible": strs("qcom,smem"),
        "reg-names": strs(*stock["smem"]["reg_names"]),
        "reg": cells(*[cell for pair in stock["smem"]["reg_pairs"]
                       for cell in pair]),
        "qcom,mpu-enabled": b"",
    }}
    l2 = stock["block_at_b011000"]
    nodes[l2["node"]] = {"compatible": strs(*l2["compatible"]),
                         "reg": cells(*l2["reg_pair"])}
    for name in SOURCE_NAMES:
        endpoint = stock["endpoints"][name]
        kind = "smd" if name.startswith("smd-") else "smsm"
        nodes[f"{STOCK_SMEM}/qcom,{name}"] = {
            f"qcom,{kind}-irq-bitmask": cells(endpoint["mask"]),
            f"qcom,{kind}-irq-offset": cells(endpoint["offset"]),
            f"qcom,{kind}-edge": cells(endpoint["edge"]),
            "interrupts": cells(0, endpoint["spi"], 1),
        }
    ts = stock["tsens"]
    nodes[ts["node"]] = {
        "compatible": strs(*ts["compatible"]),
        "qcom,sensors": cells(ts["count"]),
        "qcom,sensor-id": cells(*ts["ids"]),
        "qcom,client-id": cells(*ts["ids"]),
        "reg": cells(*[c for pair in ts["reg_pairs"] for c in pair]),
        "qcom,slope": cells(*([ts["slope_each"]]*ts["slope_count"])),
    }
    sp = stock["spmi"]
    nodes["/soc/qcom,spmi@200f000"] = {
        "reg-names": strs(*sp["reg_names"]),
        "reg": cells(*[c for pair in sp["reg_pairs"] for c in pair]),
    }
    return nodes


def fixture_candidate(ref):
    base = ref["candidate"]["apcs"]["reg_pair"][0]
    return {"ipc": {
        name: {"absolute_mmio": base + props[2], "bit": props[3]}
        for name, props in ref["candidate"]["ipc"].items()
    }}


class TestStockFdtReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = json.loads(REFERENCE.read_text(encoding="utf-8"))

    def test_pin_hashes_and_seven_fdt_source(self):
        p = self.ref["provenance"]
        self.assertEqual(p["boot_size"], 67108864)
        self.assertEqual(p["boot_sha256"], BOOT_SHA)
        self.assertEqual(p["fdt_count"], 7)
        self.assertFalse(p["raw_stock_in_repo"])
        self.assertEqual(self.ref["stock"]["c100"]["board"], [77, 49408])
        self.assertEqual(self.ref["stock"]["c200"]["board"], [77, 49664])
        self.assertEqual(self.ref["stock"]["c100"]["offset"], 0xb7820a)
        self.assertEqual(self.ref["stock"]["c200"]["offset"], 0xabe4f6)
        self.assertEqual(self.ref["candidate"]["pvt1"]["sha256"], CAND_SHA["pvt1"])
        self.assertEqual(self.ref["candidate"]["pvt2"]["sha256"], CAND_SHA["pvt2"])

    def test_stock_reference_synthetic_geometry(self):
        self.assertTrue(check_stock_nodes(fixture_stock(self.ref), self.ref))

    def test_bad_rpm_mask_rejected(self):
        nodes = fixture_stock(self.ref)
        nodes[f"{STOCK_SMEM}/qcom,smd-rpm"]["qcom,smd-irq-bitmask"] = cells(2)
        with self.assertRaisesRegex(ValueError, "smd-rpm"):
            check_stock_nodes(nodes, self.ref)

    def test_bad_thermal_count_rejected(self):
        nodes = fixture_stock(self.ref)
        nodes["/soc/tsens@4a8000"]["qcom,sensors"] = cells(16)
        with self.assertRaisesRegex(ValueError, "TSENS"):
            check_stock_nodes(nodes, self.ref)

    def test_rpm_and_two_smsm_numeric_mmio_matches_not_runtime(self):
        records = compare_numeric(self.ref, fixture_candidate(self.ref))
        self.assertEqual(len(records), 3)
        self.assertEqual([v["bit"] for v in records], [0, 13, 19])
        self.assertTrue(all(v["numeric_match"] for v in records))
        self.assertTrue(all(v["register_mmio"] == 0xb011008 for v in records))
        self.assertTrue(all(v["host_and_firmware_equivalence"] == "HOLD"
                            for v in records))

    def test_doorbell_corruption_is_rejected(self):
        fake = fixture_candidate(self.ref)
        fake["ipc"]["smsm-modem-bit"]["bit"] = 12
        with self.assertRaisesRegex(ValueError, "numeric MMIO/bit mismatch"):
            compare_numeric(self.ref, fake)

    def test_invalid_stock_boot_never_claimed_direct(self):
        with self.assertRaisesRegex(ValueError, "stock boot image"):
            all_stock_fdt(b"ANDROID!" + b"\0"*4096, self.ref)

    def test_stock_extra_smd_channels_and_15_sensor_hold(self):
        stock = self.ref["stock"]
        self.assertEqual(sorted(v["edge"] for name, v in stock["endpoints"].items()
                                if name.startswith("smd-")), [0, 1, 6, 15])
        self.assertEqual(stock["tsens"]["count"], 15)
        self.assertEqual(self.ref["candidate"]["tsens"]["count"], 16)
        self.assertEqual(stock["smem"]["reg_pairs"][1][0], 0xb011008)
        self.assertEqual(self.ref["candidate"]["apcs"]["reg_pair"][0], 0xb011000)


if __name__ == "__main__":
    unittest.main()
