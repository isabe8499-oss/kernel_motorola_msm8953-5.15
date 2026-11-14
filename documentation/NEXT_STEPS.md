# Next engineering steps

## Gate 0 — source import

- [x] Pin official ACK source: `android14-5.15-lts`, commit `5cb316cf9d39318326075731e4e0c39b725d9c99`.
- [x] Publish both permanent refs at the exact pinned SHA.
- [x] Record 63,852 first-parent commits, 1,092,253 reachable commits and 64 incremental pushes.
- [x] Verify the two refs against the pinned SHA and confirm staging ref absence.
- [x] Run `git fsck --full`; report PASS in `documentation/ACK_IMPORT_VERIFICATION.md`.

## Gate 1 — ACK base configuration and compiler smoke

1. Run `gki_defconfig` and `olddefconfig` on the pinned tree.
2. Enable only the existing MSM8953 GCC and pinctrl drivers under Kconfig dependency checks.
3. Compile `gcc-msm8953.o` and `pinctrl-msm8953.o` with a pinned LLVM toolchain.
4. Preserve the resolved config, compiler version, source revision, logs and object hashes.

## Gate 2 — Deen hardware identity and boot contract

1. Identify whether the handset uses PVT1 (`0x4D 0xC100`) or PVT2 (`0x4D 0xC200`); do not select a DTB from model name alone.
2. Record the currently booted Android 12 boot image layout and intended Android 14 ROM's boot/vendor_boot/dtbo format, header version, page size, offsets, cmdline and AVB expectations.
3. Preserve a known-good boot image and tested recovery method before any flash test.

## Gate 3 — MSM8953 Device Tree foundation

1. Use `documentation/DEEN_MAINLINE_DTS_AUDIT.md` to select the minimum MSM8953/PMIC nodes to backport to ACK 5.15.
2. Port and compile the SoC DTS, PM8953/PMI8950 nodes and Deen board nodes; resolve every external phandle.
3. Preserve PVT1/PVT2 as separate board candidates until hardware revision is identified.
4. Run dtc and schema checks; review warnings and verify memory/reserved-memory, regulators, clocks, pinctrl, interrupts and eMMC.

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
