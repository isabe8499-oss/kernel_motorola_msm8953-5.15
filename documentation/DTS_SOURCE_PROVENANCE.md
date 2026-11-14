# Deen DTS bring-up source provenance

This branch is a scratch bring-up branch based on the exact ACK 5.15 LTS commit. Its first DTS files are imported unchanged as reference inputs; they are not yet a Deen board description.

| Destination | Upstream source | Upstream ref | Blob SHA | License |
|---|---|---|---|---|
| arch/arm64/boot/dts/qcom/msm8953.dtsi | torvalds/linux | v6.1 | 6b992a6d56c16d5151785df04fa2053c67ee7fad | BSD-3-Clause |
| arch/arm64/boot/dts/qcom/pm8953.dtsi | torvalds/linux | v6.1 | a1d36f9ebbd259e41a80e3af516d9a044419afe0 | SPDX header retained from upstream |

These files are being evaluated for a selective backport to ACK 5.15. Do not treat this branch as a bootable Deen tree. No vendor peripherals, panel, touchscreen, camera, GPU, board ID, boot image or defconfig has been added.


## Deen board foundation sources

- `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi`: adapted from the upstream Motorola Deen DTS added in commit `b62af30ebdb4ae4ec6230c5e39eea97f65b9f5ea`. The PM8953 SMD regulator values and eMMC supply links are retained from the upstream Deen board description; only the basic volume-key, PMIC regulator and primary eMMC nodes are included at this stage.
- `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt1.dts`: PVT1 wrapper with donor board ID `0x4D 0xC100`.
- `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dts`: PVT2 wrapper with donor board ID `0x4D 0xC200`.
- The two candidate wrappers use the mainline compatible pair `motorola,deen`, `qcom,msm8953`, plus the Motorola donor's `qcom,board-id` value.
- `arch/arm64/boot/dts/qcom/Makefile` declares both DTB targets.

The current board foundation deliberately does not enable the removable SD slot, USB, NFC, display, touchscreen, GPU, camera, audio, WLAN, Bluetooth, fingerprint or other sensors. It is a compile candidate, not a validated device tree. The current PVT in the user's handset remains unknown.


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
