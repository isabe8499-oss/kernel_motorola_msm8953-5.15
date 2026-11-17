# Deen XT1941-3 — live repository state verification

Audit date: 2026-11-17 (latest API snapshot)
Repository: `isabe8499-oss/kernel_motorola_msm8953-5.15`
Target: Motorola One Deen XT1941-3 / MSM8953 / stock C100 (PVT1)
ROM goal: AOSPA Android 14
Kernel base: ACK Android Common Kernel 5.15 LTS

## Executive result

The requested sequence was rechecked against live GitHub refs, recent commits, Actions runs/jobs/artifacts, the actual Boot B/DTO B archive available in the working session, and the latest committed stock-FDT reconciliation reports.

**Decision: do not advance to device integration or boot packaging yet.** The repository and several narrow build gates pass. The stock Boot B/DTO B evidence is hash-verified and the embedded stock C100 FDT is identified. However, the candidate remains a minimal bring-up tree with major gaps versus stock. Schema is REVIEW_REQUIRED. A proposed SMEM correction exists on a separate branch but has not been built or schema-validated.

## 1. Live repository and branch state

- Repository is accessible; default branch is `main`.
- `main` HEAD at this snapshot: `06cd601572a1f9f0e1032f2041424d2e08e28ae2` (commit message: `docs: record Nov 17 sequenced Deen gate audit`).
- Latest push reported by GitHub: 2026-11-17T16:12:16Z.
- Repository permissions returned for the linked connection include admin/push.
- Main's latest commit is documentation-only; it does not merge the experimental Deen DTS or ACK source branches.

Current relevant refs:
- `ack/android14-5.15-base`: `465a6eaea4d73813ebc479eed763c1f0c888803f`
- `upstream/android14-5.15-lts`: `5cb316cf9d39318326075731e4e0c39b725d9c99`
- `deen/bringup`: `9c9742fb756790889bf8a83c365cfa0742932aa4`
- `deen/bringup-ack515-base`: `5cb316cf9d39318326075731e4e0c39b725d9c99`
- `deen/dts-bringup`: `12aa70c6b6f9f2a9b438edf44a78785c15b6ec23`
- `deen/c100-schema-reconcile-v2`: `372a9ae6591f15b691f68cdbd2e6971f2d91c108`
- `deen/c100-memory-smem-reconciliation`: `6496f53fb8120b2f6f62146547ee9b9bfd49384a`
- `deen/c100-smem-memory-region-fix`: `8dd376a6291729fd388622d6058fa8a0e0cd5df5`
- `deen/c100-dtb-match`: `42926baf8c3a3b68d23753b3bef0d92912065dab`
- `deen/c100-dtb-validation`: `ca715ed21813ee98eca6e714cedff7d2993bdf1a`
- `deen/msm8953-remoteproc-backports`: `12366f09d36b13ab47eec139ea4aec574c59fdef`
- `ci/kernel-build`: `bc232d2eb95c416aaa26b36f6d00b49e920c18d0`

Branch relationships:
- `deen/c100-smem-memory-region-fix` is exactly one commit ahead of `deen/c100-schema-reconcile-v2`, modifying only `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi` (+22 lines). The diff separates the SMEM platform device from the reserved-memory node and gives it `memory-region = <&smem_mem>`, RPM message-RAM and hwlock references. This is a proposed correction only; it has no verified CI result yet.
- `deen/c100-memory-smem-reconciliation` is three commits ahead of `main`, and its changes are documentation-only. Its ledger includes an explicit erratum withdrawing the earlier unsupported claim that stock `other_ext_region` is proven to be a 32+1+4 MiB QSEE/SMEM partition. It explicitly leaves memory/SMEM on HOLD.
- `deen/c100-schema-reconcile-v2` is 58 commits ahead of the pinned upstream ACK branch. It remains experimental and is not merged into `main`.
- Some independently imported kernel branches have unrelated histories; GitHub compare reports no common ancestor for direct comparisons against `main`. Do not infer that they are safe to merge by branch name alone.

## 2. Latest GitHub Actions

Latest repository-wide run:
- `44073094414` — Repository sanity checks, `main`, commit `06cd601572a1f9f0e1032f2041424d2e08e28ae2`, completed success. Job `134004023982`.
- This is repository sanity only; it does not compile the kernel or DTB.

Latest device-specific validation runs still present in Actions:
- `43763534296` — Deen C100 DTB identity validation, completed success; job `132963421860`; artifact `14180369413` (580,968 bytes). It fetched `deen/c100-schema-reconcile-v2` at `372a9ae6591f15b691f68cdbd2e6971f2d91c108`.
- `43762367961` — Deen C100 structural gate, completed success; job `132959778552`; artifact `14180977348`. It compiled the source snapshot `10f0142545dd614ef6ec2629a3db8889ec43a674`.
- No newer device-specific DTB/schema or structural run appears after `43763534296`; the more recent Actions runs are repository sanity checks.

Historical but relevant build gates:
- `43684266664` — generic GKI + Deen DTB full Image feasibility build, completed success; artifact `14150664185`.
- `43697546575` — GKI plus Deen base-fragment Kconfig/object audit, completed success; artifact `14155361150`.

### Schema interpretation

Run `43763534296` completed successfully for DTB compilation, board-ID readback and artifact upload. Its schema step is explicitly `continue-on-error: true` and logs diagnostics for both PVT1 and PVT2. The report classifies schema as `REVIEW_REQUIRED`, not PASS.

Remaining PVT1/PVT2 diagnostics include:
- zero-sized root memory placeholder;
- SMEM device/reserved-memory modeling (`memory-region` required; `reg`/`no-map` rejected on the SMEM device binding);
- SMD RPM / RPMPD child property shape;
- TSENS compatible `oneOf` mismatch;
- GCC clock binding properties;
- SPMI reg tuple count;
- PM8xxx RTC reg/reg-names;
- DWC3 compatible/clock names/interrupt shape;
- APCS mailbox compatible list cardinality.

The latest schema run has no cache diagnostics after the ARM cache topology correction. Do not reintroduce cache changes without evidence.

## 3. Boot B / DTO B archive independently checked in this session

Archive path in the working session: `/mnt/data/Deen_Boot_B_Audit.tar`.
- TAR size: 83,891,200 bytes.
- TAR SHA-256: `e946172035f563cc0e1189b82306eed972848c2041604f12e8a7f0fefaea4b8a`.
- Archive contains `boot_b-original.img`, `dto_b-original.img`, `RELATORIO.txt`, `SHA256SUMS.txt`.

Recomputed partition image hashes match the report:
- Boot B: 67,108,864 bytes; SHA-256 `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`.
- DTO B: 16,777,216 bytes; SHA-256 `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e`.
- DTO B has 0 non-zero bytes in this exact dump. This does not prove every boot chain/firmware version ignores the partition.

Boot B fields parsed from raw bytes:
- Magic `ANDROID!`.
- Header version at offset 40: 1.
- Page size: 2048.
- Kernel size: 12,785,442 bytes; load address 0x80008000.
- Ramdisk size: 19,092,140 bytes; load address 0x81000000.
- Second stage size: 0.
- Tags address: 0x80000100.
- Kernel payload starts at file offset 2048.
- Ramdisk starts at offset 12,787,712.
- The gzip stream within the kernel field terminates successfully; it is followed by an appended FDT collection. A naive whole-field gzip decompression fails because of that trailing FDT payload; this is expected for the observed concatenated layout.

Seven FDT v17 blobs were found and structurally parsed inside Boot B:
- Each has 1,471 nodes and size 253,700–253,704 bytes.
- Stock C100 Deen FDT: offset `0x00b7820a`, size 253,704, compatible `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`, MSM ID `0x125/0`, board ID `0x4d/0xc100`.
- Stock C200 Deen FDT: offset `0x00abe4f6`, board ID `0x4d/0xc200`.
- Other blobs include MSM8953 variants and one SDM450 Deen variant.

This proves the supplied Boot B image contains a C100 FDT; it does not prove which FDT the bootloader selects at runtime. Do not assume first-FDT selection.

## 4. Candidate DTB versus stock FDT

The committed stock-to-candidate report records:
- Stock C100 FDT: 1,471 nodes, 253,704 bytes.
- Candidate PVT1 DTB from run `43763534296`: 248 nodes, 23,966 bytes.
- 44 common node paths.
- 1,427 stock node paths absent from candidate.
- 204 candidate-only node paths.
- 104 missing properties and 26 differing raw property values on common paths.

These are inventory/diff counts, not a complete semantic mapping, but they establish that the candidate is a minimal bring-up DTB and not stock-equivalent.

Structural gate run `43762367961` confirms compiled CPU0..CPU7, separate L1 I/D cache nodes, L2 nodes/links and PVT1/PVT2 identity. This is narrow structural evidence only.

## 5. Existing kernel build and config work — artifact re-inspected

### Full Image feasibility build
Artifact `14150664185` downloaded and inspected:
- Contains a 39,483,904-byte ARM64 `Image`.
- Image SHA-256: `85584de409a2dbb019286532d53dcb3e6c07bf82ea46629035c28d9abe2191c8`.
- Contains PVT1/PVT2 DTBs (23,786 bytes each).
- Build used source branch `deen/dts-bringup`, commit `8345f67abd78a0b6fc8e776c9279d9c88cdc5356`.
- Config was generic GKI plus MSM8953 platform/PMIC/eMMC options.
- Compiler Clang 18.1.3.
- LTO/CFI profile: ThinLTO + CFI. Full LTO is not validated.
- It is not a Deen-specific final defconfig, not a boot.img and not a hardware boot test.

### Defconfig/object audit
Artifact `14155361150` downloaded and inspected:
- 20 selected MSM8953 bring-up symbols survive GKI `olddefconfig`.
- Fragment: `arch/arm64/configs/deen-msm8953-base.fragment` on `deen/dts-bringup`.
- The audit also requires remoteproc Kconfig symbols and compiles 13 selected platform/remoteproc objects according to the workflow.
- This is a minimal base fragment/object audit, not a complete Deen device defconfig or full Image build using that fragment.

## 6. Critical memory / SMEM and TSENS decisions

### Memory/SMEM
The branch `deen/c100-memory-smem-reconciliation` contains a corrective erratum: stock evidence establishes a 37 MiB `other_ext_region` and a separate SMEM device node at `/soc/qcom,smem@86300000`, but does not prove that the region is a 32+1+4 MiB partition. That earlier claim is withdrawn.
- Candidate PVT1 DTB has 32 MiB QSEE reservation, a 1 MiB `qcom,smem` reserved-memory node and an unnamed 4 MiB reservation. The arithmetic is contiguous; ownership equivalence is unproven.
- The schema rejects the current candidate SMEM layout because the platform device should have a `memory-region` phandle rather than being modeled as a reserved-memory node itself.
- A separate branch `deen/c100-smem-memory-region-fix` proposes exactly that device/region separation. It is one commit ahead of the schema branch, modifies only the common Deen DTSI, and has no CI validation yet.
- Do not merge or trust that patch until a branch-specific DTB build, schema run, stock property/phandle diff and interval/consumer audit pass.

### TSENS
The stock C100 FDT TSENS contract is `qcom,msm8953-tsens`, 15 sensors, stock register windows/names, two interrupts, sensor IDs/client IDs 1..15 and 15 slope values of 0xc80. The candidate instead describes a 16-sensor generic v2 arrangement with different windows and omits the stock mapping. The donor 3.18.140 driver maps this compatible to TSENS_TYPE3. The ACK 5.15 generic v2 fallback is not proof of equivalence.
**TSENS remains HOLD.** Port/adapt the TYPE3 implementation and preserve stock resources/calibration before adding the 5.15 OF match/binding.

## 7. Gate matrix and next permitted actions

| Gate | Status |
|---|---|
| Repository/branch inventory | PASS |
| Latest main sanity workflow | PASS (repository only) |
| Latest C100 identity/DTB compile | PASS (narrow) |
| Structural CPU/cache gate | PASS (narrow) |
| Boot B/DTO B archive and image hash audit | PASS (read-only) |
| Seven stock FDTs parsed; C100 identified | PASS |
| Schema/bindings | REVIEW_REQUIRED |
| Candidate versus stock DT coverage | HOLD — major gap |
| Memory/SMEM ownership and device-region mapping | HOLD |
| TSENS TYPE3 contract | HOLD |
| Full Image feasibility | PASS with generic GKI + ThinLTO/CFI only |
| Deen-specific full defconfig | NOT COMPLETE |
| Full LTO | NOT VALIDATED |
| Boot image repackaging/runtime boot/flash | HOLD |

Next permitted sequence:
1. Validate `deen/c100-smem-memory-region-fix` in an isolated workflow; do not merge it yet.
2. Extract exact raw stock and candidate FDT properties/phandles for `other_ext_region`, QSEE/QSEECom, SMEM and all memory-region consumers; build a full reservation/consumer ledger.
3. Reconcile stock memory and SMEM model before modem/MSS, ADSP or WCNSS enablement.
4. Port TSENS TYPE3 separately with stock calibration/interrupt resources.
5. Reconcile RPM/PMIC, GCC, SPMI/RTC, DWC3 and APCS using exact 5.15 driver contracts.
6. Repeat PVT1/PVT2 DTB build, schema diagnostics, property diff and overlap/reference validation after every isolated subsystem patch.
7. Only after semantic DT coverage, firmware/IPC and Deen defconfig are approved should full Image/modules and boot packaging proceed.

No boot image was generated, no partition was written, no merge to main was made, and no flashing is approved by this audit.
