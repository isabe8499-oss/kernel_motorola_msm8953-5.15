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

## Gate D — kernel Image build: ThinLTO feasibility / Full LTO HOLD

First attempt: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43621721595 (exit 143 during LTO `vmlinux.o`; no compiler diagnostic or artifact was produced).

Second attempt: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43634169633 (commit `8d677631bef03f683e87390a21e46fc0fd16061d`). The operator-provided Actions screenshot shows the build step ending with `Process completed with exit code 143` after entering `LTO vmlinux.o`; the artifact/report steps had not started in the captured UI. The GitHub API continued reporting this run as in progress with no artifacts, so its final runner conclusion remains unavailable. This is a termination signal, not a compiler diagnostic; OOM has not been established.

The first isolated mitigation attempts, runs https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43640092181 and https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43640192256, passed configuration and bounded-swap setup but failed at the CI-only LLD preflight before starting the kernel build. The captured log identified a workflow bug: `readlink -f` resolved the `ld.lld` alias to the generic `lld-18` driver, changing argv[0]. This was not a kernel compiler/linker failure. The generated artifact is available and the job logs show the precise failure.

Corrected retry: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43640092181 was not used for full compilation; the corrected wrapper now keeps an executable alias named `ld.lld` and must pass a real smoke ELF link with `--threads=1` before entering the expensive stage. A further run was triggered by commit `b98bd3c85b01db46eb9805d76d6bddacdf7a02a7`; wait for its exact run ID and outcome below before considering Gate D.

CI-only mitigations preserve `CONFIG_LTO_CLANG_FULL=y` and `CONFIG_CFI_CLANG=y`, cap LLD's own link-time worker pool at one thread, create only 2–4 GiB swap when filesystem headroom allows (instead of a fixed 12 GiB), and persist 30-second RAM/swap/PSI/cgroup/OOM-counter telemetry as an artifact.

Captured failure evidence (operator screenshot, run `43640473415`): the final visible counters were `pswpin=452308`, `pswpout=1070203`, `pgmajfault=242730`, `oom_kill=0`; `/dev/root` showed 83 GiB free. The step ended with exit 143 after approximately 52m17s in the build step (run duration shown as 1h38m1s by GitHub). This is strong evidence of substantial paging/swap churn, not evidence of a cgroup OOM kill. It does not identify who sent SIGTERM or exclude host/runner-level memory pressure. The download-log endpoint remains `BlobNotFound` and no artifacts were uploaded because subsequent steps were skipped.

The diagnostics retry `43657148581` (job `132638101488`) finally exposed the resource ceiling. The retrieved Actions log recorded `ld.lld` RSS growing from 7.6 GiB to 15.4 GiB; system memory reached 15 GiB used of 15 GiB, the 3 GiB swap reached 3 GiB used, PSI `full avg10` peaked at 15.53, swap-out rose above 1.1 million pages, and `oom_kill` remained zero. GitHub then explicitly logged `The runner has received a shutdown signal` followed by exit 143. This is evidence of Full-LTO link memory pressure exceeding the practical standard-runner envelope, not a source/compiler diagnostic and not proof of a kernel cgroup OOM kill.

The standard 16 GiB runner is no longer treated as a valid execution target for this Full-LTO workload. The current CI workflow was changed to ThinLTO+CFI strictly as a **feasibility** build of Image and both Deen DTB candidates. That result cannot pass the Full-LTO gate. Full LTO remains required for final validation and must be run on a larger-memory runner or a separately provisioned host. No kernel-source or DTS changes are implied by this CI-profile adjustment.

The build still uses generic GKI configuration plus the audited MSM8953 platform/PMIC/eMMC options, then attempts to link the complete ARM64 Image and build both Deen candidate DTBs. This is not the final Deen defconfig and not a boot image. Full success, hashes and artifact inspection are required before Gate D can pass.

## Gate E — identify actual handset hardware revision: BLOCKED ON DEVICE EVIDENCE

The clean 4.19 donor contains:
- PVT1: 0x4D 0xC100
- PVT2: 0x4D 0xC200

The physical revision in the XT1941-3 handset is unknown. Do not choose a production DTB based on the model number alone. Use the read-only bootloader queries in documentation/HARDWARE_IDENTIFICATION_GATE.md to collect only product, board and hwrev. Do not send full fastboot getvar all, because it can include device identifiers.

## Gate F — Deen-specific defconfig and device tree completion: NOT STARTED

Must wait for Gate D and Gate E. Then:
1. Create a Deen defconfig from the pinned ACK Kconfig; never transplant the 4.19 defconfig wholesale.
2. Audit the full reserved-memory, console, clocks, pinctrl, regulators, eMMC, thermal and remote-processor dependency graph.
3. Port subsystems in isolated patches and compile/test each group.
4. Verify proprietary firmware and userspace ABI assumptions against the Android 12 vendor baseline and target Android 14 ROM.

## Gate G — boot image integration and device validation: BLOCKED

Do not produce or flash a boot image until:
- The actual PVT variant is identified.
- The target AOSPA Android 14 boot contract is measured, including boot/vendor_boot/dtbo/vbmeta partitions and image header.
- A known-good boot/recovery rollback image exists.
- Full Image, exact DTB and packaging metadata are reproducible and reviewed.

No CI result so far authorizes flashing. No physical device write has been performed by this project.
