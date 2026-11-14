# Deen MSM8953/PM8953 base DTS compile smoke

- Result: PASS
- Branch: deen/dts-bringup
- Branch commit: d86ecf2fa95fe3635b4ffc606fdd39b048760d1e
- SoC DTSI source: Linux v6.1, blob 6b992a6d56c16d5151785df04fa2053c67ee7fad
- PMIC DTSI source: Linux v6.1, blob a1d36f9ebbd259e41a80e3af516d9a044419afe0
- ACK base: Android Common Kernel 5.15 LTS
- Compiler: Ubuntu clang version 18.1.3 (1ubuntu1)
- Test: generated base fixture plus Deen PVT1/PVT2 DTBs
- dt-doc-validate exit: 0
- dt-mk-schema exit: 0
- targeted dt-validate exit: 0
- Backported MSM8953 rpmpd.o SHA-256:
  7080ba714a8135cfb7f48c483ed29bfc6d470e1c490ca0afdb186487bedbfe1d  /home/runner/work/_temp/deen-out/drivers/soc/qcom/rpmpd.o
- Base-only fixture DTB SHA-256: cc6135f44e12cadf1422d817e5d639143bacca0325c582e7cce385864a37da85
- Deen PVT1 DTB SHA-256 (board ID 0x4D 0xC100): 41a0106d6ade5492497a6736a9c930c82f85fe3c909791968f3f7b0726fe5532
- Deen PVT2 DTB SHA-256 (board ID 0x4D 0xC200): c06cc92f0487675277588594e03c1ad49eb5e69ff43ae7924bec2f50cb371055

This is a minimal Deen board-DTS compile and schema smoke test. The PVT1 and PVT2 wrapper DTBs do contain their respective qcom,board-id values (0x4D 0xC100 and 0x4D 0xC200). The shared board DTSI currently describes the 32 MiB QSEE reservation at 0x84300000, PM8953 RPM regulator rails, Volume Up/Down keys and primary non-removable eMMC. It intentionally leaves display, touchscreen, GPU, camera, audio, USB, NFC, WLAN, Bluetooth, fingerprint, sensors, modem/remote processors and removable SD disabled. The physical handset PVT has not been identified. This is not a complete device tree, not a boot-image integration test and not approved for flashing.
