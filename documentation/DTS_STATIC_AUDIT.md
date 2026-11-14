# Deen DTS static audit — initial PVT candidates

Audit date: 2026-11-14  
Branch: `deen/dts-bringup`

## Files checked

| File | Blob SHA-1 | Size |
|---|---|---:|
| `arch/arm64/boot/dts/qcom/msm8953.dtsi` | `6b992a6d56c16d5151785df04fa2053c67ee7fad` | 28,216 bytes |
| `arch/arm64/boot/dts/qcom/pm8953.dtsi` | `a1d36f9ebbd259e41a80e3af516d9a044419afe0` | 1,983 bytes |
| `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi` | `68f287263619cf32dd6d0adf182edce259a38461` | 4,182 bytes |
| `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt1.dts` | `f5b97d8e3d855aca47ba511a0f2d0ef9d413f513` | 474 bytes |
| `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dts` | `c0fcd9d9c9c4c33bc46d303d564aae85f84613a3` | 474 bytes |

## Binding compatibility

The ACK 5.15 `Documentation/devicetree/bindings/arm/qcom.yaml` predates the MSM8953 Deen compatible. The bring-up branch adds the minimal `motorola,deen` + `qcom,msm8953` pair, based on mainline commit `51c5d61ba73bde54d7900276cb1c0e37d416adfb`. This is a limited schema addition; it does not replace the old binding file.

## Reserved-memory layout

The Deen common DTSI now moves QSEE to the mainline/donor Deen region at 0x84300000 (32 MiB), deletes the overlapping inherited 0x85b00000 (8 MiB) region and removes the initial continuous-splash reservation at 0x90001000. The complete address/size arithmetic and deferred vendor memory regions are recorded in `documentation/DEEN_MEMORY_LAYOUT_AUDIT.md`. The DTC workflow must validate the absolute reserved-memory node deletion syntax.

## Power-domain support backport

The v6.1 MSM8953 DTSI references `MSM8953_VDDCX` and a `qcom,msm8953-rpmpd` provider. The ACK 5.15 baseline lacked those seven power-domain IDs and the matching rpmpd driver descriptor. The Deen branch now carries the narrowly scoped v6.1 backport in `include/dt-bindings/power/qcom-rpmpd.h` and `drivers/soc/qcom/rpmpd.c`, plus the `qcom,msm8953-rpmpd` compatible in `Documentation/devicetree/bindings/power/qcom,rpmpd.yaml`. The ACK smoke compiles `drivers/soc/qcom/rpmpd.o`; DTS validation will include this schema.

## Static phandle result

- Label definitions found across the five files: **137**
- Phandle references found: **77**
- Unresolved references: **0**
- PM8953 regulator labels defined locally: S1, S3, S4, L1–L3, L5–L13, L15–L17, L19, L22 and L23.
- The board wrappers contain distinct vendor board IDs:
  - PVT1: `0x4D 0xC100`
  - PVT2: `0x4D 0xC200`

The static check resolves references within the five source files and verifies that the two board wrappers include the shared DTSI. It does not run the C preprocessor, dtc, dt-schema, Kbuild or a hardware boot. A zero-unresolved-label result is not a DTB compile pass.

## Current enabled hardware scope

The common file currently:
- Includes the v6.1 MSM8953 SoC and PM8953 PMIC descriptions.
- Defines the VPH fixed supply.
- Adds GPIO85 Volume Up and enables PM8953 resin as Volume Down.
- Adds the PM8953 SMD RPM regulator table adapted from the mainline Deen board DTS.
- Enables only `sdhc_1` (non-removable primary eMMC) and maps VMMC/VQMMC to PM8953 L8/L5.

It intentionally does not enable SDHC2, USB, remote processors, NFC, display, touchscreen, GPU/KGSL, camera, audio, WLAN, Bluetooth, fingerprint or sensors.

## Open blockers

1. CI/Kbuild compilation of the synthetic base fixture and both PVT DTBs is pending.
2. `dt-doc-validate` and targeted `dt-validate` using the processed Qualcomm ARM/RPM schemas are pending.
3. Device-side stock DTB/bootloader evidence is required to identify PVT1 vs PVT2.
4. Deen QSEE memory override is now drafted at 0x84300000/32 MiB; the inherited 0x85b00000 QSEE reservation and 0x90001000 continuous-splash reservation are deleted. The new DTC smoke must validate these overrides and ensure no overlap. Ramoops/TZ log/watchdog memory remains deferred until the exact DRAM map and 5.15 driver bindings are checked.
5. UART console route must be confirmed before enabling.
6. The eMMC and PMIC electrical configuration has not been tested on hardware.

No DTB from this branch is approved for flashing.
