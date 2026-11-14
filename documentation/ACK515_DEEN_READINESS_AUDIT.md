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

A recursive Git tree inspection of the pinned upstream ACK confirmed no Deen board DTS, no MSM8953 SoC DTSI under arch/arm64/boot/dts/qcom, and no Motorola Deen defconfig. These gaps are now addressed partially on the isolated deen/dts-bringup branch; they remain absent from the immutable upstream ref.

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

Branch deen/dts-bringup is based on the pinned ACK commit. It now contains:

- unchanged Linux v6.1 msm8953.dtsi and pm8953.dtsi reference imports;
- a minimal Deen common DTSI with QSEE reserved-memory adjustment, PM8953 RPM regulator mapping, volume keys and primary eMMC;
- separate PVT1/PVT2 board wrappers with board IDs 0x4D 0xC100 and 0x4D 0xC200;
- MSM8953 RPM power-domain IDs, driver descriptor and bindings backported from v6.1;
- the minimal motorola,deen compatible binding.

CI run 43620086484 compiled the base fixture and both PVT candidate DTBs. dt-doc-validate, schema generation and targeted dt-validate all returned exit code 0; the backported rpmpd.o also compiled. The branch is still an experimental minimal board description, not a complete or bootable Deen tree.

## 6. Next-phase plan and acceptance criteria

### Phase A — SoC DTSI, bindings and minimal board syntax/schema: PASS
1. The imported v6.1 MSM8953/PM8953 DTSI files are integrated on the isolated Deen branch.
2. The Deen QSEE reservation, PM8953 RPM rails, volume keys, primary eMMC and two PVT wrappers are present.
3. The MSM8953 RPM power-domain driver and dt-bindings were selectively backported with provenance.
4. CI run 43620086484 compiled the synthetic base fixture and PVT1/PVT2 DTBs, passed dt-doc-validate, processed schema generation and targeted dt-validate, and compiled the branch rpmpd.o.

### Phase B — Full kernel link and Deen board description
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

The source import, ACK config/object smoke and minimal Deen DTS compile/schema smoke are approved. A full generic-GKI Image link with MSM8953 options and the two Deen candidate DTBs is now running as a separate CI gate. The Deen-specific defconfig, complete peripheral stack, boot-image packaging and device boot are not approved.

No device drivers have been copied into the upstream branch, no donor branch has been modified, and no flashable artifact is claimed.

## 8. Board revision evidence from the clean 4.19 donor

The donor's two board files declare the same compatible chain but distinct board IDs:

- PVT1: qcom,board-id = <0x4D 0xC100>
- PVT2: qcom,board-id = <0x4D 0xC200>

The donor Makefile builds both DTBs under CONFIG_MACH_MOTOROLA_DEEN. Do not choose one by assumption. The actual XT1941-3 board ID must be read from the device's bootloader/device-tree evidence before selecting a production DTB. Until then, both variants must remain available in the bring-up work.

## 9. Current CI validation records

The initial temporary DTSI fixture workflow has been superseded by the Deen board smoke workflow:

- Workflow: .github/workflows/deen-dts-base-smoke.yml
- Passing run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43620086484
- Tested branch commit: d86ecf2fa95fe3635b4ffc606fdd39b048760d1e
- Tested artifacts: base fixture, PVT1 DTB and PVT2 DTB
- Schema checks: dt-doc-validate, processed schema generation and targeted dt-validate all exit 0
- Backported MSM8953 rpmpd.o compiled.

A separate full Image build is running:
https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43621721595

That workflow uses generic GKI defconfig plus MSM8953 options. It is not a Deen-specific defconfig, not a boot image and not a hardware test. Its result must be reviewed before the next gate is marked complete.
