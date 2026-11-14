# Deen MSM8953/PM8953 base DTS compile smoke

- Result: FAIL
- Branch: deen/dts-bringup
- Branch commit: f1251b5fc6df5d4d6bb4aa0637ab48ca8b11c4bf
- SoC DTSI source: Linux v6.1, blob 6b992a6d56c16d5151785df04fa2053c67ee7fad
- PMIC DTSI source: Linux v6.1, blob a1d36f9ebbd259e41a80e3af516d9a044419afe0
- ACK base: Android Common Kernel 5.15 LTS
- Compiler: Ubuntu clang version 18.1.3 (1ubuntu1)
- Test: generated base fixture plus Deen PVT1/PVT2 DTBs
- qcom.yaml dt_binding_check exit: 2
- qcom.yaml dtbs_check exit: 2
- Base-only fixture DTB SHA-256: not-built
- Deen PVT1 DTB SHA-256 (board ID 0x4D 0xC100): not-built
- Deen PVT2 DTB SHA-256 (board ID 0x4D 0xC200): not-built

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
Error: /home/runner/work/_temp/deen-src/arch/arm64/boot/dts/qcom/msm8953.dtsi:813.28-29 syntax error
FATAL ERROR: Unable to parse input tree
make[2]: *** [/home/runner/work/_temp/deen-src/scripts/Makefile.lib:349: arch/arm64/boot/dts/qcom/msm8953-deen-base-smoke.dtb] Error 1
make[1]: *** [/home/runner/work/_temp/deen-src/Makefile:1503: qcom/msm8953-deen-base-smoke.dtb] Error 2
make[1]: Leaving directory '/home/runner/work/_temp/deen-out'
make: *** [Makefile:244: __sub-make] Error 2
make: Leaving directory '/home/runner/work/_temp/deen-src'

## Last dt_binding_check log lines
	http://devicetree.org/schemas/iio/dac/adi,ad5686.yaml#
Warning: Duplicate compatible "adi,ad5675r" found in schemas matching "$id":
	http://devicetree.org/schemas/iio/dac/adi,ad5696.yaml
	http://devicetree.org/schemas/iio/dac/adi,ad5686.yaml#
Warning: Duplicate compatible "adi,ad5696" found in schemas matching "$id":
	http://devicetree.org/schemas/iio/dac/adi,ad5696.yaml
	http://devicetree.org/schemas/iio/dac/adi,ad5686.yaml#
Warning: Duplicate compatible "adi,ad5696r" found in schemas matching "$id":
	http://devicetree.org/schemas/iio/dac/adi,ad5696.yaml
	http://devicetree.org/schemas/iio/dac/adi,ad5686.yaml#
Warning: Duplicate compatible "adi,ad5671r" found in schemas matching "$id":
	http://devicetree.org/schemas/iio/dac/adi,ad5696.yaml
	http://devicetree.org/schemas/iio/dac/adi,ad5686.yaml#
Warning: Duplicate compatible "adi,ad5694r" found in schemas matching "$id":
	http://devicetree.org/schemas/iio/dac/adi,ad5696.yaml
	http://devicetree.org/schemas/iio/dac/adi,ad5686.yaml#
Warning: Duplicate compatible "maxim,max1237" found in schemas matching "$id":
	http://devicetree.org/schemas/iio/adc/maxim,max1238.yaml
	http://devicetree.org/schemas/trivial-devices.yaml#
Warning: Duplicate compatible "gmt,g751" found in schemas matching "$id":
	http://devicetree.org/schemas/hwmon/lm75.yaml
	http://devicetree.org/schemas/trivial-devices.yaml#
Warning: Duplicate compatible "maxim,max6625" found in schemas matching "$id":
	http://devicetree.org/schemas/hwmon/lm75.yaml
	http://devicetree.org/schemas/trivial-devices.yaml#
Warning: Duplicate compatible "dallas,ds75" found in schemas matching "$id":
	http://devicetree.org/schemas/hwmon/lm75.yaml
	http://devicetree.org/schemas/trivial-devices.yaml#
Warning: Duplicate compatible "ti,tmp275" found in schemas matching "$id":
	http://devicetree.org/schemas/hwmon/lm75.yaml
	http://devicetree.org/schemas/trivial-devices.yaml#
Warning: Duplicate compatible "national,lm75" found in schemas matching "$id":
	http://devicetree.org/schemas/hwmon/lm75.yaml
	http://devicetree.org/schemas/trivial-devices.yaml#
Warning: Duplicate compatible "dallas,ds1775" found in schemas matching "$id":
	http://devicetree.org/schemas/hwmon/lm75.yaml
	http://devicetree.org/schemas/trivial-devices.yaml#
  DTEX    Documentation/devicetree/bindings/arm/qcom.example.dts
  DTC     Documentation/devicetree/bindings/arm/qcom.example.dt.yaml
  CHECK   Documentation/devicetree/bindings/arm/qcom.example.dt.yaml
Traceback (most recent call last):
  File "/home/runner/work/_temp/dtschema-venv/bin/dt-validate", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb_validate.py", line 443, in main
    dtb_diagnostics = sg.check_dtb(filename)
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb_validate.py", line 331, in check_dtb
    dt = self.validator.decode_dtb(f.read(), decode_errors)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/validator.py", line 631, in decode_dtb
    return [dtschema.dtb.fdt_unflatten(self, dtb)]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb.py", line 588, in fdt_unflatten
    fdt = libfdt.Fdt(dtb)
          ^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/libfdt.py", line 584, in __init__
    FdtRo.__init__(self, data)
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/libfdt.py", line 174, in __init__
    check_err(fdt_check_header(self._fdt));
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/libfdt.py", line 129, in check_err
    raise FdtException(val)
libfdt.FdtException: pylibfdt error -9: FDT_ERR_BADMAGIC
make[2]: *** [/home/runner/work/_temp/deen-src/scripts/Makefile.lib:376: Documentation/devicetree/bindings/arm/qcom.example.dt.yaml] Error 1
make[2]: *** Deleting file 'Documentation/devicetree/bindings/arm/qcom.example.dt.yaml'
make[1]: *** [/home/runner/work/_temp/deen-src/Makefile:1538: dt_binding_check] Error 2
make[1]: Leaving directory '/home/runner/work/_temp/deen-out'
make: *** [Makefile:244: __sub-make] Error 2
make: Leaving directory '/home/runner/work/_temp/deen-src'

## Last dtbs_check log lines
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-nanopi-a64.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-oceanic-5205-5inmfd.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-olinuxino.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-olinuxino-emmc.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-orangepi-win.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pine64-lts.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pine64-plus.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pine64.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pinebook.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pinephone-1.0.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pinephone-1.1.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pinephone-1.2.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pinetab.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-pinetab-early-adopter.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-sopine-baseboard.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-teres-i.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a100-allwinner-perf1.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-bananapi-m2-plus.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-bananapi-m2-plus-v1.2.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-emlid-neutis-n5-devboard.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-libretech-all-h3-cc.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-libretech-all-h3-it.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-libretech-all-h5-cc.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-nanopi-neo2.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-nanopi-neo-plus2.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-nanopi-r1s-h5.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-orangepi-pc2.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-orangepi-prime.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-orangepi-zero-plus.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h5-orangepi-zero-plus2.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h6-beelink-gs1.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h6-orangepi-3.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h6-orangepi-lite2.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h6-orangepi-one-plus.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h6-pine-h64.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h6-pine-h64-model-b.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-h6-tanix-tx6.dtb
  DTC     arch/arm64/boot/dts/allwinner/sun50i-a64-amarula-relic.dt.yaml
  CHECK   arch/arm64/boot/dts/allwinner/sun50i-a64-amarula-relic.dt.yaml
Traceback (most recent call last):
  File "/home/runner/work/_temp/dtschema-venv/bin/dt-validate", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb_validate.py", line 443, in main
    dtb_diagnostics = sg.check_dtb(filename)
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb_validate.py", line 331, in check_dtb
    dt = self.validator.decode_dtb(f.read(), decode_errors)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/validator.py", line 631, in decode_dtb
    return [dtschema.dtb.fdt_unflatten(self, dtb)]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb.py", line 588, in fdt_unflatten
    fdt = libfdt.Fdt(dtb)
          ^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/libfdt.py", line 584, in __init__
    FdtRo.__init__(self, data)
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/libfdt.py", line 174, in __init__
    check_err(fdt_check_header(self._fdt));
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/libfdt.py", line 129, in check_err
    raise FdtException(val)
libfdt.FdtException: pylibfdt error -9: FDT_ERR_BADMAGIC
make[3]: *** [/home/runner/work/_temp/deen-src/scripts/Makefile.lib:376: arch/arm64/boot/dts/allwinner/sun50i-a64-amarula-relic.dt.yaml] Error 1
make[3]: *** Deleting file 'arch/arm64/boot/dts/allwinner/sun50i-a64-amarula-relic.dt.yaml'
make[2]: *** [/home/runner/work/_temp/deen-src/scripts/Makefile.build:549: arch/arm64/boot/dts/allwinner] Error 2
make[1]: *** [/home/runner/work/_temp/deen-src/Makefile:1510: dtbs] Error 2
make[1]: Leaving directory '/home/runner/work/_temp/deen-out'
make: *** [Makefile:244: __sub-make] Error 2
make: Leaving directory '/home/runner/work/_temp/deen-src'
