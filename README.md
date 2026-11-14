# Motorola One Deen — Linux 5.15 kernel port

Independent development repository for the Motorola One Deen (MSM8953, ARM64).

## Project status

**Bring-up / source-integration stage. Not a bootable kernel yet.**

This repository is kept separate from the existing Linux 3.18.140 and 4.19.325 trees. Those repositories remain read-only donors during the initial inventory and porting process.

## Source strategy

- Android Common Kernel (ACK): `https://android.googlesource.com/kernel/common`, branch `android14-5.15-lts`.
- Device-specific donor: `isabe8499-oss/kernel_motorola_msm8953-22`, branch `4.19.325-WIP`.
- Legacy reference: `isabe8499-oss/kernel_motorola_msm8953`, branch `lineage-18.1`.

The import target is pinned to `5cb316cf9d39318326075731e4e0c39b725d9c99`. The first full-history push failed with HTTP 500; GitHub's 2 GiB single-push limit is the likely cause. The import workflow has been changed to send sequential first-parent checkpoints below that limit. The full upstream history has been published to both permanent refs and both refs compare as identical to the pinned SHA. A full git fsck integrity gate is still required before Deen porting starts. Device drivers and board support are ported selectively; the 4.19 tree is not copied wholesale into ACK.

## Required engineering rules

1. Preserve upstream ACK history and identify every imported donor commit.
2. Keep device tree, defconfig, driver ports, and build-system changes isolated and reviewable.
3. Do not carry SUSFS, NoMount, KernelSU, BakaSU, Magisk, or other root/hiding modifications in the clean bring-up baseline.
4. Do not treat a successful compilation as proof of bootability or hardware compatibility.
5. Require artifact hashes, build logs, DTB verification, and a documented rollback path for every device test.
6. Never flash an unverified image. Maintain a known-good boot image and recovery path.

## Initial target

- Device family: Motorola One Deen (XT1941 series; exact board revision to verify)
- SoC family: Qualcomm MSM8953
- Architecture: ARM64
- Android target: Android 14
- Kernel target: ACK Linux 5.15

## Repository layout

- `documentation/`: source inventory, porting matrix, validation plan
- `arch/arm64/configs/`: Deen defconfig work
- `arch/arm64/boot/dts/`: Deen DTS/DTBO port
- `drivers/`, `techpack/`: selectively ported hardware support
- `.github/workflows/`: reproducible CI and static validation

## Current limitations

The initial commit contains project documentation and CI scaffolding only. It intentionally does not contain a full ACK checkout or copied kernel drivers. A complete kernel source import is a separate, large Git operation and should preserve the upstream source lineage rather than being recreated through individual file API writes.
