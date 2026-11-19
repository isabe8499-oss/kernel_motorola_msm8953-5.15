# Standalone TSENS `hw_ids` bound check — ACK 5.15, Deen C100

Data: 2026-11-19. Origin: original [PR #12](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/12), whose base includes the deliberately incomplete staged 15-ID TSENS descriptor from [PR #11](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/11).

## Why split this patch

The driver `drivers/thermal/qcom/tsens.c` on **`deen/c100-schema-reconcile-v2` at `372a9ae6591f15b691f68cdbd2e6971f2d91c108`** has the same generic unbounded count path. `tsens_probe()` reads `data->num_sensors`, permits `#qcom,sensors` to override it, and then reads `data->hw_ids[i]` up to the overridden count. Therefore, an explicit `hw_ids` table shorter than an override could be indexed out of bounds **before** the existing check of callbacks.

This branch cherry-picks the *nine-line meaning* of the TSENS limit fix from #12 onto the older ACK-derived base **without importing**:
- `data_msm8953_stage_only`, its 15-element table, or any OF-match changes;
- the later Deen-specific RPM/SPI/remoteproc experiment chain;
- DTS or binding modifications, firmware enablement or boot config.

This allows a source reviewer to assess the generic TSENS memory safety fix independently of unresolved Motorola One hardware semantics.

## Change

After the `num_sensors <= 0` early return and **before** allocation/indexing:

```c
if (data->hw_ids && num_sensors > data->num_sensors) {
    dev_err(dev, "%s: sensor count exceeds hardware ID map\n", __func__);
    return -EINVAL;
}
```

- The default `hw_ids == NULL` path (sequential IDs) is unaffected by the additional condition.
- Valid explicit tables with `num_sensors <= data->num_sensors` remain permitted by this check.
- Larger DT overrides are rejected with `-EINVAL` rather than accessing beyond the driver's explicit table.
- This is only a correctness check on a generic API. It neither enables MSM8953-specific TSENS nor validates any physical temperature/IRQ/calibration.
- A future patch that introduces a dedicated MSM8953 descriptor still must reconcile whether the candidate DT declares **16 sensors** while stock C100 reports **15 IDs**, and must have independent runtime safety evidence.

## GitHub Actions

Workflow `.github/workflows/deen-ack515-tsens-hwids-standalone.yml` runs:
- six host tests covering the exact real-source ordering of `#qcom,sensors`, the new guard, the first `data->hw_ids[i]` read and callback checks; positive/negative counts and unchanged fallback path;
- LLVM 18 `gki_defconfig`, then a **transient CI-only** selection `NVMEM=y`, `QCOM_QFPROM=y` and `QCOM_TSENS=y` via `scripts/config`/`olddefconfig`, followed by compilation of `qcom_tsens.o` (including `tsens.o` and `tsens-v2.o`);
- object classification (LLVM LTO bitcode or AArch64 ELF) and SHA-256 verification, publishing only object/config/log artifacts.

**No kernel Image, boot.img, DTB modifications, flash package, firmware or boot action.**

## Integration decision

A successful object build supports **READY_FOR_CODE_REVIEW**, not merge into the documentation-only `main` (different Git history). The source branch `deen/c100-schema-reconcile-v2` is the immediate review base; review its history and hardware dependencies before merging. The proposal does **not** unblock PR #11, runtime TSENS, RPM/SMEM, full Deen defconfig or Android boot.

`TSENS_OBJECT_GUARD = PENDING_CI`; `TSENS_RUNTIME = HOLD`; `DEEN_STOCK_TEMPERATURE = HOLD`; `ACK_INTEGRATION_REVIEW = PENDING`; `BOOT/FLASH/FIRMWARE = HOLD`.

## Primeiro CI: falha de Kbuild por Kconfig não selecionado

[Run #44589007903](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44589007903) **falhou** na compilação inicial com `No rule to make target 'drivers/thermal/qcom/tsens.o'`. Os seis testes de lógica passaram. A causa foi observada no Makefile/Kconfig exato desta branch: `obj-$(CONFIG_QCOM_TSENS) += qcom_tsens.o`, com `QCOM_TSENS` dependente de `QCOM_QFPROM`. O GKI inicial não selecionava esses componentes para compilação como objetos diretos.

A correção de **workflow apenas** habilita `NVMEM`, `QCOM_QFPROM` e `QCOM_TSENS` no `.config` **temporário do runner**, executa `olddefconfig`, exige LTO Full/CFI inalterados e constrói `drivers/thermal/qcom/qcom_tsens.o` com as unidades reais incluídas pelo Kbuild. A geração pode produzir LLVM bitcode sob Full LTO, portanto o CI classifica bitcode ou objeto ELF AArch64, sem declarar que o kernel foi vinculado ou que o sensor está ativo no hardware. O resultado vermelho histórico foi preservado e não reclassificado.

A segunda execução [#44589691451](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44589691451) **também falhou na etapa de compilação**, mas desta vez `QCOM_TSENS=y` foi confirmado: o Kbuild não disponibilizou `qcom_tsens.o` como alvo final direto nessa invocação. O workflow foi ajustado para solicitar a construção normal do **diretório Kbuild `drivers/thermal/qcom/`**, exigindo depois os arquivos `tsens.o`, `tsens-v2.o` e `qcom_tsens.o`. A correção de nove linhas em `tsens.c` continua igual; a nova execução ainda precisa passar antes da revisão.
