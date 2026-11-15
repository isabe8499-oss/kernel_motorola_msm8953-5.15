# Deen C100 DTB source reconciliation work plan

Date: 2026-11-15
Target: Motorola One Deen XT1941-3, bootloader hwrev PVT1, stock identity tuple MSM 0x125/0 + board 0x4d/0xc100.

## Current verified state

- Stock boot_b archive was provided and checksum verified.
- Stock boot_b contains seven FDTs; one Deen FDT carries the target tuple.
- The stock C100 FDT has 1,471 nodes and 253,704 bytes.
- Existing minimal ACK 5.15 candidate is only 248 nodes and ~23.8 KiB; it is an identity/build smoke candidate, not a port.
- The original DTB schema workflow run 43739618835 did not reach compilation. Checkout stopped because it asserted the presence of `scripts/deen_dtb_audit.py`, absent from the selected source branch.
- Do not claim any C100 DTB schema PASS from that run.
- The stock DTB's root memory reg is zero-filled, suggesting a bootloader-populated vendor convention. Do not invent physical RAM bounds.
- Stock has an `other_ext_region@0` range 0x84300000/0x02500000; candidate splits the same 37 MiB span across qseecom/smem/other ranges. Semantics need consumer/firmware tracing.

## Critical source reconciliation

The current C100 validation workflow is a *metadata smoke workflow*, not a complete DTB schema workflow. The next iteration must not require non-existent helper scripts or check source assumptions inconsistent with the selected branch.

1. Create a minimal identity/build smoke workflow that:
   - fetches the named source branch and records exact SHA
   - verifies PVT1 contains `qcom,msm-id = <0x125 0>` and `qcom,board-id = <0x4D 0xC100>`
   - verifies PVT2 `qcom,board-id = <0x4D 0xC200>`
   - compiles only PVT1/PVT2 DTBs
   - reads metadata from resulting binary with `fdtget`
   - uploads DTBs, .config, build log, readback and hashes
   - returns identity/build PASS independent of schema state.
2. Put schema checks in a separate non-blocking diagnostic job, pinned to the exact ACK 5.15 schema tree and dtschema version. Report each diagnostic; do not make it a gate until upstream/vendor binding reconciliation is reviewed.
3. Source branch is `deen/c100-schema-reconcile-v2`. It currently has root compatible `motorola,deen`, `qcom,msm8953` and stock identity tuple.
4. PVT2 should remain comparison-only. It is not the user's hardware.
5. Remove `scripts/deen_dtb_audit.py` from mandatory checkout assertions unless the script is committed on the selected source branch and tested.

## Subsystem port order (each step needs a dedicated patch + build + diff report)

A. Stock DTB inventory:
- Export every node path and property from the stock C100 FDT.
- Diff candidate node paths/properties against stock. Classify nodes by: exact upstream binding; legacy vendor binding needing port; obsolete/bootloader-only; unknown.
- Preserve raw stock DTS dump, FDT hash, parser version, and diff artifacts.

B. Memory map:
- Trace each reserved-memory node, labels, consumers, no-map/reusable semantics, and firmware names.
- Reconcile SMEM, modem, ADSP, WCNSS, Venus, QSEE, splash, ramoops, TZ logs, watchdog, RMTFS and all other regions.
- Validate overlap and alignment; do not resize/relabel based only on matching address spans.
- Keep root memory reg bootloader-populated until bootloader contract proves a safe replacement.

C. SMEM/IPC foundation:
- Map RPM, SMD, SMSM, SMP2P, GLINK (if present) endpoints, edge IDs, interrupts, channels, state masks and mutex/hwspinlock providers.
- Check ACK 5.15 compatible strings and drivers; compile the required configs.

D. Remoteproc/firmware:
- MSS/modem PIL: firmware filename, memory-region, q6v5/glink/SMD and handoff/recovery.
- ADSP: firmware name, memory/SMEM, SMD/SMSM, audio DSP clients.
- WCNSS: firmware name, memory region, SMD/SMP2P, WLAN driver transport.
- Verify firmware blobs exist in the stock vendor image and record hashes; don't invent firmware filenames.

E. Core board devices:
- PMIC/SPMI/SSBI, regulator dependencies, clocks, resets, pinctrl, GPIO, thermal, storage, IOMMU and interconnects.
- Compare resources and interrupt count/order to stock and drivers.

F. Peripherals:
- USB PHY/controller/role switch, display/MDSS/DPU, panel, touch, GPU/KGSL, camera/ISP, codecs/audio, NFC, sensors, charger/battery and thermal zones.
- Port each subsystem separately; no blanket `status = "okay"`.

## Gate definitions

- G0 stock evidence: PASS (source dumps/hash present).
- G1 identity: PASS only after binary DTB readback matches MSM/board tuple.
- G2 build: PASS only if DTB compiles, build artifacts are archived and hash verified.
- G3 schema: DIAGNOSTIC only until bindings in the pinned ACK 5.15 tree are reconciled; stock/vendor nodes must not be silenced by deleting properties.
- G4 semantic device-tree port: HOLD until memory/IPC/firmware/peripheral mapping is complete.
- G5 boot package: HOLD until original boot image layout, bootloader DT selection and rollback route are confirmed.
- No flashable image is permitted at this stage.
