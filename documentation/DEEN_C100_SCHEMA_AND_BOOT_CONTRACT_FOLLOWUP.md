# Deen C100 schema and boot-contract engineering follow-up

Audit date: 2026-11-15
Target: Motorola One Deen XT1941-3 / MSM8953 / PVT1 (bootloader hwrev PVT1, Android property hwrev 0xC100).

## A. Verified smoke-test evidence

The prior GitHub Actions run 43743256412 produced PVT1 and PVT2 DTB artifacts and binary metadata readback:
- PVT1: MSM ID 0x125/0, board ID 0x4D/0xC100.
- PVT2: board ID 0x4D/0xC200.
This is only a minimal DTB identity/build smoke test using generic arm64 defconfig. It is not a complete device-tree build or bootability test.

## B. Schema diagnostics — safe disposition

### L1/L2 cache nodes
The common MSM8953 DTSI models L1 instruction and data caches as separate child nodes and points the CPUs/clusters at L2 nodes. The L1 nodes are currently generic `compatible = "cache"` entries without cache-level metadata. The correct conservative repair is to supply only the missing level metadata after checking the exact cache binding in this tree. Do not mark split I-cache/D-cache nodes as unified. Do not claim cache schema clean until the compiled PVT1 DTB passes the same pinned schema.

### TSENS
The board DTS uses `qcom,msm8953-tsens` with `qcom,tsens-v2` fallback. The pinned generic binding does not list the first compatible, but that alone does not justify substituting another SoC's compatible. Check the TSENS driver match table, register map, interrupts, calibration data and stock C100 DTB. If the driver explicitly supports `qcom,tsens-v2` as a fallback and the MSM8953 register layout matches that v2 implementation, extend the binding with a properly documented MSM8953 entry in a separate patch. Otherwise preserve the DTS and record a vendor binding exception until the correct binding is established.

### Schema workflow governance
Keep schema diagnostics visible and independently reported. The identity/build smoke test may remain green while schema remains REVIEW_REQUIRED; never label that as full device tree PASS. A separate strict schema gate should fail when diagnostics remain after all supported bindings are reconciled. Pin the dtschema package version and use the schema from the same kernel commit being built.

## C. Boot-contract evidence from user-provided captures

The device reports:
- `ro.boot.bootdevice=7824900.sdhci`
- `ro.boot.slot_suffix=_a`
- `ro.boot.hardware=qcom`
- `ro.boot.hardware.sku=XT1941-3`
- `/proc/device-tree/model=deen`
- `/proc/device-tree/compatible`: qcom,msm8953-deen; qcom,msm8953-moto; qcom,msm8953
- `ro.boot.bootheader.version` is empty; the generic bootimage property query only found `ro.bootimage.build.type=user`.
- boot_a and boot_b are 64 MiB. dto_a and dto_b are 16 MiB. vbmeta slots are 64 KiB. The captured by-name partition inventory contains boot_a/b, dto_a/b, vbmeta_a/b, system_a/b, vendor_a/b, modem_a/b and dsp_a/b; it does not show vendor_boot or recovery partitions.
- boot images begin with `ANDROID!`, header version field at offset 40 reads 1, page size 2048, and the old boot header layout contains kernel+ramdisk+embedded DTBs.
- dto_a and dto_b dumps were fully zero-filled. This is an observation about the captured dumps, not proof that every boot path ignores those partition labels.
- Fastboot reports product=deen, board=deen, hwrev=PVT1. Android property reports ro.boot.hwrev=0xC100.

## D. Boot packaging gate — HOLD

Do not assume a modern boot/vendor_boot split or modern header version. The current evidence is consistent with a legacy Android boot image v1 carrying an appended DTB collection. Before packaging:
1. Audit the stock boot_a and boot_b complete headers with a known AOSP boot image parser and independently verify kernel/ramdisk sizes, DTB offsets and trailing data.
2. Inspect stock bootloader/kernel command line and bootconfig handling without modifying partitions.
3. Determine how the bootloader selects among appended DTBs (MSM ID/board ID matching) from the Qualcomm/Motorola boot chain or a controlled stock boot trace. Do not infer selection solely from one matching FDT.
4. Verify the exact partition map and AVB/vbmeta constraints for the current firmware.
5. Define a reversible recovery path and verify the stock images are backed up before any future experiment.
6. Only then choose the exact boot image header/packing utility and create a host-side unpack/repack round-trip test where repacked stock boot parses identically and sizes/offsets remain valid.

No flashable image is approved by this document.

## E. Next engineering order

1. Use a source-tree-pinned cache binding; make only narrowly justified cache metadata changes and re-run PVT1 schema.
2. Resolve TSENS through driver+stock-DTB+binding evidence. Do not use a different SoC compatible as a shortcut.
3. Reconcile high-risk memory reservations from stock C100 first, especially modem/MSS, ADSP, WCNSS, SMEM, QSEE and firmware regions. Trace every consumer and firmware name; check overlap/alignment.
4. Reconcile IPC (SMD/SMSM/SMP2P/GLINK if present), remoteproc and firmware handoff.
5. Bring up PMIC/SPMI, regulators, clocks, pinctrl, storage, USB, display, touch, GPU, camera, audio and sensors in isolated patches.
6. Build a complete PVT1 DTB and a full kernel Image/modules only after semantic DT coverage is reviewed.
7. Keep AOSPA Android 14 and boot package integration blocked until kernel ABI, vendor compatibility and boot contract are established.

## Status

- C100 identity smoke: PASS.
- Minimal PVT1/PVT2 DTB compile: PASS.
- Schema: REVIEW_REQUIRED / HOLD.
- Full stock-DTB semantic equivalence: HOLD.
- Full kernel 5.15 image: not yet proven by this smoke test.
- Boot image format/packing: HOLD.
- Flashing: not authorized.
