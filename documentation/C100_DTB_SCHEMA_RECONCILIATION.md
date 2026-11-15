# C100 DTB schema reconciliation — evidence and scope

Date: 2026-11-15
Repository: isabe8499-oss/kernel_motorola_msm8953-5.15

## 1. Confirmed device identity

Evidence supplied by the handset owner:
- `fastboot getvar product` = `deen`
- `fastboot getvar board` = `deen`
- `fastboot getvar hwrev` = `PVT1`
- Android properties identify SKU `XT1941-3` and `ro.boot.hwrev=0xC100`.

Independent stock image evidence:
- Seven valid FDT blobs were extracted from the supplied stock `boot_b-original.img`.
- One Deen MSM8953 FDT contains `qcom,msm-id = <0x125 0>` and `qcom,board-id = <0x4D 0xC100>`.
- The selected stock root has `model = "deen"` and the stock compatible list `qcom,msm8953-deen`, `qcom,msm8953-moto`, `qcom,msm8953`.

The bootloader's PVT1 report and stock FDT C100 tuple agree. This confirms the tuple exists in the installed stock boot set; runtime selection logic is still not directly traced.

## 2. Workflow #5 result

Run: [43737218875](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43737218875)
Job: `132882446888`
Source commit: `581beba2f442b159aaa47a9138efd3706522d824`
Artifact: `14169939865` (`deen-c100-dtb-validation`)

Observed outcomes:
- source metadata assertions: PASS
- minimal ACK configuration: PASS
- PVT1/PVT2 DTB compilation: PASS
- metadata readback: PASS
- schema stage: FAILURE / HOLD
- report and artifact upload: PASS

The C100 identity assertions were therefore not the failure. The schema stage reports numerous concrete diagnostics. Examples include:
- pinctrl SDC state missing `function`;
- legacy MSM8953 GCC/SMD-RPM/PMIC/RTC properties rejected by the selected upstream schema revision;
- DWC3 clock-name and interrupt-count mismatches;
- APCS compatible cardinality mismatch;
- missing CPU cache properties in the minimal PVT2 candidate;
- root memory node uses the same zero-filled `reg = <0 0 0 0>` convention in stock and candidate, with the DTSI comment stating that the bootloader fills it.

Do not blindly alter hardware values to satisfy a schema designed for a different binding revision. For each diagnostic, decide whether it is a real DTS error, an ACK 5.15 binding mismatch, or a documented vendor convention. Any unresolved schema diagnostic remains HOLD.

## 3. Corrected Qualcomm root binding

The ACK 5.15 tree's `Documentation/devicetree/bindings/arm/qcom.yaml` explicitly accepts the root pair:
```dts
compatible = "motorola,deen", "qcom,msm8953";
```

The preceding experimental branch had replaced it with a three-item qcom list not accepted by this binding. The correction branch now preserves the tree-supported root pair and adds only the stock-backed identity tuple:

PVT1:
```dts
model = "deen";
compatible = "motorola,deen", "qcom,msm8953";
qcom,msm-id = <0x125 0>;
qcom,board-id = <0x4D 0xC100>;
```

PVT2 remains a control candidate with board ID C200 and no asserted `qcom,msm-id`.

Branch: `deen/c100-schema-reconcile-v2`
- PVT1 commit: `6bdb3ce57a9b2d69faeefcbdc328f7b89e1448d9`
- PVT2 commit: `b7d7bc3abb65c2d5ec39cacb64a8dfab9ceac1ca`

The main-branch workflow has been updated to validate this branch by default and to report schema outcomes separately. The schema stage preserves the full log and does not convert diagnostics to PASS.

## 4. Important structural finding: the DTB is still a minimal skeleton

Stock C100 FDT:
- 253,704 bytes
- 1,471 nodes
- 255 unique compatible strings

Previous minimal PVT1 candidate:
- approximately 23.8 KiB
- 248 nodes
- 56 unique compatible strings
- 235 stock compatible strings absent verbatim in candidate

The stock/candidate topology differs substantially (stock has a large `/soc` tree; candidate uses a smaller `/soc@0` tree). Node and compatible counts are inventory signals only, not one-to-one semantic device mapping. Some vendor compatibles map to upstream drivers with different strings. Do not blindly copy strings or nodes.

### High-priority subsystem gaps

| Subsystem | Stock C100 evidence | Minimal candidate state | Gate |
|---|---|---|---|
| Modem/MSS | `qcom,pil-q6v55-mss`, `modem` firmware, modem memory reference | MSS/PIL node absent | HOLD |
| ADSP | ADSP loader, SMD/SMSM, firmware/reservation | ADSP loader and endpoint graph absent | HOLD |
| WCNSS/Wi-Fi | `qcom,wcnss_wlan`, SMP2P/SMD/SMSM, firmware reservation | WCNSS graph absent | HOLD |
| SMEM/IPC | Stock SMEM and modem/ADSP/WCNSS channels | Only generic RPM/SMSM foundation | HOLD |
| USB | Stock DWC3/PHY config | USB PHY path disabled | HOLD |
| Display/camera/audio | MDSS, camera/ISP, codec/QDSP | Not represented | HOLD |

Successful object compilation of drivers does not prove device-tree wiring, memory mapping, firmware naming, IPC channel topology, or runtime handshake compatibility.

## 5. Reserved memory reconciliation

The audit found:
- Stock C100 reserves `other_ext_region@0` at 0x84300000, size 0x02500000 (37 MiB).
- Candidate splits a 37 MiB span into qseecom 32 MiB plus adjacent 1 MiB and 4 MiB reservations. Consumers/semantics have not been proven equivalent.
- Stock modem: 0x86c00000 / 0x06a00000
- ADSP: 0x8d600000 / 0x01100000
- WCNSS: 0x8e700000 / 0x00700000
- DFPS: 0x90000000 / 0x1000
- splash: 0x90001000 / 0x013ff000
- ramoops: 0xef000000 / 0x000c0000
- TZ log: 0xaefd2000 / 0x2000
- watchdog CPU context: 0xaefd4000 / 0x2c000

The candidate has matching modem, ADSP, WCNSS and DFPS ranges, but does not yet reproduce stock ramoops, TZ-log, watchdog-context or splash reservations. It also introduces extra reservations requiring consumer reconciliation. Do not change any range without tracing firmware/driver consumers.

The zero-filled root memory `reg` also occurs in stock C100 and the upstream MSM8953 DTSI, with the comment that the bootloader populates it. Do not invent RAM bounds to silence schema.

## 6. Next engineering work

The next branch work should remain non-flashable and proceed in this order:

1. Import/reconcile stock C100 FDT and source topology as a read-only inventory.
2. Memory and SMEM: map every `memory-region` phandle to reserved-memory entries and confirm driver expectations.
3. Modem/MSS: verify ACK 5.15 remoteproc/PIL compatible, firmware filename, memory regions, interrupts, resets, clocks, and SMD/SMSM links against stock.
4. ADSP: map loader, firmware, SMEM, SMD/SMSM and SMP2P links.
5. WCNSS: map firmware reservation, WCNSS node, transport and SMP2P links.
6. Only after each subsystem has a fully evidenced mapping, add its nodes in an isolated commit and run dtc + binding validation.
7. Resolve remaining vendor binding/schema deltas deliberately and record exceptions; never suppress diagnostics.

No boot image, flash operation, or boot test is authorized by this report. The current DTB is not stock-equivalent and must not be flashed.
