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

## Gate 3 — MSM8953 Device Tree foundation — syntax/binary PASS; full-tree schema HOLD

- The isolated `deen/dts-bringup` branch carries the v6.1 MSM8953/PM8953 base plus a shared Deen board DTSI and separate PVT1/PVT2 wrappers.
- CI compiles the base fixture and both candidate DTBs and verifies board-ID/QSEE binary properties. The PVT schema log contains 160 diagnostic lines even though validator processes returned exit 0; full-tree schema acceptance is HOLD. See `documentation/DTS_SCHEMA_DIAGNOSTIC_TRIAGE.md`.
- The QSEE 32 MiB reservation and conflicting inherited QSEE/continuous-splash reservations were checked by the same DTB compile.
- Both PVT candidates remain available until the handset's hardware revision is read from the bootloader. Neither is approved for flashing.
- Runtime regulator/eMMC sequencing, memory behavior, bootloader matching and serial console still require device-specific evidence.

## Gate 4 — Minimal Deen kernel configuration — BASE FRAGMENT PASS

- The 20-symbol `deen-msm8953-base.fragment` was merged with ACK `gki_defconfig`, passed `olddefconfig`, and all required symbols remained enabled.
- Full donor inventory run 43699488864 classified 700 unique 4.19 symbols: 208 have no Kconfig definition in ACK 5.15; 125 are defined but not selected in the minimal fragment; 355 are explicitly represented in GKI; 12 overlap with the Deen fragment. Eight additional fragment symbols are 5.15-specific base requirements.
- Do not copy the donor defconfig wholesale. Generate the full Deen defconfig only after subsystem/firmware/ABI decisions are reviewed.

## Gate 5 — Peripheral ports and device tests

1. Remoteproc object audit PASS: run 43702964898 compiled MSS, ADSP PAS and Pronto-v3 AArch64 objects and validated the ADSP YAML document. Keep `deen/msm8953-remoteproc-backports` isolated.
2. Complete donor-to-5.15 resource mapping before DTS activation: donor modem uses `qcom,pil-q6v55-mss`; ADSP/Pronto use `qcom,pil-tz-generic`; Deen `misc.dtsi` disables the modem/ADSP/WCNSS SMP2P endpoints. See `documentation/DEEN_REMOTEPROC_INTEGRATION_AUDIT.md`.
3. Inspect stock Android 12 vendor firmware and verify MBA/MPSS, ADSP and WCNSS images, hashes and search paths. Reconcile the donor memory pools against QSEE/SMEM and the actual DRAM map; verify clocks, resets, power domains and SMEM/SMP2P routing.
4. Only after resource/firmware review, create separate MSS and ADSP DTS candidates and validate each independently. Keep WCNSS WLAN driver/HAL work separate from Pronto remoteproc.
5. Port MSM8953 QUSB2 PHY data and reconcile DWC3 schema/driver handling in a separate branch.
6. Resolve the NFC hardware conflict: donor 4.19 is NQ-NCI, while the mainline reference is PN553; verify the physical chip before choosing.
7. Port display/touch, GPU/KGSL, camera/audio, battery and thermal as isolated driver/ABI workstreams.
8. Rebuild Image/DTBs and archive exact configs/hashes after each subsystem; only then generate the full Deen defconfig. Integrate only after boot layout, PVT and a rollback image are confirmed. No flash until a known-good recovery path exists.

No donor tree is to be modified. SUSFS, NoMount and all root/hiding features remain outside this clean baseline.
