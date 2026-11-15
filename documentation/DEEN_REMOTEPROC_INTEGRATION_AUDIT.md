# Motorola One Deen — remoteproc backport and integration audit

Audit date: 2026-11-15  
Target: MSM8953 / Motorola One Deen XT1941-3 / Android 14 AOSPA  
Pinned kernel baseline: ACK android14-5.15-lts  
Scope: MSS/MPSS, ADSP and Pronto-v3/WCNSS

## 1. Targeted object gate — PASS

Workflow: [run 43702964898](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43702964898)  
Job: 132777875808  
Isolated branch: `deen/msm8953-remoteproc-backports`  
Base commit: `ff2a86b64b9357bbb79435b8fa88ea94c52c4111`  
Tested head: `12366f09d36b13ab47eec139ea4aec574c59fdef`  
Delta: 7 commits, 6 changed source/binding files.

The audit workflow passed:
- `git diff --check` against the Deen bring-up base;
- presence checks for the three MSM8953 compatible strings and their binding entries;
- `dt-doc-validate` for `Documentation/devicetree/bindings/remoteproc/qcom,adsp.yaml`;
- ARM64 object compilation of the three selected remoteproc drivers.

Artifact:
- Name: `deen-msm8953-remoteproc-backport-audit`
- ID: `14156939219`
- ZIP SHA-256: `9417e40c5787f5d2d75594499bf7a61a70246dded7270b3880d4991110bd2ab4`
- Resolved config SHA-256: `081908a3fbae7e1c0739774a1cd91d9048d3da4a8c12066dc231ba622622a8d5`

Compiled objects (all verified as ELF64, little-endian, AArch64 relocatable objects):
| Object | Size | SHA-256 |
|---|---:|---|
| `qcom_q6v5_mss.o` | 520,456 bytes | `b27e7291ab74c6793622da954db58f56ce1cf595700e4a61038bc104dbd8faa4` |
| `qcom_q6v5_pas.o` | 327,944 bytes | `42588eeedcb22029e273a1301c6c9cf916b411cd37a5e5f22efb260d442bf78a` |
| `qcom_wcnss.o` | 313,536 bytes | `c30383c52a94d3890db03ad0170019a81606dca5a8f4202c37e5557880c32200` |

This is an object-level compile gate. It is not a full `vmlinux`/Image link, DTB binding validation for Deen, firmware-load test, remoteproc start/stop test, or physical device test. The workflow only validates the ADSP YAML document; the Q6V5 and WCNSS binding documents are legacy text specifications and were checked for compatible/resource coverage, not through `dt-schema`.

## 2. Exact scope of the isolated backport

The branch changes only:
- `drivers/remoteproc/qcom_q6v5_mss.c`: adds the MSM8953 MSS resource descriptor, MSM8953-specific reset handling and PAS memory setup (PAS ID 5);
- `drivers/remoteproc/qcom_q6v5_pas.c`: adds an MSM8953 ADSP resource descriptor (firmware `adsp.mdt`, PAS ID 1, CX power-domain requirement);
- `drivers/remoteproc/qcom_wcnss.c`: adds Pronto-v3 resource data (PMU offset `0x1004`, spare offset `0x1088`, power-domain names `mx,cx`, VDDPX 1.8 V);
- `Documentation/devicetree/bindings/remoteproc/qcom,adsp.yaml`;
- `Documentation/devicetree/bindings/remoteproc/qcom,q6v5.txt`;
- `Documentation/devicetree/bindings/remoteproc/qcom,wcnss-pil.txt`.

The three source changes follow upstream Linux driver architecture and add the MSM8953 data/match entries; they do not port the entire downstream 4.19 PIL framework or the downstream WLAN stack.

## 3. Donor 4.19 contract is not a drop-in match

The clean donor source was inspected at `kernel_motorola_msm8953-22:4.19.325-WIP`. Its device tree and drivers use downstream interfaces that differ from the newly backported upstream 5.15 drivers.

### MPSS / modem

Donor node:
- Node: `qcom,mss@4080000`
- Compatible: `qcom,pil-q6v55-mss`
- PAS ID: 5
- Firmware property: `qcom,firmware-name = "modem"`
- `qcom,pil-mss-memsetup`, `qcom,pil-self-auth`, `qcom,sequential-fw-load`
- Memory region: `&modem_mem`
- SMEM/SMP2P remote PID 1; donor interrupt and state names are downstream-style.
- Clocks use donor names `xo`, `iface_clk`, `bus_clk`, `mem_clk` plus `qcom,proxy-clock-names` and `qcom,active-clock-names`.

The donor 4.19 implementation is `drivers/soc/qcom/pil-q6v5-mss.c`, built around the downstream PIL/SSR framework. The new 5.15 implementation is `drivers/remoteproc/qcom_q6v5_mss.c` and registers `qcom,msm8953-mss-pil`. Its resource descriptor must be mapped to the donor clocks, resets, regulators/power domains, interrupts, memory and firmware layout explicitly. The PAS ID matching at 5 is useful evidence but is not sufficient to prove the full contract.

### ADSP / LPASS

Donor node:
- Node: `qcom,lpass@c200000`
- Compatible: `qcom,pil-tz-generic`
- PAS ID: 1
- Firmware property: `qcom,firmware-name = "adsp"`
- Memory region: `&adsp_fw_mem`
- SMEM ID 423, sysmon ID 1, SSCTL instance ID `0x14`
- Donor clocks are SCM/XO clocks; donor proxy-clock and regulator properties use the legacy `qcom,proxy-*` interface.
- Donor interrupt/SMP2P edges are named fatal, ready, proxy-unvote and stop-ack.

The 5.15 branch adds a specialized `qcom,msm8953-adsp-pil` entry with `adsp.mdt`, PAS ID 1 and a CX power-domain requirement. The firmware search path, resource naming, clocks, SMEM/SSR signals, RAM dump behavior and reserved-memory usage must be reconciled before converting the node.

### Pronto-v3 / WCNSS

Donor node:
- Node: `qcom,pronto@a21b000`
- Compatible: `qcom,pil-tz-generic`
- PAS ID: 6
- Firmware property: `qcom,firmware-name = "wcnss"`
- Memory region: `&wcnss_fw_mem`
- SMEM ID 422, sysmon ID 6, SSCTL instance ID `0x13`
- Donor uses an older `qcom,proxy-clock-names`/SCM-clock resource model.

The 5.15 branch adds `qcom,pronto-v3-pil` data for the upstream `qcom_wcnss` remoteproc driver. This is not the same as the donor's separate custom `qcom,wcnss_wlan` device at `0x0a000000`. The old WLAN driver is `drivers/soc/qcom/wcnss/wcnss_wlan.c`; it includes Pronto/IRIS power, GPIO/pinctrl, calibration/NV, WLAN control and radio integration. The remoteproc backport does not port that Wi-Fi stack or prove Android WLAN HAL compatibility.

### SMP2P / subsystem signalling

The donor's `arch/arm64/boot/dts/vendor/qcom/motorola/deen/misc.dtsi` explicitly sets these nodes to disabled:
- `qcom,smp2p-modem@0x0b011008`
- `qcom,smp2p-wcnss@0x0b011008`
- `qcom,smp2p-adsp@0x0b011008`

The underlying MSM8953 SoC DTSI defines SMP2P endpoint structures and the three remote PIDs (modem 1, ADSP 2, WCNSS 4), but the Deen board override disables those endpoints. They must not be re-enabled without confirming the exact stock board behavior and remoteproc protocol.

## 4. Donor firmware and memory contract to verify

The 4.19 SoC DTSI declares adjacent non-overlapping firmware pools:
| Region | Start | Size | End (exclusive) |
|---|---:|---:|---:|
| MPSS modem | `0x86c00000` | `0x06a00000` | `0x8d600000` |
| ADSP firmware | `0x8d600000` | `0x01100000` | `0x8e700000` |
| WCNSS firmware | `0x8e700000` | `0x00700000` | `0x8ee00000` |

These addresses were measured in the donor DTS source, not validated against the current Android 12 stock DTB or a live handset. They are not yet present in the minimal 5.15 Deen board DTS.

The donor board memory file also expands `other_ext_mem` to `0x84300000/0x02500000` and sets `qcom_seecom` to `0x84300000/0x02000000`. The current 5.15 minimal Deen DTS has a separate QSEE reservation at `0x84300000/0x02000000`. Do not combine or copy these memory definitions until the actual stock memory map, QSEE consumer expectations, reserved-memory semantics and overlap rules are reconciled. Ramoops/TZ-log/watchdog reservations are also still deferred.

The Android 12 vendor firmware payloads have not been inspected. Required files and filenames must be confirmed from the actual vendor image (including MBA/MPSS, ADSP, WCNSS and any RF/IRIS/calibration data); do not assume the donor DTS filename strings correspond directly to the firmware names expected by the 5.15 drivers.

## 5. Current decision and next actions

**Object-level backport gate: PASS. Remoteproc device integration: HOLD.**

Keep `deen/msm8953-remoteproc-backports` isolated. Do not merge it into `deen/dts-bringup` or enable MSS/ADSP/WCNSS nodes yet.

Required next steps:
1. Extract/inspect the stock Android 12 vendor firmware tree and stock DTB (read-only); record exact firmware paths and hashes, not device identifiers.
2. Compare donor 4.19 MSS/ADSP/Pronto node resources against the new 5.15 driver probe/resource requirements, property by property.
3. Design separate 5.15 DTS candidates for MSS, ADSP and WCNSS, retaining the three nodes disabled by default until their SMP2P and reset dependencies are proven.
4. Audit the three reserved-memory ranges against DRAM, QSEE, SMEM, `other_ext_mem`, ramoops, TZ-log and watchdog regions; run binary overlap/read-back checks.
5. Compile each candidate DTS and validate its exact bindings; compile the relevant objects and finally link the complete kernel.
6. Treat WCNSS WLAN driver/HAL integration as a separate workstream from Pronto remoteproc.

Do not generate a final Deen defconfig from this object-only audit. The 20-symbol base fragment remains the only approved config foundation.

## 6. Acceptance boundary

- Remoteproc object build: PASS.
- ADSP YAML document validation: PASS.
- Donor-to-upstream DT resource mapping: NOT COMPLETE.
- Vendor Android 12 firmware presence/hash: NOT VERIFIED.
- SMP2P/SMEM runtime protocol: NOT VERIFIED.
- Remoteproc reserved-memory integration: NOT APPROVED.
- Full-tree PVT schema gate: HOLD (see `DTS_SCHEMA_DIAGNOSTIC_TRIAGE.md`).
- Full LTO final link: HOLD (see `BRINGUP_GATES.md`).
- Hardware PVT: UNKNOWN.
- Device boot/flash: NOT APPROVED.
