# Source reconciliation: Motorola Deen board-level common include

Target branch: `deen/c100-schema-reconcile-v2`
Date: 2026-11-15
Source file: `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi`
Current blob SHA: `3f9b941d2b609727b32b47481272378601bf286d`

## Finding

The structural workflow run `43754524992` failed during DTC compilation, after source inventory passed. Errors reported unresolved labels `spmi_bus`, `/reserved-memory`, `pm8953_resin`, `rpm_requests`, and `sdhc_1`.

Reinspection confirms this file's source content is not enough to infer the cause solely by searching for those labels. The correct root of the failure is the actual preprocessed translation unit and include order used by the workflow, not a text grep. This report records the exact source snapshot to prevent stale assumptions.

## Required validation

1. Capture full preprocessed DTS for PVT1/PVT2 using the exact Kbuild DTC command with `-E`/preprocessor output preserved.
2. Inspect `scripts/Makefile.lib` and `DTC_FLAGS`, confirm that CPP includes the same source directory and common includes.
3. Verify that the PVT DTS starts with `/dts-v1/;`, then includes board common, which includes SoC and PMIC DTSI, and that every `&label` reference occurs after a definition in the preprocessed stream.
4. Do not invent empty label definitions or add phandles purely to suppress unresolved-reference errors.
5. After fixing the build command/include composition, compile DTBs and assert CPU/cache nodes plus PVT1/PVT2 identity by reading the binaries.

## Gate

Current state: **HOLD**. No full structural build approval, no full-kernel approval, and no boot/flash approval.
