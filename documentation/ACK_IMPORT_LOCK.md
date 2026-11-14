# Android Common Kernel import lock

- Upstream repository: https://android.googlesource.com/kernel/common
- Upstream branch: android14-5.15-lts
- Immutable imported commit: 5cb316cf9d39318326075731e4e0c39b725d9c99
- Kernel version at imported tip: Linux 5.15.223
- First-parent commits traversed: 63,852
- Total reachable commits: 1,092,253
- Incremental Git pushes: 64
- Largest estimated incremental pack: 458,419,390 bytes
- Publication method: full Git fetch followed by sequential first-parent checkpoints below GitHub's single-push limit.
- Permanent refs: upstream/android14-5.15-lts and deen/bringup-ack515-base
- Temporary staging ref: removed after promotion.

Both permanent refs compare as identical to the pinned source commit. The independent verification report records the exact remote SHA matches, successful fetch-back checks, absence of the staging ref and a passing git fsck --full.

Measured Git object store during verification: pack size 2.03 GiB; .git directory 2.1 GB. This is the repository's total object store, not an individual push. The largest single incremental pack was approximately 458 MB.

This locks the source import only. It does not certify Deen device support, a successful device-specific build, DTB validity or bootability.
