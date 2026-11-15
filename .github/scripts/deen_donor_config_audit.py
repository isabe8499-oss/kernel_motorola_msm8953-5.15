#!/usr/bin/env python3
"""Read-only donor CONFIG inventory against the ACK 5.15 Kconfig source tree."""
from __future__ import annotations
import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ASSIGN_RE = re.compile(r"^\s*CONFIG_([A-Za-z0-9_]+)=(.*?)\s*$")
UNSET_RE = re.compile(r"^\s*#\s*CONFIG_([A-Za-z0-9_]+)\s+is not set\s*$")
DEF_RE = re.compile(r"^\s*(?:menu)?config\s+([A-Za-z0-9_]+)\b")

def parse_config(path: Path):
    values = {}
    duplicates = defaultdict(list)
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = ASSIGN_RE.match(line)
        if match:
            symbol, value = match.group(1), match.group(2)
        else:
            match = UNSET_RE.match(line)
            if not match:
                continue
            symbol, value = match.group(1), "n"
        record = {"value": value, "line": number}
        if symbol in values:
            duplicates[symbol].append(values[symbol])
        values[symbol] = record
    return values, duplicates

def scan_kconfig_definitions(root: Path):
    definitions = defaultdict(set)
    scanned = 0
    for path in root.rglob("Kconfig*"):
        if not path.is_file():
            continue
        if any(part in {".git", "out", "build", "tmp"} for part in path.parts):
            continue
        scanned += 1
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line in lines:
            match = DEF_RE.match(line)
            if match:
                definitions[match.group(1)].add(rel)
    return definitions, scanned

def category(symbol: str) -> str:
    groups = [
        ("GPU_KGSL", ("KGSL", "GPU", "ADRENO", "MSM_GFX")),
        ("CAMERA_MEDIA", ("CAMERA", "MSM_CAM", "MSMB_", "MSM_VIDC", "VIDEO_", "V4L")),
        ("DISPLAY_PANEL", ("FB_MSM", "MDSS", "DRM_", "DISPLAY", "BACKLIGHT", "MDP")),
        ("AUDIO_RADIO", ("SND", "SOUND", "SLIMBUS", "RADIO_", "WCD", "TFA")),
        ("WLAN_BLUETOOTH", ("WLAN", "WCNSS", "PRONTO", "CLD_", "CFG80211", "BT_", "BLUETOOTH")),
        ("TOUCH_FINGERPRINT_INPUT", ("TOUCHSCREEN", "INPUT_", "FINGER", "EGISTEC", "FPC_", "HBTP")),
        ("POWER_THERMAL_BATTERY", ("QPNP", "PMIC", "REGULATOR", "THERMAL", "BCL_", "CHARGER", "FUEL", "CPR")),
        ("REMOTE_PROCESSOR_MODEM", ("REMOTE", "RPMSG", "QCOM_SMD", "MSM_PIL", "SUBSYSTEM", "ADSP", "MODEM", "QRTR", "QMI", "SMD_", "SMEM", "SMP2P", "SMSM", "DIAG_", "RMNET", "IPA")),
        ("STORAGE_FILESYSTEM", ("MMC", "SDHCI", "UFS", "SCSI", "BLK_", "F2FS", "EXT4", "EROFS", "FUSE", "EXFAT", "NTFS")),
        ("USB_CONNECTIVITY", ("USB_", "USB", "TYPEC", "NFC", "I2C_", "SPI_")),
        ("SECURITY_CRYPTO", ("QSEECOM", "QTEE", "CRYPTO", "SECURITY", "SELINUX", "ICE", "VERITY")),
        ("SCHED_POWER_MGMT", ("CPU_FREQ", "CPU_IDLE", "SCHED_", "WALT", "MSM_PM", "MSM_PERFORMANCE", "DEVFREQ", "ENERGY_MODEL")),
        ("DEBUG_DIAGNOSTICS", ("DEBUG", "KGDB", "TRACING", "FTRACE", "IPC_LOG", "MSM_TZ_LOG", "RDBG", "KALLSYMS")),
    ]
    for name, prefixes in groups:
        if any(symbol.startswith(prefix) for prefix in prefixes):
            return name
    return "GENERAL_KERNEL"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--donor-config", required=True, type=Path)
    parser.add_argument("--gki-config", required=True, type=Path)
    parser.add_argument("--fragment", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    for path in (args.source_root, args.donor_config, args.gki_config, args.fragment):
        if not path.exists():
            raise SystemExit(f"required input does not exist: {path}")

    donor, donor_duplicates = parse_config(args.donor_config)
    gki, _ = parse_config(args.gki_config)
    fragment, _ = parse_config(args.fragment)
    definitions, scanned = scan_kconfig_definitions(args.source_root)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "donor-config-symbol-inventory.csv"
    rows = []
    counts = Counter()
    group_counts = defaultdict(Counter)

    for symbol in sorted(donor):
        defined = symbol in definitions
        in_fragment = symbol in fragment
        in_gki = symbol in gki
        if in_fragment:
            status = "SELECTED_IN_MINIMAL_DEEN_FRAGMENT"
        elif not defined:
            status = "NO_KCONFIG_DEFINITION_FOUND_IN_ACK_TREE"
        elif in_gki:
            status = "DEFINED_AND_EXPLICIT_IN_GKI_BASELINE"
        else:
            status = "DEFINED_BUT_NOT_SELECTED_IN_MINIMAL_FRAGMENT"

        group = category(symbol)
        counts[status] += 1
        group_counts[group][status] += 1
        rows.append({
            "symbol": symbol,
            "donor_value": donor[symbol]["value"],
            "donor_line": donor[symbol]["line"],
            "ack_kconfig_definition_found": "yes" if defined else "no",
            "definition_files": ";".join(sorted(definitions.get(symbol, ()))),
            "gki_defconfig_explicit": gki.get(symbol, {}).get("value", "not-explicit"),
            "deen_minimal_fragment": fragment.get(symbol, {}).get("value", "not-selected"),
            "classification": status,
            "review_category": group,
            "donor_duplicate_assignments": len(donor_duplicates.get(symbol, ())),
        })

    fieldnames = [
        "symbol", "donor_value", "donor_line", "ack_kconfig_definition_found",
        "definition_files", "gki_defconfig_explicit", "deen_minimal_fragment",
        "classification", "review_category", "donor_duplicate_assignments"
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    undefined_fragment = sorted(symbol for symbol in fragment if symbol not in definitions)
    fragment_not_y = sorted(symbol for symbol, record in fragment.items() if record["value"] != "y")

    report = [
        "# Deen 4.19 donor configuration — ACK 5.15 symbol inventory",
        "",
        "## Scope and interpretation",
        "",
        "This is a read-only symbol-definition inventory. It does not copy or enable donor options.",
        "A symbol marked as defined only means a config/menuconfig definition was found in a Kconfig file in the checked-out ACK source tree. It does not prove that dependencies resolve, that the driver is compatible with Deen, or that firmware/userspace ABI is available.",
        "A symbol with no definition found is not carried into ACK 5.15 by this audit. It may be a downstream/vendor-only option, renamed option, or removed feature; each requires source-level investigation.",
        "",
        "## Inputs",
        "",
        f"- Kconfig files scanned: **{scanned}**",
        f"- Donor unique CONFIG symbols: **{len(donor)}**",
        f"- Donor duplicate-assignment symbols: **{len(donor_duplicates)}**",
        f"- Minimal fragment symbols: **{len(fragment)}**",
        "",
        "## Donor symbol classification",
        "",
        "| Classification | Count |",
        "|---|---:|",
    ]
    for name, count in counts.most_common():
        report.append(f"| {name} | {count} |")
    report += [
        "",
        "## Review category distribution",
        "",
        "| Category | Donor symbols | No Kconfig definition | Defined but not in minimal fragment | Selected in minimal fragment |",
        "|---|---:|---:|---:|---:|",
    ]
    for group in sorted(group_counts):
        c = group_counts[group]
        report.append(
            f"| {group} | {sum(c.values())} | "
            f"{c['NO_KCONFIG_DEFINITION_FOUND_IN_ACK_TREE']} | "
            f"{c['DEFINED_BUT_NOT_SELECTED_IN_MINIMAL_FRAGMENT']} | "
            f"{c['SELECTED_IN_MINIMAL_DEEN_FRAGMENT']} |"
        )
    report += [
        "",
        "## Minimal fragment integrity",
        "",
        f"- Fragment symbols without any ACK Kconfig definition: **{len(undefined_fragment)}**",
        f"- Fragment symbols not explicitly set to y: **{len(fragment_not_y)}**",
    ]
    if undefined_fragment:
        report += ["", "Undefined fragment symbols:"] + [f"- {s}" for s in undefined_fragment]
    if fragment_not_y:
        report += ["", "Fragment values other than y:"] + [f"- {s}={fragment[s]['value']}" for s in fragment_not_y]

    report += [
        "",
        "## Review rules",
        "",
        "1. Keep the existing 20-symbol minimal fragment unchanged unless a specific enabled DTS node or proven boot dependency requires a change.",
        "2. Do not copy the 4.19 vendor defconfig wholesale.",
        "3. For each donor symbol not selected in the minimal fragment, inspect its ACK 5.15 Kconfig definition, dependencies, driver source, DT binding, firmware interface and Android 14 userspace ABI before deciding whether to add, replace or defer it.",
        "4. Treat prefix-based review categories as triage hints only; they are not semantic driver mappings.",
        "5. Vendor KGSL, legacy camera/audio techpacks, Wi-Fi, NFC, fingerprint, touch/display and thermal/power policy remain separate workstreams.",
        "6. The final device defconfig must be resolved with olddefconfig, checked for dropped symbols and then compiled; this report alone cannot approve a symbol.",
        "",
        "## Outputs",
        "",
        "- donor-config-symbol-inventory.csv: per-symbol evidence and first-level classification.",
        "- deen-config-audit.md: this summary.",
        "- The workflow separately archives resolved.config, savedefconfig, merge.log and the fragment.",
        "",
    ]
    (args.output_dir / "deen-config-audit.md").write_text("\n".join(report), encoding="utf-8")

    if undefined_fragment or fragment_not_y:
        print("ERROR: minimal fragment integrity check failed", file=sys.stderr)
        return 2
    print(f"PASS: inventoried {len(donor)} donor symbols; {len(undefined_fragment)} undefined fragment symbols")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
