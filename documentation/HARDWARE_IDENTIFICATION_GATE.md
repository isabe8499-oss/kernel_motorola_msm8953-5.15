# Motorola One XT1941-3 — hardware identity gate

## Purpose

The 4.19 Deen donor contains two board variants. The project must not select one based only on the retail model name.

- PVT1 board ID: 0x4D 0xC100
- PVT2 board ID: 0x4D 0xC200

The exact revision on the target handset has not yet been observed.

## Read-only collection

When the phone is already in bootloader/fastboot mode, run only:

    fastboot getvar product
    fastboot getvar board
    fastboot getvar hwrev

These are read-only queries. They do not unlock, erase, flash, switch slots or modify partitions.

Expected identity fields:
- product: should identify deen.
- board: should identify deen.
- hwrev: expected to identify the hardware revision, such as PVT1 or PVT2.

Only share those three output lines. Do not share the full fastboot getvar all output; it may expose serial number, IMEI, carrier and other device identifiers.

If the phone is not already in bootloader mode, do not reboot it solely for this check during the current no-device-write phase. This can be collected later when convenient.

## Decision rule

- If hwrev=PVT1, continue testing the PVT1 DTB candidate.
- If hwrev=PVT2, continue testing the PVT2 DTB candidate.
- If the value is missing, ambiguous or different, stop and inspect the stock DTB/bootloader board data. Do not guess.

## Safety boundary

No DTB is approved for flashing by this document. Board-ID agreement is necessary but not sufficient; memory layout, boot image format, vendor firmware, regulator sequencing and runtime hardware tests remain required.
