# Build and CI design

## Reproducibility

- Pin the exact ACK commit and LLVM/Clang toolchain version; never build from a moving branch head.
- Keep source and output directories separate.
- Preserve the resolved .config, source SHA, host/target compiler versions, command line and full build logs.
- Generate SHA-256 manifests for every Image, DTB/DTBO, module archive and packaged image.
- Fail when an expected artifact is absent, empty or has an unexpected format.

## CI phases

1. **Source gate — PASS:** exact ACK SHA, both permanent ref identities, staging cleanup and git fsck --full are recorded in ACK_IMPORT_VERIFICATION.md.
2. **ACK config/object smoke — PASS:** gki_defconfig, olddefconfig, 10 MSM8953/PMIC/SPMI/RPM/SDHCI/GPIO-key objects compiled using Clang/LLD 18. See `ACK_BASE_CONFIG_SMOKE.md`.
3. **DTS validation — compile/schema PASS:** CI run 43620086484 compiled the synthetic base fixture and both PVT1/PVT2 candidates; `dt-doc-validate`, schema generation and targeted `dt-validate` passed. This is not a boot or runtime test.
4. **SoC/board validation:** add storage, regulators, clocks, pinctrl, thermal and serial console in a dependency-ordered way.
5. **Kernel build — current gate:** CI run 43621721595 is linking the full arm64 Image with generic GKI configuration plus MSM8953 platform options and both PVT candidate DTBs. It is not yet the final Deen defconfig.
6. **Boot integration:** disabled until the target ROM's boot/vendor_boot/dtbo layout is measured and the rollback path is tested.

## Toolchain

The 4.19 donor's build script is useful as a reference, but its toolchain settings are not automatically authoritative for ACK 5.15. The initial smoke workflow pins LLVM/Clang 18 and uses the exact ACK commit. Any later full build must retain the exact compiler identity and artifact checksums.

## Runner constraints

GitHub-hosted standard runners may not have sufficient disk or time for repeated full Android kernel builds. The initial config/object smoke is deliberately narrow. Measure free disk before full builds; use shallow fetches for validation where full history is not needed. Do not delete arbitrary tools or imply that disk cleanup creates capacity that is not available.

## Current state

- Full ACK source history: imported and integrity-verified.
- MSM8953 GCC and pinctrl drivers: present in ACK and targeted by the object smoke.
- Deen base/board DTSI and PVT1/PVT2 candidates: compiled and schema-validated in CI; actual board revision, runtime behavior and flash packaging remain unverified.
- Deen defconfig, DTBO and boot image: not yet created. A generic GKI Image smoke is currently running; it must pass before the Deen-specific defconfig stage.
- No device flashing is authorized before the boot layout, correct PVT board ID and rollback path are recorded.
