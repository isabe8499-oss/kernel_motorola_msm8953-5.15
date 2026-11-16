# Deen XT1941-3 — sequenced pre-integration gate review

Date: 2026-11-16
Repository: isabe8499-oss/kernel_motorola_msm8953-5.15

## Gate 1 — repository and branches: PASS
- Repository exists, is public, default branch `main`.
- Main head at review: `2acbc341f4a5476c69bbb8fdd0030c2fdd341dc4`.
- Experimental DTS branch: `deen/c100-schema-reconcile-v2` at `372a9ae6591f15b691f68cdbd2e6971f2d91c108`.
- Other branches preserved: `ack/android14-5.15-base`, `upstream/android14-5.15-lts`, `deen/bringup`, `deen/bringup-ack515-base`, `deen/c100-dtb-match`, `deen/c100-dtb-validation`, `deen/dts-bringup`, `deen/msm8953-remoteproc-backports`, `ci/kernel-build`.
- Compare `10f0142545dd614ef6ec2629a3db8889ec43a674...372a9ae6591f15b691f68cdbd2e6971f2d91c108`: two commits ahead, zero behind; only binding files changed (`Documentation/devicetree/bindings/arm/qcom.yaml`, `Documentation/devicetree/bindings/pinctrl/qcom,msm8953-pinctrl.yaml`). The DTS source is unchanged since the structural run's source commit.

## Gate 2 — latest GitHub Actions: PASS for the scoped jobs
- C100 identity/schema run 17: `43763534296`, job `132963421860`, conclusion success; artifact `14180369413` (580,968 bytes). It fetched and built the experimental branch at `372a9ae6591f15b691f68cdbd2e6971f2d91c108`.
- Structural gate run 11: `43762367961`, job `132959778552`, conclusion success; artifact `14180977348`. It built experimental source commit `10f0142545dd614ef6ec2629a3db8889ec43a674`.
- Latest main repository sanity runs: `43858207689` (run 271) and `43858313352` (run 272), both success. They validate repository inventory only; they are not kernel/DTB builds.
- Run 17 schema step is diagnostic-only. Job success is not schema acceptance.

## Gate 3 — Boot B / DTO B: evidence audit recorded
Repository audit records the supplied Boot B dump as 67,108,864 bytes, SHA-256 `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`, Android boot magic `ANDROID!`, header version 1, page size 2048, kernel payload 12,785,442 bytes, ramdisk 19,092,140 bytes. Seven valid FDTs were found in the kernel payload.
- Stock C100 FDT offset `0x00b7820a`, size 253,704 bytes, 1,471 nodes, MSM ID `0x125/0`, board ID `0x4d/0xc100`.
- Stock C200 FDT offset `0x00abe4f6`.
- DTO B dump recorded as 16,777,216 bytes, SHA-256 `080acf35a507ac9849fcba47dc2ad83e01b75663a516279c8b9d243b719643e`, all bytes zero in that captured dump.
- This is an observation about the supplied DTO B image only; do not infer bootloader selection/behavior from zero-fill.
- Bootloader readback: product=deen, board=deen, hwrev=PVT1; Android properties: XT1941-3, ro.boot.hwrev=0xC100, active slot _a.
- Do not assume the bootloader selection algorithm from the existence of the C100 FDT; seven FDTs are present.

## Gate 4 — binding/schema: REVIEW_REQUIRED
Run 17 artifact `14180369413` was downloaded and inspected. Both PVT1/PVT2 DTBs compile; schema log contains diagnostics. No cache diagnostics remain after the ARM arch-cache representation update, but outstanding diagnostics include:
- root memory zero-reg placeholder (also present in stock C100 and bootloader-populated convention; don't invent RAM bounds);
- SMEM `memory@86300000` required memory-region/property pattern;
- SMD RPM / RPMPD child property patterns;
- TSENS compatible pair `qcom,msm8953-tsens`, `qcom,tsens-v2` rejected by pinned oneOf;
- GCC clock-controller clocks/clock-names pattern;
- SPMI reg tuple count;
- PM8xxx RTC reg/reg-names;
- DWC3 compatible, clock-names, interrupt and interrupt-name counts;
- APCS mailbox compatible list length.
Schema command exit status 0 is diagnostic behavior; classification remains REVIEW_REQUIRED. Do not remove properties or replace compatible strings just to silence the validator.

## Gate 5 — DTB structural integrity: PASS, narrow scope only
Artifact `14180977348` was downloaded and inspected:
- PVT1 DTB: 23,966 bytes, SHA-256 `2c5fb810fdfcae65768167327bdb4ac4ba824aea6cfa2dc4b5117838aa9ae442`.
- PVT2 DTB: 23,934 bytes, SHA-256 `5998d09cae4ebb4b65ebc2e7085ae83ae61ac5a7b8ae6adf3c725f753f20ecff`.
- Workflow asserted CPU0..CPU7, separate L1 instruction/data cache nodes for each CPU, two L2 cluster cache nodes and CPU-to-L2 phandle links, root compatible, PVT1 C100 tuple and PVT2 C200 tuple. Every structural-gate step passed.
- Run 17 is two commits later but the branch comparison shows only binding YAML files changed; DTS source was unchanged, so the structural result remains applicable to the same DTS source revision.

## Critical limitation — candidate is not stock-equivalent
Latest candidate PVT1 from run 17: 23,966 bytes / 248 nodes.
Stock C100 FDT: 253,704 bytes / 1,471 nodes.
Property diff: 44 common node paths, 1,427 stock-only paths, 204 candidate-only paths, 104 missing properties and 26 differing raw property values on common paths.
This is a minimal bring-up DTB, not a complete device tree. It must not be flashed or treated as bootable.

High-risk reserved-memory differences still need consumer/firmware reconciliation: stock other_ext_region 0x84300000/0x02500000 versus candidate qseecom plus adjacent regions; stock modem, ADSP, WCNSS, DFPS, splash, ramoops, TZ-log and watchdog-context areas; dynamic shared pools and modem/ADSP/WCNSS/SMEM/SMP2P links. Candidate does not yet reproduce the complete stock memory/IPC/peripheral graph.

## Gate decision
| Gate | Status |
|---|---|
| Repository/branch inventory | PASS |
| Recent GitHub Actions scoped jobs | PASS |
| Boot B / DTO B evidence audit | PASS (read-only) |
| Binding/schema | REVIEW_REQUIRED |
| DTB structural identity/cache test | PASS (narrow) |
| Full C100 stock-tree equivalence | HOLD |
| Full kernel Image/modules for Deen | HOLD |
| Boot image packaging / device boot / flash | HOLD |

## Next permitted work
1. Preserve all stock dumps and checksums; no writes to handset.
2. Build a semantic, subsystem-grouped reconciliation plan from stock C100 FDT: reserved-memory/SMEM first, then modem/MSS, ADSP, WCNSS/SMP2P, TSENS, RPM/PMIC, GCC/SPMI/RTC, USB/APCS.
3. For each patch, cite stock node/property evidence and exact ACK 5.15 driver/binding contract; change one subsystem at a time.
4. Run DTB compile, schema diagnostic, FDT property diff and artifact hash checks after each isolated patch.
5. Do not proceed to full Deen kernel Image/modules or boot packaging until critical memory/firmware/peripheral contracts are reconciled.

No boot image was generated, no partition was written, no merge to main was made, and no flash is approved by this review.
