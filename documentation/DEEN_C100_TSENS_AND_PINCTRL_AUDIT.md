# Deen C100 thermal and pinctrl binding audit

Date: 2026-11-15
Target stock node: `/soc/tsens@4a8000` in the C100 FDT embedded in the supplied boot_b image.

## 1. Stock TSENS contract

Binary extraction from stock C100 FDT (boot_b, offset 0x00b7820a) shows one TSENS node:
- Node: `/soc/tsens@4a8000`
- compatible: `qcom,msm8953-tsens`
- reg: `<0x4a8000 0x2000>, <0xa4000 0x1000>`
- reg-names: `tsens_physical`, `tsens_eeprom_physical`
- interrupts: SPI 184 and 314
- interrupt-names: `tsens-upper-lower`, `tsens-critical`
- `qcom,sensors = <15>`
- `qcom,client-id = <1 2 3 4 5 6 7 8 9 10 11 12 13 14 15>`
- `qcom,sensor-id = <1 2 3 4 5 6 7 8 9 10 11 12 13 14 15>`
- `qcom,slope`: 15 entries, each `0xc80`
- `qcom,valid-status-check` boolean

This is materially different from the current experimental candidate node (`thermal-sensor@4a9000`, `qcom,msm8953-tsens` plus `qcom,tsens-v2`, two 0x1000 TM/SROT ranges, 16 sensors, and no stock sensor-ID/slope mapping).

## 2. Vendor 3.18.140 driver evidence

The user's existing repository `isabe8499-oss/kernel_motorola_msm8953` has `drivers/thermal/msm-tsens.c` with an explicit OF match:
- `qcom,msm8953-tsens` -> `TSENS_CALIB_FUSE_MAP_NONE`
- The device setup maps this compatible to `TSENS_TYPE3`.
- TSENS_TYPE3 code has distinct register offsets, critical/upper-lower interrupt handling, and expects the `tsens_eeprom_physical` resource.
- The DT parser reads `qcom,sensors`, `qcom,slope`, `qcom,client-id` and `qcom,sensor-id`.

This is the concrete legacy hardware contract. The ACK 5.15 driver `drivers/thermal/qcom/tsens.c` does not have a specific `qcom,msm8953-tsens` match; its generic `qcom,tsens-v2` match uses `data_tsens_v2`. The v2 data sets up to 16 sensors and split SROT/TM registers, but it does not by itself establish equivalence with the stock TYPE3 calibration/data path.

## 3. TSENS decision

**HOLD — do not relabel the stock block as a generic v2 sensor yet.**

Required port/validation work:
1. Port or adapt the MSM8953 TYPE3 logic from the vendor driver to the Linux 5.15 thermal API.
2. Preserve the 15 stock sensor IDs, client IDs and slope calibration values.
3. Map the stock TSENS register window and EEPROM resource exactly, with bounds and alignment checks.
4. Validate both interrupts and thermal sensor index mapping.
5. Add an OF match for `qcom,msm8953-tsens` only when the correct implementation is present.
6. Add the binding schema for this legacy compatible and required properties after the driver contract is implemented.
7. Build a unit/compile test and validate schema against the stock-derived PVT1 node.

No TSENS compatible, sensor count, register mapping or calibration values were changed in this audit.

## 4. Pinctrl SDC1/SDC2 binding reconciliation

The ACK 5.15 `drivers/pinctrl/qcom/pinctrl-msm8953.c` declares dedicated fixed SDCC groups through `SDC_QDSD_PINGROUP`:
- sdc1_clk, sdc1_cmd, sdc1_data, sdc1_rclk
- sdc2_clk, sdc2_cmd, sdc2_data

These fixed SDCC groups are not entries in the selectable `msm8953_functions` mux enum. The old stock pinctrl representation likewise stores SDC2 pin configs without an alternate mux function. The schema previously required `function` for every pin configuration node, producing false-positive diagnostics for these fixed-function SDCC groups.

A narrow binding change was committed on the experimental branch:
- Commit: `372a9ae6591f15b691f68cdbd2e6971f2d91c108`
- It makes `function` optional only when the pins list contains one of the seven fixed SDCC group names; all other pin groups still require `function`.
- No pin numbers, pulls, drive strengths or pin states were changed.

This binding patch is experimental and awaits the next schema run.

## 5. Other remaining schema issues

The latest schema run after root compatible correction removed the Deen root-compatible error and no longer reported cache node errors. Remaining diagnostics included:
- GCC clock-controller clock property shape;
- SPMI resource count and PM8xxx RTC register layout;
- DWC3 compatible list;
- APCS mailbox compatible count;
- SMEM reserved-memory node shape;
- RPM/RPMPD child property schema;
- TSENS compatible schema.
Each requires comparison to stock FDT and its exact kernel driver/binding. Do not suppress the errors by deleting hardware resources.

## 6. Current gate

- C100 identity and minimal DTB build: PASS.
- Stock root compatible: matched; qcom.yaml binding updated in branch commit `33659fab9533e1b6bdf4b04b49db501f17c1b4bc`.
- Cache topology and compatible: matched against stock and compiled.
- SDC2 binding correction: awaiting validation.
- TSENS: HOLD pending TYPE3 driver port.
- Memory reservations: HOLD pending consumer/firmware mapping.
- Full-tree semantic equivalence, full kernel Image, boot image and flashing: HOLD.
