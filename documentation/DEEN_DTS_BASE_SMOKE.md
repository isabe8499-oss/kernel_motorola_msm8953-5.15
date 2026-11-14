# Deen MSM8953/PM8953 base DTS compile smoke

- Result: FAIL
- Branch: deen/dts-bringup
- Branch commit: c963cbd09a77488721ad23f8917a985f8a0aed95
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
	from schema $id: http://devicetree.org/schemas/soc/qcom/qcom,smd-rpm.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: power-controller (qcom,msm8953-rpmpd): 'clock-names', 'clocks' do not match any of the regexes: '^pinctrl-[0-9]+$'
	from schema $id: http://devicetree.org/schemas/power/qcom,rpmpd.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: smsm (qcom,smsm): qcom,ipc-1: b'\x00\x00\x00\x0f\x00\x00\x00\x08\x00\x00\x00\r' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: smsm (qcom,smsm): qcom,ipc-3: b'\x00\x00\x00\x0f\x00\x00\x00\x08\x00\x00\x00\x13' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: thermal-sensor@4a9000 (qcom,msm8953-tsens): compatible: 'oneOf' conditional failed, one must be fixed:
	['qcom,msm8953-tsens', 'qcom,tsens-v2'] is too long
	'qcom,msm8953-tsens' is not one of ['qcom,ipq8064-tsens']
	'qcom,msm8953-tsens' is not one of ['qcom,mdm9607-tsens', 'qcom,msm8916-tsens', 'qcom,msm8939-tsens', 'qcom,msm8974-tsens']
	'qcom,msm8953-tsens' is not one of ['qcom,msm8976-tsens', 'qcom,qcs404-tsens']
	'qcom,msm8953-tsens' is not one of ['qcom,msm8996-tsens', 'qcom,msm8998-tsens', 'qcom,sc7180-tsens', 'qcom,sc7280-tsens', 'qcom,sc8180x-tsens', 'qcom,sdm630-tsens', 'qcom,sdm845-tsens', 'qcom,sm8150-tsens', 'qcom,sm8250-tsens', 'qcom,sm8350-tsens']
	'qcom,tsens-v0_1' was expected
	'qcom,tsens-v1' was expected
	from schema $id: http://devicetree.org/schemas/thermal/qcom-tsens.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-clk-on-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-clk-off-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-cmd-on-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-cmd-off-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-data-on-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-data-off-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-rclk-on-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc1-rclk-off-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc2-clk-on-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc2-clk-off-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc2-cmd-on-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc2-cmd-off-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc2-data-on-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: pinctrl@1000000 (qcom,msm8953-pinctrl): sdc2-data-off-pins: 'function' is a required property
	from schema $id: http://devicetree.org/schemas/pinctrl/qcom,msm8953-pinctrl.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: clock-controller@1800000 (qcom,gcc-msm8953): 'clock-names', 'clocks' do not match any of the regexes: '^pinctrl-[0-9]+$'
	from schema $id: http://devicetree.org/schemas/clock/qcom,gcc.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: spmi@200f000 (qcom,spmi-pmic-arb): reg: [[33615872, 4096], [37748736, 8388608], [46137344, 8388608], [58720256, 2097152], [33595392, 8448]] is too long
	from schema $id: http://devicetree.org/schemas/spmi/spmi.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: spmi@200f000 (qcom,spmi-pmic-arb): qcom,ee: b'\x00\x00\x00\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: spmi@200f000 (qcom,spmi-pmic-arb): qcom,channel: b'\x00\x00\x00\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: rtc@6000 (qcom,pm8941-rtc): reg: [[24576], [24832]] is too long
	from schema $id: http://devicetree.org/schemas/rtc/qcom-pm8xxx-rtc.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: rtc@6000 (qcom,pm8941-rtc): 'reg-names' does not match any of the regexes: '^pinctrl-[0-9]+$'
	from schema $id: http://devicetree.org/schemas/rtc/qcom-pm8xxx-rtc.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: usb@70f8800 (qcom,msm8953-dwc3): compatible:0: 'qcom,msm8953-dwc3' is not one of ['qcom,msm8996-dwc3', 'qcom,msm8998-dwc3', 'qcom,sc7180-dwc3', 'qcom,sc7280-dwc3', 'qcom,sdm660-dwc3', 'qcom,sdm845-dwc3', 'qcom,sdx55-dwc3', 'qcom,sm4250-dwc3', 'qcom,sm6115-dwc3', 'qcom,sm8150-dwc3', 'qcom,sm8250-dwc3', 'qcom,sm8350-dwc3']
	from schema $id: http://devicetree.org/schemas/usb/qcom,dwc3.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: usb@70f8800 (qcom,msm8953-dwc3): clock-names:3: 'mock_utmi' was expected
	from schema $id: http://devicetree.org/schemas/usb/qcom,dwc3.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: usb@70f8800 (qcom,msm8953-dwc3): clock-names:4: 'sleep' was expected
	from schema $id: http://devicetree.org/schemas/usb/qcom,dwc3.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: usb@70f8800 (qcom,msm8953-dwc3): interrupts: [[0, 136, 4], [0, 220, 4]] is too short
	from schema $id: http://devicetree.org/schemas/usb/qcom,dwc3.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: usb@70f8800 (qcom,msm8953-dwc3): interrupt-names: ['hs_phy_irq', 'ss_phy_irq'] is too short
	from schema $id: http://devicetree.org/schemas/usb/qcom,dwc3.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: usb@7000000 (snps,dwc3): phy_mode: b'utmi\x00' is not of type 'object', 'integer', 'array', 'boolean', 'null'
	from schema $id: http://devicetree.org/schemas/dt-core.yaml
/home/runner/work/_temp/deen-out/arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb: mailbox@b011000 (qcom,msm8953-apcs-kpss-global): compatible: ['qcom,msm8953-apcs-kpss-global', 'syscon'] is too long
	from schema $id: http://devicetree.org/schemas/mailbox/qcom,apcs-kpss-global.yaml
