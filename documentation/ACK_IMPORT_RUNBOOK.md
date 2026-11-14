# ACK 5.15 LTS import runbook

## First attempt result

Workflow run: https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43598636592

Verified from job logs:
- Checkout completed.
- Full fetch from `https://android.googlesource.com/kernel/common.git` completed.
- Fetched revision matched `5cb316cf9d39318326075731e4e0c39b725d9c99`.
- Disk space after fetch: approximately 83 GiB available.
- Publication failed during the single large push with `RPC failed; HTTP 500`.
- Neither permanent destination ref was created.

The error is consistent with GitHub's documented 2 GiB maximum for one push. GitHub recommends splitting large history imports into smaller sequential pushes. The original import used one push for both refs, which was not safe for this repository's pack size.

## Corrected strategy

The revised workflow:
1. Fetches the same immutable ACK revision and verifies its SHA.
2. Builds the first-parent chain in chronological order.
3. Estimates each incremental pack with `git pack-objects --stdout --revs`.
4. Uses an adaptive checkpoint size, reducing it until the estimated pack is below 1.3 GB.
5. Pushes each checkpoint to a temporary staging ref. Every checkpoint is a descendant of the previous first-parent checkpoint, so pushes are fast-forward updates and preserve original commit IDs and parent relationships.
6. Resumes from an existing staging checkpoint if a runner stops mid-import.
7. Promotes the completed tip to `upstream/android14-5.15-lts` and `deen/bringup-ack515-base`.
8. Removes the temporary staging ref only after both permanent refs point at the pinned tip.
9. Writes the exact SHA, checkpoint count and push count into `documentation/ACK_IMPORT_LOCK.md`.

## Independent post-import verification

The repository also contains `.github/workflows/verify-ack-import.yml`. It is triggered by the completion of this import workflow and independently:
- Reads both permanent remote refs and requires each to equal the pinned ACK SHA.
- Fetches both refs back into a clean runner and checks their resolved commit IDs.
- Requires the temporary staging ref to be absent.
- Runs `git fsck --full` against the pinned commit.
- Records first-parent/reachable commit counts and the measured Git object-store size.

The source import is not approved for device-port work until this independent verification workflow succeeds.

## Safety conditions

- The workflow refuses to import if upstream branch head differs from the pinned SHA.
- It refuses to overwrite unexpected existing destination refs.
- It does not rewrite or force-push any upstream commit.
- It does not change the 3.18 or 4.19 donor repositories.
- Completion is not declared until both destination refs are fetched back and verified to point to the exact pinned SHA.

## Source of GitHub's push limit

https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit
