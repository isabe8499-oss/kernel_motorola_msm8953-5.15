# Deen DTS bring-up source provenance

This branch is a controlled Deen board bring-up based on the exact ACK 5.15 LTS commit. It contains unchanged v6.1 SoC/PMIC DTSI sources plus a minimal board-specific DTSI and PVT1/PVT2 wrappers. CI has compiled both candidate DTBs and verified board-ID/QSEE binary properties. The schema validator exits 0 but emits 160 diagnostic lines against the ACK 5.15 schema set; full-tree schema acceptance is HOLD pending provenance reconciliation. The branch is not a complete or bootable Deen tree.

| Destination | Upstream source | Upstream ref | Blob SHA | License |
|---|---|---|---|---|
| arch/arm64/boot/dts/qcom/msm8953.dtsi | torvalds/linux | v6.1 | 6b992a6d56c16d5151785df04fa2053c67ee7fad | BSD-3-Clause |
| arch/arm64/boot/dts/qcom/pm8953.dtsi | torvalds/linux | v6.1 | a1d36f9ebbd259e41a80e3af516d9a044419afe0 | SPDX header retained from upstream |

These unchanged v6.1 source files provide the SoC/PMIC node base for the Deen port. The board-specific work remains limited to QSEE reservation, PM8953 RPM regulators, volume keys, primary eMMC, and PVT wrappers. Do not treat the branch as a bootable Deen tree.


## Deen board foundation sources

- `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi`: adapted from the upstream Motorola Deen DTS added in commit `b62af30ebdb4ae4ec6230c5e39eea97f65b9f5ea`. The PM8953 SMD regulator values and eMMC supply links are retained from the upstream Deen board description; the QSEE memory region, volume-key, PMIC regulator and primary eMMC nodes are included at this stage.
- `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt1.dts`: PVT1 wrapper with donor board ID `0x4D 0xC100`.
- `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dts`: PVT2 wrapper with donor board ID `0x4D 0xC200`.
- The two candidate wrappers use the mainline compatible pair `motorola,deen`, `qcom,msm8953`, plus the Motorola donor's `qcom,board-id` value.
- `arch/arm64/boot/dts/qcom/Makefile` declares both DTB targets.

The current board foundation deliberately does not enable the removable SD slot, USB, NFC, display, touchscreen, GPU, camera, audio, WLAN, Bluetooth, fingerprint, thermal/battery policy or remote processors. CI run 43623081943 compiled both board candidates and verified board-ID/QSEE binary properties. Its dt-validate log contains 160 diagnostic lines, so full-tree schema acceptance is HOLD. This does not validate runtime behavior. The current PVT in the handset remains unknown.


## Binding compatibility source

- `Documentation/devicetree/bindings/arm/qcom.yaml` adds the minimal `motorola,deen` + `qcom,msm8953` compatible pair.
- Upstream source: torvalds/linux commit `51c5d61ba73bde54d7900276cb1c0e37d416adfb` (the original 2026 patch adds `motorola,deen` to the MSM8953 compatible list).
- The 5.15 binding file predates this SoC/board entry, so the bring-up branch adds only the required schema pair instead of replacing the older complete binding file.
- A full `dtbs_check`/dt-schema validation is still required.


## MSM8953 RPM power-domain backport

The imported Linux v6.1 MSM8953 DTS references `MSM8953_VDDCX` and `qcom,msm8953-rpmpd`. The ACK 5.15 branch had neither the MSM8953 identifiers nor the matching RPM power-domain descriptor, so the board DTS could not be parsed/resolved correctly and the runtime power-domain provider would have been missing.

Selective upstream backport:
- `include/dt-bindings/power/qcom-rpmpd.h`: only the seven MSM8953 IDs from Linux v6.1 blob `f5f82dde73998ca2358b0134e54560b0e8a9fa96`.
- `drivers/soc/qcom/rpmpd.c`: only the MSM8953 domain definitions/table/descriptor and `qcom,msm8953-rpmpd` match entry from Linux v6.1 blob `337b1ad1cd3bfecd4119dd417a4676655f9ee7bf`.
- Existing ACK 5.15 RPMPD implementation and other SoC entries are preserved.

This is a focused driver/binding backport. It must be compiled as `drivers/soc/qcom/rpmpd.o` and validated with the Deen DTB candidates before being treated as integrated.


- `Documentation/devicetree/bindings/power/qcom,rpmpd.yaml`: added `qcom,msm8953-rpmpd` to the compatible enum using Linux v6.1 schema semantics. The ACK 5.15 schema predated MSM8953 support.


## Deen reserved-memory adaptation

The clean 4.19 donor's `reserved-memory.dtsi` was audited against the current mainline Deen DTS and the Linux v6.1 MSM8953 base:
- The vendor donor configures QSEE memory at `0x84300000` with a 32 MiB secure region; the current mainline Deen DTS uses the same base and size.
- The v6.1 SoC DTSI has an inherited anonymous 8 MiB reservation at `0x85b00000`, which falls inside the Deen 32 MiB QSEE range. The Deen common DTSI now deletes that inherited node before adding the Deen QSEE region.
- The v6.1 base also carries a continuous-splash reservation at `0x90001000` of size `0x13ff000`; the mainline Deen DTS deletes this node for its initial display-disabled support. The Deen common DTSI applies the same deletion.
- The donor's ramoops area at `0xef000000` (0xC0000 bytes), TZ backup log at `0xeefe4000` (0x2000 bytes), and watchdog CPU-context area at `0xeefe6000` (0x1A000 bytes) are recorded but not yet enabled. TZ-log and watchdog contiguous-region properties are vendor-specific and need matching 5.15 driver/binding support. Ramoops is deferred until its schema and actual DRAM map are checked.
- The donor's legacy `other_ext_mem` / `qcom_seecom` nodes are not copied; mainline Deen expresses the QSEE reservation directly in `reserved-memory`.

The deletion uses the absolute `/reserved-memory` node reference because the v6.1 source uses anonymous child nodes (unlike newer mainline, which labels them `qseecom_mem` and `cont_splash_mem`). CI run 43623081943 compiled the resulting DTBs and verified QSEE/overlap properties. Full-tree schema validation remains HOLD due to 160 diagnostics against the ACK 5.15 schema set. The donor ramoops/TZ-log/watchdog reservations remain unported.


## CI workflow cleanup

The earlier experimental workflow `.github/workflows/deen-msm8953-dtsi-validation.yml` was retired after the integrated main-branch Deen smoke workflow began compiling the base fixture and both PVT DTBs with pinned Clang 18 and targeted schema validation. The main workflow is the authoritative CI result; the retired GCC/defconfig fixture must not be used as evidence for board readiness.
