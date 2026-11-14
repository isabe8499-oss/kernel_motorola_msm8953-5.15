# Motorola One Deen memory and reserved-memory audit

Audit date: 2026-11-14  
Base: ACK `android14-5.15-lts` commit `5cb316cf9d39318326075731e4e0c39b725d9c99`  
Board references: Linux v6.1 MSM8953 DTSI and clean Motorola Deen 4.19.325 donor

## 1. Existing Linux v6.1 MSM8953 reserved-memory map

| Node in v6.1 MSM8953 DTSI | Start | Size | End (exclusive) | Role |
|---|---:|---:|---:|---|
| `zap_shader_region` | `0x81800000` | `0x2000` | `0x81802000` | Adreno ZAP shader |
| anonymous `memory@85b00000` | `0x85b00000` | `0x800000` | `0x86300000` | inherited QSEE/secure memory reservation |
| `smem_mem` | `0x86300000` | `0x100000` | `0x86400000` | Qualcomm shared memory |
| anonymous `memory@86400000` | `0x86400000` | `0x400000` | `0x86800000` | reserved firmware/system area |
| `mpss_mem` | `0x86c00000` | `0x6a00000` | `0x8d600000` | modem firmware |
| `adsp_fw_mem` | `0x8d600000` | `0x1100000` | `0x8e700000` | ADSP firmware |
| `wcnss_fw_mem` | `0x8e700000` | `0x700000` | `0x8ee00000` | WCNSS firmware |
| anonymous `memory@90000000` | `0x90000000` | `0x1000` | `0x90001000` | DFPS data |
| anonymous `memory@90001000` | `0x90001000` | `0x13ff000` | `0x91400000` | continuous splash |
| `venus_mem` | `0x91400000` | `0x700000` | `0x91b00000` | Venus firmware |
| `mba_mem` | `0x92000000` | `0x100000` | `0x92100000` | modem boot accelerator |
| RMTFS `memory@f2d00000` | `0xf2d00000` | `0x180000` | `0xf2e80000` | remote filesystem |

These ranges are inherited from the v6.1 SoC DTSI, not measured from the user's physical handset.

## 2. Deen-specific QSEE reservation

Both the clean 4.19 donor and current mainline Deen use a secure-memory area beginning at `0x84300000`. Mainline Deen reserves 32 MiB:
- Start: `0x84300000`
- Size: `0x02000000`
- End (exclusive): `0x86300000`

This exactly abuts the v6.1 `smem_mem` start at `0x86300000`. It also fully contains the inherited anonymous 8 MiB `memory@85b00000` node (`0x85b00000` through `0x86300000`). Leaving the inherited 8 MiB node in place would create overlapping reservations.

The current Deen common DTSI therefore:
1. Deletes the v6.1 anonymous `memory@85b00000` node.
2. Adds a Deen `qseecom@84300000` reservation with `reg = <0x0 0x84300000 0x0 0x02000000>` and `no-map`.
3. Deletes the inherited `memory@90001000` continuous-splash reservation, matching the initial mainline Deen DTS. The adjacent `memory@90000000` DFPS page and `venus_mem` region remain.

The delete-node statements use an absolute reference to `/reserved-memory` because the imported v6.1 SoC DTSI names these two child nodes anonymously. Newer mainline source gives them labels; those newer labels cannot be referenced in the v6.1 donor without changing its original source.

## 3. Motorola 4.19 donor-only debug reservations

The donor's `moto-mem-reserve.h` defines:
- CPU-context area per CPU: `0x3400` bytes
- 8-CPU watchdog context size: `0x3400 * 8 = 0x1a000`
- Watchdog context end: `0xef000000`
- Watchdog context base: `0xeefe6000`
- TZ backup log size: `0x2000`
- TZ backup log base: `0xeefe4000`
- Ramoops start/size: `0xef000000` / `0xC0000`

The intervals are adjacent:
- TZ backup log: `0xeefe4000`–`0xeefe6000`
- Watchdog CPU context: `0xeefe6000`–`0xef000000`
- Ramoops: `0xef000000`–`0xef0c0000`

The arithmetic shows no overlap among these three vendor intervals. It does **not** establish that the ranges are available RAM on every XT1941-3 firmware.

These vendor-only regions are deliberately not enabled in the current 5.15 DTS:
- TZ log uses a Motorola-specific `linux,contiguous-region` property and a vendor TZ-log node.
- Watchdog CPU-context uses the same vendor contiguous-region convention.
- The ramoops area is not part of the initial mainline Deen DTS and still needs validation against the target handset memory map and the ramoops binding.
- ACK 5.15 driver/binding support for the Motorola TZ-log/watchdog extensions has not been established.

The donor's `other_ext_mem` (37 MiB at `0x84300000`) and `qcom_seecom` (32 MiB at the same base) are not copied. The mainline Deen representation is the single `reserved-memory` QSEE region.

## 4. Validation status

- Static arithmetic: complete.
- DTC compilation of the QSEE replacement and splash deletion: pending the current CI run.
- Processed-schema validation of the Deen DTBs: pending the current CI run.
- Physical DRAM map and bootloader memory carve-outs: not available from repository evidence.
- Actual board revision and memory map from the XT1941-3 handset: not yet identified.

No ramoops, TZ-log or watchdog-context reservation should be enabled until the actual memory map and 5.15 driver contract are confirmed. No DTB is approved for flashing by this audit.
