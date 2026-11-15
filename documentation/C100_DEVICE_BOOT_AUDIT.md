# Motorola One Deen — device boot audit evidence

Date: 2026-11-15
Source: user-supplied on-device readbacks and archive manifest.
Archive SHA-256: `e946172035f563cc0e1189b82306eed972848c2041604f12e8a7f0fefaea4b8a`

## Confirmed device identity
- `ro.product.device=deen`
- `ro.product.board=msm8953`
- `ro.boot.hardware=qcom`
- `ro.boot.hardware.sku=XT1941-3`
- `ro.boot.hwrev=0xC100`
- `ro.boot.slot_suffix=_a`
- Device-tree model: `deen`
- Device-tree compatible: `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`
- Reported stock fingerprint: Motorola Deen Android 10, build QPKS30.54-22-27.

This confirms the target hardware revision is C100/PVT1 for the next board-specific validation. PVT2/C200 remains a comparison fixture only; it must not be treated as the user's hardware target.

## Boot and partition layout
- `boot_a`: 67,108,864 bytes (64 MiB); raw image begins with Android boot magic `ANDROID!`; the supplied header readback reports version 1.
- `boot_b`: 67,108,864 bytes (64 MiB); raw image SHA-256: `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`.
- `dto_a`: 16,777,216 bytes (16 MiB).
- `dto_b`: 16,777,216 bytes (16 MiB); raw image SHA-256: `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e`.
- `vbmeta_a` and `vbmeta_b`: 65,536 bytes each.
- A/B slotting is present, and the separate partition is named `dto` (not `dtbo`).

The supplied shell output does not conclusively show the first eight bytes/magic of boot_b; do not infer it from the boot_a readback. The boot_b archive command also failed to create the requested ZIP because the device's toybox has no `zip` command. The tar archive itself was created and hashed.

## Implications for build/boot packaging
1. Keep C100/PVT1 as the only target board variant for device-specific bring-up.
2. Preserve the original boot_a and boot_b dumps and their hashes; never overwrite either slot during bring-up.
3. Treat Android boot image header v1 as the confirmed boot_a packaging baseline. Reconfirm boot_b magic/header and inspect the full stock boot_a/boot_b payloads before final packaging.
4. Investigate the platform's `dto_a/dto_b` partition format and bootloader consumption path. Do not assume a standard Android DTBO image solely from partition naming.
5. Determine the exact slot update/rollback procedure and vbmeta policy before any boot or DTO write.
6. Continue with DTB-only compile/readback validation. No kernel Image, boot image, DTO image, flashable ZIP, or device flashing is authorized by this audit.

## Current engineering status
The structural DTB workflow validates a minimal candidate tree, not a stock-equivalent full device tree. A successful DTB smoke test does not prove the current tree contains all board peripherals, memory reservations, PMIC wiring, regulators, storage, display, modem, Wi-Fi, audio, or thermal calibration data.
