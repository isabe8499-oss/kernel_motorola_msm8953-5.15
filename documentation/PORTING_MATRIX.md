# Deen 4.19 → ACK 5.15 porting matrix

Status values: **Inventory** = identified in donor; **Pending** = API/ABI and dependency audit required; **Not validated** = no 5.15 build or device test yet.

| Area | 4.19 donor evidence | 5.15 work | Priority |
|---|---|---|---|
| SoC / machine | ARCH_MSM8953, MACH_MOTOROLA_DEEN | Confirm ACK SoC support; add board glue only where absent | P0 |
| Device Tree | Deen PVT1/PVT2 DTS + modular DTSI | Port nodes, bindings, regulators, GPIOs, reserved memory; compile DTBs | P0 |
| Clocks / reset / pinctrl | Deen and Qualcomm DTS fragments | Resolve provider and binding differences | P0 |
| PMIC / regulators | PM8953 / PMI8950 fragments | Validate supply names, ranges, sequencing | P0 |
| Storage | SDHC1/SDHC2 device config | Validate eMMC/SD controller, crypto and boot storage | P0 |
| Thermal / power | TSENS, ADC thermal, battery and charger | Audit thermal zones, trips and charger integration | P0 |
| Display | MDSS/DSI, Tianma/Nova panels | Port panel and MDSS path against ACK display framework | P1 |
| Touchscreen | Novatek NVT, FocalTech FT8006U DTS | Identify exact driver sources and dependencies; validate IRQ/reset | P1 |
| GPU | Qualcomm KGSL / Adreno 506 | Match GPU driver ABI, firmware and userspace expectations | P1 |
| Camera | Legacy MSM camera, VFE/ISPIF/CCI and sensors | High-risk ABI port; retain 3.18/4.19 calibration and sensor compatibility | P1 |
| Audio | ASoC / TFA9874 / Qualcomm DSP | Port machine and codec paths; validate DSP interfaces | P2 |
| WLAN / Bluetooth | Prima/Pronto, WCNSS, Bluetooth power | Match firmware and vendor HAL expectations | P2 |
| NFC | NFC_NQ and Deen pin configuration | Verify device node, GPIO and clock changes | P2 |
| Fingerprint | Deen fingerprint DTSI | Identify actual sensor driver and trusted-app dependencies | P2 |
| Vibrator / haptics | Deen vibrator, PMIC haptics | Validate regulator and timing | P2 |
| Android integration | Binder, ashmem, SELinux, vendor hooks | Use ACK equivalents; avoid obsolete compatibility shims unless needed | P0 |
| Root / hiding | Separate BakaSU/SUSFS branch | Excluded from clean baseline | Deferred |

## Mandatory gate

Nothing moves from donor to target merely because the symbol name matches. Check Kconfig, Makefile wiring, structure/API changes, DT bindings, runtime dependencies, firmware, userspace ABI and licensing.
