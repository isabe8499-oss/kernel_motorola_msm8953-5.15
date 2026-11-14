# Next engineering steps

## Gate 0 — source import

- [x] Pin official ACK source: `android14-5.15-lts`, commit `5cb316cf9d39318326075731e4e0c39b725d9c99`.
- [x] Publish both permanent refs at the exact pinned SHA.
- [x] Record 63,852 first-parent commits, 1,092,253 reachable commits and 64 incremental pushes.
- [x] Verify the two refs against the pinned SHA and confirm staging ref absence.
- [x] Run `git fsck --full`; report PASS in `documentation/ACK_IMPORT_VERIFICATION.md`.

## Gate 1 — ACK base configuration and controller-object smoke — PASS

- `gki_defconfig` and `olddefconfig` passed on the pinned ACK revision.
- MSM8953 GCC/pinctrl, SPMI PMIC arbiter/MFD, SMD RPM/RPMPD, both regulator paths, SDHCI MSM and GPIO keys resolved as built-in.
- Ten selected objects compiled with Clang/LLD 18. Their hashes and the resolved config are recorded in `documentation/ACK_BASE_CONFIG_SMOKE.md`.
- This is not a full kernel link; the next CI gate builds the complete `Image`.

## Gate 2 — Deen hardware identity and boot contract

1. Identify whether the handset uses PVT1 (`0x4D 0xC100`) or PVT2 (`0x4D 0xC200`); do not select a DTB from model name alone.
2. Use documentation/BOOT_CONTRACT_AUDIT.md as a provisional reference, then capture the exact device's boot_a/boot_b, vendor_boot, dtbo, recovery and vbmeta partition inventory and unpack the current Android 12 boot image. Do not rely on old BoardConfig values alone.
3. Preserve a known-good boot image and tested recovery method before any flash test.

## Gate 3 — MSM8953 Device Tree foundation — COMPILE/SCHEMA PASS

- The isolated `deen/dts-bringup` branch carries the v6.1 MSM8953/PM8953 base plus a shared Deen board DTSI and separate PVT1/PVT2 wrappers.
- CI run 43620086484 compiled the base fixture and both candidate DTBs; `dt-doc-validate`, schema generation and targeted `dt-validate` all returned exit 0.
- The QSEE 32 MiB reservation and conflicting inherited QSEE/continuous-splash reservations were checked by the same DTB compile.
- Both PVT candidates remain available until the handset's hardware revision is read from the bootloader. Neither is approved for flashing.
- Runtime regulator/eMMC sequencing, memory behavior, bootloader matching and serial console still require device-specific evidence.

## Gate 4 — Minimal Deen kernel configuration

1. Generate a fresh Deen config from the pinned ACK Kconfig; do not transplant the 4.19 defconfig.
2. Enable storage, clocks, pinctrl, regulators, thermal and serial console dependencies first.
3. Compare requested symbols with `olddefconfig` output and fail on unknown or silently dropped options.

## Gate 5 — Peripheral ports and device tests

- Add USB/remote processors/NFC after static and firmware audits.
- Port display/touch, then GPU/KGSL and camera/audio as isolated workstreams.
- Build Image and DTBs with pinned toolchain; archive config, logs and hashes.
- Integrate only after boot layout is measured and packaging is validated.
- First boot requires a known-good rollback image; test storage, display, touch and thermal independently before other hardware.

No donor tree is to be modified. SUSFS, NoMount and all root/hiding features remain outside this clean baseline.
