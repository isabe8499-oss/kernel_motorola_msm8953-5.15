# Build and CI design

## Reproducibility

- Pin the exact ACK commit and LLVM/Clang toolchain version; never build from a moving branch head.
- Keep source and output directories separate.
- Preserve the resolved .config, source SHA, host/target compiler versions, command line and full build logs.
- Generate SHA-256 manifests for every Image, DTB/DTBO, module archive and packaged image.
- Fail when an expected artifact is absent, empty or has an unexpected format.

## CI phases

1. **Source gate — PASS:** exact ACK SHA, both permanent ref identities, staging cleanup and git fsck --full are recorded in ACK_IMPORT_VERIFICATION.md.
2. **ACK config/object smoke — running by workflow:** gki_defconfig, olddefconfig, enable only MSM8953 GCC and pinctrl, then compile gcc-msm8953.o and pinctrl-msm8953.o using Clang 18. The result is recorded only after those checks pass.
3. **DTS validation:** compile the minimal MSM8953/PM8953/PMI8950 and Deen board DTS after the missing base and binding dependencies have been ported.
4. **SoC/board validation:** add storage, regulators, clocks, pinctrl, thermal and serial console in a dependency-ordered way.
5. **Kernel build:** build Image and required modules/DTBs with pinned LLVM/Clang and complete artifacts.
6. **Boot integration:** disabled until the target ROM's boot/vendor_boot/dtbo layout is measured and the rollback path is tested.

## Toolchain

The 4.19 donor's build script is useful as a reference, but its toolchain settings are not automatically authoritative for ACK 5.15. The initial smoke workflow pins LLVM/Clang 18 and uses the exact ACK commit. Any later full build must retain the exact compiler identity and artifact checksums.

## Runner constraints

GitHub-hosted standard runners may not have sufficient disk or time for repeated full Android kernel builds. The initial config/object smoke is deliberately narrow. Measure free disk before full builds; use shallow fetches for validation where full history is not needed. Do not delete arbitrary tools or imply that disk cleanup creates capacity that is not available.

## Current state

- Full ACK source history: imported and integrity-verified.
- MSM8953 GCC and pinctrl drivers: present in ACK and targeted by the object smoke.
- Deen Device Tree base and board files: not yet ported.
- Deen defconfig, Image, DTB/DTBO, modules and boot image: not yet created.
- No device flashing is authorized before the boot layout, correct PVT board ID and rollback path are recorded.
