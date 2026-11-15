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
