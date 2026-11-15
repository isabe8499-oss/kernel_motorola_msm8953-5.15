# Stock Deen C100 boot_b FDT versus ACK 5.15 candidate — binary reconciliation

Audit date: 2026-11-15
Device: Motorola One XT1941-3, bootloader product/board `deen`, bootloader hwrev `PVT1`.
Stock input: user-supplied `Deen_Boot_B_Audit.tar`.

## 1. Backup integrity

The uploaded TAR SHA-256 was recomputed:
`e946172035f563cc0e1189b82306eed972848c2041604f12e8a7f0fefaea4b8a`.

Embedded partition images were recomputed and match the device-side report:
- boot_b: 64 MiB, SHA-256 `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`
- dto_b: 16 MiB, SHA-256 `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e`

The DTO B image is entirely zero-filled. This is a property of the supplied partition dump; it does not prove all firmware versions ignore that partition label.

## 2. Stock FDT inventory

The 64 MiB boot_b image contains seven valid FDT blobs. One FDT at offset `0x00b7820a` has:
- size: 253,704 bytes
- nodes: 1,471
- model: `deen`
- compatible: `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`
- `qcom,msm-id = <0x125 0>`
- `qcom,board-id = <0x4d 0xc100>`

This exactly matches the user's reported PVT1/C100 identity. The same boot_b also contains other board IDs, including a C200 variant and an SDM450 variant. Do not assume the first FDT in the image is the selected one.

## 3. Candidate binary comparison (structural gate artifact)

Artifact from workflow run `43757007156`, artifact ID `14179010778`.
- PVT1: 23,836 bytes, 248 nodes
- PVT2: 23,804 bytes, 248 nodes

PVT1 identity fields were correct, but the pre-reconciliation candidate differed from the stock C100 FDT:
- root compatible in candidate was `motorola,deen`, `qcom,msm8953`; stock root chain is three Qualcomm strings shown above.
- candidate L1 caches used `compatible = "cache"`; stock uses `compatible = "arm,arch-cache"`.
- candidate put two L2 cache nodes at `/cpus/l2-cache_0` and `/cpus/l2-cache_1`; stock attaches each L2 node as `/cpus/cpu@0/l2-cache` and `/cpus/cpu@100/l2-cache`. CPU nodes link to these with `next-level-cache`.
- stock tree includes 1,471 nodes; candidate contains only 248. Raw path diff reports 1,429 stock paths without exact path match and 206 candidate-only paths; this includes naming/parent-path differences such as stock `/soc` versus candidate `/soc@0`. It is not appropriate to label every unmatched path an entirely absent device without semantic normalization.

## 4. Memory reservations — critical HOLD

Stock C100 reserved-memory includes these fixed regions:
- other_ext_region@0: 0x84300000 / 0x02500000 (37 MiB), `removed-dma-pool`, `no-map`
- modem_region@0: 0x86c00000 / 0x06a00000 (106 MiB), `removed-dma-pool`, `no-map`
- adsp_fw_region@0: 0x8d600000 / 0x01100000 (17 MiB), `removed-dma-pool`, `no-map`
- wcnss_fw_region@0: 0x8e700000 / 0x00700000 (7 MiB), `removed-dma-pool`, `no-map`
- dfps_data_mem: 0x90000000 / 0x1000
- splash_region: 0x90001000 / 0x013ff000
- ramoops: 0xef000000 / 0xc0000
- tzlog backup: 0xaefd2000 / 0x2000
- watchdog CPU context: 0xaefd4000 / 0x2c000
- stock also has dynamic/reusable shared-dma-pool nodes for ADSP, GPU, QSEECom, secure and Venus with no fixed `reg` in the FDT.

Candidate currently contains different names and semantics:
- qseecom@84300000 as a fixed 32 MiB no-map reservation at the start of stock's 37 MiB other_ext region;
- separate candidate ranges at 0x86300000, 0x86400000 and other locations;
- generic memory@ nodes for modem, ADSP and WCNSS ranges, rather than the corresponding stock node names/compatibles;
- some stock dynamic reusable pools are absent; candidate has additional fixed reservations.

These layouts are not proven semantically equivalent. Do not split, rename, resize, or reassign these regions until every consumer is traced through drivers, firmware names, bootloader handoff and reserved-memory references. This is a boot-safety blocker.

## 5. Evidence-backed source changes made on the experimental branch

Branch: `deen/c100-schema-reconcile-v2`
- Commit `856326c383e645bf1e40a8e58faff3cfd1c0151c`: changed cache compatible strings to `arm,arch-cache` and moved L2 nodes under cpu@0/cpu@100, preserving the stock split L1 / per-cluster L2 arrangement.
- Commit `35b183c43a03f9a5cb6bd4dec0d819bc97493432`: changed PVT1 root compatible chain to the exact stock Deen chain.
- Commit `10f0142545dd614ef6ec2629a3db8889ec43a674`: same root-compatible correction on PVT2 control.

Workflow gate updates:
- `9188eda6210b724746ff6890706625bb811be581`: structural gate now verifies stock cache topology and cache compatible strings in compiled FDTs.
- `01a0388c46f46d8e42b4d59da3d77f2e13581e8c`: identity/schema workflow source assertions updated to the stock compatible chain.

These changes are still experimental and await the CI runs listed below. No memory map changes were made.

## 6. Revalidation runs

Two structural runs triggered after changes:
- `43762313020` — structural gate, triggered by workflow change.
- `43762367961` — structural gate, triggered by structural gate request marker.
Schema/identity run:
- `43762372326` — identity and schema diagnostic run.

At initial inspection all three were in progress and none was claimed successful. Check their results and artifacts before accepting any of the source changes.

## 7. Next gates

1. Verify all three CI runs and inspect PVT1 compiled DTB root compatible and cache paths.
2. Compare candidate PVT1 reserved-memory nodes with stock C100, property by property and by semantic consumer.
3. Trace modem/MSS, ADSP, WCNSS, QSEECom, Venus, SMEM, RMTFS, ramoops, splash and watchdog references.
4. Only then plan a separate memory-map patch.
5. Reconcile remaining 1,223-node count deficit and exact path differences by subsystem; preserve stock nodes where required and port only supported ACK 5.15 bindings.
6. Keep full Image, boot repackaging and flashing blocked.

**Gate status:** C100 identity evidence PASS; previous candidate DTB smoke/CPU-cache structural test PASS for its then-current source; stock root/cache/memory reconciliation patch awaiting CI; full-tree semantic equivalence HOLD; boot contract HOLD; no flashable artifact approved.
