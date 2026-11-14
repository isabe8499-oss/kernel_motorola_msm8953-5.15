# Android Common Kernel import lock

- Upstream repository: https://android.googlesource.com/kernel/common
- Upstream branch: android14-5.15-lts
- Immutable imported commit: 5cb316cf9d39318326075731e4e0c39b725d9c99
- Kernel version at imported tip: Linux 5.15.223
- First-parent commits traversed: 63,852
- Incremental Git pushes: 64
- Largest estimated incremental pack: 458,419,390 bytes
- Publication method: full Git fetch followed by sequential first-parent checkpoints. The largest measured checkpoint remained below the configured 1.3 GB safety threshold.
- Permanent refs: upstream/android14-5.15-lts and deen/bringup-ack515-base
- Temporary staging ref: import/staging-android14-5.15-lts; removed after promotion.

The two permanent refs were independently compared against the pinned source commit using GitHub's compare endpoint. Both comparisons returned identical, with zero commits ahead and zero behind.

This file locks the source import only. It does not claim that Deen device support has been ported, that the kernel builds for this device, or that it boots on the Motorola One Deen.
