# Build and CI design

## Reproducibility

- Pin the exact ACK commit and LLVM/Clang toolchain version; never build from a moving branch head.
- Keep source and output directories separate.
- Preserve the resolved `.config`, source SHA, host/target compiler versions, command line and full build logs.
- Generate SHA-256 manifests for every Image, DTB/DTBO, module archive and packaged image.
- Fail when an expected artifact is absent, empty or has an unexpected format.

## CI phases

1. **Source gate:** exact ACK SHA, both permanent ref identities, staging cleanup and `git fsck --full`.
2. **ACK config smoke:** `gki_defconfig`, `olddefconfig`, and Kconfig dependency verification.
3. **SoC object smoke:** build native ACK MSM8953 GCC and pinctrl objects before adding Deen-specific code.
4. **DTS validation:** run dtc and binding/schema checks after the base SoC and Deen DTS are ported.
5. **Kernel build:** build Image and required modules/DTBs with pinned LLVM/Clang and complete artifacts.
6. **Boot integration:** disabled until the target ROM's boot/vendor_boot/dtbo layout is measured and the rollback path is tested.

## Toolchain

The 4.19 donor's build script is useful as a reference, but its toolchain settings are not automatically authoritative for ACK 5.15. Select a version compatible with the imported ACK branch, record the exact version and checksum, and use the same toolchain in CI and local builds.

## Runner constraints

GitHub-hosted standard runners may not have sufficient disk or time for repeated full Android kernel builds. Measure free disk before the run; use shallow fetches for validation where full history is not needed. Do not delete arbitrary tools or imply that disk cleanup creates capacity that is not available.

## Current state

The source import is available in `upstream/android14-5.15-lts` and `deen/bringup-ack515-base`. The project control branch `main` holds documentation and CI. The repository does not yet contain a Deen 5.15 DTS, defconfig, ported vendor driver or bootable image.
