# Deen 4.19 → ACK 5.15 porting matrix

Status values: **Present** = implementation exists in pinned ACK; **Gap** = device support absent; **Audit** = implementation exists but binding/API/ABI compatibility is unproven; **Not started** = no Deen 5.15 port or device test.

| Area | 4.19 donor evidence | Pinned ACK 5.15 evidence / gap | Priority |
|---|---|---|---|
| SoC / machine | `ARCH_MSM8953`, Deen board support, PVT1/PVT2 | Qualcomm platform support is present, but no Deen board integration or MSM8953 board DTS. Do not recreate vendor machine code unless the ACK Kconfig requires it. | P0 |
| Base Device Tree | Vendor `msm8953.dtsi`, `msm8953-pinctrl.dtsi`, PMIC fragments | No `arch/arm64/boot/dts/qcom/msm8953.dtsi` in pinned ACK. Port and normalize the base SoC DTS first. | P0 |
| Deen DTS / DTB | PVT1 and PVT2 board DTS; board IDs C100/C200; modular Deen DTSI | No Deen DTB target in ACK qcom Makefile. Select correct board revision, port includes and bindings, then add DTB build wiring. | P0 |
| Clocks / reset | Deen GCC, RPM clocks and reset references | MSM8953 GCC driver and Kconfig exist. Audit clock IDs, resets, parents and all DT references before wiring. | P0 |
| Pinctrl / GPIO | Deen TLMM pin groups and GPIO assignments | MSM8953 pinctrl driver and Kconfig exist. Port pin states only after matching function/group definitions and GPIO IRQ semantics. | P0 |
| PMIC / regulators | PM8953 / PMI8950 nodes and named supplies | Qualcomm SPMI/regulator framework exists, but Deen supply names, voltage ranges, load modes and sequencing need binding-level validation. | P0 |
| Storage | SDHC1 eMMC and SDHC2 removable SD; power and pinctrl details | `sdhci-msm.c` exists. Port eMMC/SD nodes, regulators, bus widths, rates, crypto and boot-storage mapping. | P0 |
| Thermal / power | TSENS, ADC thermal sensors, charger and battery nodes | TSENS driver exists; vendor ADC thermal, charger and battery policy must be checked against ACK frameworks. | P0 |
| Display | Vendor MDSS/DSI, Tianma/Nova 720p panels | ACK's DRM/MSM stack is architecturally different from legacy MDSS. Requires display-path and panel-binding review, not blind DTS copying. | P1 |
| Touchscreen | Novatek NVT (0x62) and FocalTech FT8006U (0x38), GPIO64/65, 720x1520 | Generic FT5x06 support exists, but exact FT8006U compatibility is unproven; Novatek vendor driver also needs source/ABI audit. | P1 |
| GPU | KGSL / Adreno 506, GPU OPP and bus-frequency data | No vendor KGSL tree in pinned ACK. DRM/MSM is not ABI-compatible with KGSL blobs by assumption. Major port or userspace/vendor-stack decision required. | P1 |
| Camera | Legacy MSM camera-v2, VFE/ISPIF/CCI, EEPROM and sensors | Legacy camera-v2/techpack stack is absent from pinned ACK. High-risk API, media ABI, DMA/ION, power and sensor port. Keep isolated. | P2 |
| Audio | ASoC, TFA9874, Qualcomm DSP/audio legacy | Vendor audio machine/codec/DSP integration needs a separate dependency and userspace ABI audit. | P2 |
| WLAN / Bluetooth | Prima/Pronto, WCNSS and Bluetooth power sequencing | Match the Android 14 vendor firmware/HAL, bus transport and suspend interfaces. | P2 |
| NFC | NFC_NQ, GPIO and clock configuration | Verify NQ driver presence, regulators, IRQ/reset and device node before enabling. | P2 |
| Fingerprint / sensors | Deen fingerprint and sensor DTSI | Identify exact sensor drivers, firmware and trusted-application dependencies. | P2 |
| Vibrator / haptics | PMIC haptics and Deen vibrator nodes | Map to ACK haptics/regulator APIs and verify voltage/timing. | P2 |
| Android integration | Binder, ashmem, SELinux, vendor hooks | Start from ACK Android configuration and the matching Android 14 vendor ABI; avoid obsolete compatibility shims unless proven necessary. | P0 |
| Root / hiding | Separate SUSFS/NoMount/BakaSU branch | Explicitly excluded from clean baseline. | Deferred |

## Bring-up order

1. Source integrity, ACK base configuration and toolchain smoke test.
2. Base SoC DTS, clocks, pinctrl, PMIC/regulators and storage.
3. Thermal sensors, boot console and minimal init.
4. Display and touchscreen.
5. GPU/KGSL and camera/audio vendor interfaces.
6. Remaining connectivity and sensors.

## Mandatory review gate

A matching Kconfig symbol or compatible string is not sufficient. For every port, inspect Kconfig dependencies, Makefile wiring, structures and function signatures, DT bindings, interrupt/GPIO semantics, DMA/IOMMU, firmware, userspace ABI and licensing. Do not merge unreviewed donor code into the bring-up branch.
