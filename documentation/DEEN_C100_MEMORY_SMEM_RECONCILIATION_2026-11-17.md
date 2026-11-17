# Deen C100 — memory / SMEM reconciliation ledger

Date: 2026-11-17
Repository: `isabe8499-oss/kernel_motorola_msm8953-5.15`
Target: Motorola One Deen XT1941-3, MSM8953, C100/PVT1
Working branch: `deen/c100-memory-smem-reconciliation`
Base: `main` at `06cd601572a1f9f0e1032f2041424d2e08e28ae2`

## Scope and safety boundary

This is a read-only evidence reconciliation document. It does not modify DTS/DTSI, driver code, Kconfig, firmware, boot images, or device partitions. It does not authorize merging, boot packaging, or flashing.

Inputs are the previously audited user-provided Boot B archive and the committed stock-FDT binary/property reports:
- `documentation/DEEN_SEQUENCED_GATE_AUDIT_2026-11-17.md`
- `documentation/DEEN_C100_STOCK_FDT_BINARY_RECONCILIATION.md`
- `documentation/DEEN_C100_STOCK_FDT_PROPERTY_DIFF.md`
- `documentation/DEEN_REMOTEPROC_INTEGRATION_AUDIT.md`

The source of truth for the stock board layout is the C100 FDT extracted from Boot B at offset `0x00b7820a`, with MSM ID `0x125/0` and board ID `0x4d/0xc100`. Donor 4.19 DTS and upstream Linux DTS are corroborating references, not substitutes for the stock C100 FDT.

## 1. Interval arithmetic — confirmed

All ranges below are represented as half-open intervals `[start, end)`; end is computed as `start + size`.

### Stock fixed ranges recorded from the C100 FDT audit

| Region | Start | Size | End (exclusive) |
|---|---:|---:|---:|
| other_ext_region | `0x84300000` | `0x02500000` (37 MiB) | `0x86800000` |
| modem_region | `0x86c00000` | `0x06a00000` (106 MiB) | `0x8d600000` |
| adsp_fw_region | `0x8d600000` | `0x01100000` (17 MiB) | `0x8e700000` |
| wcnss_fw_region | `0x8e700000` | `0x00700000` (7 MiB) | `0x8ee00000` |
| dfps_data_mem | `0x90000000` | `0x00001000` | `0x90001000` |
| splash_region | `0x90001000` | `0x013ff000` | `0x91400000` |
| ramoops | `0xef000000` | `0x000c0000` | `0xef0c0000` |
| tzlog_bck_region | `0xaefd2000` | `0x00002000` | `0xaefd4000` |
| wdog_cpuctx_region | `0xaefd4000` | `0x0002c000` | `0xaf000000` |

The fixed modem, ADSP and WCNSS intervals are exactly adjacent:
- modem ends at `0x8d600000`, where ADSP begins;
- ADSP ends at `0x8e700000`, where WCNSS begins.
No gap or overlap exists between those three recorded firmware ranges.

The DFPS and splash intervals are also exactly adjacent: splash ends at `0x91400000`.

The TZ log and watchdog CPU-context intervals are exactly adjacent: TZ log ends at `0xaefd4000`, where watchdog context begins.

These arithmetic checks establish interval relationships only. They do not prove that all consumers, attributes, cacheability, ownership, or boot-time reservations are equivalent.

## 2. Important geometric correspondence inside other_ext_region

The stock FDT audit records:
- `other_ext_region`: `[0x84300000, 0x86800000)`, 37 MiB.
- stock SMEM device node at `0x86300000`, with a 1 MiB region recorded in the candidate/common SoC description.

The current candidate source description records these adjacent intervals:
- QSEE candidate: `[0x84300000, 0x86300000)`, 32 MiB.
- SMEM candidate: `[0x86300000, 0x86400000)`, 1 MiB.
- adjacent candidate reserved interval: `[0x86400000, 0x86800000)`, 4 MiB.

Arithmetic:
- `0x84300000 + 0x02000000 = 0x86300000`
- `0x86300000 + 0x00100000 = 0x86400000`
- `0x86400000 + 0x00400000 = 0x86800000`
- `32 MiB + 1 MiB + 4 MiB = 37 MiB`

**Finding:** the three candidate intervals form an exact, contiguous geometric partition of the stock `other_ext_region` envelope. There is no gap or overlap between those three candidate intervals, and their combined span exactly equals the stock envelope.

**Do not overstate this finding.** The stock FDT's `other_ext_region` node and the candidate's QSEE/SMEM/adjacent nodes do not automatically have equivalent ownership or driver semantics. The stock FDT also has its own SMEM node and QSEE-related shared/dynamic pool descriptions. The 4 MiB candidate interval at `0x86400000` has not yet been mapped to a named stock consumer. The candidate QSEE fixed reservation may not be equivalent to the stock dynamic/reusable QSEECom pool. This is a promising address-layout correspondence, not an approval to retain or change the candidate definitions.

Required proof before any DTS change:
1. Identify every stock FDT node that references `other_ext_region`, SMEM, QSEE/QSEECom, secure shared memory, and any related memory-region phandle.
2. Recover the exact stock node properties: compatible, reg, no-map, reusable, alignment, alloc-ranges, memory-region, and phandle references.
3. Trace the 5.15 QSEECom/SCM, SMEM, RPM, remoteproc and firmware consumers that claim or map these ranges.
4. Establish whether the 4 MiB interval is a separate pool, a suballocation, a bootloader carveout, or an unused portion; do not infer from its size.
5. Confirm DRAM bounds and all other reservations from the actual C100 stock FDT/boot handoff. Do not infer RAM size from the zero-filled root memory reg placeholder.
6. Run an interval overlap checker against the complete normalized reservation inventory, while explicitly modelling intentional parent-envelope/subregion relationships rather than treating every containment as a collision.

## 3. Remote firmware memory ranges

| Consumer candidate | Start | Size | End | Current evidence |
|---|---:|---:|---:|---|
| MPSS / modem | `0x86c00000` | `0x06a00000` | `0x8d600000` | Stock FDT range recorded; remoteproc resource/firmware mapping not approved |
| ADSP firmware | `0x8d600000` | `0x01100000` | `0x8e700000` | Stock FDT range recorded; PAS/firmware/SMEM mapping not approved |
| WCNSS firmware | `0x8e700000` | `0x00700000` | `0x8ee00000` | Stock FDT range recorded; Pronto/WLAN integration not approved |

The isolated remoteproc branch has compiled MSS, ADSP PAS and Pronto-v3 objects. That object-level result does not validate the board DTS contract.

Before activating any remoteproc node, the following must match the exact driver probe contract:
- firmware filename and search path (including MBA/MPSS, ADSP and WCNSS MDT/BIN components);
- `memory-region` phandle and exact region size;
- register resources and interrupt names/counts;
- clocks, resets, regulators and power-domain names/order;
- PAS IDs and subsystem-specific resource descriptors;
- SMEM item IDs, SMD edge IDs, SMP2P remote PIDs and state-bit names;
- sysmon/SSCTL IDs and crash/stop/ready handshakes;
- dump/recovery behavior and Android vendor userspace expectations.

Current donor-to-5.15 audit explicitly says the 4.19 Deen board disables modem, ADSP and WCNSS SMP2P endpoints. Do not enable these endpoints merely because the 5.15 driver objects compile.

## 4. SMEM / IPC evidence ledger

| Item | Current evidence | Missing proof / disposition |
|---|---|---|
| SMEM physical region | Candidate description has `0x86300000/0x00100000`; stock FDT contains an SMEM device node at this address | Confirm stock node's exact compatible, properties, hwlock, RPM message RAM reference and memory ownership |
| RPM message RAM | Candidate MSM8953 SoC DTS has `rpm_msg_ram` at SoC offset `0x60000`, size `0x8000` | Match stock FDT resource and ACK 5.15 RPM/SMD consumer |
| RPM SMD edge | Candidate description records RPM SMD edge 15 and `rpm_requests` channel | Verify stock edge/channel and RPM driver contract |
| SMSM | Candidate description contains AP-side SMSM node and IPC tuples | Compare stock host/remote state layout and interrupt routing |
| Modem SMD/SMP2P | Donor board disables modem SMP2P endpoint; remoteproc branch has MSS object support | Do not enable until stock C100 endpoint/remote PID/state bits and 5.15 handshake match |
| ADSP SMD/SMP2P | Donor board disables ADSP SMP2P endpoint; ADSP PAS object compiles | Verify SMEM 423, sysmon 1, SSCTL 0x14, interrupts and power/firmware sequence |
| WCNSS SMD/SMP2P | Donor board disables WCNSS SMP2P endpoint; Pronto-v3 object compiles | Verify SMEM 422, sysmon 6, SSCTL 0x13, IRIS, regulators, interrupts and WLAN stack separately |

SMEM IDs above are donor/audit evidence, not a statement that every item is present or correctly routed in the current C100 candidate.

## 5. Required subsystem reconciliation order

1. **Normalize stock reservations:** extract each stock node into a machine-readable ledger with path, compatible, start, size, end, flags, phandles and consumers. Preserve parent-envelope and subregion relationships explicitly.
2. **Resolve other_ext/QSEE/SMEM:** determine whether the 32+1+4 MiB candidate decomposition matches the stock memory ownership model. No address or property edits until this is proven.
3. **Resolve modem/ADSP/WCNSS fixed ranges:** verify exact stock labels and `memory-region` references against remoteproc driver expectations and actual Android 12 vendor firmware.
4. **Resolve IPC graph:** map RPM SMD, SMEM, SMSM, SMD edges, SMP2P endpoints, remote PIDs, interrupts and state bits from stock to ACK 5.15.
5. **Resolve remaining reservations:** DFPS, splash, Venus, GPU, QSEE dynamic pools, ramoops, TZ log, watchdog context, RMTFS and all reusable/shared DMA pools.
6. **Run static checks:** interval containment/overlap checks, phandle/reference checks, exact binding validation with schemas pinned to the same kernel commit, and DTB property-level diff.
7. **Only after review:** make one isolated DTS patch per subsystem, compile the PVT1 candidate, archive logs/DTB hashes, and compare against stock again.

## 6. Acceptance status

| Gate | Status |
|---|---|
| Stock Boot B / C100 FDT identity and hashes | PASS (read-only audit) |
| Fixed interval arithmetic in this ledger | PASS |
| other_ext 32+1+4 MiB geometric partition | PASS (arithmetic only) |
| other_ext/QSEE/SMEM semantic ownership | HOLD |
| 4 MiB interval consumer identification | OPEN |
| Modem/ADSP/WCNSS firmware and memory-region mapping | HOLD |
| SMEM/SMD/SMSM/SMP2P graph equivalence | HOLD |
| Full reserved-memory overlap/reference validation | NOT RUN |
| Full PVT1 DT schema gate | REVIEW_REQUIRED |
| Full kernel Image/modules integration | HOLD |
| Boot repackaging, runtime boot and flashing | NOT APPROVED |

## Final decision

The address arithmetic narrows the memory investigation and identifies a plausible exact decomposition of the 37 MiB stock `other_ext_region`. It does not justify a DTS patch yet. The next implementation step remains blocked on stock node semantics, the unexplained 4 MiB interval, QSEE/SMEM consumers, full reservation inventory, and the remoteproc/IPC resource graph.

No DTS or driver code was changed by this work. No boot image was generated and no device partition was written.
