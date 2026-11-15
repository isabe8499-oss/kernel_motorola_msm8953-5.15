# Deen 4.19 → ACK 5.15 porting matrix

Status values: **Present** = implementation exists in pinned ACK; **Gap** = device support absent; **Audit** = implementation exists but binding/API/ABI compatibility is unproven; **Not started** = no Deen 5.15 port or device test.

| Area | 4.19 donor evidence | Pinned ACK 5.15 evidence / gap | Priority |
|---|---|---|---|
| SoC / machine | `ARCH_MSM8953`, Deen PVT1/PVT2 support | The pinned ACK has the Qualcomm framework; a minimal Deen DTS foundation now lives on `deen/dts-bringup`. No Deen-specific defconfig or runtime board validation exists yet. | P0 |
| Base Device Tree | Vendor `msm8953.dtsi`, `msm8953-pinctrl.dtsi`, PMIC fragments | Unchanged v6.1 `msm8953.dtsi` and `pm8953.dtsi` are on `deen/dts-bringup`. CI compiles the base fixture and PVT1/PVT2 candidates and verifies board-ID/QSEE read-back. The full-tree schema run emits 160 diagnostics against ACK 5.15 schemas; schema acceptance is HOLD pending version reconciliation. Hardware use remains unverified. | P0 |
| Deen DTS / DTB | PVT1/PVT2 DTS + modular Deen fragments; board IDs C100/C200 | PVT1/PVT2 wrappers compile and their board IDs/QSEE reservations are verified from generated DTBs. Full-tree binding validation remains HOLD with 160 diagnostics. The handset's actual PVT is still unknown. | P0 |
| Clocks / reset | Deen GCC, RPM clocks and reset references | MSM8953 GCC driver, Kconfig and Makefile wiring exist. Audit clock IDs, resets, parents and DT references. | P0 |
| Pinctrl / GPIO | Deen TLMM pin groups and GPIO assignments | MSM8953 pinctrl driver, Kconfig and Makefile wiring exist. Port pin states only after matching function/group definitions and IRQ semantics. | P0 |
| PMIC / regulators | PM8953 / PMI8950 nodes and named supplies | SPMI/regulator framework exists, but the Deen PMIC DTS and supply graph are absent. Validate voltage/load modes and sequencing. | P0 |
| Storage | SDHC1 eMMC and SDHC2 removable SD; power and pinctrl details | `sdhci-msm.c` exists. Port eMMC/SD nodes, regulators, bus widths, rates, crypto and boot-storage mapping. | P0 |
| Thermal / power | TSENS, ADC thermal sensors, charger and battery nodes | TSENS driver exists; port thermal zones and audit ADC, charger and battery policy. | P0 |
| USB / remote processors | HS USB PHY, DWC3, SMD RPM, ADSP/MPSS/WCNSS | ACK Kconfig has DWC3-QCOM, QUSB2 PHY and Q6V5 frameworks, but the exact MSM8953 QUSB2 compatible and remoteproc platform compatibles were missing in the 5.15 driver tables. A separate branch `deen/msm8953-remoteproc-backports` adds MSS/ADSP/Pronto-v3 matches and bindings; object CI is pending. USB PHY and DWC3 data remain a separate backport. | P0 |
| Display | Vendor MDSS/DSI, Tianma/Nova 720p panels | ACK's DRM/MSM stack and current mainline bindings differ from legacy MDSS. Mainline Deen DTS has supply wiring but no panel enablement. | P1 |
| Touchscreen | Novatek NVT (0x62) and FocalTech FT8006U (0x38), GPIO64/65, 720x1520 | Donor config selects `TOUCHSCREEN_NT36XXX` and disables `TOUCHSCREEN_FT5X06`; neither donor symbol has a definition in ACK 5.15. Exact controller and vendor driver must be identified/ported. | P1 |
| GPU | KGSL / Adreno 506, GPU OPP and bus-frequency data | No vendor KGSL tree in pinned ACK. DRM/MSM is not ABI-compatible with KGSL userspace blobs by assumption. | P1 |
| Camera | Legacy MSM camera-v2, VFE/ISPIF/CCI, EEPROM and sensors | Legacy camera-v2/techpack stack is absent from pinned ACK. High-risk API, media ABI, DMA/ION, power and sensor port. Keep isolated. | P2 |
| Audio | ASoC, TFA9874, Qualcomm DSP/audio legacy | Vendor audio machine/codec/DSP integration needs separate dependency and userspace ABI audit. | P2 |
| WLAN / Bluetooth | Prima/Pronto, WCNSS and Bluetooth power sequencing | Match Android 14 vendor firmware/HAL, bus transport and suspend interfaces. | P2 |
| NFC | Donor uses `qcom,nq-nci` / `CONFIG_NFC_NQ`; mainline uses PN553 / NXP-NCI | ACK has generic NXP-NCI I2C support, but the donor's NQ-NCI driver/config is absent and the mainline PN553 reference conflicts with the donor. Confirm the actual chip from stock DTB/vendor image before enabling. | P2 |
| Fingerprint / sensors | Deen fingerprint and sensor DTSI | Identify exact sensor drivers, firmware and trusted-application dependencies. | P2 |
| Vibrator / haptics | PMIC haptics and Deen vibrator nodes | Map to ACK haptics/regulator APIs and verify voltage/timing. | P2 |
| Android integration | Binder, ashmem, SELinux, vendor hooks | Start from ACK Android configuration and matching Android 14 vendor ABI; avoid obsolete compatibility shims unless proven necessary. | P0 |
| Root / hiding | Separate SUSFS/NoMount/BakaSU branch | Explicitly excluded from clean baseline. | Deferred |



The detailed evidence, exact compatible matches and outstanding firmware/ABI gates are consolidated in `documentation/DEEN_SUBSYSTEM_COMPATIBILITY_AUDIT.md`. The full 700-symbol Kconfig inventory is in `documentation/DEEN_DEFCONFIG_SYMBOL_AUDIT.md` and its CI artifact.

## Hardware-source decision

Use the modern mainline Deen DTS as a binding/board reference only. Its initial upstream support does not enable the panel, touchscreen controller, camera or KGSL stack, and its dependencies do not match the 5.15-era base. The complete audit is in `documentation/DEEN_MAINLINE_DTS_AUDIT.md`.

## Bring-up order

1. Verified source import and ACK config/object smoke.
2. Minimal MSM8953 SoC DTS, PM8953/PMI8950, GCC, pinctrl, RPM/SMD and eMMC.
3. Serial console, boot memory map and thermal sensors.
4. USB/remote processors/NFC after phandle and firmware checks.
5. Display and touchscreen with exact panel/sensor drivers.
6. GPU/KGSL and camera/audio vendor interfaces as isolated workstreams.

## Mandatory review gate

A matching Kconfig symbol or compatible string is not sufficient. Check Kconfig dependencies, Makefile wiring, structures/function signatures, DT bindings, interrupt/GPIO semantics, DMA/IOMMU, firmware, userspace ABI and licensing. Do not merge unreviewed donor code into the bring-up branch.
