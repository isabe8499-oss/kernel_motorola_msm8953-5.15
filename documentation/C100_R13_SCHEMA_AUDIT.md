# C100 run 13 schema audit

Date: 2026-11-15
Workflow run: 43751213115
Job: 132925353673
Artifact ID: 14176253326
Artifact SHA-256: cc000ae044f65efdcf251c8f411ad86ddb1aeb5a03a3d1e5bd0cf562fc1dbe55

## Verified build and identity
- Both PVT1 and PVT2 DTBs compiled in the identity smoke test.
- PVT1 readback: msm-id 125 0; board-id 4d c100.
- PVT2 readback: board-id 4d c200.
- PVT1 output size in run 13: 24,054 bytes.
- PVT2 output size in run 13: 24,022 bytes.
- This is a minimal DTB-only build, not a complete device tree or kernel Image.

## Actual schema diagnostics from both DTBs
1. `l1-icache` and `l1-dcache`:
   - cache-level 1 rejected because the generated generic cache schema has minimum 2;
   - cache-unified is required;
   - cache-level is rejected as unevaluated.
2. `l2-cache_0` and `l2-cache_1`:
   - cache-unified is required.
3. `thermal-sensor@4a9000`:
   - compatible array `qcom,msm8953-tsens`, `qcom,tsens-v2` fails the selected binding's oneOf/ordered compatible patterns.
4. PVT2 also has additional diagnostics:
   - memory@86300000 missing memory-region and no-map/reg property pattern mismatch under qcom,smem binding;
   - rpm-requests / power-controller binding property pattern mismatches.
   
These are emitted by the generic schema across this old/vendor-style device tree and need reconciliation against the exact ACK 5.15 bindings and upstream DTS representation.

## Important correction to previous understanding
The source DTS does contain `cache-level = <1>` for separate L1 I/D cache nodes and `cache-level = <2>` for L2 nodes. The diagnostic is caused by the generated schema's generic cache constraint, not missing level properties. Do not label cache-level as absent. Do not mark split L1 I/D caches unified purely to satisfy the schema. Inspect the cache binding inherited by this kernel commit, the dtschema-generated JSON, and canonical ARM cache descriptions before patching.

## TSENS
The source DTS declares:
- `compatible = "qcom,msm8953-tsens", "qcom,tsens-v2"`
- TM range 0x4a9000/0x1000 and SROT range 0x4a8000/0x1000
- 16 sensors
- interrupts 184 and 314 named `uplow` and `critical`

The driver has generic `qcom,tsens-v2` fallback matching data_tsens_v2, but this alone does not prove the MSM8953 TSENS IP/calibration variant. Preserve the current compatible array until stock C100 DTB and driver registers/calibration are independently reconciled. A binding extension may be submitted only with evidence and proper schema documentation.

## Workflow governance
- Run 13 status success indicates the build/readback smoke job completed.
- Schema step is diagnostic-only and `continue-on-error`; schema classification is REVIEW_REQUIRED, not PASS.
- Do not merge schema changes into main until a clean validator run or explicitly documented, reviewed vendor binding exception exists.

## Next actions
1. Compare cache node structure and phandles against the stock C100 FDT.
2. Compare TSENS resources and sensor count/calibration metadata against stock C100 FDT and the exact TSENS v2 driver.
3. Review memory@86300000 and RPM-related nodes against matching qcom,smem.yaml/qcom,smd-rpm.yaml/rpmpd bindings; avoid transplanting PVT2-only warnings into PVT1 fixes.
4. Split schema logs/report per variant and preserve every diagnostic.
5. Keep boot image, full kernel, and flashing gates blocked.

## Follow-up: restoration of MSM8953 CPU/cache source (2026-11-15)

A temporary source-edit attempt used the contents API on `arch/arm64/boot/dts/qcom/msm8953.dtsi` and replaced the file body unintentionally. This was immediately detected by re-fetching the branch file and corrected by restoring the intended minimal eight-core source. Current file blob SHA: `3c4b5cc577a8e19c9970ac185a8ad4fca652eae4`.

Re-fetch verification after restoration:
- CPU nodes: 8 (CPU0 through CPU7).
- Separate `l1-icache` child nodes: 8.
- Separate `l1-dcache` child nodes: 8.
- L2 cluster cache nodes: 2.
- L1 nodes retain `cache-level = <1>`; L2 nodes retain `cache-level = <2>` and `cache-unified`.
- Root memory node still has zero reg, which is bootloader-populated/minimal placeholder behavior and must not be treated as a complete memory map.
- This source restoration has NOT yet been validated by a fresh compile. The last successful artifact predates the restoration and must not be cited as validating this source snapshot.

Next step: run an isolated compile of PVT1/PVT2 from the restored branch and verify the CPU/cache nodes in the produced binary before further schema edits.