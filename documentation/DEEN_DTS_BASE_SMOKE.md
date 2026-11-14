# Deen MSM8953/PM8953 base DTS compile smoke

- Result: FAIL
- Branch: deen/dts-bringup
- Branch commit: 06e98fd1484cd28819e7fc22bf9eca8e5e6bf657
- SoC DTSI source: Linux v6.1, blob 6b992a6d56c16d5151785df04fa2053c67ee7fad
- PMIC DTSI source: Linux v6.1, blob a1d36f9ebbd259e41a80e3af516d9a044419afe0
- ACK base: Android Common Kernel 5.15 LTS
- Compiler: Ubuntu clang version 18.1.3 (1ubuntu1)
- Test: generated base fixture plus Deen PVT1/PVT2 DTBs
- dt-doc-validate exit: 0
- dt-mk-schema exit: 0
- targeted dt-validate exit: 1
- Backported MSM8953 rpmpd.o SHA-256:
  7080ba714a8135cfb7f48c483ed29bfc6d470e1c490ca0afdb186487bedbfe1d  /home/runner/work/_temp/deen-out/drivers/soc/qcom/rpmpd.o
- Base-only fixture DTB SHA-256: cc6135f44e12cadf1422d817e5d639143bacca0325c582e7cce385864a37da85
- Deen PVT1 DTB SHA-256 (board ID 0x4D 0xC100): 41a0106d6ade5492497a6736a9c930c82f85fe3c909791968f3f7b0726fe5532
- Deen PVT2 DTB SHA-256 (board ID 0x4D 0xC200): c06cc92f0487675277588594e03c1ad49eb5e69ff43ae7924bec2f50cb371055

This is only a base-DTS syntax/include smoke test. It has no Deen PVT board ID or peripheral enablement and is not a flashable device tree.

## Last DTS compile log lines
make: Entering directory '/home/runner/work/_temp/deen-src'
make[1]: Entering directory '/home/runner/work/_temp/deen-out'
  UPD     include/config/kernel.release
  DTC     arch/arm64/boot/dts/qcom/msm8953-deen-base-smoke.dtb
  DTC     arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt1.dtb
  DTC     arch/arm64/boot/dts/qcom/msm8953-motorola-deen-pvt2.dtb
make[1]: Leaving directory '/home/runner/work/_temp/deen-out'
make: Leaving directory '/home/runner/work/_temp/deen-src'

## Last dt-doc-validate log lines

## Last dt-mk-schema log lines

## Last targeted dt-validate log lines
preprocessed schema file is not valid JSON or YAML

Traceback (most recent call last):
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/validator.py", line 349, in __init__
    schema_cache = json.load(f)
                   ^^^^^^^^^^^^
  File "/usr/lib/python3.12/json/__init__.py", line 293, in load
    return loads(fp.read(),
           ^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/json/decoder.py", line 337, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/json/decoder.py", line 355, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/_temp/dtschema-venv/bin/dt-validate", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb_validate.py", line 127, in main
    sg = schema_group(args.schema)
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/dtb_validate.py", line 23, in __init__
    self.validator = dtschema.DTValidator([schema_file])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/dtschema/validator.py", line 354, in __init__
    schema_cache = yaml.load(f.read())
                   ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/main.py", line 454, in load
    return constructor.get_single_data()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/constructor.py", line 117, in get_single_data
    node = self.composer.get_single_node()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/composer.py", line 77, in get_single_node
    document = self.compose_document()
               ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/composer.py", line 100, in compose_document
    node = self.compose_node(None, None)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/composer.py", line 144, in compose_node
    node = self.compose_mapping_node(anchor)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/composer.py", line 220, in compose_mapping_node
    while not self.parser.check_event(MappingEndEvent):
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/parser.py", line 141, in check_event
    self.current_event = self.state()
                         ^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/parser.py", line 600, in parse_block_mapping_key
    if self.scanner.check_token(KeyToken):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/scanner.py", line 170, in check_token
    self.fetch_more_tokens()
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/scanner.py", line 278, in fetch_more_tokens
    return self.fetch_value()
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/_temp/dtschema-venv/lib/python3.12/site-packages/ruamel/yaml/scanner.py", line 628, in fetch_value
    raise ScannerError(
ruamel.yaml.scanner.ScannerError: mapping values are not allowed here
  in "<unicode string>", line 1, column 123:
     ... c-controller.yaml: wakeup-source: missing type definition
                                         ^ (line: 1)

## Last backported rpmpd object build log lines
  HDRINST usr/include/asm/sigcontext.h
  HDRINST usr/include/asm/kvm.h
  HDRINST usr/include/asm/ptrace.h
  HDRINST usr/include/asm/sve_context.h
  HDRINST usr/include/asm/fcntl.h
  HDRINST usr/include/asm/perf_regs.h
  HDRINST usr/include/asm/param.h
  HDRINST usr/include/asm/bitsperlong.h
  HDRINST usr/include/asm/hwcap.h
  HDRINST usr/include/asm/signal.h
  HDRINST usr/include/asm/posix_types.h
  HDRINST usr/include/asm/bpf_perf_event.h
  HDRINST usr/include/asm/ucontext.h
  HDRINST usr/include/asm/statfs.h
  HDRINST usr/include/asm/auxvec.h
  HDRINST usr/include/asm/unistd.h
  HDRINST usr/include/asm/socket.h
  HDRINST usr/include/asm/siginfo.h
  HDRINST usr/include/asm/kvm_para.h
  HDRINST usr/include/asm/termbits.h
  HDRINST usr/include/asm/errno.h
  HDRINST usr/include/asm/shmbuf.h
  HDRINST usr/include/asm/swab.h
  HDRINST usr/include/asm/poll.h
  HDRINST usr/include/asm/sembuf.h
  HDRINST usr/include/asm/ioctl.h
  HDRINST usr/include/asm/resource.h
  HDRINST usr/include/asm/ipcbuf.h
  HDRINST usr/include/asm/msgbuf.h
  HDRINST usr/include/asm/stat.h
  HDRINST usr/include/asm/sockios.h
  HDRINST usr/include/asm/types.h
  HDRINST usr/include/asm/termios.h
  HDRINST usr/include/asm/ioctls.h
  HOSTCC  scripts/extract-cert
  GEN     arch/arm64/include/generated/asm/cpucaps.h
  CC      scripts/mod/empty.o
  HOSTCC  scripts/mod/mk_elfconfig
  CC      scripts/mod/devicetable-offsets.s
  MKELF   scripts/mod/elfconfig.h
  HOSTCC  scripts/mod/modpost.o
  HOSTCC  scripts/mod/sumversion.o
  UPD     scripts/mod/devicetable-offsets.h
  HOSTCC  scripts/mod/file2alias.o
  HOSTLD  scripts/mod/modpost
  CC      kernel/bounds.s
  UPD     include/generated/timeconst.h
  CALL    /home/runner/work/_temp/deen-src/scripts/atomic/check-atomics.sh
  UPD     include/generated/bounds.h
  CC      arch/arm64/kernel/asm-offsets.s
  UPD     include/generated/asm-offsets.h
  CALL    /home/runner/work/_temp/deen-src/scripts/checksyscalls.sh
  LDS     arch/arm64/kernel/vdso/vdso.lds
  CC      arch/arm64/kernel/vdso/vgettimeofday.o
  AS      arch/arm64/kernel/vdso/note.o
  AS      arch/arm64/kernel/vdso/sigreturn.o
  LD      arch/arm64/kernel/vdso/vdso.so.dbg
  VDSOSYM include/generated/vdso-offsets.h
  OBJCOPY arch/arm64/kernel/vdso/vdso.so
  LDS     arch/arm64/kernel/vdso32/vdso.lds
  CC32    arch/arm64/kernel/vdso32/note.o
  CC32    arch/arm64/kernel/vdso32/vgettimeofday.o
  HOSTCC  arch/arm64/kernel/vdso32/../../../arm/vdso/vdsomunge
  LD32    arch/arm64/kernel/vdso32/vdso.so.raw
  MUNGE   arch/arm64/kernel/vdso32/vdso.so.dbg
  VDSOSYM include/generated/vdso32-offsets.h
  OBJCOPY arch/arm64/kernel/vdso32/vdso.so
  CC      drivers/soc/qcom/rpmpd.o
make[1]: Leaving directory '/home/runner/work/_temp/deen-out'
make: Leaving directory '/home/runner/work/_temp/deen-src'
