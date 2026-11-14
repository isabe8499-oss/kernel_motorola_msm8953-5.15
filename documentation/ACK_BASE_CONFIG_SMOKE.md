# ACK Android 14 5.15 base configuration smoke

- Result: PASS
- ACK repository: https://android.googlesource.com/kernel/common.git
- Branch: android14-5.15-lts
- Pinned source SHA: 5cb316cf9d39318326075731e4e0c39b725d9c99
- Architecture: arm64
- Base configuration: gki_defconfig followed by olddefconfig
- Required resolved symbols: MSM8953 GCC/pinctrl, SPMI PMIC arbiter/MFD, SMD RPM and both regulator paths, SDHCI MSM and GPIO keys (all y)
- Clang: Ubuntu clang version 18.1.3 (1ubuntu1)
- LLD: Ubuntu LLD 18.1.3 (compatible with GNU linkers)
- Resolved config SHA-256: 5f080d7cfae114db34fa5e9f56bee98189429fc7758c0539a510b38b436b6089

## Compiled object SHA-256 values

7fd32631d9ccc7b72927ca69678c123265502e28d5557260f88aa30583d0e7f9  /home/runner/work/_temp/ack-out/drivers/clk/qcom/gcc-msm8953.o
2b8e233fa2a8b43b1c2cf1026c4c26b985aa648620f3332e332b4e8f1f02772e  /home/runner/work/_temp/ack-out/drivers/pinctrl/qcom/pinctrl-msm8953.o
09b7fc96346f32a8ba2bee0439de8bbe6a5cf5365ce261d60ee753197d77e721  /home/runner/work/_temp/ack-out/drivers/spmi/spmi-pmic-arb.o
b32ce75855713836bfddf7a2a65f302d75d4c292edf661ab140dda9187d9cb0c  /home/runner/work/_temp/ack-out/drivers/mfd/qcom-spmi-pmic.o
8d04870b74e4bf56caba5f28ff21e8c6cec61ab0ee760f2c12ec5e61fe32c2b3  /home/runner/work/_temp/ack-out/drivers/soc/qcom/smd-rpm.o
6c82c159802fa33adc1cd285de6ce48f3c34e66dc6bf9a58af1b0358549e478f  /home/runner/work/_temp/ack-out/drivers/regulator/qcom_smd-regulator.o
d751a5a9378ea8c6cf7efb4ca0f7ccd13f8491361d4f5fcac56b506118f5ee24  /home/runner/work/_temp/ack-out/drivers/regulator/qcom_spmi-regulator.o
4f560c65c38452ce6784b671e43dc86ac0c25253bf1b19be288b14ec0a00a5e8  /home/runner/work/_temp/ack-out/drivers/mmc/host/sdhci-msm.o
c1061539f74f713f4a066543c4fe2be3b8a9eed9bcf3d3d8f72a27bfe670938f  /home/runner/work/_temp/ack-out/drivers/input/keyboard/gpio_keys.o

This is a configuration and selected SoC/controller object compile smoke test only. It is not a full Image/DTB build, Deen device build, ABI validation or boot test.
