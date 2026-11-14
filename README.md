# Motorola One Deen — Linux 5.15 kernel port

Independent clean kernel bring-up for Motorola One Deen (XT1941 series, Qualcomm MSM8953, ARM64), targeting Android 14.

## Project status

**Source import completed; Deen bring-up has not started and there is no bootable kernel yet.**

The project control branch `main` contains documentation and CI. The full Android Common Kernel source history is available on the permanent branches below. Existing Linux 3.18.140 and 4.19.325 repositories remain read-only donors.

## Source branches

- ACK source: `upstream/android14-5.15-lts`
- Deen bring-up base: `deen/bringup-ack515-base`
- Pinned ACK commit: `5cb316cf9d39318326075731e4e0c39b725d9c99`
- Kernel version at imported tip: Linux 5.15.223
- Device donor: `isabe8499-oss/kernel_motorola_msm8953-22`, branch `4.19.325-WIP`, audited tip `b7ef28b2acd6a61a4d890b87e57e0d5de6c93c4e`.
- Legacy reference: `isabe8499-oss/kernel_motorola_msm8953`, branch `lineage-18.1`, audited tip `1f700e4c2e31c435358e7531dfc0c2e41e2a2684`.

The ACK history import traversed 63,852 first-parent commits and was published through 64 sequential increments. Both permanent refs compare as identical to the pinned upstream commit. The import workflow now runs a full Git object-integrity check and records its verification report before the source gate can be considered complete.

## Important hardware-port findings

The pinned ACK already contains MSM8953 GCC clock and pinctrl drivers, plus Qualcomm SDHCI and TSENS support. It does not contain the Deen/MSM8953 board DTS, the vendor KGSL tree or the legacy MSM camera stack used by the 4.19 donor. The port therefore requires a carefully normalized SoC/board DTS and separate vendor-ABI work; it is not a straight defconfig transplant.

PVT1 and PVT2 donor DTS files use board IDs `0x4D 0xC100` and `0x4D 0xC200`. The exact hardware revision in the handset must be identified before selecting the final DTB.

## Engineering rules

1. Preserve upstream ACK history and record provenance for every imported patch.
2. Keep DTS, config, SoC glue and peripheral ports isolated and reviewable.
3. Do not carry SUSFS, NoMount, KernelSU, BakaSU, Magisk or root/hiding modifications into the clean baseline.
4. A successful compile is not proof of bootability or hardware compatibility.
5. Require source SHA, build logs, resolved config, artifact hashes, DTB validation and rollback instructions for device tests.
6. Never flash an unverified image; keep a known-good boot image and recovery route.

## Repository layout

- `documentation/`: source inventory, gap audit, porting matrix, validation plan and build design
- `.github/workflows/`: source import, integrity validation and build smoke CI
- `upstream/android14-5.15-lts`: unmodified Android Common Kernel history
- `deen/bringup-ack515-base`: clean starting point for Deen-specific patches

No Deen 5.15 defconfig, DTS/DTBO, ported vendor driver or boot image has been created yet.
