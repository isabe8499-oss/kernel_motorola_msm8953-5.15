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
