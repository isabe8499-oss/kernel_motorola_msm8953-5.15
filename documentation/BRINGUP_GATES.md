# Motorola One Deen — engineering gates

Audit date: 2026-11-14
Target: Motorola One XT1941-3 / MSM8953 / ARM64
Android target: AOSPA Android 14
Kernel base: Android Common Kernel 5.15 LTS

## Gate A — upstream source integrity: PASS

- Upstream: android14-5.15-lts
- Pinned SHA: 5cb316cf9d39318326075731e4e0c39b725d9c99
- First-parent commits: 63,852
- Reachable commits: 1,092,253
- Incremental pushes: 64
- Both permanent refs match the pinned SHA.
- Temporary staging ref is absent.
- Full git fsck --full passed.
- Evidence: documentation/ACK_IMPORT_VERIFICATION.md.

## Gate B — ACK Kconfig and SoC object smoke: PASS

CI run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43612819332

The pinned ACK 5.15 GKI configuration retained the requested MSM8953 GCC/pinctrl, SPMI PMIC arbiter/MFD, SMD RPM/RPMPD, regulator, SDHCI MSM and GPIO-key symbols. Ten selected objects compiled under Clang/LLD 18. Resolved configuration and SHA-256 object hashes are in documentation/ACK_BASE_CONFIG_SMOKE.md.

This proves selected Kconfig and object compilation, not a complete kernel link.

## Gate C — Deen DTS syntax and binding smoke: PASS

CI run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43620086484

Tested source branch commit: d86ecf2fa95fe3635b4ffc606fdd39b048760d1e.

The run generated:
- A synthetic MSM8953/PM8953 base-only fixture DTB.
- Deen PVT1 candidate DTB with board ID 0x4D 0xC100.
- Deen PVT2 candidate DTB with board ID 0x4D 0xC200.

dt-doc-validate, processed schema generation and targeted dt-validate returned exit code 0. The MSM8953 RPM power-domain provider object from the Deen branch also compiled.

Evidence and DTB hashes are in documentation/DEEN_DTS_BASE_SMOKE.md; source inventory and static audit are in documentation/DTS_STATIC_AUDIT.md.

The tested DTS blobs (common board DTSI, both PVT wrappers, rpmpd driver and Qualcomm ARM binding) were compared with the current deen/dts-bringup branch and are unchanged. Subsequent changes on that branch are documentation-only.

## Gate D — full kernel Image link: RUNNING / NOT YET APPROVED

Run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43621721595 (currently step 6: full build).

It uses generic GKI configuration plus the audited MSM8953 platform/PMIC/eMMC options, then attempts to link the complete ARM64 Image and build both Deen candidate DTBs. This is not the final Deen defconfig and not a boot image. The report is documentation/DEEN_IMAGE_SMOKE.md once the job completes.

## Gate E — identify actual handset hardware revision: BLOCKED ON DEVICE EVIDENCE

The clean 4.19 donor contains:
- PVT1: 0x4D 0xC100
- PVT2: 0x4D 0xC200

The physical revision in the XT1941-3 handset is unknown. Do not choose a production DTB based on the model number alone. Use the read-only bootloader queries in documentation/HARDWARE_IDENTIFICATION_GATE.md to collect only product, board and hwrev. Do not send full fastboot getvar all, because it can include device identifiers.

## Gate F — Deen-specific defconfig and device tree completion: NOT STARTED

Must wait for Gate D and Gate E. Then:
1. Create a Deen defconfig from the pinned ACK Kconfig; never transplant the 4.19 defconfig wholesale.
2. Audit the full reserved-memory, console, clocks, pinctrl, regulators, eMMC, thermal and remote-processor dependency graph.
3. Port subsystems in isolated patches and compile/test each group.
4. Verify proprietary firmware and userspace ABI assumptions against the Android 12 vendor baseline and target Android 14 ROM.

## Gate G — boot image integration and device validation: BLOCKED

Do not produce or flash a boot image until:
- The actual PVT variant is identified.
- The target AOSPA Android 14 boot contract is measured, including boot/vendor_boot/dtbo/vbmeta partitions and image header.
- A known-good boot/recovery rollback image exists.
- Full Image, exact DTB and packaging metadata are reproducible and reviewed.

No CI result so far authorizes flashing. No physical device write has been performed by this project.
