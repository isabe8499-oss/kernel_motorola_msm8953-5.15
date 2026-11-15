# Motorola One Deen — Linux 5.15 kernel port

Independent clean kernel bring-up for Motorola One Deen (XT1941 series, Qualcomm MSM8953, ARM64), targeting Android 14.

## Project status

**ACK source import and selected Qualcomm object smoke passed. A generic GKI ARM64 Image plus both Deen PVT DTB candidates were successfully built in CI using ThinLTO + CFI (run 43684266664). Full LTO final validation, clean full-tree DTS schema validation, a Deen-specific device config, boot-image packaging and hardware validation remain open.**

Existing Linux 3.18.140 and 4.19.325 repositories remain read-only donors.

## Source branches

- ACK source: `upstream/android14-5.15-lts`
- Deen bring-up base: `deen/bringup-ack515-base`
- Pinned ACK commit: `5cb316cf9d39318326075731e4e0c39b725d9c99`
- Kernel version at imported tip: Linux 5.15.223
- Device donor: `isabe8499-oss/kernel_motorola_msm8953-22`, branch `4.19.325-WIP`, tip `b7ef28b2acd6a61a4d890b87e57e0d5de6c93c4e`.
- Legacy reference: `isabe8499-oss/kernel_motorola_msm8953`, branch `lineage-18.1`, tip `1f700e4c2e31c435358e7531dfc0c2e41e2a2684`.

The import traversed 63,852 first-parent commits in 64 pushes. Both permanent refs are identical to the pinned upstream commit. The independent report `documentation/ACK_IMPORT_VERIFICATION.md` records successful remote ref checks and `git fsck --full`.

## Hardware-port findings

ACK 5.15 already contains MSM8953 GCC clock, pinctrl, SDHCI, USB HS PHY, remoteproc, SMD RPM and TSENS driver support. The pinned ACK did not contain the MSM8953/PM8953 Device Tree base; unchanged Linux v6.1 copies of `msm8953.dtsi` and `pm8953.dtsi` are now on the isolated `deen/dts-bringup` branch. A minimal Deen board foundation and separate PVT1/PVT2 candidates are present there. CI run 43620086484 compiled the generated base fixture and both board DTBs, passed the Qualcomm ARM/RPM binding checks, and compiled the backported MSM8953 RPM power-domain driver. The current board DTS contains the QSEE 32 MiB reservation, PM8953 RPM rails, volume keys and primary eMMC.

Mainline Linux added an initial Motorola Deen DTS in September 2026. It is a useful reference for generic bindings, but only describes an initial subset of hardware and depends on a much newer MSM8953 DTS than the 5.15 branch. See `documentation/DEEN_MAINLINE_DTS_AUDIT.md` before adding device-tree files. The provisional boot-image contract and device-side evidence gate are documented in `documentation/BOOT_CONTRACT_AUDIT.md`; the no-write engineering gates are consolidated in `documentation/BRINGUP_GATES.md`.

The 4.19 donor has PVT1 and PVT2 DTS variants with board IDs `0x4D 0xC100` and `0x4D 0xC200`. The actual revision in the handset remains to be identified; do not select or flash a DTB based only on XT1941-3.

## Engineering rules

1. Preserve upstream ACK history and record provenance for every imported patch.
2. Keep DTS, config, SoC glue and peripheral ports isolated and reviewable.
3. Do not carry SUSFS, NoMount, KernelSU, BakaSU, Magisk or root/hiding modifications into the clean baseline.
4. A successful compile is not proof of bootability or hardware compatibility.
5. Require source SHA, build logs, resolved config, artifact hashes, DTB validation and rollback instructions for device tests.
6. Never flash an unverified image; keep a known-good boot image and recovery route.

A generic GKI Image and PVT1/PVT2 candidate DTBs exist as verified CI artifacts, but this is not a Deen-specific production kernel. No final Deen defconfig, DTBO/boot image, or runtime-validated vendor driver set exists yet. The DTBs compile, but full-tree schema validation remains on HOLD due to 160 diagnostics; neither DTB is approved for flashing.
