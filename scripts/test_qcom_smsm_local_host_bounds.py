#!/usr/bin/env python3
"""Source-level regression checks for the isolated SMSM local-host guard.

These assertions are not runtime firmware/SMEM tests. Compilation is checked
separately by GitHub Actions on ARM64 with the kernel's real Kbuild.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "drivers/soc/qcom/smsm.c"


def host_index_valid(local_host, num_entries, num_hosts):
    return (0 <= local_host < num_entries and
            0 <= local_host < num_hosts)


class TestSmsmLocalHostBounds(unittest.TestCase):
    def test_guard_checks_both_dimensions_exactly_once(self):
        s = SOURCE.read_text(encoding="utf-8")
        expr = ("if (smsm->local_host >= smsm->num_entries ||\n"
                "\t    smsm->local_host >= smsm->num_hosts)")
        self.assertEqual(s.count(expr), 1)
        self.assertIn("local host index exceeds SMSM dimensions", s)

    def test_guard_precedes_host_probe_and_pointer_arithmetic(self):
        s = SOURCE.read_text(encoding="utf-8")
        probe = s.index("static int qcom_smsm_probe(")
        local = s.index('"qcom,local-host",', probe)
        check = s.index("if (smsm->local_host >= smsm->num_entries ||", local)
        parse = s.index("smsm_parse_ipc(smsm, id)", check)
        state = s.index("smsm->local_state = states + smsm->local_host;", parse)
        matrix = s.index("smsm->subscription = intr_mask + smsm->local_host", state)
        self.assertTrue(probe < local < check < parse < state < matrix)

    def test_guard_exits_using_existing_cleanup_path(self):
        s = SOURCE.read_text(encoding="utf-8")
        guard = s.index("if (smsm->local_host >= smsm->num_entries ||",
                        s.index("static int qcom_smsm_probe("))
        block = s[guard:s.index("/* Parse the host properties */", guard)]
        self.assertIn("ret = -EINVAL;", block)
        self.assertIn("goto out_put;", block)
        cleanup = s[s.index("out_put:", guard):]
        self.assertIn("of_node_put(local_node);", cleanup)

    def test_default_and_valid_hosts_unchanged(self):
        for entries, hosts, local in ((8, 3, 0), (8, 3, 1),
                                      (8, 3, 2), (8, 4, 3),
                                      (1, 1, 0), (15, 8, 7)):
            with self.subTest(entries=entries, hosts=hosts, local=local):
                self.assertTrue(host_index_valid(local, entries, hosts))

    def test_out_of_range_host_is_rejected(self):
        for entries, hosts, local in ((8, 3, 3), (8, 3, 8),
                                      (3, 8, 3), (0, 4, 0),
                                      (8, 0, 0), (0, 0, 0),
                                      (8, 4, 0xffffffff)):
            with self.subTest(entries=entries, hosts=hosts, local=local):
                self.assertFalse(host_index_valid(local, entries, hosts))

    def test_no_enablement_or_dts_changes_needed(self):
        s = SOURCE.read_text(encoding="utf-8")
        self.assertIn("#define SMSM_DEFAULT_NUM_ENTRIES\t8", s)
        self.assertIn("#define SMSM_DEFAULT_NUM_HOSTS\t\t3", s)
        self.assertIn("smsm_get_size_info(smsm)", s)
        self.assertIn("qcom_smem_get(QCOM_SMEM_HOST_ANY, SMEM_SMSM_SHARED_STATE, &size)", s)
        self.assertIn("qcom_smem_state_register(local_node, &smsm_state_ops, smsm)", s)


if __name__ == "__main__":
    unittest.main()
