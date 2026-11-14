# Next engineering steps

## Gate 0 — source import

- [x] Pin official ACK source: `android14-5.15-lts`, commit `5cb316cf9d39318326075731e4e0c39b725d9c99`.
- [x] Publish both permanent refs at the exact pinned SHA.
- [x] Record import counts: 63,852 first-parent commits, 64 incremental pushes.
- [ ] Confirm `documentation/ACK_IMPORT_VERIFICATION.md` is generated after full `git fsck --full` and remote-ref read-back.

## Gate 1 — ACK base validation

1. Run `gki_defconfig` and `olddefconfig` on the pinned tree.
2. Enable only the MSM8953 clock and pinctrl drivers under Kconfig dependency checks.
3. Compile `gcc-msm8953.o` and `pinctrl-msm8953.o` with a pinned LLVM toolchain.
4. Preserve the resolved config, compiler versions, build logs and hashes in CI.

## Gate 2 — Deen hardware identity and boot contract

1. Identify whether the handset is PVT1 (`0x4D 0xC100`) or PVT2 (`0x4D 0xC200`); do not select a DTB from model name alone.
2. Record the currently booted Android 12 boot image layout and the intended Android 14 ROM's boot/vendor_boot/dtbo format, header version, page size, offsets, cmdline and AVB expectations.
3. Preserve a known-good boot image and recovery method before any flash test.

## Gate 3 — Device Tree foundation

1. Complete the include/dependency inventory for the donor base `msm8953.dtsi`, common Motorola DTSI and Deen fragments.
2. Port the SoC DTS into the ACK Qualcomm DTS layout, normalize bindings and remove obsolete vendor-only properties.
3. Port Deen PVT board files and enable exactly the verified board revision.
4. Compile DTBs with schema checks and review all warnings before adding peripheral drivers.

## Gate 4 — Minimal Deen kernel configuration

1. Generate a fresh Deen config from the pinned ACK Kconfig; do not transplant the 4.19 defconfig.
2. Add storage, clocks, pinctrl, regulators, thermal and serial console dependencies first.
3. Compare requested symbols with `olddefconfig` output and fail on unknown or silently dropped options.

## Gate 5 — Peripheral ports and device testing

- Port display/touch, then GPU/KGSL and camera/audio as isolated workstreams.
- Build Image and DTBs with pinned toolchain; archive config, logs and hashes.
- Integrate only after boot layout is measured and packaging is validated.
- First boot requires a known-good rollback image; test storage, display, touch and thermal independently before other hardware.

No donor tree is to be modified. SUSFS, NoMount and all root/hiding features remain outside this clean baseline.
