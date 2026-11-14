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
- Resolved config SHA-256: 0ac5c4a92bc35d2c7e4d47eded27629d8aad1d0dbb4222316b5a58df085305f5

## Compiled object SHA-256 values

7fd32631d9ccc7b72927ca69678c123265502e28d5557260f88aa30583d0e7f9  /home/runner/work/_temp/ack-out/drivers/clk/qcom/gcc-msm8953.o
2b8e233fa2a8b43b1c2cf1026c4c26b985aa648620f3332e332b4e8f1f02772e  /home/runner/work/_temp/ack-out/drivers/pinctrl/qcom/pinctrl-msm8953.o
96c9a38fe2b3fa6225932fb61af1f0a00eb6fa8b1a45ea64b357b5c6da62c296  /home/runner/work/_temp/ack-out/drivers/spmi/spmi-pmic-arb.o
b32ce75855713836bfddf7a2a65f302d75d4c292edf661ab140dda9187d9cb0c  /home/runner/work/_temp/ack-out/drivers/mfd/qcom-spmi-pmic.o
23f4fac4796125f61da90ae803dd7ba6b087865b5b87e6d8b80c3ca3cfd8d1a7  /home/runner/work/_temp/ack-out/drivers/soc/qcom/smd-rpm.o
ec27aab24099288c7fd65657a049fd352e2f3193783bc815062b582196175c29  /home/runner/work/_temp/ack-out/drivers/soc/qcom/rpmpd.o
6c82c159802fa33adc1cd285de6ce48f3c34e66dc6bf9a58af1b0358549e478f  /home/runner/work/_temp/ack-out/drivers/regulator/qcom_smd-regulator.o
4155814e6801b991a75f9d8692905b62e802aeaf22a537d2b63ca8aa0ff16d0d  /home/runner/work/_temp/ack-out/drivers/regulator/qcom_spmi-regulator.o
4c0536e87e87dc9ce73a52305442f501c433340db56f2fd131a7b961cdfd0904  /home/runner/work/_temp/ack-out/drivers/mmc/host/sdhci-msm.o
5ea49ca865f9232e2f3fdee53e3871a70b895e7e9a88617e21792b24c67be3a1  /home/runner/work/_temp/ack-out/drivers/input/keyboard/gpio_keys.o

This is a configuration and selected SoC/controller object compile smoke test only. It is not a full Image/DTB build, Deen device build, ABI validation or boot test.
