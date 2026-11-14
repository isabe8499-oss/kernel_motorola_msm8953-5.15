# Motorola One Deen boot contract audit

Audit date: 2026-11-14

## Cross-tree findings

The public Deen Android device trees checked retain a legacy boot-image layout:

| Reference tree | Android target | Kernel target | Header | Kernel image | Page size | Boot partition |
|---|---:|---:|---:|---|---:|---:|
| isabe8499-oss/device_motorola_deen-22, lineage-19.1 | Android 12 | separate kernel tree | v1 | Image.gz-dtb | 2048 | 64 MiB |
| MaciejMalczyk/device_motorola_deen, lineage-21/wip | Android 14 | Linux 3.18 | v1 | Image.gz-dtb | 2048 | 64 MiB |
| Sanders-Revived/device_motorola_deen, 15.0 | Android 15 | Linux 4.19 | v1 | Image.gz-dtb | 2048 | 64 MiB |

The Android 15 BoardConfig additionally specifies:
- Kernel base: 0x80000000
- Kernel offset: 0x00008000
- Flash block size: 131072
- Recovery-as-boot: enabled
- AVB build integration: disabled
- A/B updater: enabled, with boot/system/vendor in the OTA partition list
- Kernel source/config: kernel/motorola/msm8953, vendor/deen_defconfig, kernel version 4.19

The Lineage 19.1 tree separately points at device/motorola/deen-kernel and packages Image.gz-dtb as the local kernel. The Lineage 21/wip reference still targets Linux 3.18. The Android 15 reference targets Linux 4.19. None of these references establishes existing Deen 5.15 support.

## Android 15 reference fstab

The checked Android 15 tree uses:
- Slot-selected first-stage mounts for system and vendor.
- F2FS userdata with a formattable data partition.
- Separate modem, DSP and FSG firmware partitions.
- Persist and persist2 partitions.
- Removable SD and USB storage entries.

The BoardConfig checked does not declare a separate vendor_boot image or a DTBO image. The Deen kernel trees instead build Image.gz-dtb. This is a strong historical indication of a legacy boot.img layout, but absence of a BoardConfig variable is not definitive proof that a partition does not exist on every handset or firmware build.

## Provisional packaging profile (not approved for flashing)

The following values are a working reference only:
- BOOT_HEADER_VERSION = 1
- Image = Image.gz-dtb
- base = 0x80000000
- kernel offset = 0x00008000
- page size = 2048
- boot partition = 64 MiB
- recovery-as-boot = true
- A/B slots = likely; confirm live slot and partition names
- AVB = historical device tree disables AVB build integration; confirm actual boot chain and vbmeta state

Do not package or flash the 5.15 kernel solely from this table. The target AOSPA Android 14 product may change BoardConfig, vendor partitioning, recovery handling or boot image expectations.

## Required device-side evidence before packaging

Collect these from the exact XT1941-3 handset and the firmware currently installed:
1. Read-only output of `fastboot getvar product`, `fastboot getvar board` and `fastboot getvar hwrev` to establish product and PVT. Do not share full `fastboot getvar all`; it can expose serial number, IMEI and carrier data.
2. Read-only partition inventory for boot_a/boot_b, vendor_boot_a/vendor_boot_b, dtbo_a/dtbo_b, recovery and vbmeta, showing which actually exist.
3. Extracted current boot image and its unpacked header version, page size, kernel/ramdisk sizes, cmdline, OS version and header metadata.
4. Existing DTB/DTBO contents and board compatible/board ID, if present.
5. A known-good backup and tested rollback path before any write operation.

Also identify the handset's Deen board revision. The 4.19 donor contains PVT1 board ID 0x4D C100 and PVT2 board ID 0x4D C200. Do not choose one from model number alone.

The device-specific evidence can be captured without flashing. Until it is reviewed, boot packaging and device tests remain blocked.
