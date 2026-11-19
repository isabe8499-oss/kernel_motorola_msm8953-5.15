#!/usr/bin/env python3
"""Negative tests for Deen SMSM-only (no APCS mailbox) host experiment."""
import struct
from pathlib import Path
import tempfile
import unittest

from deen_c100_smsm_only_host_gate import (
    APCS_PATH, EXPECTED_IPC, config_gate, inspect_candidate_nodes, source_gate)
from deen_gki_smem_rpm_config_gate import MINIMAL, HOST_ONLY

ROOT = Path(__file__).resolve().parents[1]


def cells(*seq):
    return struct.pack(">" + "I" * len(seq), *seq)


def fixed_candidate():
    nodes = {
        "/": {"qcom,board-id": cells(0x4d, 0xc100)},
        APCS_PATH: {
            "compatible": b"qcom,msm8953-apcs-kpss-global\x00syscon\x00",
            "reg": cells(0x0b011000, 0x1000),
            "phandle": cells(13),
        },
        "/smd/rpm": {"qcom,ipc": cells(13, 8, 0), "qcom,smd-edge": cells(15)},
        "/smsm": {"compatible": b"qcom,smsm\x00",
                  "qcom,ipc-1": cells(13, 8, 13),
                  "qcom,ipc-3": cells(13, 8, 19)},
    }
    return nodes


def config_file(path, values):
    path.write_text("".join(f"CONFIG_{k}={v}\n" for k, v in values.items()))
    return path


class TestSmsmWithoutApcsMailbox(unittest.TestCase):
    def test_legacy_syscon_consumer_graph(self):
        problems = inspect_candidate_nodes(fixed_candidate(), "pvt1")
        self.assertEqual(problems, [])
        self.assertEqual(len(EXPECTED_IPC), 3)

    def test_wrong_provider_or_offset_rejected(self):
        for wrong in (cells(999, 8, 0), cells(13, 0xc, 0),
                      cells(13, 8, 32)):
            with self.subTest(value=wrong):
                nodes = fixed_candidate()
                nodes["/smd/rpm"]["qcom,ipc"] = wrong
                self.assertTrue(inspect_candidate_nodes(nodes, "pvt1"))

    def test_mailbox_consumer_switch_is_rejected(self):
        nodes = fixed_candidate()
        nodes["/smd/rpm"]["mboxes"] = cells(13, 0)
        self.assertTrue(any("mailbox" in x for x in
                            inspect_candidate_nodes(nodes, "pvt1")))

    def test_missing_smsm_host_interrupt_bit_rejected(self):
        nodes = fixed_candidate()
        nodes["/smsm"]["qcom,ipc-3"] = cells(13, 8, 20)
        self.assertTrue(inspect_candidate_nodes(nodes, "pvt1"))

    def test_source_legacy_contract_is_present(self):
        self.assertEqual(source_gate(ROOT)["errors"], [])
        self.assertEqual(source_gate(ROOT)["apcs_mailbox_requirement"], "NOT_PROVEN")

    def test_config_one_symbol_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prior = {k: "y" for k in MINIMAL + HOST_ONLY}
            prior.update({"QCOM_SMEM_STATE": "y", "CFI_CLANG": "y",
                          "LTO_CLANG_FULL": "y"})
            before = config_file(root / "before", prior)
            after = config_file(root / "after", {**prior, "QCOM_SMSM": "y"})
            frag = config_file(root / "fragment", {"QCOM_SMSM": "y"})
            self.assertEqual(config_gate(before, after, frag)["errors"], [])

    def test_apcs_enablement_or_remoteproc_is_forbidden(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prior = {k: "y" for k in MINIMAL + HOST_ONLY}
            prior.update({"QCOM_SMEM_STATE": "y", "CFI_CLANG": "y",
                          "LTO_CLANG_FULL": "y"})
            before = config_file(root / "before", prior)
            frag = config_file(root / "fragment", {"QCOM_SMSM": "y"})
            for forbidden in ("QCOM_APCS_IPC", "QCOM_Q6V5_MSS", "QCOM_SMP2P"):
                with self.subTest(symbol=forbidden):
                    after = config_file(root / "after",
                                        {**prior, "QCOM_SMSM": "y", forbidden: "y"})
                    self.assertTrue(config_gate(before, after, frag)["errors"])


if __name__ == "__main__":
    unittest.main()
