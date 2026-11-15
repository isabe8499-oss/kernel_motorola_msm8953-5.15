# Deen stock boot A/B and DTB extraction audit

Date: 2026-11-15  
Device reported by Android: Motorola One XT1941-3 / product `deen` / board `msm8953` / `ro.boot.hwrev=0xC100`.

## Inputs

User-supplied `shs.zip` contains complete raw read-only copies:
- `boot_a-original.img` — 67,108,864 bytes.
- `dto_a-original.img` — 16,777,216 bytes.

User-supplied `Deen_Boot_B_Audit.zip` contains:
- `boot_b-original.img` — 67,108,864 bytes.
- `dto_b-original.img` — 16,777,216 bytes.

The device copy command's output shows `dd` read all 16/16 blocks for boot and 4/4 blocks for DTO on each slot. The user-space command `toybox zip` failed on the handset because this build did not include its zip applet; the ZIP uploaded later was nevertheless valid and contained the full image files.

## Hashes of original partitions

| Image | SHA-256 |
|---|---|
| boot_a | `3d653bf0a8c65c0adefefa348959450ee655a11c0ab90429b69490032372f06d` |
| boot_b | `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765` |
| dto_a | `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e` |
| dto_b | `080acf35a507ac9849cfcba47dc2ad83e01b75663a516279c8b9d243b719643e` |

## Boot image header

Both partitions begin with `ANDROID!`, use header version 1 and page size 2048.

| Field | boot_a | boot_b |
|---|---:|---:|
| kernel_size | 12,778,220 | 12,785,442 |
| kernel_addr | 0x80008000 | 0x80008000 |
| ramdisk_size | 19,008,680 | 19,092,140 |
| ramdisk_addr | 0x81000000 | 0x81000000 |
| second_size | 0 | 0 |
| second_addr | 0 | 0 |
| tags_addr | 0x80000100 | 0x80000100 |
| page_size | 2048 | 2048 |
| header_version | 1 | 1 |
| recovery_dtbo_size | 0 | 0 |
| recovery_dtbo_offset | 0 | 0 |
| header_size | 1648 | 1648 |

Kernel gzip and ramdisk gzip streams were found and decompressed. Both kernels decompress to the same 27,065,856-byte ARM64 Image (SHA-256 `08ff474b8d8d94f3e6644a8b9e7f968606c5273111883df9aec50683b371fdd4`). The two ramdisks decompress to a 56,796,340-byte CPIO newc archive with 3,526 entries; the decompressed CPIO contents are byte-identical. Their compressed stream lengths differ, explaining why full boot images and compressed component sizes are not identical.

## Seven DTBs concatenated inside the kernel segment

The compressed kernel gzip stream ends before the end of the boot header's declared kernel segment. Seven FDT v17 blobs immediately follow it. Each blob's magic, total size and FDT structure header were parsed. The seven blobs extracted from boot_b have SHA-256 values identical to the seven extracted from boot_a.

| Index | Model | SoC | qcom,msm-id | qcom,board-id | SHA-256 |
|---|---|---|---|---|---|
| 01 | deen | MSM8953 | (0x125,0) | (0x47,0xB1A0) | `db90582485060fc737e6ef965c59fe9ac48091e5e1180fbc7b116e94b970cfb3` |
| 02 | deen | MSM8953 | (0x125,0) | (0x4D,0xC200) | `f1bd9bb41f203ebb443b79bfd38564e6203fb858be3d53d8ad132792952c9a16` |
| 03 | deen | MSM8953 | (0x125,0) | (0x47,0xB200) | `807c5eb493215d2a33c45dca492065d1b8d0f6301cb7cc49c85fb423e2d909b2` |
| 04 | deen | SDM450 | (0x152,0) | (0x48,0xA100) | `12255d74580f6ec3f704abb4293f73453a769a06cd5a333480750a7d08e0fbcb` |
| 05 | deen | MSM8953 | (0x125,0) | (0x4D,0xC100) | `537dc8c3f0a75fbe0b27d8d32b067c7efa8472dccd86b33698700e7e4022408a` |
| 06 | deen | MSM8953 | (0x125,0) | (0x47,0xA200) | `7b33da8cc1a02a91992417d0a26a61eb6c1df605198fb10ee7ff52055a1624be` |
| 07 | deen | MSM8953 | (0x125,0) | (0x47,0xB1B0) | `91e132e5fb705ac372199e61962c645c2b7da26f55d07cedb89d831fa8f030d4` |

All entries use compatible data including `qcom,msm8953-deen` (or for DTB 04, `qcom,sdm450-deen`), followed by Motorola and SoC compatibles. The board IDs and MSM IDs above are the root-level FDT properties from the stock blobs.

## DTO partition contents

Both 16 MiB DTO dumps consist entirely of zero bytes and have equal hashes. No FDT/DTBO magic is present. This audit does not infer partition semantics from the label `dto`; only the bytes in the supplied copies are confirmed zero-filled.

## Hardware revision match

Previously supplied Android properties reported `ro.boot.hwrev=0xC100`, with product `deen`, board `msm8953`, and hardware SKU `XT1941-3`.

Stock DTB 05's root `qcom,board-id=(0x4D,0xC100)` exactly matches the reported hardware revision. This is strong evidence that stock DTB 05 is the matching board table entry. It does not independently capture the bootloader's selected FDT during the boot session or establish how the bootloader chooses among entries.

## Comparison to current 5.15 PVT1 candidate

The current 5.15 PVT1 wrapper has `qcom,board-id=<0x4D 0xC100>`, matching the stock board ID, but its compatible list is `motorola,deen`, `qcom,msm8953` and it lacks the explicit `qcom,msm-id=<0x125 0>` present in stock C100. Do not assume compatible-list parity or Qualcomm multi-DTB selection behavior from board ID alone. Inspect the downstream bootloader's device-tree selection/packaging expectations or use bootloader logs/stock boot evidence before deciding whether the 5.15 multi-DTB table is accepted.

The current 5.15 Deen DTS is explicitly a minimal foundation, not a complete board tree or bootable image. It only enables volume keys, a PM8953 regulator table and primary eMMC. Display, touch, GPU, camera, audio, USB, WLAN, NFC, fingerprint, thermal/battery and remoteproc integration remain gated.

## Decision

- Read-only boot A/B and DTO dumps: PASS.
- Boot header v1 and page size 2048: PASS.
- Kernel/ramdisk decomposition and equality across slots: PASS.
- Seven stock DTBs extracted and hashes cross-matched across A/B: PASS.
- Hardware-revision C100 match to stock DTB 05: strong match.
- Bootloader's exact multi-DTB selection algorithm: HOLD.
- Current 5.15 candidate compatible/MSM ID parity with stock: HOLD.
- Android 14 boot image and AVB contract: HOLD.
- No boot.img was created and no partition was written or flashed by this audit.
