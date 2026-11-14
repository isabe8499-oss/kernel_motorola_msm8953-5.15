# ACK 5.15 LTS import runbook

## Selected source

- Canonical upstream: https://android.googlesource.com/kernel/common.git
- Branch: android14-5.15-lts
- Pinned commit: 5cb316cf9d39318326075731e4e0c39b725d9c99
- Imported kernel version: Linux 5.15.223

## Publication result

The original full-history push failed with HTTP 500 after a successful source fetch. The failure was consistent with GitHub's documented 2 GiB maximum for a single push. The import was redesigned to publish chronological first-parent checkpoints, each estimated below a conservative 1.3 GB ceiling.

The successful publication traversed 63,852 first-parent commits in 64 incremental pushes. The largest estimated checkpoint was 458,419,390 bytes. The resulting repository object store was measured at 2.03 GiB. Both permanent refs point to the exact pinned SHA:
- upstream/android14-5.15-lts
- deen/bringup-ack515-base

The temporary import/staging-android14-5.15-lts ref was removed after promotion.

## Integrity gate

The report `documentation/ACK_IMPORT_VERIFICATION.md` records PASS and confirms:
- 1,092,253 reachable commits.
- Both permanent refs match the pinned SHA.
- Both refs were fetched back and their commit IDs checked.
- The temporary staging ref is absent.
- `git fsck --full` passed.

The import workflow also performs its own full fsck before writing the lock and verification report. The imported source is therefore approved for the next engineering phase: ACK configuration and object smoke testing.

This approval certifies source-history integrity only. It is not a device-specific build, DTB validation or boot test.

## Recovery and safety

The importer is idempotent. If both permanent refs already equal the pinned SHA and staging is absent, it skips history publication and reruns the source integrity/read-back/documentation gates. If publication stops mid-way, it resumes only from a staging commit on the pinned first-parent chain. It never force-pushes donor or ACK history and never modifies the 3.18 or 4.19 donor repositories.

GitHub push-limit reference:
https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit
