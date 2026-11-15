# Deen ACK 5.15 full Image compile smoke

- Result: PASS
- Source branch: deen/dts-bringup
- Source commit: 8345f67abd78a0b6fc8e776c9279d9c88cdc5356
- Base config: generic GKI defconfig plus MSM8953 platform/PMIC/eMMC options
- Resolved config SHA-256: 83d34fb4ead2c65d37348b3eacef7b30b59324fcac59af3267f47311b52579c8
- Compiler: Ubuntu clang version 18.1.3 (1ubuntu1)
- LTO/CFI: ThinLTO feasibility profile with Clang CFI; Full LTO remains a separate final gate
- CI memory mitigation: bounded swap based on free disk, serial build (-j1), LLD link threads=1, persistent RAM/swap/PSI/cgroup telemetry
- Build target: full arm64 Image plus PVT1 and PVT2 DTBs
- PVT1 board ID: 0x4D 0xC100
- PVT2 board ID: 0x4D 0xC200
- Image SHA-256: 85584de409a2dbb019286532d53dcb3e6c07bf82ea46629035c28d9abe2191c8
- PVT1 DTB SHA-256: 41a0106d6ade5492497a6736a9c930c82f85fe3c909791968f3f7b0726fe5532
- PVT2 DTB SHA-256: c06cc92f0487675277588594e03c1ad49eb5e69ff43ae7924bec2f50cb371055

This is a full kernel link smoke using generic GKI configuration. It is not a Deen-specific defconfig, boot.img, vendor_boot/DTBO integration, hardware boot test or permission to flash.
