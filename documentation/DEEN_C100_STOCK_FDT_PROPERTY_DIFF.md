# C100 stock FDT property-level comparison

Source of truth: `boot_b-original.img` from `Deen_Boot_B_Audit.zip`.
Selected stock FDT offset: `0x00b7820a`.
Stock FDT size: 253,704 bytes; 1,471 nodes.
Candidate: latest PVT1 DTB from run 43763534296, 23,966 bytes; 248 nodes.

## Comparison totals

- Common node paths: 44
- Stock node paths absent from candidate: 1,427
- Candidate-only node paths: 204
- Missing properties on common nodes: 104
- Candidate-only properties on common nodes: 16
- Properties with differing raw values on common nodes: 26

Missing node groups:
- SoC/peripherals: 1,402
- Reserved memory: 14
- Firmware: 5
- Board data: 3
- Aliases: 1
- HW metadata: 1
- U-tags: 1

This confirms that the current candidate is a deliberately small bring-up DTB, not a near-complete stock C100 tree. The passing CPU/cache structural gate covers only a small part of the hardware contract.

## Boot B parsing

Boot B SHA-256: `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`.
Magic: `ANDROID!`; page size: 2048; header version word: 1.
Kernel payload: 12,785,442 bytes starting at offset 2048.
Ramdisk: 19,092,140 bytes starting at offset 12,787,712.
Seven FDT blobs were found inside the kernel payload. The C100 matching blob is at `0x00b7820a`; another Deen MSM8953 blob is C200 at `0x00abe4f6`.
The C100 stock root is `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`, MSM ID `0x125/0`, board ID `0x4d/0xc100`.

DTO B SHA-256: `080acf35a507ac9849fcba47dc2ad83e01b75663a516279c8b9d243b719643e`; size 16 MiB; every byte is zero in this captured dump.

## Reserved-memory comparison — high risk

Stock C100 defines these named regions (address/size):
- `adsp_fw_region`: 0x8d600000 / 0x01100000
- `modem_region`: 0x86c00000 / 0x06a00000
- `other_ext_region`: 0x84300000 / 0x02500000
- `wcnss_fw_region`: 0x8e700000 / 0x00700000
- `dfps_data_mem`: 0x90000000 / 0x1000
- `splash_region`: 0x90001000 / 0x013ff000
- `ramoops_mem_region`: 0xef000000 / 0x000c0000
- `tzlog_bck_region`: 0xaefd2000 / 0x2000
- `wdog_cpuctx_region`: 0xaefd4000 / 0x2c000
- plus stock ADSP/GPU/QSEECOM/VENUS shared/reusable pools whose reg is supplied dynamically or by firmware and must be recovered from the complete source/boot data.

Candidate currently has different labels/coverage:
- `memory@84300000` is absent; instead it has `qseecom@84300000` with size 0x02000000, while stock `other_ext_region` spans 0x02500000. Do not assume these are equivalent.
- Candidate includes a `memory@86c00000` region matching the stock modem range numerically but lacks the stock `modem_region` name/compatible semantics.
- Candidate has the ADSP firmware and WCNSS numeric ranges, but not all stock named memory pools/consumers.
- Candidate lacks the stock ramoops and TZ log/watchdog CPU-context regions.

Do not change these addresses or sizes without checking every consumer (remoteproc, firmware loader, ramoops, display, QSEE and bootloader carveouts) and ensuring no overlap.

## Schema result — latest run 43763534296

CI step status is success because schema is diagnostic-only and exits 0; classification remains REVIEW_REQUIRED. Findings include root memory placeholder, SMEM, RPM/RPMPD, TSENS compatible, GCC, SPMI, RTC, DWC3 and APCS binding mismatches. Cache diagnostics no longer appear in this latest log after the ARM cache representation change.

## Decision and next action

- Repository/branch inventory: complete.
- Latest identity/build CI: pass.
- Narrow CPU/cache structural gate: pass.
- Boot B and DTO B binary audit: complete.
- Binding/schema: review required.
- Full candidate-vs-stock coverage: not approved (major gap).
- Full kernel/boot packaging/flash: HOLD.

Next work is to generate and review a subsystem-by-subsystem DTS expansion plan from this diff, starting with reserved-memory + SMEM + remoteproc firmware dependencies, then PMIC/RPM and core SoC resources. No image packaging or flashing until the stock C100 contract is substantially reconciled.
