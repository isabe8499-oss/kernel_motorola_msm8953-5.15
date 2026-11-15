# Motorola One Deen — subsystem compatibility audit

Audit date: 2026-11-15  
Target: XT1941-3 / MSM8953 / ARM64 / AOSPA Android 14  
Kernel target: ACK 5.15, imported tip Linux 5.15.223

## Executive decision

The generic GKI feasibility Image and both PVT candidate DTBs compile with ThinLTO+CFI. The 20-symbol minimal Deen Kconfig fragment resolves successfully. This is sufficient to move from a generic feasibility build to a controlled subsystem-port audit, but it is not a complete device kernel.

The donor 4.19 configuration must not be copied wholesale. The full inventory found 700 unique donor CONFIG symbols; 208 have no Kconfig definition anywhere in the checked-out ACK 5.15 source tree. A definition found in Kconfig is only a first-level existence check, not proof that a driver supports the exact MSM8953 compatible, DT binding, firmware or Android userspace ABI.

## 1. Configuration inventory — PASS

Source references:
- 4.19 donor: `kernel_motorola_msm8953-22`, branch `4.19.325-WIP`, donor defconfig blob `ecef3b19eb5cbe5fef0c343b8fee2d54071a3c37`.
- ACK source used for inventory: `deen/dts-bringup`, commit `ff2a86b64b9357bbb79435b8fa88ea94c52c4111`.
- Inventory workflow: [run 43699488864](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43699488864).
- Artifact: `deen-donor-config-inventory`, ID `14156096378`; ZIP SHA-256 `3d24cc02c49c03a3d7d42af11b4c501a4949fb4b20de42a177a767245a24bac2`.

The donor file contains 643 explicit CONFIG assignments and 57 disabled-symbol records, with 700 unique symbol keys and no duplicate assignments. The inventory scanned 1,615 Kconfig files in ACK 5.15 and classified those keys as follows:

| Classification | Count |
|---|---:|
| Definition found and explicitly present in GKI baseline | 355 |
| No Kconfig definition found in ACK source tree | 208 |
| Definition found, but not selected in the minimal Deen fragment and not explicit in GKI | 125 |
| Selected in the minimal Deen fragment (also present in donor) | 12 |
| **Total donor symbols** | **700** |

The 20-symbol minimal fragment includes 12 symbols also present in the donor and 8 additional 5.15 requirements that are not explicit in the 4.19 donor config: `COMMON_CLK_QCOM`, `MSM_GCC_8953`, `PINCTRL_MSM`, `RPMSG`, `QCOM_RPMPD`, `SPMI_MSM_PMIC_ARB`, `REGULATOR_QCOM_SMD_RPM` and `REGULATOR_QCOM_SPMI`.

The corrected workflow re-ran GKI defconfig + fragment merge + olddefconfig and retained all 20 required symbols. Resolved .config SHA-256: `7fd7204305ffec3ea0e07acd93c081fb9e7ef81d52cf6a3c25516372e6e92a30`; savedefconfig SHA-256: `870133b82ebc2a3adda0f53213e4b98050eb94af91437829aef54e5f2b92cd6a`.

## 2. Subsystem readiness matrix

| Subsystem | Evidence from 4.19 donor / mainline Deen | ACK 5.15 finding | Decision |
|---|---|---|---|
| GCC / pinctrl / PMIC / eMMC base | MSM8953 board DTS, PM8953 supplies, SDHC1 eMMC and GPIO volume keys | 20-symbol minimal fragment resolves; ThinLTO Image and PVT candidate DTBs compile | **Base only — static pass, no hardware boot** |
| Removable SD (SDHC2) | 4.19 donor and current mainline Deen describe SDHC2, card-detect GPIO and VDD supplies | SDHCI MSM driver exists; exact card-detect, pinctrl and regulator sequence still needs validation | **Hold** |
| USB / QUSB2 / DWC3 | Mainline SoC node uses `qcom,msm8953-dwc3` with generic `qcom,dwc3` fallback and `qcom,msm8953-qusb2-phy` | ACK has `USB_DWC3_QCOM` and QUSB2 PHY framework. Its DWC3 table can see the generic fallback, but has no MSM8953-specific match data; the 5.15 QUSB2 PHY match table lacks the MSM8953 compatible | **Hold; QUSB2 MSM8953 data and schema reconciliation required** |
| USB-C / FUSB302 | 4.19 donor uses legacy `fairchild,fusb302` plus Motorola-specific GPIO properties. Mainline Deen uses the standard `fcs,fusb302` binding | ACK has generic `TYPEC_FUSB302`, but donor symbol `FUSB302` is not defined in ACK. Mainline's temporary/fixed 5 V VBUS reference is not accepted as production power switching | **Hold; identify real VBUS supply and port standard binding only** |
| NFC | 4.19 donor uses `qcom,nq-nci`, GPIO/clock setup and `CONFIG_NFC_NQ`. Mainline Deen describes PN553 with `nxp,pn553` and generic NXP NCI fallback | ACK has `NFC_NXP_NCI` / I2C support, but donor's `NFC_NQ` symbol and `qcom,nq-nci` binding are absent | **Hardware identity conflict; do not enable until chip is confirmed** |
| MPSS modem | Mainline MSM8953 SoC compatible is `qcom,msm8953-mss-pil`; donor firmware/config are from the 4.19 vendor baseline | ACK Kconfig has Q6V5 MSS, but 5.15 driver previously lacked the MSM8953 descriptor and PAS memory-setup path | **Backport staged on isolated branch; object CI pending** |
| ADSP / audio DSP | Mainline MSM8953 uses `qcom,msm8953-adsp-pil`; donor audio uses legacy Qualcomm AFE/DAI and codec integration | ACK Q6V5 PAS exists, but 5.15 OF table lacked MSM8953 ADSP resource mapping | **Backport staged; runtime firmware/audio ABI still blocked** |
| WCNSS / WLAN | Mainline MSM8953 uses `qcom,pronto-v3-pil`; donor 4.19 config selects vendor PRONTO/WCNSS WLAN stack | ACK has WCNSS PIL but its 5.15 OF table only covered Riva/Pronto v1/v2, not v3 | **Pronto v3 backport staged; WLAN firmware/HAL and suspend path remain blocked** |
| Display / panel | 4.19 donor references Tianma/Nova 720×1520 panel and legacy MDSS/DSI nodes. Current mainline Deen deliberately does not enable the panel | No validated 5.15 panel, DSI PHY, backlight, WLED/IBB and PMIC supply sequence for this device | **Hold** |
| Touchscreen | Donor DTS contains Novatek NVT at I²C 0x62 and FocalTech FT8006U at 0x38; donor config selects NT36XXX and disables FT5X06 | Neither donor symbol `TOUCHSCREEN_NT36XXX` nor `TOUCHSCREEN_FT5X06` has a Kconfig definition in ACK 5.15; custom compatibles are not validated | **Vendor touchscreen driver port required; verify actual controller first** |
| GPU | Donor config requests `QCOM_KGSL` / Adreno 506 | `QCOM_KGSL` has no ACK Kconfig definition. DRM/MSM is not assumed ABI-compatible with Android KGSL vendor userspace | **Hold; do not substitute DRM for KGSL without a userspace plan** |
| Camera | Donor uses MSM camera-v2 / Motorola legacy camera symbols, CSI/ISPIF/CCI and sensor nodes | Core Motorola camera techpack symbols have no definitions in ACK 5.15 | **Large isolated vendor-port workstream; not ready** |
| Audio machine / codec | Donor uses legacy MSM AFE/DAI and TFA9874 integration | ADSP support is only one dependency; machine driver, Slimbus, codec, firmware and Android audio HAL contract remain unported | **Hold** |
| Thermal / battery / charging | Donor has TSENS, PMIC ADC/charger and battery policy; SoC DTS has an MSM8953 TSENS compatible | Generic TSENS framework exists, but calibration, thermal zones, battery/charger ADC, thresholds and safety policy have not been validated | **Hold; required before device acceptance** |
| Fingerprint / sensors / haptics | Donor contains vendor sensor and fingerprint options | Exact devices, firmware, trusted-app dependencies and 5.15 drivers are not established | **Hold** |

## 3. Isolated remoteproc backport branch

An isolated branch was created from the current Deen bring-up base:

- Branch: `deen/msm8953-remoteproc-backports`
- Base commit: `ff2a86b64b9357bbb79435b8fa88ea94c52c4111`
- Current branch head: `12366f09d36b13ab47eec139ea4aec574c59fdef`

It contains six focused commits:
1. Add the MSM8953 MSS resource descriptor, reset/memory sequence and PAS memory setup to `qcom_q6v5_mss.c`, adapted to the fields available in ACK 5.15.
2. Add a dedicated MSM8953 ADSP PAS resource descriptor and OF compatible to `qcom_q6v5_pas.c`.
3. Add Pronto v3 resource data and OF compatible to `qcom_wcnss.c`.
4. Add `qcom,msm8953-adsp-pil` to the ADSP schema's compatible and conditional property lists.
5. Document MSM8953 MSS interrupt, clock, supply and power-domain names in `qcom,q6v5.txt`.
6. Document Pronto v3 compatible and power-domain order in `qcom,wcnss-pil.txt`.

Upstream provenance:
- MSS support: [torvalds/linux commit 0201f759](https://github.com/torvalds/linux/commit/0201f759594b1248635185a92a5e39f47441ad6a).
- ADSP support: [torvalds/linux commit 1cfaa13b](https://github.com/torvalds/linux/commit/1cfaa13b82c73977e8ddaca63c791203addc39c1).
- Pronto v3: [torvalds/linux commit 4c707cf5](https://github.com/torvalds/linux/commit/4c707cf5c7ddd43c6d574281a5591f71ed8d310c).

CI run [43702140932](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43702140932) stopped before object compilation because its shallow fetch did not contain the base commit for `git diff --check`. This was a workflow defect, not a source compile failure. The workflow now fetches the base commit explicitly; corrected run [43702461753](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43702461753) is the current validation gate.

**Important:** this branch does not enable MPSS, ADSP or WCNSS nodes in the Deen board DTS. Object compilation and binding acceptance must pass first; the vendor Android 12 firmware files and the exact reserved-memory/power-domain/clock/SMEM wiring must then be verified before node activation.

## 4. Required order from this audit

1. Pass targeted compilation of the three remoteproc objects and ADSP binding validation.
2. Verify vendor firmware availability and filenames for MBA/MPSS, ADSP and WCNSS against the actual Android 12 vendor image.
3. Reconcile MSM8953 memory-region addresses, power-domain IDs, SMD/SMP2P edges, clocks and resets before enabling any remoteproc node.
4. Port MSM8953 QUSB2 PHY driver data and reconcile DWC3 binding/compatible support in a separate patch series.
5. Resolve the NFC hardware identity conflict between donor NQ-NCI and mainline PN553.
6. Identify the handset's PVT via read-only bootloader/stock-DTB evidence.
7. Continue display/touch/GPU/camera/audio/thermal ports as separate driver/ABI workstreams.
8. Only after the above and the DTS schema gate pass should a final Deen defconfig be generated and a boot image contract be implemented.

## Safety and acceptance boundary

- ThinLTO+CFI feasibility build is successful; Full LTO final validation is still open.
- Full-tree PVT schema validation remains HOLD due unresolved diagnostics.
- The actual hardware revision remains unknown.
- No remoteproc node is activated by this audit.
- No boot image is approved or generated for flashing.
- No physical-device write or flash has been performed.
