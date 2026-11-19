#!/usr/bin/env python3
"""Pure host tests for the staged 5-symbol Deen SMEM/RPM Kconfig plan."""
from pathlib import Path
import tempfile
import unittest

from deen_gki_smem_rpm_config_gate import (
    MINIMAL, HOST_ONLY, read_config, fragment_symbols, audit)

ROOT = Path(__file__).resolve().parents[1]


def write(path, content):
    path.write_text(content, encoding="utf-8")
    return path


class TestDeenGkiSmemRpmConfig(unittest.TestCase):
    def test_minimal_and_host_fragment_are_exact_and_disjoint(self):
        minimal = fragment_symbols(
            ROOT / "arch/arm64/configs/deen-msm8953-base.fragment")
        host = fragment_symbols(
            ROOT / "arch/arm64/configs/deen-msm8953-smem-rpm-host.fragment")
        self.assertEqual(minimal, set(MINIMAL))
        self.assertEqual(host, set(HOST_ONLY))
        self.assertEqual(len(minimal), 20)
        self.assertEqual(len(host), 5)
        self.assertFalse(minimal & host)

    def test_kconfig_parser_handles_not_set_and_modules(self):
        with tempfile.TemporaryDirectory() as td:
            config = write(Path(td) / ".config",
                           "CONFIG_FOO=y\n# CONFIG_BAR is not set\nCONFIG_BAZ=m\n")
            self.assertEqual(read_config(config), {"FOO": "y", "BAR": "n", "BAZ": "m"})

    def test_reject_duplicate_assignments(self):
        with tempfile.TemporaryDirectory() as td:
            p = write(Path(td) / "dup", "CONFIG_FOO=y\n# CONFIG_FOO is not set\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                read_config(p)

    def make_fixture(self, directory, requested_host=True, unsafe=False):
        root = Path(directory)
        fragment = root / "base.fragment"
        additions = root / "host.fragment"
        gki = root / "gki.config"
        minimal = root / "minimal.config"
        host = root / "host.config"
        write(fragment, "".join(f"CONFIG_{x}=y\n" for x in MINIMAL))
        write(additions, "".join(f"CONFIG_{x}=y\n" for x in HOST_ONLY))
        write(gki, "CONFIG_ARCH_QCOM=y\n")
        write(minimal, "".join(f"CONFIG_{x}=y\n" for x in MINIMAL))
        host_entries = {x: "y" for x in MINIMAL}
        host_entries.update({x: "y" for x in HOST_ONLY})
        if not requested_host:
            host_entries["QCOM_SMEM"] = "n"
        if unsafe:
            host_entries["QCOM_Q6V5_MSS"] = "y"
        write(host, "".join(f"CONFIG_{k}={v}\n" for k, v in host_entries.items()))
        return gki, minimal, host, fragment, additions

    def test_valid_five_symbol_host_audit_only(self):
        with tempfile.TemporaryDirectory() as td:
            args = self.make_fixture(td)
            result = audit(*args)
            self.assertEqual(result["scope_gate"], "PASS_CONFIG_HOST_ONLY")
            self.assertEqual(result["minimal_symbol_count"], 20)
            self.assertEqual(len(result["additional_host_only_symbols"]), 5)
            self.assertEqual(result["firmware_remoteproc_enablement"], "HOLD")
            self.assertEqual(result["hardware_boot_flash_merge"], "HOLD")

    def test_missing_qcom_smem_fails_even_if_other_four_selected(self):
        with tempfile.TemporaryDirectory() as td:
            result = audit(*self.make_fixture(td, requested_host=False))
            self.assertEqual(result["scope_gate"], "FAIL")
            self.assertTrue(any("QCOM_SMEM" in err for err in result["problems"]))

    def test_reject_accidental_remoteproc_enablement(self):
        with tempfile.TemporaryDirectory() as td:
            result = audit(*self.make_fixture(td, unsafe=True))
            self.assertEqual(result["scope_gate"], "FAIL")
            self.assertTrue(any("QCOM_Q6V5_MSS" in err for err in result["problems"]))


if __name__ == "__main__":
    unittest.main()
