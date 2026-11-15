# Motorola One Deen — 4.19 donor to ACK 5.15 configuration audit

Audit date: 2026-11-15

## Source inputs and immutable references

| Input | Ref | Blob SHA |
|---|---|---|
| Donor config | `isabe8499-oss/kernel_motorola_msm8953-22:4.19.325-WIP/arch/arm64/configs/vendor/deen_defconfig` | `ecef3b19eb5cbe5fef0c343b8fee2d54071a3c37` |
| ACK baseline | `kernel_motorola_msm8953-5.15:upstream/android14-5.15-lts/arch/arm64/configs/gki_defconfig` | `808c9ed384d22207ddfe8cea757f52fa51c9eab5` |

The donor config is reference material only. It must not be copied wholesale into ACK 5.15.

## Mechanical key comparison

The raw assignment-key comparison found:

- Donor 4.19 `deen_defconfig`: 643 explicit `CONFIG_*=value` assignments plus 57 `# CONFIG_*=n` entries (700 unique keys total).
- ACK 5.15 `gki_defconfig`: 656 assignments.
- 314 explicit assignment keys appear in the donor but not in the explicit-assignment set of the GKI baseline.
- 327 assignment keys appear in the GKI baseline but not explicitly in the donor.

These counts are a set comparison of config keys. They do **not** prove that every donor-only symbol is missing from the 5.15 Kconfig tree, nor that every GKI-only option is required by Deen. Kconfig definition, dependencies, architecture/API compatibility and Android 14 userspace ABI must be evaluated separately.

## 5.15 Kconfig definitions verified in source

The following MSM8953 dependencies were found in the pinned ACK 5.15 Kconfig files:

| Symbol | Kconfig source | Blob SHA |
|---|---|---|
| `MSM_GCC_8953` | `drivers/clk/qcom/Kconfig` | `4c8bb23ca730493ab69c77fba5f3004ae9b8de79` |
| `PINCTRL_MSM8953` | `drivers/pinctrl/qcom/Kconfig` | `f1b5176a5085bd2efc4c330f29e3c3c03693c319` |
| `QCOM_SMD_RPM`, `QCOM_RPMPD` | `drivers/soc/qcom/Kconfig` | `6a97e8af939085dc577e3ecaf404598d9cf1869b` |
| `SPMI_MSM_PMIC_ARB` | `drivers/spmi/Kconfig` | `2874b6c26028b45136bd3dc2b2c3ebff95ae94ea` |
| `MMC_SDHCI_MSM` | `drivers/mmc/host/Kconfig` | `a79dc4e95dcf506cb0703c152918b5b860dd17c7` |

The existing readiness audit separately establishes that the pinned ACK lacks the donor's downstream KGSL tree and Motorola camera/audio legacy techpacks. Their vendor config symbols must not be treated as supported merely because they appear in the 4.19 config.

Legacy machine/platform symbols such as `ARCH_MSM8953`, `MACH_MOTOROLA_DEEN` and `MACH_MOTOROLA_MSM8953` are not copied into the new fragment. The 5.15 bring-up is based on the generic Qualcomm architecture plus the board's Device Tree compatible and explicit SoC drivers, not the donor's 4.19 machine Kconfig architecture.


## Full donor symbol-definition inventory — PASS

A second, read-only audit scanned the ACK 5.15 source tree rather than comparing only the names in two config files.

- Workflow: [43699488864](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43699488864)
- ACK source commit: `ff2a86b64b9357bbb79435b8fa88ea94c52c4111`
- Kconfig files scanned: 1,615
- Donor unique symbols: 700
- Duplicate donor symbol assignments: 0
- Symbols with no Kconfig definition found in ACK: 208
- Symbols defined in ACK and explicitly represented in GKI baseline: 355
- Symbols defined in ACK but neither explicit in GKI nor selected by the minimal fragment: 125
- Donor symbols also selected in the minimal Deen fragment: 12
- The 20-symbol minimal fragment contains 8 additional symbols not present in the 4.19 donor config; they are 5.15-specific base requirements.

Artifact:
- Name: `deen-donor-config-inventory`
- ID: `14156096378`
- ZIP SHA-256: `3d24cc02c49c03a3d7d42af11b4c501a4949fb4b20de42a177a767245a24bac2`
- Donor config SHA-256: `9eb465f7aa489af4a49439b8f720e7c330448a2e104c031bd8f25f49e73869c8`
- Resolved fragment .config SHA-256: `7fd7204305ffec3ea0e07acd93c081fb9e7ef81d52cf6a3c25516372e6e92a30`
- Generated savedefconfig SHA-256: `870133b82ebc2a3adda0f53213e4b98050eb94af91437829aef54e5f2b92cd6a`

High-impact donor symbols with no ACK Kconfig definition include `QCOM_KGSL`, `MSM_CAMERA`, `MSMB_CAMERA`, `NFC_NQ`, `PRONTO_WLAN`, `USB_DWC3_MSM`, `FUSB302`, `TOUCHSCREEN_NT36XXX` and `TOUCHSCREEN_FT5X06`. Their absence is consistent with missing vendor techpacks or different upstream subsystem names; it does not mean an unrelated upstream driver is ABI-equivalent.

Conversely, ACK 5.15 has generic equivalents such as `TYPEC_FUSB302`, `USB_DWC3_QCOM` and `NFC_NXP_NCI_I2C`, but their compatible strings, wiring, firmware and userspace contracts must be checked against the actual Deen board. A Kconfig symbol's existence is not sufficient evidence to enable the subsystem.

The detailed cross-subsystem decision matrix is in `documentation/DEEN_SUBSYSTEM_COMPATIBILITY_AUDIT.md`.

## Minimal Deen bring-up fragment

A minimal fragment was added on branch `deen/dts-bringup`:

- Path: `arch/arm64/configs/deen-msm8953-base.fragment`
- Commit: `5ae9f4d7d2dc533fbf1ae41e72c93b41e12d487a`
- Blob SHA: `8fb9f794c626c87d53293a2d2881205b9de322e7`

It contains 20 selected symbols covering Qualcomm architecture/clock, MSM8953 GCC, pinctrl, mailbox/RPMSG, SMD RPM/RPMPD, SPMI/PMIC regulators, SDHCI/eMMC and GPIO keys. This scope maps to the currently enabled minimal Deen DTS foundation.

It intentionally does not enable downstream KGSL, camera/audio techpacks, WLAN, NFC, fingerprint, display, touch or vendor power/thermal policy. Those require separate driver, binding, firmware and userspace ABI audits.

## Resolution test — PASS

The corrected dedicated Kconfig audit passed:

- Workflow run: [43697546575](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/43697546575)
- Job: `132761315172`
- Source commit for the fragment: `ff2a86b64b9357bbb79435b8fa88ea94c52c4111`
- Artifact: `deen-defconfig-symbol-audit`, ID `14155361150`
- Artifact ZIP SHA-256: `76c282013135374c58aabb75d45a6563e2b6b78b50a163aaab9e894bc0c5471e`
- Resolved `.config` SHA-256: `7fd7204305ffec3ea0e07acd93c081fb9e7ef81d52cf6a3c25516372e6e92a30`
- Generated `savedefconfig` SHA-256: `870133b82ebc2a3adda0f53213e4b98050eb94af91437829aef54e5f2b92cd6a`
- Fragment SHA-256: `0b62555f7b6743391a05f991c4c41f12242361bdf4163f36ac248ba63b13923d`

The workflow starts from pinned ACK `gki_defconfig`, merges the Deen base fragment, runs `olddefconfig`, verifies all 20 required symbols and generates `savedefconfig`. The artifact was downloaded and independently inspected; all 20 expected `CONFIG_*=y` entries were present. Merge-log notices were ordinary redundant/redefined fragment settings; no required symbol was dropped.

This validates only the minimal base fragment, not a complete device defconfig. It does not compile the kernel and does not create a flashable image.

The final Deen device configuration remains gated on schema remediation, peripheral/firmware support and board revision evidence.
