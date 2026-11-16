# Deen XT1941-3 — repository, CI, Boot B and DTB audit

Audit date: 2026-11-16
Repository: `isabe8499-oss/kernel_motorola_msm8953-5.15`
Default branch: `main`
Target source branch: `deen/c100-schema-reconcile-v2`

## 1. Repository and branch state

The repository is accessible and its default branch is `main`.
Branches present at audit time:
- `main` — 2a93c7563d3ee78934790d6b48810d20decc4b9a
- `deen/c100-schema-reconcile-v2` — 372a9ae6591f15b691f68cdbd2e6971f2d91c108
- `deen/bringup`
- `deen/bringup-ack515-base`
- `deen/c100-dtb-match`
- `deen/c100-dtb-validation`
- `deen/dts-bringup`
- `deen/msm8953-remoteproc-backports`
- `ack/android14-5.15-base`
- `upstream/android14-5.15-lts`
- `ci/kernel-build`

Keep the experimental Deen DTS branch separate from the base kernel branches. No merge to main is approved by this audit.

## 2. Latest GitHub Actions

### Latest C100 identity/schema run
- Run: 43763534296
- Commit on main: 2a93c7563d3ee78934790d6b48810d20decc4b9a
- Job: 132963421860 — completed success
- Artifact: 14180369413, 580,968 bytes
- Source branch actually fetched by the workflow: `deen/c100-schema-reconcile-v2`
- Source commit actually built: 372a9ae6591f15b691f68cdbd2e6971f2d91c108

Identity/build succeeded for PVT1 and PVT2. Schema step is diagnostic-only and its exit code is zero even with emitted validation findings; classification is `REVIEW_REQUIRED`, not PASS.

### Latest structural gate
- Run: 43762367961
- Job: 132959778552 — completed success
- Artifact: 14180977348
- Experimental source fetched: `deen/c100-schema-reconcile-v2` at 10f0142545dd614ef6ec2629a3db8889ec43a674
- It asserted eight CPU nodes, eight L1 I-cache and eight L1 D-cache nodes, two L2 cache nodes, and their phandle links; compiled PVT1/PVT2 and checked C100/C200 metadata.

This structural gate is a narrow CPU/cache/identity test. It does not establish complete stock-tree equivalence or kernel bootability.

## 3. Boot B and DTO B binary audit

The uploaded `Deen_Boot_B_Audit.zip` contains:
- `boot_b-original.img`: 67,108,864 bytes (64 MiB)
- `dto_b-original.img`: 16,777,216 bytes (16 MiB)
- `RELATORIO.txt`
- `SHA256SUMS.txt`

Checksums verified against the archive:
- boot_b: `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`
- dto_b: `080acf35a507ac9849fcba47dc2ad83e01b75663a516279c8b9d243b719643e`

DTO B is entirely zero-filled (0 non-zero bytes). Treat this as an observation about this exact partition dump; do not infer undocumented bootloader behavior from it.

Boot B:
- Magic: `ANDROID!`
- Header version word at offset 40: `1`
- Page size: 2048
- Kernel size: 12,785,442 bytes
- Ramdisk size: 19,092,140 bytes
- Second stage size: 0
- Kernel begins at offset 2048; ramdisk begins at offset 12,787,712.

Seven valid FDT blobs were parsed inside the kernel payload. All are 253,700–253,704 bytes and each has 1,471 nodes. Their root identity tuples include:
- C100 stock FDT: offset `0x00b7820a`, MSM ID `0x125/0`, board ID `0x4d/0xc100`.
- C200 stock FDT: offset `0x00abe4f6`, MSM ID `0x125/0`, board ID `0x4d/0xc200`.
- Other FDTs have board IDs 0x47/0xb1a0, 0x47/0xb200, 0x48/0xa100 (SDM450), 0x47/0xa200 and 0x47/0xb1b0.

The C100 FDT root compatible is:
`qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`.

This confirms that the stock boot_b payload contains a Deen MSM8953 C100 FDT. It does not prove the bootloader's selection algorithm or whether the exact same image is currently active on the user's device.

## 4. Candidate PVT1 vs stock C100 FDT

The latest identity workflow artifact reports:
- Candidate PVT1 DTB: 23,966 bytes, 248 nodes.
- Stock C100 FDT: 253,704 bytes, 1,471 nodes.

An independent FDT structure comparison confirms:
- 1,427 stock node paths are absent from the current candidate.
- 204 candidate node paths are not in the stock C100 FDT.

This is a major coverage gap. The candidate is a minimal bring-up DTB, not a complete device tree. Its CPU/cache structural gate passing must not be interpreted as full Deen DT coverage.

## 5. Binding/schema findings from latest CI

No cache-specific schema diagnostics were emitted in the latest run after the ARM cache representation was changed to `arm,arch-cache` with two L2 nodes at level 2. The CPU/cache structural assertions pass.

Remaining reported schema issues include:
- root memory node has a zero-sized `reg` placeholder;
- `memory@86300000` SMEM binding mismatch (required `memory-region`, property pattern mismatch);
- SMD RPM / RPMPD child-property pattern mismatches;
- TSENS compatible pair `qcom,msm8953-tsens`, `qcom,tsens-v2` rejected by the current oneOf list;
- GCC clock binding property mismatch;
- SPMI reg list too long;
- PM8xxx RTC reg/reg-names mismatch;
- DWC3 compatible, clock names and interrupt list mismatch;
- APCS mailbox compatible list too long.

These diagnostics require comparison with the stock C100 FDT and the exact ACK 5.15 driver/binding revision. Do not remove properties or substitute unrelated compatibles simply to obtain a clean schema report.

## 6. Gate decision

| Gate | Status |
|---|---|
| Repository and branch inventory | PASS |
| Latest identity/build CI | PASS |
| Structural CPU/cache CI | PASS (narrow scope) |
| Boot B checksum and header audit | PASS (read-only analysis) |
| DTO B checksum and zero-fill check | PASS (observation only) |
| C100 stock FDT extraction | PASS |
| Full candidate-vs-stock DT coverage | FAIL / major gap |
| Binding/schema | REVIEW_REQUIRED |
| Complete memory/firmware/peripheral equivalence | HOLD |
| Full kernel Image/modules | NOT YET APPROVED |
| Boot image repackaging/flash | HOLD |

## 7. Next work, in order

1. Preserve this audit as the baseline; no merge or flash.
2. Generate a machine-readable property-level diff for the C100 stock FDT against candidate PVT1, grouped by subsystem and risk.
3. Reconcile high-risk reserved-memory regions and SMEM/modem/MSS/ADSP/WCNSS consumers from stock evidence.
4. Reconcile TSENS, RPM/PMIC, GCC, SPMI/RTC, USB and APCS using exact driver and binding contracts.
5. Expand the candidate DTS only through small subsystem patches and repeat DTB + schema + stock-diff checks.
6. Only when the full device tree is materially reconciled, proceed to full kernel Image/modules and later boot packaging.

No boot image was generated, no partition was written, and no flash is authorized by this audit.
