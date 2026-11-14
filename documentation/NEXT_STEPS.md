# Next engineering steps

1. Pin `aosp-mirror/kernel_common:android14-5.15` to an exact commit.
2. Verify exact Deen hardware revision (PVT1/PVT2) and target ROM boot layout.
3. Inventory ACK MSM8953 support and identify missing machine/device-tree drivers.
4. Compare 3.18 and 4.19 Deen DTS fragments and select only required changes.
5. Produce a minimal Deen defconfig based on ACK Kconfig rather than transplanting the 4.19 config.
6. Bring up storage, pinctrl, regulators, clocks, thermal and display in dependency order.
7. Add peripheral drivers only after static/API/ABI review.
8. Establish reproducible CI and boot-log collection before device tests.
