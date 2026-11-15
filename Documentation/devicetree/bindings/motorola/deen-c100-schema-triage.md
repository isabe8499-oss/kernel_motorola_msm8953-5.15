# Deen C100 DTB — schema and integration triage

Date: 2026-11-15
Audited source: `deen/c100-schema-reconcile-v2` at `b7d7bc3abb65c2d5ec39cacb64a8dfab9ceac1ca`
Evidence: GitHub Actions run [#11](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43743256412), artifact `deen-c100-dtb-validation`.

## Verified

- PVT1 DTB compiles; root identity is `qcom,msm-id = <0x125 0>` and `qcom,board-id = <0x4D 0xC100>`.
- PVT2 control DTB compiles; root board identity is `<0x4D 0xC200>`.
- The C100 tuple agrees with the supplied stock `boot_b` FDT and the device's reported PVT1 hardware revision.
- This is a minimal identity/build smoke test only. It does not establish bootloader DT selection, complete board coverage, boot-image packaging, or bootability.

## Schema diagnostics traced to imported SoC DTSI

Inspection of `arch/arm64/boot/dts/qcom/msm8953.dtsi` shows the current schema diagnostics are present in the shared SoC description, not in the Deen PVT1/PVT2 root identity files:

1. Each Cortex-A53 CPU declares `l1-icache` and `l1-dcache` with only `compatible = "cache"`. The validator reports missing `cache-level` and `cache-unified` properties. Do not add values mechanically: the two nodes represent split instruction/data caches, so any schema-compatible representation must preserve that semantic distinction and be checked against the target kernel's cache binding and CPU topology.
2. The inherited memory node deliberately has `reg = <0 0 0 0>` with the source comment “We expect the bootloader to fill in the reg”. The validator rejects the zero tuple under the root-node schema. Do not replace it with guessed RAM geometry. Determine the target bootloader's memory handoff contract and decide whether this is a supported vendor convention or whether the 5.15 port needs an explicit, evidence-backed memory description.
3. The inherited TSENS node uses `compatible = "qcom,msm8953-tsens", "qcom,tsens-v2"`. The validator reports a conditional mismatch for this compatible. Resolve against the exact TSENS binding and the actual 5.15 driver compatible table before changing the node; do not remove the legacy compatible or substitute a different TSENS generation without evidence.

The same diagnostics affect both PVT1 and PVT2 because they share the SoC DTSI. The current workflow treats schema validation as diagnostic, so a successful job must not be described as schema-clean.

## Board-completeness blockers

The current common Deen DTS intentionally enables only basic keys, PMIC regulators, and primary eMMC. Comparison against the supplied stock C100 FDT still requires a deliberate, node-by-node reconciliation of at least:

- modem/MSS PIL and its memory/firmware relationship;
- ADSP loader and SMD/SMSM endpoints;
- WCNSS WLAN and its SMD/SMSM/SMP2P endpoints;
- USB PHY/controller configuration and board-specific pinctrl/supplies;
- display, panel, camera, audio, and related regulators/GPIO/pinctrl;
- reserved-memory ownership, including stock ramoops, TZ log, watchdog context, splash, and vendor-specific regions.

Do not copy every stock compatible string into the candidate. Each node must be mapped to a supported 5.15 driver/binding and its resources reconciled. Preserve exact stock addresses/sizes only where ownership and overlap are understood.

## Required next gates

1. Resolve the three inherited schema diagnostics with binding/driver evidence and add regression checks.
2. Produce a structured stock-vs-candidate node/property/reserved-memory diff for C100, classifying each item as preserved, intentionally omitted with rationale, unsupported in 5.15, or unresolved.
3. Reconcile modem, ADSP, and WCNSS dependencies and all board peripherals against the 5.15 driver set.
4. Verify bootloader DT selection and the Android boot image's actual DTB packaging/header contract. The audited `dto_b` partition was zero-filled; do not treat it as a usable DTBO source.
5. Only after the above: build a full kernel and ROM, validate boot image size/format and AVB/slot behavior, then design a reversible test plan. No flashing before these gates pass.

## Safety status

**NOT FLASHABLE.** The successful PVT1/PVT2 DTB compile is not a boot test and must not be used as authorization to flash either DTB or a kernel image.
