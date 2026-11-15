# Motorola One Deen — engineering gates

Audit date: 2026-11-14
Target: Motorola One XT1941-3 / MSM8953 / ARM64
Android target: AOSPA Android 14
Kernel base: Android Common Kernel 5.15 LTS

## Gate A — upstream source integrity: PASS

- Upstream: android14-5.15-lts
- Pinned SHA: 5cb316cf9d39318326075731e4e0c39b725d9c99
- First-parent commits: 63,852
- Reachable commits: 1,092,253
- Incremental pushes: 64
- Both permanent refs match the pinned SHA.
- Temporary staging ref is absent.
- Full git fsck --full passed.
- Evidence: documentation/ACK_IMPORT_VERIFICATION.md.

## Gate B — ACK Kconfig and SoC object smoke: PASS

CI run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43612819332

The pinned ACK 5.15 GKI configuration retained the requested MSM8953 GCC/pinctrl, SPMI PMIC arbiter/MFD, SMD RPM/RPMPD, regulator, SDHCI MSM and GPIO-key symbols. Ten selected objects compiled under Clang/LLD 18. Resolved configuration and SHA-256 object hashes are in documentation/ACK_BASE_CONFIG_SMOKE.md.

This proves selected Kconfig and object compilation, not a complete kernel link.

## Gate C — Deen DTS syntax and binary read-back: PASS; full-tree schema: HOLD

CI run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43620086484

Tested source branch commit: d86ecf2fa95fe3635b4ffc606fdd39b048760d1e.

The run generated:
- A synthetic MSM8953/PM8953 base-only fixture DTB.
- Deen PVT1 candidate DTB with board ID 0x4D 0xC100.
- Deen PVT2 candidate DTB with board ID 0x4D 0xC200.

dt-doc-validate, processed schema generation and targeted dt-validate returned exit code 0. The MSM8953 RPM power-domain provider object from the Deen branch also compiled.

Evidence and DTB hashes are in documentation/DEEN_DTS_BASE_SMOKE.md; source inventory and static audit are in documentation/DTS_STATIC_AUDIT.md.

The tested DTS blobs (common board DTSI, both PVT wrappers, rpmpd driver and Qualcomm ARM binding) were compared with the current deen/dts-bringup branch and are unchanged. Subsequent changes on that branch are documentation-only. A further binary read-back test using fdtget is running in CI run 43623081943; it checks the actual compiled qcom,board-id values, QSEE reg cells and absence of the two replaced memory nodes.

## Gate D — ThinLTO feasibility Image: PASS / Full LTO HOLD

First attempt: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43621721595 (exit 143 during LTO `vmlinux.o`; no compiler diagnostic or artifact was produced).

Second attempt: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43634169633 (commit `8d677631bef03f683e87390a21e46fc0fd16061d`). The operator-provided Actions screenshot shows the build step ending with `Process completed with exit code 143` after entering `LTO vmlinux.o`; the artifact/report steps had not started in the captured UI. The GitHub API continued reporting this run as in progress with no artifacts, so its final runner conclusion remains unavailable. This is a termination signal, not a compiler diagnostic; OOM has not been established.

The first isolated mitigation attempts, runs https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43640092181 and https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43640192256, passed configuration and bounded-swap setup but failed at the CI-only LLD preflight before starting the kernel build. The captured log identified a workflow bug: `readlink -f` resolved the `ld.lld` alias to the generic `lld-18` driver, changing argv[0]. This was not a kernel compiler/linker failure. The generated artifact is available and the job logs show the precise failure.

Historical mitigation attempts and wrapper-preflight failures are recorded above; they are superseded by the measured Full-LTO memory diagnosis and the successful ThinLTO feasibility build below.

Captured failure evidence (operator screenshot, run `43640473415`): the final visible counters were `pswpin=452308`, `pswpout=1070203`, `pgmajfault=242730`, `oom_kill=0`; `/dev/root` showed 83 GiB free. The step ended with exit 143 after approximately 52m17s in the build step (run duration shown as 1h38m1s by GitHub). This is strong evidence of substantial paging/swap churn, not evidence of a cgroup OOM kill. It does not identify who sent SIGTERM or exclude host/runner-level memory pressure. The download-log endpoint remains `BlobNotFound` and no artifacts were uploaded because subsequent steps were skipped.

The diagnostics retry `43657148581` (job `132638101488`) finally exposed the resource ceiling. The retrieved Actions log recorded `ld.lld` RSS growing from 7.6 GiB to 15.4 GiB; system memory reached 15 GiB used of 15 GiB, the 3 GiB swap reached 3 GiB used, PSI `full avg10` peaked at 15.53, swap-out rose above 1.1 million pages, and `oom_kill` remained zero. GitHub then explicitly logged `The runner has received a shutdown signal` followed by exit 143. This is evidence of Full-LTO link memory pressure exceeding the practical standard-runner envelope, not a source/compiler diagnostic and not proof of a kernel cgroup OOM kill.

The standard 16 GiB runner is no longer treated as a valid execution target for this Full-LTO workload. The current CI workflow was changed to ThinLTO+CFI strictly as a **feasibility** build of Image and both Deen DTB candidates. That result cannot pass the Full-LTO gate. Full LTO remains required for final validation and must be run on a larger-memory runner or a separately provisioned host. No kernel-source or DTS changes are implied by this CI-profile adjustment.

**Feasibility result passed (2026-11-15):** run [`43684266664`](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43684266664), commit `cf5856257cb115342d96374c92581efbe01358fc`, completed all build, artifact-upload and report-publication steps successfully. It produced ARM64 `Image` and both DTB candidates using ThinLTO+CFI. Source: `deen/dts-bringup` commit `8345f67abd78a0b6fc8e776c9279d9c88cdc5356`. Resolved config SHA-256: `83d34fb4ead2c65d37348b3eacef7b30b59324fcac59af3267f47311b52579c8`. Artifact ID: `14150664185`; ZIP SHA-256: `133a5a2760ad5a768b0a0129e475b1914edb081baa35ce183b9f0ffc896e6215`.

Verified output SHA-256 values: Image `85584de409a2dbb019286532d53dcb3e6c07bf82ea46629035c28d9abe2191c8`; PVT1 DTB `41a0106d6ade5492497a6736a9c930c82f85fe3c909791968f3f7b0726fe5532`; PVT2 DTB `c06cc92f0487675277588594e03c1ad49eb5e69ff43ae7924bec2f50cb371055`. Artifact ZIP inspection confirmed an ARM64 kernel Image and two DTB v17 files (23,786 bytes each); headers are structurally consistent and both DTBs are included in the successful build. This is not DT schema acceptance, device-specific defconfig approval, hardware PVT selection, boot.img, or Full LTO validation.

The generic GKI feasibility build already linked the ARM64 Image and both candidate DTBs in run `43684266664` using ThinLTO+CFI; its artifacts and hashes were independently verified. Gate D therefore passes for ThinLTO feasibility, while the separate Full LTO final gate remains HOLD. This is not the final Deen defconfig and not a boot image.

## Gate E — identify actual handset hardware revision: BLOCKED ON DEVICE EVIDENCE

The clean 4.19 donor contains:
- PVT1: 0x4D 0xC100
- PVT2: 0x4D 0xC200

The physical revision in the XT1941-3 handset is unknown. Do not choose a production DTB based on the model number alone. Use the read-only bootloader queries in documentation/HARDWARE_IDENTIFICATION_GATE.md to collect only product, board and hwrev. Do not send full fastboot getvar all, because it can include device identifiers.

## Gate F — minimal Deen Kconfig fragment: PASS / complete device defconfig: HOLD

The minimal base fragment passed Kconfig resolution in run `43697546575`:
- It merges with the pinned ACK `gki_defconfig`.
- All 20 required MSM8953 base symbols survive `olddefconfig`.
- `savedefconfig` and the fully resolved `.config` were generated and archived as artifact `14155361150`.
- Detailed symbol inventory and hashes: `documentation/DEEN_DEFCONFIG_SYMBOL_AUDIT.md`.

This is not a complete Deen device defconfig. The full config remains gated on board revision evidence, clean DTS schema validation and subsystem-by-subsystem driver/firmware/userspace ABI audit. Next:
1. Map the remaining donor 4.19 config symbols one by one to an ACK 5.15 Kconfig symbol or an explicitly deferred vendor subsystem.
2. Audit downstream KGSL/Adreno 506, camera-legacy/VFE/ISPIF, audio-legacy, WLAN, NFC, fingerprint, touch/display, sensors and power/thermal requirements before adding their symbols.
3. Keep the current minimal fragment limited to the drivers used by the base DTS; do not mark it as the final `deen_defconfig`.

## Gate G — boot image integration and device validation: BLOCKED

Do not produce or flash a boot image until:
- The actual PVT variant is identified.
- The target AOSPA Android 14 boot contract is measured, including boot/vendor_boot/dtbo/vbmeta partitions and image header.
- A known-good boot/recovery rollback image exists.
- Full Image, exact DTB and packaging metadata are reproducible and reviewed.

No CI result so far authorizes flashing. No physical device write has been performed by this project.
