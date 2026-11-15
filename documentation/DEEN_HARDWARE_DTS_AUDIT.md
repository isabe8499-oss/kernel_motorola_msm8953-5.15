# Deen hardware and Device Tree porting audit

Date: 2026-11-14

## Scope and evidence

This audit compares the clean Motorola Deen 4.19.325 donor (`kernel_motorola_msm8953-22`, branch `4.19.325-WIP`) with the Android Common Kernel 5.15 LTS base and the upstream Linux v6.1 Motorola Deen Device Tree.

The ACK source import is independently verified at commit `5cb316cf9d39318326075731e4e0c39b725d9c99`. The Deen bring-up branch is a separate working branch; this report does not authorize flashing any DTB.

## Board identity

The clean 4.19 donor contains two board candidates:

- PVT1: `qcom,board-id = <0x4D 0xC100>`
- PVT2: `qcom,board-id = <0x4D 0xC200>`

The product model XT1941-3 / codename Deen does not, by itself, prove which PVT board ID is present. Do not select one candidate for a device build until the actual handset's bootloader hardware revision and stock DTB board ID are checked. Capture `fastboot getvar hwrev` and inspect the stock boot/vendor_boot DTB (or the device's live FDT where available). The PVT1/PVT2 DTS files are candidates only.

## Memory map decisions

### Kept in the 5.15 bring-up base

The upstream Linux v6.1 Motorola Deen DTS defines a QSEE reservation at:

- base: `0x84300000`
- size: `0x02000000` (32 MiB)
- `no-map`

The current minimal Deen common DTSI moves the inherited anonymous MSM8953 reservation at `0x85b00000` out of the way, removes the inherited continuous-splash reservation at `0x90001000`, and creates the QSEE reservation at the upstream Deen address and size. This matches the upstream Deen board DTS layout, but still requires device-level validation.

### Deliberately not copied from the 4.19 donor

The 4.19 Deen overlay also changes `other_ext_mem` to `0x84300000 / 0x02500000` (37 MiB), changes a vendor `qcom_seecom` node, and adds ramoops, TZ log and watchdog CPU-context reservations. These are not copied into the 5.15 tree yet:

- the old `other_ext_mem` and QSEE regions overlap at the same base address and need the exact vendor driver contract before being represented in a modern DTS;
- the old `TZLOG_BCK_*` and `WDOG_CPUCTX_*` symbols are vendor-tree-specific and have not been established in the upstream 5.15 binding/source;
- the ramoops region at `0xef000000` needs confirmation against the target RAM map and stock DTB;
- vendor-only QSEE/secure-app nodes must not be revived merely because they existed in the 4.19 downstream tree.

This is intentional risk reduction, not a claim that these legacy facilities are unnecessary.

## Current bring-up scope

The minimal common DTS currently contains only board-independent foundations:

- upstream MSM8953 and PM8953 SoC descriptions;
- Deen QSEE reserved-memory adjustment based on upstream v6.1;
- fixed VPH supply;
- volume-up GPIO key and PMIC resin volume-down key;
- PM8953 RPM regulator supply mapping;
- primary eMMC controller enablement with its regulator supplies.

It does not yet enable display, touchscreen, camera, fingerprint, NFC, WLAN, Bluetooth, audio, sensors, thermal policy, or the full vendor memory/secure-world stack.

## Build and validation evidence

The ACK configuration smoke has compiled the MSM8953 GCC, pinctrl, SMD RPM and RPM power-domain objects, plus PMIC, regulator, SDHCI and GPIO-key objects. The backported `drivers/soc/qcom/rpmpd.o` in the Deen working tree also compiled successfully in the DTS smoke job.

The three DTS candidates (a CI-only base fixture, PVT1 and PVT2) compiled with Clang 18 in CI run 43623081943; the Deen branch's backported MSM8953 `rpmpd.o` also compiled. The validator processes returned exit code 0, but the PVT logs contain 160 diagnostic lines; full-tree schema acceptance is HOLD (see `documentation/DTS_SCHEMA_DIAGNOSTIC_TRIAGE.md`).

Subsequently, CI run 43684266664 successfully linked a generic GKI ARM64 Image using ThinLTO+CFI and rebuilt both PVT DTB candidates. The uploaded artifact was independently downloaded and its Image/DTB SHA-256 values were checked. This remains a syntax/build feasibility result, not clean schema acceptance, a physical board-ID match, an electrical test or a boot test.

## Next gated steps

1. Generic GKI Image and both PVT candidate DTBs now build with ThinLTO+CFI (run 43684266664); keep Full LTO as a separate gate requiring a higher-memory runner.
2. Verify the handset PVT/board ID using the read-only gate in `documentation/HARDWARE_IDENTIFICATION_GATE.md`.
3. Compare the Deen donor's display, touchscreen, storage, regulator, thermal, NFC, Wi-Fi, camera, audio and fingerprint nodes against upstream 5.15 drivers and bindings one subsystem at a time.
4. Port only nodes whose drivers and dependencies exist or have an independently reviewed backport.
5. Create a Deen-specific defconfig from the pinned ACK Kconfig and run full Image/DTB/module builds.
6. Only after boot-image integration and a tested recovery path exist should device boot testing be considered.

No SUSFS, NoMount, KernelSU, Magisk or root integration is part of this base.
