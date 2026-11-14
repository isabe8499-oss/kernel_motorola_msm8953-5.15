# Repository layout and branch policy

## Long-lived branches

- `main`: reviewed integration and documentation.
- `ack/android14-5.15-base`: pinned ACK import point.
- `deen/bringup`: device tree and minimal boot support.
- `port/qcom-msm8953`: Qualcomm platform ports.
- `port/motorola-deen`: device-specific peripherals.
- `ci/kernel-build`: CI and reproducibility tooling.

Branches are created only when there is a concrete set of changes. Avoid long-lived empty branches and do not create a separate branch for every tiny change.

## Review policy

- Keep patches small and subsystem-specific.
- Include upstream origin and donor commit references in commit messages.
- Do not push experimental root/hiding changes into the clean bring-up branch.
- Use pull requests for nontrivial code imports.
