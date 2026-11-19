#!/usr/bin/env python3
"""Synthetic corruption tests of the real Deen DTB IPC contract verifier."""
from pathlib import Path
import struct
import tempfile
import unittest

from deen_c100_apcs_smsm_ipc_gate import (
    APCS, LOCK, SMD, SMSM, SMEM, NEW, EXPECTED_IPC, inspect_nodes,
    config_audit, source_audit, DTB_SHA)
from deen_gki_smem_rpm_config_gate import MINIMAL, HOST_ONLY
from deen_c100_spmi_schema_gate import KNOWN_NON_SPMI

ROOT = Path(__file__).resolve().parents[1]


def pack(*values):
    return struct.pack(">" + "I" * len(values), *values)


def node(*, compatible=None, **props):
    data = dict(props)
    if compatible is not None:
        data["compatible"] = b"\0".join(s.encode("utf-8") for s in compatible) + b"\0"
    return data


def candidate():
    """Minimal synthetic DTB-properties model, NOT stock/hardware provenance."""
    d = {
        "/": node(**{"qcom,board-id": pack(0x4d, 0xc100)}),
        "/soc@0": node(**{"#address-cells": pack(1), "#size-cells": pack(1)}),
        APCS: node(compatible=["qcom,msm8953-apcs-kpss-global", "syscon"],
                   phandle=pack(13), reg=pack(0x0b011000, 0x1000),
                   **{"#mbox-cells": pack(1)}),
        SMD: node(**{"qcom,ipc": pack(13, 8, 0),
                     "qcom,smd-edge": pack(15),
                     "interrupts": pack(0, 168, 1)}),
        SMSM: node(compatible=["qcom,smsm"],
                   **{"qcom,ipc-1": pack(13, 8, 13),
                      "qcom,ipc-3": pack(13, 8, 19)}),
        "/smsm/apps@0": node(reg=pack(0),
                             **{"#qcom,smem-state-cells": pack(1)}),
        "/smd": node(compatible=["qcom,smd"]),
        "/smd/rpm/rpm-requests": node(compatible=["qcom,rpm-msm8953"]),
        SMEM: node(compatible=["qcom,smem"],
                   **{"memory-region": pack(0x47),
                      "qcom,rpm-msg-ram": pack(0x48),
                      "hwlocks": pack(0x49, 3)}),
        "/reserved-memory/memory@86300000": node(phandle=pack(0x47)),
        "/soc@0/sram@60000": node(phandle=pack(0x48)),
        LOCK: node(compatible=["qcom,tcsr-mutex"],
                   phandle=pack(0x49),
                   **{"#hwlock-cells": pack(1)}),
    }
    return d


def write(path, mapping):
    path.write_text("".join(f"CONFIG_{k}={v}\n" for k, v in mapping.items()),
                    encoding="utf-8")
    return path


class TestDeenApcsSmsmHostAudit(unittest.TestCase):
    def test_clean_synthetic_candidate_topology(self):
        problems, endpoints = inspect_nodes(candidate(), "pvt1")
        self.assertEqual(problems, [])
        self.assertEqual(set(endpoints), set(EXPECTED_IPC))
        self.assertTrue(all(x["provider"] == APCS for x in endpoints.values()))
        self.assertEqual([endpoints[k]["cells"][2] for k in EXPECTED_IPC],
                         [0, 13, 19])

    def test_bad_phandle_is_rejected(self):
        d = candidate()
        d[SMD]["qcom,ipc"] = pack(0x49, 8, 0)  # Points at the hwlock, not APCS
        issues, _ = inspect_nodes(d, "pvt1")
        self.assertTrue(any("qcom,ipc" in x or "provider" in x for x in issues))

    def test_smd_and_smsm_register_offset_and_bit_corruption(self):
        for path, prop, raw in (
            (SMD, "qcom,ipc", pack(13, 0xc, 0)),
            (SMSM, "qcom,ipc-1", pack(13, 8, 32)),
            (SMSM, "qcom,ipc-3", pack(13, 8, 20)),
        ):
            with self.subTest(path=path, prop=prop):
                d = candidate()
                d[path][prop] = raw
                issues, _ = inspect_nodes(d, "pvt1")
                self.assertTrue(issues)

    def test_smd_mbox_switch_and_invalid_smsm_state(self):
        d = candidate()
        d[SMD]["mboxes"] = pack(13, 0)
        d["/smsm/apps@0"]["#qcom,smem-state-cells"] = pack(2)
        issues, _ = inspect_nodes(d, "pvt1")
        self.assertTrue(any("mboxes" in err for err in issues))
        self.assertTrue(any("#qcom,smem-state-cells" in err for err in issues))

    def test_config_host_two_options_and_exact_delta(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            keys = dict.fromkeys(MINIMAL + HOST_ONLY, "y")
            keys.update({"LTO_CLANG_FULL": "y", "CFI_CLANG": "y",
                         "QCOM_SMEM_STATE": "y"})
            before = write(root / "host5", keys)
            after = write(root / "host7", {**keys, **dict.fromkeys(NEW, "y")})
            fragment = write(root / "frag", dict.fromkeys(NEW, "y"))
            result = config_audit(before, after, fragment)
            self.assertEqual(result["scope_gate"], "PASS_HOST_CONFIG_ONLY")
            self.assertEqual(set(result["delta"]), set(NEW))
            self.assertEqual(result["old_smem_state"], "y")
            self.assertEqual(result["new_smem_state"], "y")

    def test_missing_smsm_and_unexpected_remoteproc_delta_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = dict.fromkeys(MINIMAL + HOST_ONLY, "y")
            config.update({"LTO_CLANG_FULL": "y", "CFI_CLANG": "y",
                           "QCOM_SMEM_STATE": "y"})
            before = write(root / "host5", config)
            fragment = write(root / "fragment", dict.fromkeys(NEW, "y"))
            after = write(root / "bad", {**config, "QCOM_APCS_IPC": "y",
                                         "QCOM_SMSM": "n",
                                         "QCOM_Q6V5_MSS": "y"})
            result = config_audit(before, after, fragment)
            self.assertEqual(result["scope_gate"], "FAIL")
            self.assertTrue(any("QCOM_SMSM" in x for x in result["errors"]))
            self.assertTrue(any("QCOM_Q6V5_MSS" in x for x in result["errors"]))

    def test_source_matches_and_11_expected_dtb_schema_findings(self):
        self.assertEqual(source_audit(ROOT)["errors"], [])
        self.assertEqual(len(DTB_SHA), 2)
        self.assertEqual(sum(KNOWN_NON_SPMI.values()), 11)


if __name__ == "__main__":
    unittest.main()
