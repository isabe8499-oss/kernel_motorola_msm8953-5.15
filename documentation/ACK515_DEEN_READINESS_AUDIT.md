# ACK 5.15 LTS — Deen readiness audit

Audit date: 2026-11-14

## 1. Source import gate

Status: PASS.

- Official source: https://android.googlesource.com/kernel/common
- Branch: android14-5.15-lts
- Pinned commit: 5cb316cf9d39318326075731e4e0c39b725d9c99
- Kernel release at tip: Linux 5.15.223
- Permanent refs upstream/android14-5.15-lts and deen/bringup-ack515-base compare identical to the pinned commit.
- Independent report: documentation/ACK_IMPORT_VERIFICATION.md
- The report records exact ref matches, no staging ref, 63,852 first-parent commits, 1,092,253 reachable commits, and a passing git fsck --full.
- The import was published as 64 first-parent increments; the largest estimated pack was 458,419,390 bytes.

## 2. What ACK 5.15 already contains for MSM8953

The pinned ACK tree contains the following MSM8953-specific upstream components:

- drivers/clk/qcom/gcc-msm8953.c
- drivers/pinctrl/qcom/pinctrl-msm8953.c
- include/dt-bindings/clock/qcom,gcc-msm8953.h
- Documentation/devicetree/bindings/pinctrl/qcom,msm8953-pinctrl.yaml

The corresponding Makefiles register the clock and pinctrl drivers. This is useful SoC-level support, but it is not a complete Motorola Deen platform port.

## 3. Gaps found in the pinned ACK tree

A recursive Git tree inspection found no Deen board DTS, no MSM8953 SoC DTSI under arch/arm64/boot/dts/qcom, and no Motorola Deen defconfig. The qcom DTB Makefile does not yet register an MSM8953 target.

The upstream ACK tree also does not contain the donor's downstream KGSL tree (drivers/gpu/msm) or Motorola's techpack camera/audio legacy trees. Those are significant Android vendor-kernel integration gaps, not small DTS-only omissions.

The ACK tree has generic upstream Qualcomm CAMSS/venus infrastructure, but that must not be assumed ABI-compatible with the Deen vendor userspace or sensor stack. The Deen donor uses downstream camera-legacy/VFE/ISPIF and audio-legacy interfaces; their ABI and firmware expectations require a separate port analysis.

No SUSFS, NoMount, KernelSU, Magisk or BakaSU paths were found in the inspected ACK tree. The new base remains free of those integrations.

## 4. Deen donor findings

The clean donor remains kernel_motorola_msm8953-22 branch 4.19.325-WIP. Its source inventory includes:

- arch/arm64/configs/vendor/deen_defconfig
- arch/arm64/boot/dts/vendor/qcom/motorola/msm8953-deen-pvt1.dts
- arch/arm64/boot/dts/vendor/qcom/motorola/msm8953-deen-pvt2.dts
- arch/arm64/boot/dts/vendor/qcom/motorola/deen/*.dtsi
- downstream KGSL/Adreno 506
- camera-legacy and audio-legacy techpacks

The donor's defconfig and DTS files are reference material only. Do not copy its 4.19 config wholesale into 5.15; Kconfig symbols, subsystem APIs, bindings and vendor ABI have changed.

## 5. Existing scratch branch

Branch deen/dts-bringup is based directly on the pinned ACK commit and is three commits ahead. Its current delta is limited to:

- arch/arm64/boot/dts/qcom/msm8953.dtsi
- arch/arm64/boot/dts/qcom/pm8953.dtsi
- documentation/DTS_SOURCE_PROVENANCE.md

The two DTSI files are documented as unchanged reference imports from torvalds/linux v6.1. They are SoC/PMIC starting points, not a Deen board description. They are not yet registered in the ACK 5.15 DTB Makefile, and no dtbs/dtbs_check result has been recorded. Treat this branch as experimental, not bootable.

## 6. Next-phase plan and acceptance criteria

### Phase A — Validate the SoC DTSI backport
1. Review every include, label, compatible string, clock/reset/power-domain reference and binding used by msm8953.dtsi and pm8953.dtsi against ACK 5.15.
2. Identify properties/bindings introduced after 5.15; replace only with 5.15-supported equivalents, with provenance recorded.
3. Run dtc compilation and dtbs_check against the ACK 5.15 tree. Resolve all errors and document warnings individually.
4. Add the SoC DTSI to the DT build only after source review and checks pass.

### Phase B — Build a Deen board description
1. Compare both PVT1/PVT2 donor DTS files and board IDs; determine exact XT1941-3 hardware revision using available device/bootloader evidence.
2. Port the board root DTS and peripheral DTSI files selectively, not as a bulk copy.
3. Validate regulator, reserved-memory, SPMI/PMIC, clocks, interconnect, pinctrl, storage, display, touchscreen, sensors, thermal and charger descriptions against 5.15 bindings.
4. Keep display panel and touchscreen variants explicit; do not silently select one variant.
5. Register the resulting DTBs and validate their compiled contents.

### Phase C — Kernel config and vendor subsystem strategy
1. Create a new 5.15 Deen defconfig from the ACK 5.15 configuration baseline, using donor settings only as a symbol-by-symbol reference.
2. Resolve the downstream KGSL/Adreno 506 path and Android 14 userspace ABI before attempting a full device build.
3. Audit camera-legacy/VFE/ISPIF and audio-legacy interfaces, firmware dependencies, and vendor userspace ABI. Decide whether to backport, adapt, or use supported upstream alternatives.
4. Verify WLAN, NFC, fingerprint, sensors and charging support against actual Deen hardware and firmware.
5. Keep root/SUSFS/NoMount features excluded from this base.

### Phase D — Build and boot gates
1. Build the kernel and DTBs with a pinned Android-compatible Clang toolchain.
2. Run config validation, dtbs_check, module ABI/symbol checks, image/DTB packaging checks and reproducibility checks.
3. Test boot on the actual XT1941-3 with a recoverable stock boot image and capture serial/ramoops/last_kmsg evidence where available.
4. Validate display, touch, modem, Wi-Fi, Bluetooth, audio, cameras, sensors, NFC, fingerprint, charging, suspend/resume and thermal behavior.

## 7. Current decision

The source import is approved. The Deen port is not yet approved for a full kernel build or device flash. The next safe task is Phase A: a controlled 5.15 compatibility audit and build validation of the two SoC/PMIC DTSI reference files on deen/dts-bringup.

No device drivers have been copied into the upstream branch, no donor branch has been modified, and no flashable artifact is claimed.
