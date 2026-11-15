# Deen C100 DTB identity and boot-evidence audit

Audit date: 2026-11-15
Repository: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15

## Executive status

**C100 is a candidate, not yet a verified bootloader DTB match.** The handset reports `ro.boot.hwrev=0xC100` in Android, but the available device capture does not include read-only `fastboot getvar board` / `fastboot getvar hwrev`, nor an extracted stock DTB/DTBO proving the bootloader's matching tuple.

The isolated C100 candidate adds `qcom,msm-id = <0x125 0>;` and retains `qcom,board-id = <0x4D 0xC100>;`. This is a source-level candidate assertion. It is not proof that `0x125 0` is the exact tuple in the installed stock boot chain.

## Verified repository state

- Experimental branch: `deen/c100-dtb-validation`.
- Candidate commit: `e363945f62eed0a20c7b5fb5edb00c26370b25b0`.
- Workflow: `.github/workflows/deen-c100-dtb-validation.yml`, manual `workflow_dispatch`.
- The workflow has source assertions, compiles PVT1/PVT2 DTBs, reads back root metadata with `fdtget`, and runs the Qualcomm binding/schema checks.
- GitHub commit status for the candidate commit returned no status checks, and the connector's commit-associated workflow query returned no runs. Those queries do not enumerate manual dispatch runs. Therefore **no successful C100 workflow run has been verified in this audit**.
- The workflow's report currently derives its displayed `RESULT` primarily from whether DTB files exist; the final job gate separately checks build and schema step outcomes. Treat the report summary together with the actual job conclusion and schema log, not the summary label alone.

## Device evidence received

From the XT1941-3 capture:

- `ro.product.device=deen`
- `ro.product.board=msm8953`
- `ro.boot.hardware=qcom`
- `ro.boot.hardware.sku=XT1941-3`
- `ro.boot.hwrev=0xC100`
- `ro.boot.slot_suffix=_a`
- `/proc/device-tree/model=deen`
- `/proc/device-tree/compatible` contains `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`.

Partition inventory captured:

- boot_a / boot_b: 67,108,864 bytes each.
- dto_a / dto_b: 16,777,216 bytes each.
- vbmeta_a / vbmeta_b: 65,536 bytes each.
- system_a / system_b: 2,684,354,560 bytes each.
- vendor_a / vendor_b: 536,870,912 bytes each.
- The captured by-name listing did not show vendor_boot or recovery entries. Recheck before packaging; absence from this listing is not a universal statement about other firmware layouts.

Read-only image observations:

- boot_a begins with Android boot magic `ANDROID!`.
- A four-byte field read at offset 40 returned `1`, consistent with the legacy header-version field; confirm by unpacking the complete image with a boot-image parser.
- boot_a and boot_b partition sizes match at 64 MiB.
- boot_b SHA-256: `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`.
- dto_b SHA-256: `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e`.

**Important evidence gap:** the device-side archive command failed because `toybox zip` is unavailable. The raw boot_b/dto_b dumps were written to the phone's `/sdcard/Deen_Boot_B_Audit/` directory, but the ZIP was not created and those binary dumps were not delivered for direct inspection. The hashes above are from the device-side report, not independently recomputed here.

## Required next gates

1. Run only read-only fastboot queries: `fastboot getvar product`, `fastboot getvar board`, `fastboot getvar hwrev`. Do not collect `fastboot getvar all`.
2. Transfer the existing raw boot_b and dto_b files individually or package them using a known installed archiver; verify their SHA-256 after transfer.
3. Unpack boot_a and boot_b with a boot-image parser and inspect embedded DTB/DTBO content. Extract the stock DTB root `compatible`, `qcom,msm-id`, and `qcom,board-id` where present.
4. Run the manual C100 workflow and retain its run URL, conclusion, job logs, schema log, DTB binaries, and readback hashes. A successful metadata-only workflow still does not prove bootloader selection.
5. Reconcile the candidate's minimal common DTSI against stock resources, firmware, memory reservations, regulators, clocks, resets, storage and peripherals before considering a device-specific image.
6. Do not create or flash a boot image until boot layout, PVT tuple, DTB selection, and a known-good rollback path are independently confirmed.

## Safety boundary

PVT1/PVT2 DTS files remain experimental candidates. No DTB is approved for the handset based only on Android properties or a source-level grep. No flash, boot image publication, or AOSPA integration is authorized by this audit.

## Addendum — stock boot_b and bootloader evidence (2026-11-15)

The user supplied a read-only fastboot capture:
- `fastboot getvar product` → `deen`
- `fastboot getvar board` → `deen`
- `fastboot getvar hwrev` → `PVT1`

The user supplied `Deen_Boot_B_Audit.tar`. The archive contains the raw 64 MiB `boot_b-original.img`, the raw 16 MiB `dto_b-original.img`, a report, and SHA256SUMS. The locally recomputed SHA-256 values match the report:
- boot_b: `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`
- dto_b: `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e`

The dto_b image is entirely zero-filled (16,777,216 zero bytes). The boot_b image is an Android boot image with header version 1 and contains seven valid FDT blobs. One Deen MSM8953 FDT contains:
- model: `deen`
- compatible: `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`
- `qcom,msm-id = <0x125 0>`
- `qcom,board-id = <0x4D 0xC100>`

This independently confirms that the C100 tuple exists in the supplied stock boot_b image and agrees with the bootloader's PVT1 report. It does not establish which of the seven FDTs the bootloader selects at runtime.

The stock C100 FDT is 253,704 bytes and has 1,471 nodes. The compiled experimental PVT1 candidate from the validation artifact is 23,818 bytes and has 248 nodes. Therefore, matching root identity metadata must not be confused with full DTB equivalence. The current candidate remains non-flashable and is not approved for boot testing.

The experimental PVT1/PVT2 root `model` and `compatible` values were aligned to the observed stock Deen root values. The validation workflow was tightened so any non-empty `dt-validate` diagnostics produce a HOLD rather than a misleading PASS.


## Addendum — CI schema diagnostics (run 43735105437)

The push-triggered validation run completed source assertions, minimal ACK configuration, and compilation of both PVT1/PVT2 DTBs successfully. The job failed only at the Devicetree schema validation step; the report and artifact upload completed. This is an intentional HOLD gate, not a compiler failure.

Observed diagnostics include:
- PVT1 SDC1/SDC2 pinctrl state nodes missing required `function` properties.
- PVT1 GCC clock-controller `clocks`/`clock-names` schema mismatch.
- PVT1 SPMI `reg` tuple length mismatch and PM8xxx RTC `reg`/`reg-names` mismatch.
- PVT1 DWC3 compatible, clock-name and interrupt-count mismatches.
- PVT1 APCS mailbox compatible-list mismatch.
- PVT1 TSENS compatible is not accepted by the pinned current binding schema.
- PVT2 root compatible list is not accepted by the current Qualcomm root schema; its memory node contains a zero-sized/zero-address `reg` tuple.
- PVT2 cache nodes are missing required cache metadata; PVT2 TSENS also has a compatible mismatch.

These findings must be investigated against the supplied stock C100 FDT and the exact ACK 5.15 binding revision. Do not silence diagnostics, delete hardware nodes, invent register ranges, or change clocks/interrupts merely to obtain a green workflow. First determine whether each issue is (a) a real DTS defect, (b) a donor-tree/5.15 schema-version mismatch, or (c) an inherited vendor binding exception. Record each disposition with evidence before changing the DTS.

Current gate: **HOLD — DTBs compile, schema validation fails with diagnostics. No flashable DTB or boot image is approved.**


## Addendum — reproducible stock FDT structural inventory (2026-11-15)

The raw `boot_b-original.img` and the PVT1/PVT2 DTBs from Actions artifact `deen-c100-dtb-validation` were independently parsed with a standalone FDT structure reader.

The boot image contains seven valid FDT blobs. The exact tuple `qcom,msm-id = <0x125 0>` and `qcom,board-id = <0x4D 0xC100>` selects the stock FDT at byte offset 12,026,378:
- stock C100: 253,704 bytes, 1,471 nodes.
- PVT1 candidate: 23,822 bytes, 248 nodes.
- root `model` and three-entry `compatible` list match exactly.
- structural path inventory: 1,429 stock-only paths, 206 candidate-only paths, 42 common paths.
- among common paths, 98 stock property names are absent from the candidate and 16 candidate property names are not in stock.

The PVT2 control tuple `<0x4D 0xC200>` also selects one of the seven stock FDTs (offset 11,265,270); its matching candidate has 248 nodes and 23,790 bytes. The C100 and C200 stock blobs are both 253,704 bytes and 1,471 nodes, but this does not make PVT2 relevant to the user's PVT1 device.

**Interpretation:** this candidate is a minimal ACK/mainline-derived foundation, not a port of the complete stock vendor tree. Node-path differences include major topology differences (stock uses a large `/soc` tree while the candidate uses a smaller `/soc@0` tree), so raw path counts are an inventory signal, not a one-to-one count of missing physical devices. However, the current candidate is plainly far from a full stock-equivalent device tree. It must not be flashed.

A dependency-free audit utility was added at `scripts/deen_dtb_audit.py` on the experimental branch. Example:
```sh
python3 scripts/deen_dtb_audit.py boot_b-original.img msm8953-motorola-deen-pvt1.dtb \
  --msm-id 0x125,0 --board-id 0x4d,0xc100 --json c100-audit.json
```
The utility scans FDT blobs in a raw boot image, selects an exact MSM/board tuple, and reports node/property inventory. It explicitly does not claim semantic equivalence or bootability.

Current gate remains **HOLD**. Next work is a subsystem-by-subsystem semantic comparison and source reconciliation against stock/known-good Deen DTS, not mass-copying the 4.19 vendor tree or suppressing schema diagnostics.


The same binary inventory compared `compatible` strings across all nodes:
- stock C100 FDT: 255 unique compatible strings.
- candidate PVT1: 56 unique compatible strings.
- 235 stock compatible strings do not appear verbatim in the candidate.

The absent stock strings include vendor-specific entries for camera/ISP, display/MDSS, audio/QDSP, modem/MSS, GPU/ KGSL, IPA/networking, Wi-Fi/WCNSS, PMIC/charger/battery, sensors, and extensive debug/coresight infrastructure. Some vendor strings may map to different upstream compatibles or drivers, so this is not proof that every absent string needs to be copied literally. It is a subsystem inventory showing how much semantic reconciliation remains. Do not blindly add all 235 strings: map each stock function to the corresponding ACK 5.15 driver, binding, resources, and firmware contract first.


## Addendum — reserved-memory and schema cross-check

A direct read of the stock C100 FDT and the compiled PVT1 DTB shows that the broad 0x84300000–0x86800000 span is represented differently:
- Stock: one `other_ext_region@0` reservation at 0x84300000, size 0x02500000 (37 MiB).
- Candidate: `qseecom@84300000` at 0x84300000/0x02000000 (32 MiB), plus adjacent 0x86300000/0x00100000 and 0x86400000/0x00400000 regions. Their combined span is also 37 MiB, but labels, consumers and semantics are not yet proven equivalent.

The following stock reservation ranges are visible in the selected C100 FDT:
- modem: 0x86c00000/0x06a00000
- ADSP firmware: 0x8d600000/0x01100000
- WCNSS firmware: 0x8e700000/0x00700000
- DFPS data: 0x90000000/0x00001000
- splash: 0x90001000/0x013ff000
- ramoops: 0xef000000/0x000c0000
- TZ log backup: 0xaefd2000/0x00002000
- watchdog CPU context: 0xaefd4000/0x0002c000

The candidate has exact-address/size entries for modem, ADSP, WCNSS and DFPS. Its splash reservation is intentionally absent in the current minimal bring-up. It does not yet reproduce the stock ramoops, TZ-log or watchdog-context reservations; it also has additional reservations (including 0x91400000, 0x92000000 and 0xf2d00000) that require consumer/firmware reconciliation. Do not change these ranges until their consumers and firmware contracts are identified.

The root `/memory` node has a 16-byte zero-filled `reg` property in both the stock C100 FDT and candidate PVT1 DTB. Thus the schema's zero-sized memory diagnostic is also present in the stock source artifact and must be treated as a bootloader-populated/vendor convention pending validation of the boot path, not "fixed" by inventing RAM bounds.

The audit utility now also emits reserved-memory inventories and compatible-string inventories. This is intended to make range/consumer mapping reproducible while retaining the warning that inventory is not semantic equivalence.


## Addendum — subsystem presence comparison from stock C100 FDT

A targeted inventory of the selected stock C100 FDT versus the current minimal candidate found the following high-priority gaps:

| Subsystem | Stock C100 FDT evidence | Current candidate evidence | Disposition |
|---|---|---|---|
| Modem/MSS | `qcom,pil-q6v55-mss`, firmware name `modem`, modem memory-region reference | No corresponding MSS/PIL node | HOLD; port driver binding, memory-region and firmware contract |
| ADSP | `qcom,adsp-loader`, ADSP SMD/SMSM endpoints, ADSP firmware and shared-memory reservations | No corresponding ADSP loader/SMD endpoint set | HOLD; reconstruct remoteproc/ADSP path |
| WCNSS/Wi-Fi | `qcom,wcnss_wlan`, WCNSS SMD/SMSM and SMP2P endpoints, firmware reservation | No corresponding WCNSS device/endpoints | HOLD; Wi-Fi firmware and transport path absent |
| Shared memory / IPC | Stock SMEM node plus modem/WCNSS/ADSP SMD/SMSM and SMP2P endpoints | Candidate has generic `/smd/rpm` and `/smsm/apps@0`, not the complete stock endpoint graph | HOLD; reconstruct channels and state links |
| USB | Stock vendor DWC3/PHY/USB configuration | Candidate SoC USB node remains disabled in the minimal base | Not yet enabled; preserve until PHY, clocks, interrupts and role-switch contract are mapped |
| Display/camera/audio | Numerous stock MDSS, camera/ISP, codec and QDSP nodes | Not represented in the minimal board layer | HOLD; subsystem ports remain future work |

This inventory is why the earlier successful MSS/ADSP/Pronto object compilation must not be interpreted as device-tree or firmware integration. Compiling driver objects proves only that selected source files build. It does not create the missing stock device nodes, IPC topology, memory references, firmware names, or runtime handshakes.

The first full subsystem port should focus on **memory/SMEM + modem/MSS + ADSP + WCNSS/SMP2P**, because those components share reserved memory and IPC dependencies. Before enabling them, trace each stock `memory-region` phandle to its reservation, verify the ACK 5.15 driver binding and firmware filename, and map every SMD/SMSM/SMP2P channel. Keep the minimal candidate isolated until each dependency has an evidence-backed port.


## Addendum — verified C100 smoke artifact run 43743256412 (2026-11-15)

GitHub Actions run 43743256412 completed with conclusion `success` (job 132900852859). All job steps relevant to the smoke test passed: source checkout, metadata assertions, generic arm64 defconfig, PVT1/PVT2 DTB compilation, binary readback, report creation and artifact upload. Artifact ID: 14173266850 (`deen-c100-dtb-validation`, 580,955 bytes; not expired at audit time).

The artifact ZIP was downloaded and inspected. It contains both non-empty DTBs, readback, build log, generated schema JSON, schema diagnostics and report. SHA-256 values independently recomputed from the extracted DTB files:
- PVT1: `7ec387d579630fd213f68d134c76cd6721d960b2ec5ecde14b0d0453abc0fed7` (23,798 bytes).
- PVT2: `e4965e060ab04a5b9e2a10670570fe9be7a8a5b15d8f62da48861f5409c0a19b` (23,766 bytes).

Binary readback from `fdtget`:
- PVT1 `qcom,msm-id = 125 0`, `qcom,board-id = 4d c100`.
- PVT2 `qcom,board-id = 4d c200`.

Schema result remains `REVIEW_REQUIRED`. The validator process returned exit status 0 but emitted repeated cache schema diagnostics (`cache-level`, `cache-unified`) and a thermal sensor compatible `oneOf` diagnostic. This is not a clean schema pass. The workflow intentionally treats schema as a separate diagnostic classification so identity/build smoke success does not conceal the warnings.

**Gate status:** G1 identity PASS; G2 minimal DTB build PASS; G3 schema REVIEW_REQUIRED; G4 semantic full-device-tree port HOLD; G5 boot package HOLD. This run built only a minimal candidate with generic arm64 `defconfig`. It did not compile a full kernel Image, did not validate hardware semantics, did not verify bootloader DT selection, and does not authorize flashing.
