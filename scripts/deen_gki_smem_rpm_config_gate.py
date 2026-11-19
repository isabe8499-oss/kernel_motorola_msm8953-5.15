#!/usr/bin/env python3
"""Audit Deen's minimal 20-option base and a 5-option host-only SMEM/SMD gate.

Never considers config/compilation sufficient proof of real RPM, clocks,
firmware interoperability, bootability, or a safe image to flash.
"""
import argparse
import json
from pathlib import Path
import re
import sys

MINIMAL = (
    "ARCH_QCOM", "COMMON_CLK_QCOM", "MSM_GCC_8953",
    "PINCTRL_MSM", "PINCTRL_MSM8953", "MAILBOX", "RPMSG",
    "QCOM_SMD_RPM", "QCOM_RPMPD", "SPMI", "SPMI_MSM_PMIC_ARB",
    "MFD_SPMI_PMIC", "REGULATOR_QCOM_SMD_RPM", "REGULATOR_QCOM_SPMI",
    "REGULATOR_FIXED_VOLTAGE", "MMC", "MMC_SDHCI",
    "MMC_SDHCI_PLTFM", "MMC_SDHCI_MSM", "KEYBOARD_GPIO",
)
HOST_ONLY = (
    "HWSPINLOCK", "HWSPINLOCK_QCOM", "QCOM_SMEM",
    "RPMSG_QCOM_SMD", "QCOM_CLK_SMD_RPM",
)
# A new enablement of these via the host fragment requires manual review.
# Their previous state in the GKI or minimal config is left untouched.
NO_NEW_ENABLEMENT = (
    "QCOM_Q6V5_MSS", "QCOM_Q6V5_PAS", "QCOM_WCNSS_PIL",
    "QCOM_SMP2P", "QCOM_SMSM", "DRM_MSM", "QCOM_TSENS",
    "NFC_NXP_NCI_I2C", "TYPEC_FUSB302", "USB_DWC3_QCOM",
)
CONFIG_LINE = re.compile(r"^CONFIG_([A-Z0-9_]+)=(.+)$")
NOT_SET = re.compile(r"^# CONFIG_([A-Z0-9_]+) is not set$")


def read_config(path):
    config = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        assigned = CONFIG_LINE.fullmatch(line)
        disabled = NOT_SET.fullmatch(line)
        if assigned:
            name, value = assigned.groups()
        elif disabled:
            name, value = disabled.group(1), "n"
        else:
            continue
        if name in config:
            raise ValueError(f"duplicate config {name} in {path}")
        config[name] = value
    return config


def fragment_symbols(path):
    values = read_config(path)
    if any(v != "y" for v in values.values()):
        raise ValueError(f"fragment {path} must contain only built-in selections")
    return set(values)


def audit(gki_path, minimal_path, host_path, base_fragment, host_fragment):
    problems = []
    original = read_config(gki_path)
    minimal = read_config(minimal_path)
    host = read_config(host_path)
    base_keys = fragment_symbols(base_fragment)
    host_keys = fragment_symbols(host_fragment)
    if base_keys != set(MINIMAL):
        problems.append("20-symbol minimal fragment changed without separate audit")
    if host_keys != set(HOST_ONLY):
        problems.append("host-only SMEM/RPM fragment is not the exact five-symbol set")
    if base_keys & host_keys:
        problems.append("host-only fragment overlaps the minimal fragment")

    for name in MINIMAL:
        if minimal.get(name) != "y" or host.get(name) != "y":
            problems.append(f"required base driver not built-in: {name}")
    for name in HOST_ONLY:
        if host.get(name) != "y":
            problems.append(f"host audit dependency failed to resolve as built-in: {name}")
    for name in NO_NEW_ENABLEMENT:
        if minimal.get(name, "n") not in ("y", "m") and host.get(name, "n") in ("y", "m"):
            problems.append(f"unsupported subsystem newly activated by fragment: {name}")

    # This is a static source/config invariance check, not a proof of firmware.
    delta = {}
    for name in sorted(set(minimal) | set(host)):
        before, after = minimal.get(name, "n"), host.get(name, "n")
        if before != after:
            delta[name] = {"minimal": before, "host": after}
    selected_before = {k: original.get(k, "n") for k in MINIMAL}
    return {
        "scope": "host-only 20-symbol Deen base plus five SMEM/SMD clock dependencies",
        "minimal_symbol_count": len(base_keys),
        "additional_host_only_symbols": sorted(host_keys),
        "gki_to_minimal_selected_prior_values": selected_before,
        "kconfig_changes_due_to_host_fragment": delta,
        "suspect_new_activation": [name for name in NO_NEW_ENABLEMENT
                                   if any(x.endswith(name) for x in problems)],
        "firmware_remoteproc_enablement": "HOLD",
        "dtb_full_schema": "REVIEW_REQUIRED",
        "full_deen_defconfig": "HOLD",
        "hardware_boot_flash_merge": "HOLD",
        "problems": problems,
        "scope_gate": "PASS_CONFIG_HOST_ONLY" if not problems else "FAIL",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("gki-config", "minimal-config", "host-config",
                 "base-fragment", "host-fragment", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    result = audit(args.gki_config, args.minimal_config, args.host_config,
                   args.base_fragment, args.host_fragment)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(result["scope_gate"], "minimal", result["minimal_symbol_count"],
          "host", len(result["additional_host_only_symbols"]),
          "Kconfig delta", len(result["kconfig_changes_due_to_host_fragment"]))
    for error in result["problems"]:
        print("FAIL:", error, file=sys.stderr)
    return 0 if result["scope_gate"] == "PASS_CONFIG_HOST_ONLY" else 4


if __name__ == "__main__":
    sys.exit(main())
