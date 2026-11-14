# Build and CI design

## Reproducibility

- Pin ACK commit and Clang/LLVM version; do not build from moving `main` refs.
- Use a separate output directory.
- Save resolved .config, source revision, toolchain version and build logs.
- Use a checksum manifest for all artifacts.
- Fail the job when expected Image/DTB outputs are missing or empty.

## GitHub Actions phases

1. Fast static validation: YAML, shell syntax, source/config inventory.
2. Config validation: checkout pinned ACK, apply only the Deen config/patch series, run olddefconfig.
3. Build: Image and DTBs, with explicit timeout and artifact upload.
4. Release packaging: disabled until image and boot layout are device-validated.

GitHub-hosted standard runners may not have enough disk/time for a full Android kernel tree and toolchain. Avoid a workflow that pretends to build a full kernel if the runner cannot. Use disk-space cleanup only as a measured optimization, not as a substitute for adequate storage.

## Current state

CI is intentionally limited to validating the repository scaffolding. It does not claim to compile the kernel.
