# Deen MSM8953/PM8953 base DTS compile smoke

- Result: PASS
- Branch: deen/dts-bringup
- Branch commit: 3e694f45e351a0acd6471f451c72e707e8f79e40
- SoC DTSI source: Linux v6.1, blob 6b992a6d56c16d5151785df04fa2053c67ee7fad
- PMIC DTSI source: Linux v6.1, blob a1d36f9ebbd259e41a80e3af516d9a044419afe0
- ACK base: Android Common Kernel 5.15 LTS
- Compiler: Ubuntu clang version 18.1.3 (1ubuntu1)
- Test: generated base fixture plus Deen PVT1/PVT2 DTBs
- dt-doc-validate exit: 0
- dt-mk-schema exit: 0
- targeted dt-validate exit: 0
- compiled DTB board-ID read-back exit: 0
- compiled DTB QSEE/overlap read-back exit: 0
- Backported MSM8953 rpmpd.o SHA-256:
  7080ba714a8135cfb7f48c483ed29bfc6d470e1c490ca0afdb186487bedbfe1d  /home/runner/work/_temp/deen-out/drivers/soc/qcom/rpmpd.o
- Base-only fixture DTB SHA-256: cc6135f44e12cadf1422d817e5d639143bacca0325c582e7cce385864a37da85
- Deen PVT1 DTB SHA-256 (board ID 0x4D 0xC100): 41a0106d6ade5492497a6736a9c930c82f85fe3c909791968f3f7b0726fe5532
- Deen PVT2 DTB SHA-256 (board ID 0x4D 0xC200): c06cc92f0487675277588594e03c1ad49eb5e69ff43ae7924bec2f50cb371055

This is a minimal Deen board-DTS compile/schema smoke test. PVT1/PVT2 wrappers include board IDs 0x4D 0xC100/0xC200. Shared nodes cover QSEE reservation, PM8953 RPM regulators, volume keys and primary eMMC only. Display, touch, GPU, camera, audio, USB, NFC, WLAN, Bluetooth, fingerprint, sensors, modem/remote processors and SDHC2 are not enabled. The handset PVT is unknown; this is not a complete or flashable device tree.

## Schema diagnostics — follow-up audit (2026-11-14)

Although `dt-doc-validate`, processed-schema generation and `dt-validate` returned exit code 0 in CI run 43623081943, the job log contains 160 diagnostic lines for the two PVT DTBs. Examples include cache-level/cache-unified omissions, memory-node schema mismatch, pinctrl child requirements, SPMI/RTC reg shape, MSM8953 USB compatible/interrupt requirements and APCS mailbox compatible constraints. Therefore the schema check is NOT accepted as a clean pass.

The evidence points to a schema provenance mismatch that must be investigated: the imported SoC/PMIC DTSI sources are Linux v6.1, while the validation schema directory comes from the pinned ACK 5.15 tree. Some nodes in the imported full SoC description are not yet reconciled with the older schema set. The diagnostics must be triaged by node and binding; do not silence them globally or infer that they are harmless simply because the validator process returned zero.

Current acceptance:
- DTS syntax compilation: PASS.
- Compiled PVT board-ID read-back: PASS.
- QSEE reservation and deleted-overlap read-back: PASS.
- Binding document syntax validation: PASS.
- Full-tree PVT schema validation: HOLD pending schema-version reconciliation and diagnostic triage.
- No hardware boot or flash approval.
