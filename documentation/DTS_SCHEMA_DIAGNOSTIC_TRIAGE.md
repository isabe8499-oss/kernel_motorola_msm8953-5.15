# Deen PVT Device Tree schema diagnostic triage

Audit date: 2026-11-14  
Target source: `deen/dts-bringup`  
Validation run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43623081943  
Source report: `documentation/DEEN_DTS_BASE_SMOKE.md`

## Executive finding

The PVT1 and PVT2 DTBs compile, and binary read-back verifies the expected board IDs and QSEE region. However, the `dt-validate` log contains 160 diagnostic lines across both PVT DTBs even though the validator process exits with status 0. The full-tree schema gate is therefore **HOLD**, not a clean pass.

The most likely systemic cause is schema/source version skew: the imported `msm8953.dtsi` and `pm8953.dtsi` are Linux v6.1 sources, while the schema directory used by CI is from the pinned Android Common Kernel 5.15 tree. This is a hypothesis supported by the affected binding properties; it must be confirmed by comparing the exact v6.1 binding revisions and 5.15 driver contracts.

## Diagnostic inventory

Counts below are raw diagnostic lines across PVT1 and PVT2, not necessarily unique source defects.

| Node / area | Lines | Observed diagnostic class | Required investigation |
|---|---:|---|---|
| `l1-icache` | 48 | Missing `cache-level` and `cache-unified` | Compare v6.1 CPU/cache DTS conventions with the ARM cache schema used by ACK 5.15; validate expected values for Cortex-A53. |
| `l1-dcache` | 48 | Missing `cache-level` and `cache-unified` | Same as L1 I-cache; do not infer cache properties without source/architecture confirmation. |
| `pinctrl@1000000` | 28 | Child state nodes missing `function` | Compare MSM8953 pinctrl binding revision and all referenced states. Check whether eMMC SDHC1 pins are actually used by the minimal board. |
| `usb@70f8800` | 10 | MSM8953 compatible absent from 5.15 DWC3 schema; clock/interrupt shape mismatch | Determine if USB node is enabled. Reconcile donor DTS, controller driver and binding; do not enable USB in board DTS yet. |
| `memory@86300000` | 4 | Reserved-memory schema requires a different shape / `memory-region` | Confirm the exact node identity and relationship to SMEM/QSEE from donor and stock DTB. Do not alter memory map until confirmed. |
| `rtc@6000` | 4 | Multi-region `reg` and `reg-names` mismatch | Compare PM8953 RTC driver and binding revision; ensure address/size cells and register tuple are correctly represented. |
| `l2-cache_0`, `l2-cache_1` | 4 | Missing cache schema property | Verify L2 cache topology and expected Cortex-A53 cluster properties. |
| `rpm-requests`, `power-controller` | 4 | Child node / clock schema mismatch | Compare RPM/RPMPD binding revisions and the exact 5.15 backport. |
| `clock-controller@1800000` | 2 | GCC clock schema mismatch | Compare v6.1 MSM8953 clock node and ACK 5.15 GCC binding/driver. |
| `spmi@200f000` | 2 | `reg` tuple count mismatch | Compare SPMI controller node, address/size cells and 5.15 SPMI arbiter binding. |
| `thermal-sensor@4a9000` | 2 | Compatible/oneOf mismatch | Verify thermal sensor driver support and binding revision; keep disabled until proven. |
| `mailbox@b011000` | 2 | APCS compatible list mismatch | Compare mailbox driver and binding revisions; determine whether the node is required by the Deen boot path. |
| root memory node | 2 | False-schema diagnostic on zero-sized generated memory fixture | Replace the synthetic fixture memory declaration with a valid minimal memory tuple, or exclude that fixture from full board schema validation. |

## Remediation sequence

1. Preserve the imported v6.1 SoC/PMIC files unchanged until provenance is settled.
2. Retrieve exact Linux v6.1 schema revisions for each affected binding and compare with ACK 5.15 schemas.
3. For each diagnostic, identify whether it is:
   - a schema-only version difference;
   - a DTS property genuinely missing or malformed;
   - a driver/binding feature not supported by ACK 5.15;
   - an inherited node not required for the minimal Deen bring-up.
4. Backport only the minimum binding/driver changes needed, or adapt the Deen DTS to the 5.15 contract when behavior remains equivalent.
5. Do not silence diagnostics globally, blanket-disable inherited SoC nodes, or mark the entire tree schema-clean based solely on process exit code.
6. Run `dt-doc-validate`, processed-schema generation and targeted validation again; capture stdout/stderr and require zero untriaged diagnostics for the enabled Deen nodes.
7. Re-run both PVT DTBs and compare board-ID, QSEE, reserved-memory and eMMC properties after every change.

## Current gate status

- DTS syntax compile: PASS.
- PVT1/PVT2 binary board-ID read-back: PASS.
- QSEE region and removed-overlap read-back: PASS.
- Binding document syntax check: PASS.
- Full-tree PVT schema validation: HOLD — 160 diagnostic lines require triage.
- Full kernel Image: separate CI retry in progress.
- Device boot / flash: NOT AUTHORIZED.

This audit intentionally makes no source-code changes to the imported DTSI files. It records the defect evidence and the controlled remediation path.
