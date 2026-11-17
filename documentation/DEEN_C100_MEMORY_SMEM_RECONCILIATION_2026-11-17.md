# Deen C100 — memory / SMEM reconciliation ledger

> **ERRATUM / SUPERSEDING CORRECTION (2026-11-17):** The original revision overstated the evidence by describing a proven candidate 32+1+4 MiB partition. That conclusion is withdrawn. The stock FDT audit establishes a 37 MiB `other_ext_region` reservation and separately identifies an SMEM device node at `/soc/qcom,smem@86300000`. It does **not** establish that SMEM is a 1 MiB carveout inside `other_ext_region`, nor that `[0x86400000,0x86800000)` is a distinct candidate reservation or has a known consumer. The 32 MiB candidate QSEE fixed reservation merely ends at the SMEM node's base address; adjacency is not ownership equivalence. The corrected gate is HOLD pending raw stock FDT property/phandle extraction and candidate-source inspection. See sections 2, 4 and 6 below. The earlier 32+1+4 MiB partition claim is superseded and must not be used for implementation decisions.

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

## 2. Stock other_ext, QSEE and SMEM — corrected evidence

The stock C100 FDT audit establishes:
- `other_ext_region@0`: base `0x84300000`, size `0x02500000` (37 MiB), compatible `removed-dma-pool`, with `no-map`.
- A separate stock SMEM device node at `/soc/qcom,smem@86300000` (path and unit address recorded in the sequenced audit).
- Stock also contains dynamic/reusable shared-dma-pool nodes for ADSP, GPU, QSEECom, secure and Venus; their fixed `reg` values are not present in the summarized FDT audit and must be recovered from the raw FDT properties and references.

The candidate evidence recorded in the stock-vs-candidate audit is:
- `qseecom@84300000`: fixed 32 MiB no-map reservation, spanning `[0x84300000, 0x86300000)`.
- Candidate has separate entries beginning at `0x86300000` and `0x86400000`, but their exact semantics and sizes are not established by the audit summary.
- The candidate SMEM representation was flagged by schema diagnostics: it places `qcom,smem` on a reserved-memory node rather than reproducing the stock SMEM device node plus its memory-region relationship.

**Confirmed arithmetic only:** the candidate QSEE interval ends at `0x86300000`, the same base encoded in the stock SMEM node path. This proves adjacency of two addresses only. It does not prove that SMEM occupies the next 1 MiB, that the 4 MiB interval `[0x86400000,0x86800000)` exists as a candidate reservation, or that either interval is owned by `other_ext_region`.

**Withdrawn conclusion:** the prior claim that QSEE 32 MiB + SMEM 1 MiB + another 4 MiB forms a confirmed candidate partition of the stock 37 MiB `other_ext_region` is unsupported and superseded. Do not use that partition as a design assumption.

Required evidence before any DTS change:
1. Parse the selected raw stock C100 FDT node `/reserved-memory/other_ext_region@0` and `/soc/qcom,smem@86300000`; record exact `compatible`, `reg`, `#address-cells`, `#size-cells`, `ranges`, `no-map`, `reusable`, hwlock, RPM message-RAM references and phandles.
2. Enumerate all stock nodes with `memory-region`, `memory-region-names`, QSEE/QSEECom, secure shared-memory, SMEM and DMA-pool references; resolve each phandle to its target node.
3. Recover exact candidate DTS source and compiled DTB for the same commit. Do not infer candidate sizes or labels from an address appearing in a diagnostic.
4. Identify all consumers of the 32 MiB candidate QSEE reservation and any entries at `0x86300000` / `0x86400000`; prove whether they are device resources, carveouts, suballocations or unrelated address ranges.
5. Trace the ACK 5.15 QSEE/SCM, SMEM, RPM/SMD and remoteproc consumers, including hwlock and RPM message RAM contracts.
6. Confirm DRAM bounds and all reservations from the actual C100 stock FDT/boot handoff; do not infer RAM size from the zero-filled root memory reg placeholder.
7. Run an interval checker over the complete normalized inventory, modelling parent envelopes and subregions explicitly.

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
| QSEE/SMEM address adjacency | OBSERVED (arithmetic only; no ownership conclusion) |
| other_ext/QSEE/SMEM semantic ownership | HOLD |
| 4 MiB interval consumer identification | OPEN |
| Modem/ADSP/WCNSS firmware and memory-region mapping | HOLD |
| SMEM/SMD/SMSM/SMP2P graph equivalence | HOLD |
| Full reserved-memory overlap/reference validation | NOT RUN |
| Full PVT1 DT schema gate | REVIEW_REQUIRED |
| Full kernel Image/modules integration | HOLD |
| Boot repackaging, runtime boot and flashing | NOT APPROVED |

## Final decision

The address arithmetic establishes only that the candidate 32 MiB QSEE interval ends at the stock SMEM node's unit address. It does not establish a 32+1+4 MiB partition of stock other_ext_region. The memory/SMEM implementation remains blocked on exact stock node properties, candidate source provenance, QSEE/SMEM consumers, the unexplained candidate entry at 0x86400000, the full reservation inventory, and the remoteproc/IPC resource graph.

No DTS or driver code was changed by this work. No boot image was generated and no device partition was written.
