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


## Comparative binding audit against Linux v6.1 — partial confirmation (2026-11-15)

The schema/source-skew hypothesis has now been checked directly against the pinned ACK 5.15 binding files and the corresponding upstream Linux v6.1 files. This confirms that the 160 diagnostics are a mixture of real DTS contract issues and binding-version differences; they must not be treated as one category.

| Area | ACK 5.15 binding vs Linux v6.1 | Finding / disposition |
|---|---|---|
| MSM8953 DWC3 | ACK `qcom,dwc3.yaml` does not list `qcom,msm8953-dwc3`; v6.1 explicitly lists it and has a two-interrupt conditional for this compatible | **Confirmed schema skew.** Do not add the compatible to the ACK schema alone. First compare the 5.15 DWC3 wrapper driver match data, clocks, interrupts, PHY and QUSB2 implementation. USB remains disabled/HOLD. |
| PM8xxx RTC | ACK `qcom-pm8xxx-rtc.yaml` allows one `reg` item; v6.1 allows one or two and defines `reg-names` (`rtc`, `alarm`) | **Confirmed schema skew.** The Deen PM8953 RTC node's multi-region layout must also be checked against the actual ACK 5.15 RTC driver before deciding whether a minimal binding/driver backport or a DTS adaptation is correct. |
| MSM8953 TSENS | ACK `qcom-tsens.yaml` does not list `qcom,msm8953-tsens`; v6.1 lists it as TSENS v2 | **Confirmed schema skew, runtime contract still open.** The ACK 5.15 TSENS driver must be checked for MSM8953 match data, calibration cells, register regions, sensor count and interrupt model before enabling the node. Thermal safety remains a P0 hold. |
| MSM8953 pinctrl | ACK `qcom,msm8953-pinctrl.yaml` lacks `gpio-reserved-ranges` and the v6.1 binding adds a common pinctrl schema reference. Both versions require `function` in each matching `*-pins` child | **Mixed.** The missing `gpio-reserved-ranges` diagnostic can be version-related; child states missing `function` are not explained by this version difference and require DTS/driver inspection. Do not invent a function value. |
| MSM8953 GCC | The ACK common `qcom,gcc.yaml` lists MSM8953; the v6.1 common binding delegates SoC-specific compatible handling and is more permissive | **No immediate compatible gap established.** Inspect the exact node properties and ACK driver contract rather than labeling all GCC diagnostics schema skew. |
| RPM power domains | Both inspected `qcom,rpmpd.yaml` versions list `qcom,msm8953-rpmpd` | **Not explained by compatible-list skew.** Investigate the node's OPP table, power-domain cells and the exact Deen backport contract. |
| APCS mailbox | Both versions recognize the MSM8953 compatible, but v6.1 expresses legacy compatible fallback through an ordered `oneOf` sequence including `syscon`; ACK uses a simpler enum | **Potential binding-shape skew.** Verify the actual node compatible list and the 5.15 mailbox driver before any DTS change. |

This comparison establishes the existence of specific binding-version differences; it does not establish that every affected DTS node is safe or that a v6.1 binding can be copied wholesale into ACK 5.15. The exact 5.15 driver implementation and compatible table remain authoritative for runtime support.

### Required next actions

1. Build a per-node diagnostic map from the actual PVT DTBs, retaining JSON paths and diagnostic keywords rather than counting raw log lines only.
2. For each affected enabled node, compare the binding with the exact ACK driver match table and probe path.
3. For inherited but unused peripherals, determine whether they are safe to leave disabled in the source DTB; do not delete nodes solely to make validation quiet.
4. Implement narrowly scoped DTS/binding/driver changes only where the 5.15 contract is understood; keep USB, RTC, TSENS, pinctrl and RPM work isolated.
5. Require zero untriaged diagnostics for enabled Deen nodes and rerun binary read-back of board IDs, QSEE, reserved-memory and eMMC after every change.

Source comparison refs: `torvalds/linux:v6.1` and the repository's pinned `deen/dts-bringup` ACK 5.15 source. No imported SoC/PMIC DTSI, binding or driver was modified during this audit.
