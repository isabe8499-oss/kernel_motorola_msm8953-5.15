#!/usr/bin/env python3
"""Regression checks for bounded Qualcomm SMSM shared-memory item access.

Host-side code-structure and arithmetic cases; ARM64 Kbuild is a separate gate.
No proprietary firmware or hardware is executed by these tests.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "drivers/soc/qcom/smsm.c"
U64_MAX = (1 << 64) - 1


def required_sizes(entries, hosts):
    """Model size_t math on ARM64 for both SMSM vectors."""
    if not entries or not hosts:
        return None
    state = entries * 4
    mask = entries * hosts * 4
    if state > U64_MAX or mask > U64_MAX:
        return None
    return state, mask


class TestSmsmSmemBounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.probe = cls.source[cls.source.index("static int qcom_smsm_probe("):]

    def test_three_overflow_checks_guard_firmware_dimensions(self):
        self.assertIn("#include <linux/overflow.h>", self.source)
        prefix = self.probe[:self.probe.index("smsm->entries = devm_kcalloc")]
        self.assertIn("if (!smsm->num_entries || !smsm->num_hosts ||", prefix)
        self.assertEqual(prefix.count("check_mul_overflow("), 3)
        self.assertIn('return -EINVAL;', prefix)
        self.assertIn('"invalid SMSM shared memory dimensions', prefix)

    def test_state_item_reports_real_size_and_is_verified_before_dereference(self):
        s = self.probe
        start = s.index("qcom_smem_alloc(QCOM_SMEM_HOST_ANY, SMEM_SMSM_SHARED_STATE")
        fetch = s.index("qcom_smem_get(QCOM_SMEM_HOST_ANY, SMEM_SMSM_SHARED_STATE, &size)", start)
        check = s.index("if (size < state_size)", fetch)
        state = s.index("smsm->local_state = states + smsm->local_host;", check)
        self.assertLess(start, fetch)
        self.assertLess(fetch, check)
        self.assertLess(check, state)
        self.assertIn("state_size);", s[start:fetch])

    def test_mask_item_reports_real_size_and_is_verified_before_indexing(self):
        s = self.probe
        start = s.index("qcom_smem_alloc(QCOM_SMEM_HOST_ANY, SMEM_SMSM_CPU_INTR_MASK")
        fetch = s.index("qcom_smem_get(QCOM_SMEM_HOST_ANY, SMEM_SMSM_CPU_INTR_MASK,", start)
        check = s.index("if (size < mask_size)", fetch)
        indexed = s.index("smsm->subscription = intr_mask + ", check)
        self.assertLess(start, fetch)
        self.assertLess(fetch, check)
        self.assertLess(check, indexed)
        self.assertIn("mask_size);", s[start:fetch])
        self.assertIn("&size", s[fetch:check])

    def test_both_size_failures_take_existing_cleanup_path(self):
        for name in ("state_size", "mask_size"):
            with self.subTest(name=name):
                start = self.probe.index(f"if (size < {name})")
                block = self.probe[start:self.probe.index("}", start)]
                self.assertIn("ret = -EINVAL;", block)
                self.assertIn("goto out_put;", block)
        self.assertIn("out_put:\n\tof_node_put(local_node);", self.probe)

    def test_local_host_guard_from_previous_pr_still_precedes_smem_use(self):
        a = self.probe.index("if (smsm->local_host >= smsm->num_entries ||")
        b = self.probe.index("smsm_parse_ipc(smsm, id)", a)
        c = self.probe.index("qcom_smem_alloc(QCOM_SMEM_HOST_ANY, SMEM_SMSM_SHARED_STATE", b)
        self.assertLess(a, b)
        self.assertLess(b, c)

    def test_subscription_offsets_use_wide_intermediate(self):
        self.assertIn("intr_mask + (size_t)smsm->local_host * smsm->num_hosts;", self.source)
        self.assertIn("intr_mask + (size_t)id * smsm->num_hosts;", self.source)

    def test_default_dimensions_and_normal_lengths(self):
        self.assertEqual(required_sizes(8, 3), (32, 96))
        self.assertEqual(required_sizes(8, 4), (32, 128))
        self.assertEqual(required_sizes(15, 8), (60, 480))
        self.assertEqual(required_sizes(1, 1), (4, 4))
        self.assertIn("#define SMSM_DEFAULT_NUM_ENTRIES\t8", self.source)
        self.assertIn("#define SMSM_DEFAULT_NUM_HOSTS\t\t3", self.source)

    def test_invalid_or_undersized_payloads_are_rejected(self):
        for entries, hosts in ((0, 3), (8, 0), (0, 0),
                               (2**32-1, 2**32-1)):
            with self.subTest(entries=entries, hosts=hosts):
                self.assertIsNone(required_sizes(entries, hosts))
        for entries, hosts in ((8, 3), (8, 4), (1, 1)):
            state, mask = required_sizes(entries, hosts)
            for actual_state, actual_mask in ((state - 4, mask),
                                              (state, mask - 4)):
                with self.subTest(e=entries, h=hosts,
                                  state=actual_state, mask=actual_mask):
                    self.assertFalse(actual_state >= state and actual_mask >= mask)


if __name__ == "__main__":
    unittest.main()
