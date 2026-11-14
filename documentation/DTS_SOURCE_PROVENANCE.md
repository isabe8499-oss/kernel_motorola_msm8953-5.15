# Deen DTS bring-up source provenance

This branch is a scratch bring-up branch based on the exact ACK 5.15 LTS commit. Its first DTS files are imported unchanged as reference inputs; they are not yet a Deen board description.

| Destination | Upstream source | Upstream ref | Blob SHA | License |
|---|---|---|---|---|
| arch/arm64/boot/dts/qcom/msm8953.dtsi | torvalds/linux | v6.1 | 6b992a6d56c16d5151785df04fa2053c67ee7fad | BSD-3-Clause |
| arch/arm64/boot/dts/qcom/pm8953.dtsi | torvalds/linux | v6.1 | a1d36f9ebbd259e41a80e3af516d9a044419afe0 | SPDX header retained from upstream |

These files are being evaluated for a selective backport to ACK 5.15. Do not treat this branch as a bootable Deen tree. No vendor peripherals, panel, touchscreen, camera, GPU, board ID, boot image or defconfig has been added.
