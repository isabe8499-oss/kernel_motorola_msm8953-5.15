# Deen XT1941-3 — sequenced verification update

Audit date: 2026-11-17
Repository: `isabe8499-oss/kernel_motorola_msm8953-5.15`
Target: Motorola One Deen XT1941-3, MSM8953, C100/PVT1
Target ROM: AOSPA Android 14
Kernel base: Android Common Kernel 5.15 LTS

## Executive decision

The requested pre-integration sequence has been rechecked against the live repository, current branch refs, GitHub Actions API, downloaded Actions artifacts, and the user-supplied raw Boot B/DTO B archive.

**Decision: STOP before full kernel/device integration.** Repository and narrow CI/DTB gates pass. Boot B/DTO B binary inspection is now independently reproduced. Schema remains REVIEW_REQUIRED. The candidate remains a minimal 248-node bring-up DTB versus the 1,471-node stock C100 FDT, with major semantic and memory/firmware coverage gaps.

## 1. Repository and branches

- Repository is public and accessible.
- Default branch: `main`.
- Current main HEAD at this audit: `8d81fdc9e45d67fcd3f19d558ff388a5fba0946f`.
- Last push: 2026-11-16T16:20:36Z.
- Current Deen source branch: `deen/c100-schema-reconcile-v2` at `372a9ae6591f15b691f68cdbd2e6971f2d91c108`.
- Preserved branches include `ack/android14-5.15-base`, `upstream/android14-5.15-lts`, `deen/bringup`, `deen/bringup-ack515-base`, `deen/c100-dtb-match`, `deen/c100-dtb-validation`, `deen/dts-bringup`, `deen/msm8953-remoteproc-backports`, and `ci/kernel-build`.
- The main HEAD commit after the 2026-11-16 gate review is documentation-only; no DTS or kernel source integration was merged into main.
- Keep the ACK base and experimental Deen DTS branch separate. No merge approval is implied.

## 2. GitHub Actions

Latest repository-wide Actions runs returned by GitHub:
- `43906425559` — Repository sanity checks, main, completed success (2026-11-16 16:20:39Z). This checks repository inventory only.
- `43858313352` — Repository sanity checks, main, completed success.
- `43858207689` — Repository sanity checks, main, completed success.

Latest relevant device-specific build/validation runs:
- `43763534296` — Deen C100 DTB identity validation, completed success; job `132963421860`; artifact `14180369413` (580,968 bytes). It fetched and built source branch `deen/c100-schema-reconcile-v2` at `372a9ae6591f15b691f68cdbd2e6971f2d91c108`.
- `43762367961` — Deen C100 structural gate, completed success; job `132959778552`; artifact `14180977348`. It built source commit `10f0142545dd614ef6ec2629a3db8889ec43a674`. The branch comparison to current source commit shows only Qualcomm ARM and MSM8953 pinctrl binding YAML changes after that commit; DTS source is unchanged.
- No newer C100 DTB/schema or structural run appears in the current Actions run inventory after run `43763534296`; the later main runs are repository sanity checks.

Important: run `43763534296` job success means DTB compile/identity readback and artifact upload succeeded. The schema step is `continue-on-error: true`, exits zero on the emitted diagnostics and reports `REVIEW_REQUIRED`. It is not a schema pass.

## 3. Boot B and DTO B — raw-byte verification

The user-supplied `Deen_Boot_B_Audit.tar` was materialized and independently inspected.

Archive:
- Size: 83,891,200 bytes.
- SHA-256: `e946172035f563cc0e1189b82306eed972848c2041604f12e8a7f0fefaea4b8a`.
- Contains `boot_b-original.img`, `dto_b-original.img`, `RELATORIO.txt`, and `SHA256SUMS.txt`.

Partition dumps:
- `boot_b-original.img`: 67,108,864 bytes; SHA-256 `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`. Independent hash matches the device-side report.
- `dto_b-original.img`: 16,777,216 bytes; SHA-256 `080acf35a507ac9849fcba47dc2ad83e01b75663a516279c8b9d243b719643e`. Independent hash matches the device-side report. All 16 MiB are zero-filled in this exact dump.

Boot B header:
- Magic: `ANDROID!`.
- Header version field at offset 40: 1.
- Page size: 2048.
- Kernel size: 12,785,442 bytes.
- Kernel load address: 0x80008000.
- Ramdisk size: 19,092,140 bytes.
- Ramdisk load address: 0x81000000.
- Second stage size: 0.
- Tags address: 0x80000100.
- Kernel payload begins at file offset 2048.
- Ramdisk begins at file offset 12,787,712.
- Gzip kernel stream decompresses successfully and leaves the appended FDT collection as trailing payload.

Seven valid FDT v17 blobs were independently parsed from the Boot B kernel payload. Each contains 1,471 nodes and is approximately 253.7 KiB. The stock C100 Deen FDT is at offset `0x00b7820a`, size 253,704 bytes, model `deen`, compatible `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`, MSM ID `0x125/0`, board ID `0x4d/0xc100`. A C200 Deen FDT is also present at offset `0x00abe4f6`. Other FDTs include other MSM8953 board IDs and an SDM450 Deen FDT.

This proves that the supplied stock Boot B contains a C100 FDT. It does not prove which FDT the bootloader selects at runtime. The zero-filled DTO B dump is only an observation about that exact partition image; it does not prove that all firmware ignores the partition.

## 4. DTB artifacts and structural integrity

Latest identity/schema artifact `14180369413` was downloaded and inspected:
- PVT1 DTB: 23,966 bytes; SHA-256 `2c5fb810fdfcae65768167327bdb4ac4ba824aea6cfa2dc4b5117838aa9ae442`.
- PVT2 DTB: 23,934 bytes; SHA-256 `5998d09cae4ebb4b65ebc2e7085ae83ae61ac5a7b8ae6adf3c725f753f20ecff`.
- PVT1 readback: MSM ID `125 0`, board ID `4d c100`.
- PVT2 readback: board ID `4d c200`.
- Root compatible chain now matches stock C100: `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`.

Structural artifact `14180977348` confirms, in the compiled FDT:
- CPU0..CPU7 are present.
- Each CPU has separate L1 instruction and data cache children.
- L1 and L2 use `arm,arch-cache`.
- L2 nodes are placed below CPU0 and CPU4, with level 2 and CPU-to-L2 phandle links.
- PVT1/PVT2 identity fields are correct.

This is a narrow structural gate only. It does not validate all hardware nodes or runtime bootability.

## 5. Candidate versus stock C100 coverage

The selected stock C100 FDT has 1,471 nodes and 253,704 bytes. The latest PVT1 candidate has 248 nodes and 23,966 bytes.

The current property/path diff reports:
- 44 common node paths.
- 1,427 stock node paths absent from candidate.
- 204 candidate-only node paths.
- 104 missing properties on common node paths.
- 16 candidate-only properties on common paths.
- 26 differing raw property values on common paths.

These are path/property inventory metrics, not a direct one-to-one semantic device mapping. Nevertheless, they confirm a major coverage gap. The current DTB is a minimal bring-up candidate, not stock-equivalent.

### High-risk stock resources not yet reconciled

Stock C100 contains a large device graph absent or materially different in the candidate, including:
- SMEM at `/soc/qcom,smem@86300000` and SMD/SMSM channels for modem, WCNSS, ADSP and RPM.
- Modem/MSS, ADSP loader, WCNSS WLAN and SMP2P endpoints.
- PM8953/PMSI resources, USB controller/PHY, SDHCI, thermal and many other peripherals.
- Reserved memory for `other_ext_region`, modem, ADSP, WCNSS, DFPS, splash, ramoops, TZ log, watchdog CPU context, plus dynamic/reusable shared pools.

Stock C100 fixed reservations include:
- other_ext_region: 0x84300000 / 0x02500000 (37 MiB).
- modem: 0x86c00000 / 0x06a00000.
- ADSP firmware: 0x8d600000 / 0x01100000.
- WCNSS firmware: 0x8e700000 / 0x00700000.
- DFPS: 0x90000000 / 0x1000.
- splash: 0x90001000 / 0x013ff000.
- ramoops: 0xef000000 / 0x000c0000.
- TZ log: 0xaefd2000 / 0x2000.
- watchdog CPU context: 0xaefd4000 / 0x2c000.

Candidate currently models some of these ranges with different names/semantics, including a 32 MiB qseecom reservation at the start of stock's 37 MiB other_ext region, generic memory@ nodes for modem/ADSP/WCNSS, and missing stock ramoops/TZ-log/watchdog/splash pools. These are not proven equivalent. Do not alter memory addresses, sizes, labels or no-map/reusable semantics without tracing every firmware and driver consumer and validating overlaps.

## 6. Binding/schema status

No cache-specific diagnostics remain in the latest schema report after the ARM cache topology/compatible correction.

Remaining diagnostics in run 17 include:
- zero-sized root memory placeholder (also present in stock and described as bootloader-populated; do not invent RAM bounds);
- SMEM reserved-memory binding mismatch: candidate places `qcom,smem` on a reserved-memory node rather than reproducing the stock SMEM device node + memory-region relationship;
- SMD RPM / RPMPD property pattern mismatches;
- TSENS compatible oneOf mismatch;
- GCC clock property pattern mismatch;
- SPMI reg tuple count;
- PM8xxx RTC reg/reg-names;
- DWC3 compatible, clock-names and interrupt count;
- APCS mailbox compatible list cardinality.

### TSENS — hardware contract mismatch, not just a schema warning

Stock C100 TSENS node:
- Path: `/soc/tsens@4a8000`.
- Compatible: only `qcom,msm8953-tsens`.
- Registers: `0x4a8000/0x2000` and `0xa4000/0x1000`.
- Register names: `tsens_physical`, `tsens_eeprom_physical`.
- Interrupts: SPI 184 and 314; names `tsens-upper-lower`, `tsens-critical`.
- 15 sensors; client IDs 1..15; sensor IDs 1..15; 15 slope values of 0xc80; `qcom,valid-status-check`.

Current candidate TSENS node instead uses `qcom,msm8953-tsens` plus `qcom,tsens-v2`, two 0x1000 TM/SROT ranges at 0x4a9000 and 0x4a8000, 16 sensors, and omits stock sensor-ID/slope mapping. The existing vendor 3.18 driver maps `qcom,msm8953-tsens` to TSENS_TYPE3 and parses the legacy properties. The ACK 5.15 generic v2 match is not proof of TYPE3 equivalence.

**TSENS status: HOLD.** Port/adapt the MSM8953 TYPE3 implementation to 5.15, preserve stock resources/calibration/IDs, then add the specific OF match and binding. Do not relabel the stock node as generic v2.

## 7. Gate decisions

| Gate | Result |
|---|---|
| Repository/branch inventory | PASS |
| Latest main sanity CI | PASS (repository only) |
| Latest C100 identity/build CI | PASS |
| Boot B/DTO B raw hash + image audit | PASS (read-only) |
| Seven embedded FDTs parsed | PASS |
| CPU/cache structural gate | PASS (narrow) |
| Schema/bindings | REVIEW_REQUIRED |
| Full C100 DT semantic equivalence | HOLD / major gap |
| Memory/SMEM/firmware/IPC equivalence | HOLD |
| TSENS implementation compatibility | HOLD |
| Full Deen kernel Image/modules | NOT APPROVED |
| Boot image repackaging / runtime boot / flash | HOLD |

## 8. Next permitted engineering sequence

1. Preserve stock backups and hashes; no handset writes.
2. Build a subsystem-level stock-to-candidate semantic reconciliation matrix.
3. Reconcile reserved-memory and SMEM first, tracing all consumers and firmware.
4. Port modem/MSS, ADSP and WCNSS/SMP2P graphs only after matching exact ACK 5.15 drivers and firmware expectations.
5. Port TSENS TYPE3 from the donor driver with exact stock registers, interrupts, sensor IDs and slopes.
6. Reconcile RPM/PMIC, GCC, SPMI/RTC, USB/APCS and other board peripherals in isolated commits.
7. After each subsystem: DTB compile, schema report, property-level stock diff, overlap/reference checks and artifact hash verification.
8. Only after full semantic DT coverage and a Deen-specific config are reviewed should the project proceed to full Image/modules, Full LTO on a suitably provisioned host, and then boot packaging analysis.

No boot image was generated, no partition was written, no merge to main was made, and no flashing is approved by this audit.
