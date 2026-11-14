# ACK 5.15 LTS import runbook

## First attempt result

Workflow run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43598636592

Verified from job logs:
- Full fetch from `https://android.googlesource.com/kernel/common.git` completed.
- Fetched revision matched `5cb316cf9d39318326075731e4e0c39b725d9c99`.
- Disk space after fetch: approximately 83 GiB available.
- Publication failed during one large push with `RPC failed; HTTP 500`.

The error was consistent with GitHub's documented 2 GiB maximum for a single push. The import was redesigned to publish chronological first-parent checkpoints, each estimated below a conservative 1.3 GB ceiling.

## Successful history publication

The corrected import job published 63,852 first-parent commits through 64 increments. The largest estimated pack in the completed run was 458,419,390 bytes. It then created both permanent refs at the pinned SHA and deleted the temporary staging ref.

GitHub's compare endpoint returned `identical` for each permanent ref against the pinned source commit. The final workflow also performs:
- `git fsck --full --no-reflogs` on the fetched source commit.
- Remote read-back for `upstream/android14-5.15-lts` and `deen/bringup-ack515-base`.
- A remote query confirming that the temporary staging ref is absent.
- Publication of `documentation/ACK_IMPORT_LOCK.md` and `documentation/ACK_IMPORT_VERIFICATION.md` only after those gates pass.

The report file is the machine-readable project gate: Deen porting must remain blocked until it exists and shows PASS.

## Recovery design

The import workflow is idempotent. If both permanent refs already equal the pinned SHA and staging is absent, it skips history publication and runs the integrity/read-back/documentation steps. If publication stops mid-way, it resumes only from a staging commit on the pinned first-parent chain. It never force-pushes donor or ACK history.

## GitHub push-limit reference

https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit
