# Validation plan

## Gate 0 — source integrity

- Pin exact ACK commit and donor commit SHAs.
- Record license and provenance for every imported patch.
- Verify branch cleanliness and build toolchain versions.

## Gate 1 — configuration and static checks

- Generate Deen config with ACK Kconfig.
- Run olddefconfig and diff the resolved .config against requested settings.
- Confirm no unknown or silently dropped symbols.
- Compile DTS/DTBs with warnings captured.
- Run checkpatch and shell/YAML syntax validation.

## Gate 2 — compile

- Build Image, modules and device DTBs using a pinned Clang/LLVM toolchain.
- Archive full logs, .config, compiler version, source SHA and output hashes.
- Treat warnings/errors as tracked issues.

## Gate 3 — boot-image integration

- Integrate the kernel image and correct DTB/DTBO using the matching device packaging method.
- Verify image format, header, page size, offsets, cmdline and boot/vendor_boot layout against the installed ROM.
- Do not assume the 4.19 AnyKernel packaging is valid for the ACK-based Android 14 ROM.

## Gate 4 — device bring-up

- First boot only with a tested rollback path and known-good boot image.
- Capture early boot logs, pstore/ramoops and recovery access.
- Validate storage, display, touch, charging, thermal, audio, camera, sensors, Wi-Fi, Bluetooth, NFC and fingerprint separately.
- Run sustained thermal and suspend/resume tests after basic stability.

## Release criteria

No release or flash recommendation until the image boots, core hardware passes, SELinux remains enforcing, logs are reviewed, and checksum plus rollback instructions are published.
