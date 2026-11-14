# Deen MSM8953/PM8953 base DTS compile smoke

- Result: FAIL
- Branch: deen/dts-bringup
- Branch commit: 6bd8b100fc656c2a7eb51d5356253486dd699538
- SoC DTSI source: Linux v6.1, blob 6b992a6d56c16d5151785df04fa2053c67ee7fad
- PMIC DTSI source: Linux v6.1, blob a1d36f9ebbd259e41a80e3af516d9a044419afe0
- ACK base: Android Common Kernel 5.15 LTS
- Compiler: Ubuntu clang version 18.1.3 (1ubuntu1)
- Test: generated base fixture plus Deen PVT1/PVT2 DTBs
- qcom.yaml dt_binding_check exit: 1
- qcom.yaml dtbs_check exit: 0
- Base-only fixture DTB SHA-256: cc6135f44e12cadf1422d817e5d639143bacca0325c582e7cce385864a37da85
- Deen PVT1 DTB SHA-256 (board ID 0x4D 0xC100): 6f6cd605790286deebd3dc01ade4d3d774df75eb4e7a7835ec9b883b81b6f1b2
- Deen PVT2 DTB SHA-256 (board ID 0x4D 0xC200): aca3ae7df6379a2410b03b03877ca9b014a8d54d14f01327b274e316f5cf5f3b

This is only a base-DTS syntax/include smoke test. It has no Deen PVT board ID or peripheral enablement and is not a flashable device tree.

## Last DTS compile log lines
make: Entering directory '/home/runner/work/_temp/deen-src'
make[1]: Entering directory '/home/runner/work/_temp/deen-out'
  SYNC    include/config/auto.conf.cmd
  GEN     Makefile
  HOSTCC  scripts/dtc/dtc.o
  HOSTCC  scripts/dtc/flattree.o
  HOSTCC  scripts/dtc/fstree.o
  HOSTCC  scripts/dtc/data.o
  HOSTCC  scripts/dtc/livetree.o
  HOSTCC  scripts/dtc/treesource.o
  HOSTCC  scripts/dtc/srcpos.o
  HOSTCC  scripts/dtc/checks.o
  HOSTCC  scripts/dtc/util.o
  LEX     scripts/dtc/dtc-lexer.lex.c
  YACC    scripts/dtc/dtc-parser.tab.[ch]
  HOSTCC  scripts/dtc/dtc-lexer.lex.o
  HOSTCC  scripts/dtc/dtc-parser.tab.o
  HOSTCC  scripts/dtc/yamltree.o
  HOSTLD  scripts/dtc/dtc
  HOSTCC  scripts/dtc/libfdt/fdt.o
  HOSTCC  scripts/dtc/libfdt/fdt_ro.o
  HOSTCC  scripts/dtc/libfdt/fdt_wip.o
  HOSTCC  scripts/dtc/libfdt/fdt_sw.o
  HOSTCC  scripts/dtc/libfdt/fdt_rw.o
  HOSTCC  scripts/dtc/libfdt/fdt_strerror.o
  HOSTCC  scripts/dtc/libfdt/fdt_empty_tree.o
  HOSTCC  scripts/dtc/libfdt/fdt_addresses.o
  HOSTCC  scripts/dtc/libfdt/fdt_overlay.o
  HOSTCC  scripts/dtc/fdtoverlay.o
  HOSTLD  scripts/dtc/fdtoverlay
  UPD     include/config/kernel.release
  DTC     arch/arm64/boot/dts/qcom/msm8953-deen-base-smoke.dtb
  DTC     arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt1.dtb
  DTC     arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb
make[1]: Leaving directory '/home/runner/work/_temp/deen-out'
make: Leaving directory '/home/runner/work/_temp/deen-src'

## Last dt_binding_check log lines
/home/runner/work/_temp/deen-src/Documentation/devicetree/bindings/arm/qcom.yaml: title: 'QCOM device tree bindings' should not be valid under {'pattern': '([Bb]inding| [Ss]chema)'}
	hint: Everything is a binding/schema, no need to say it. Describe what hardware the binding is for.
	from schema $id: http://devicetree.org/meta-schemas/base.yaml

## Last dtbs_check log lines
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu5-thermal: polling-delay-passive: b'\x00\x00\x00\xfa' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu5-thermal: polling-delay: b'\x00\x00\x03\xe8' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu5-thermal: thermal-sensors: b'\x00\x00\x00@\x00\x00\x00\x05' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: temperature: b'\x00\x018\x80' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: hysteresis: b'\x00\x00\x07\xd0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: type: b'passive\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: temperature: b'\x00\x01\x86\xa0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: hysteresis: b'\x00\x00\x07\xd0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: type: b'critical\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: map0: trip: b'\x00\x00\x00F' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: map0: cooling-device: b'\x00\x00\x00\t\xff\xff\xff\xff\xff\xff\xff\xff' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu6-thermal: polling-delay-passive: b'\x00\x00\x00\xfa' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu6-thermal: polling-delay: b'\x00\x00\x03\xe8' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu6-thermal: thermal-sensors: b'\x00\x00\x00@\x00\x00\x00\x06' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: temperature: b'\x00\x018\x80' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: hysteresis: b'\x00\x00\x07\xd0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: type: b'passive\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: temperature: b'\x00\x01\x86\xa0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: hysteresis: b'\x00\x00\x07\xd0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: type: b'critical\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: map0: trip: b'\x00\x00\x00G' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: map0: cooling-device: b'\x00\x00\x00\n\xff\xff\xff\xff\xff\xff\xff\xff' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu7-thermal: polling-delay-passive: b'\x00\x00\x00\xfa' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu7-thermal: polling-delay: b'\x00\x00\x03\xe8' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: cpu7-thermal: thermal-sensors: b'\x00\x00\x00@\x00\x00\x00\x07' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: temperature: b'\x00\x018\x80' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: hysteresis: b'\x00\x00\x07\xd0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: trip-point0: type: b'passive\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: temperature: b'\x00\x01\x86\xa0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: hysteresis: b'\x00\x00\x07\xd0' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: crit: type: b'critical\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: map0: trip: b'\x00\x00\x00H' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: map0: cooling-device: b'\x00\x00\x00\x0b\xff\xff\xff\xff\xff\xff\xff\xff' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: regulator-vph-pwr (regulator-fixed): regulator-name: b'vph_pwr\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: key-volume-up: linux,code: b'\x00\x00\x00s' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
