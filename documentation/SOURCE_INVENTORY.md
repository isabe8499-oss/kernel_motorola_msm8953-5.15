# Source inventory

Audit date: 2026-11-14

## Donor A — Linux 4.19.325

Repository: https://github.com/isabe8499-oss/kernel_motorola_msm8953-22  
Branch: `4.19.325-WIP`

Relevant findings verified in the donor tree:

- Kernel Makefile reports VERSION=4, PATCHLEVEL=19, SUBLEVEL=325.
- Device configuration: `arch/arm64/configs/vendor/deen_defconfig`.
- Build script: `build.sh`.
- CI workflow: `.github/workflows/deen-kernel-build.yml`.
- Motorola Deen DTS directory: `arch/arm64/boot/dts/vendor/qcom/motorola/deen/`.
- Board DTS files: `msm8953-deen-pvt1.dts`, `msm8953-deen-pvt2.dts`.
- The Deen DTS includes Android, audio, battery, camera, display, fingerprint, GPU, NFC, pinctrl, PMIC, reserved memory, sensors, storage, thermal, touchscreen and vibrator fragments.
- Touchscreen DTS describes Novatek NVT and FocalTech FT8006U nodes.
- Display DTS references Tianma and Nova 720p panels.
- The Deen defconfig enables MSM8953, Deen machine support, Qualcomm KGSL, camera, audio, storage, USB, WLAN, NFC and related platform components.

The donor contains a separate branch `bakasu-susfs23-deen`. It is intentionally excluded from the clean baseline. A prior branch comparison found additional SUSFS 2.3 and NoMount changes there; those are not part of the selected donor base.

## Donor B — Linux 3.18.140

Repository: https://github.com/isabe8499-oss/kernel_motorola_msm8953  
Branch: `lineage-18.1`

Use as a compatibility and hardware-behavior reference, not as the 5.15 base. Compare its Deen defconfig, display/camera/touchscreen implementation and device-specific DTS fragments against the 4.19 donor and ACK.

## Upstream base

Repository: https://github.com/aosp-mirror/kernel_common  
Target branch: `android14-5.15`

The canonical upstream branch exists. The base commit SHA must be pinned and recorded before a full source import. Do not substitute an Android common branch from a different Android release.

## Source-integrity policy

- Record source URL, branch, commit SHA, license and origin for each imported component.
- Prefer upstream ACK implementations when present.
- Backport device support with minimal, isolated patches.
- Never copy build outputs, private signing keys, device secrets or generated vendor blobs into source control.
