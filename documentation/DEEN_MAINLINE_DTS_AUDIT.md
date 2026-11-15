# Motorola Deen mainline Device Tree audit

Audit date: 2026-11-14

## Executive finding

A modern upstream Linux Device Tree for Motorola One Deen now exists in mainline. It is a valuable hardware-reference source, but it is not a drop-in DTS for the pinned Android Common Kernel 5.15 tree.

The DTS was added by mainline commit `b62af30ebdb4ae4ec6230c5e39eea97f65b9f5ea` on 2026-09-30:
https://github.com/torvalds/linux/commit/b62af30ebdb4ae4ec6230c5e39eea97f65b9f5ea

The matching compatible binding was added by:
https://github.com/torvalds/linux/commit/51c5d61ba73bde54d7900276cb1c0e37d416adfb

Mainline file:
- Path: `arch/arm64/boot/dts/qcom/msm8953-motorola-deen.dts`
- Blob: `4bc407e23580b007873df85c988c9a764332a851`
- Compatible: `motorola,deen`, `qcom,msm8953`
- Includes: `msm8953.dtsi`, `pm8953.dtsi`, `pmi8950.dtsi`
- Mainline binding schema recognizes the Motorola Deen compatible.

## What the mainline board DTS actually enables

The original upstream commit describes this as initial support for:
- I2C peripherals, specifically NFC (PN553)
- Power button and volume keys
- PM8953 regulators
- ADSP, MPSS and WCNSS remote processors
- USB

The patch explicitly states that MDSS supply wiring is present but display is disabled because panel dependencies are missing.

The DTS contains GPIO pin states for touchscreen reset/interrupt (GPIO64/GPIO65), but it does not instantiate the Novatek NVT or FocalTech FT8006U touchscreen nodes. It does not provide the Deen camera sensor/EEPROM/VFE configuration or a KGSL/Adreno device enablement. Do not interpret the presence of GPIO pinctrl states or MDSS supply references as working touch/display support.

Upstream patch discussion and scope:
https://git.zx2c4.com/wireguard-linux/commit/arch/arm64/boot/dts/qcom?id=b62af30ebdb4ae4ec6230c5e39eea97f65b9f5ea

## Compatibility with the pinned ACK 5.15 base

The pinned ACK source is:
- Branch: `android14-5.15-lts`
- SHA: `5cb316cf9d39318326075731e4e0c39b725d9c99`

The following DTS files are absent from that ACK tree:
- `arch/arm64/boot/dts/qcom/msm8953.dtsi`
- `arch/arm64/boot/dts/qcom/pm8953.dtsi`
- `arch/arm64/boot/dts/qcom/pmi8950.dtsi`
- `arch/arm64/boot/dts/qcom/msm8953-pinctrl.dtsi`

However, the pinned ACK already has several underlying drivers:
- MSM8953 GCC: `drivers/clk/qcom/gcc-msm8953.c`, Kconfig `MSM_GCC_8953`
- MSM8953 pinctrl: `drivers/pinctrl/qcom/pinctrl-msm8953.c`, Kconfig `PINCTRL_MSM8953`
- Qualcomm SDHCI: `drivers/mmc/host/sdhci-msm.c`
- Qualcomm USB HS PHY: `drivers/phy/qualcomm/phy-qcom-usb-hs-28nm.c`
- Qualcomm remoteproc PAS: `drivers/remoteproc/qcom_q6v5_pas.c`
- Qualcomm SMD RPM: `drivers/soc/qcom/smd-rpm.c`
- Qualcomm TSENS: `drivers/thermal/qcom/tsens.c`

This is a useful foundation: the missing work is substantially DTS/binding integration and subsystem dependency reconciliation, not the absence of every MSM8953 driver.

## Why the current mainline DTS cannot be copied directly

The earliest checked mainline SoC DTS baseline, Linux v6.1, contains:
- `msm8953.dtsi`: 1,330 lines, blob `6b992a6d56c16d5151785df04fa2053c67ee7fad`
- `pm8953.dtsi`: 91 lines, blob `a1d36f9ebbd259e41a80e3af516d9a044419afe0`
- no `pmi8950.dtsi` at the checked path
- no Motorola Deen board DTS

The current mainline `msm8953.dtsi` is 2,484 lines (blob `753167c3f861903dfe6168ea672b8e487f7e6813`). The current `pmi8950.dtsi` is a separate file (blob `5bd91a5cd1245f34ef37d98b1a2669582e84876c`).

A static phandle-label comparison of the 2026 Deen DTS against the v6.1 MSM8953/PM8953 files plus the board file itself found 12 externally referenced labels missing from that older base:
`cont_splash_mem`, `usb_dwc3_hs`, `ibb`, `lpass`, `mdss_dsi0`, `mdss_dsi0_out`, `mdss_dsi0_phy`, `mpss`, `pmi8950_wled`, `q6afedai`, `wcnss`, `wcnss_iris`.

Those are concrete backport dependencies, not reasons to paste the 2026 board file unchanged into 5.15. Their backing nodes, DT bindings, driver support and Kconfig wiring must be audited individually. The current mainline SoC DTS has evolved significantly since v6.1.

## Relationship to the existing 4.19 Deen donor

The clean donor remains:
- Repository: `isabe8499-oss/kernel_motorola_msm8953-22`
- Branch: `4.19.325-WIP`
- Tip: `b7ef28b2acd6a61a4d890b87e57e0d5de6c93c4e`

The donor has two board-specific entry points:
- PVT1: `msm8953-deen-pvt1.dts`, board ID `<0x4D 0xC100>`
- PVT2: `msm8953-deen-pvt2.dts`, board ID `<0x4D 0xC200>`

The mainline Deen DTS uses the generic compatible and does not preserve those two PVT board-ID entry points. Keep PVT1/PVT2 as separate candidates until the handset's actual hardware revision is identified. The model string XT1941-3 alone is not enough to pick a DTB.

The donor contains device details absent from the initial mainline DTS:
- Novatek NVT touchscreen at I2C 0x62
- FocalTech FT8006U at I2C 0x38
- Tianma/Nova 720p display panel references
- Deen-specific camera, EEPROM, VFE/ISPIF/CCI and flash data
- GPU OPP and bus-frequency tuning

These fragments require translation to the ACK/mainline binding model and driver/API validation. Do not simply concatenate the vendor DTSI files.

## Recommended next phase

1. Treat the 2026 mainline Deen DTS as a hardware/binding reference, not a source file to copy wholesale.
2. Use the closest compatible mainline MSM8953/PM8953 source as a donor for missing generic SoC/PMIC DTS nodes, then backport only dependencies required by the Deen board to ACK 5.15.
3. Reconcile Kconfig/Makefile and DT binding dependencies against the exact pinned ACK tree.
4. Build a minimal DTS first: memory/reserved-memory, serial console, RPM/SMD, SPMI/PMIC, GCC, pinctrl and eMMC.
5. Keep both donor PVT board IDs until the handset board revision is confirmed.
6. Add USB/NFC/remote processors after the minimal tree compiles; display/touch, camera, audio and GPU remain separate later workstreams.

Selected v6.1 `msm8953.dtsi` and `pm8953.dtsi` files have been copied unchanged into the isolated `deen/dts-bringup` branch, with blob hashes recorded. A minimal board DTSI was then drafted using the mainline Deen PM8953 regulator/eMMC data and the donor's two PVT board IDs. This is a controlled partial port, not a copy of the full 2026 mainline DTS. The minimal PVT1/PVT2 candidates have since compiled with Clang 18 as part of the successful generic GKI ThinLTO+CFI Image smoke (run 43684266664). Full-tree schema validation is still on HOLD due to 160 diagnostics against ACK 5.15 schemas; no DTB is approved for device use.
