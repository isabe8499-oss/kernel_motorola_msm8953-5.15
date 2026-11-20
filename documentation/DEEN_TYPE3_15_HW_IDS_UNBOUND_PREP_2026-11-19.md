# Motorola One Deen: descritor de hardware 15× TYPE3 **não ativado**

**Origem:** [PR #17](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/17), guarda genérica que impede `#qcom,sensors` ultrapassar os IDs `hw_ids` fornecidos pelo driver. Base deste trabalho: commit `8b07dfb96abfc4c1fc49683084f7228801275c91` da árvore ACK 5.15.

O FDT stock C100/C200, verificado localmente com o `boot_b-original.img` hash-pinado, declara **15 sensores IDs de hardware 1–15**. A fonte Motorola/Lineage 3.18 identifica `qcom,msm8953-tsens` como `TSENS_TYPE3`, com `TSENS_CALIB_FUSE_MAP_NONE`. O mapeamento TYPE3 base `0x4a8000` possui offsets `0x1008`, `0x100c`, `0x10a0`, `0x10e4` para TM status/clear/status térmico/trdy; o v2 moderno usa a base TM `0x4a9000` e offsets `0x0008`, `0x000c`, `0x00a0`, `0x00e4`. **Somente os endereços físicos desses registradores têm equivalência estática demonstrada.**

A alteração em `drivers/thermal/qcom/tsens-v2.c` fornece uma descrição **candidata, sem OF match**: `data_msm8953_type3_candidate`, `num_sensors=15` e `hw_ids={1,...,15}`, que referencia campos e operações v2 **apenas como base de port a auditar**. O kernel **não seleciona nem instancia** essa estrutura. `drivers/thermal/qcom/tsens.c` mantém inalterada sua `tsens_table`, que não contém `qcom,msm8953-tsens` nem ponteiro para a nova estrutura. O Device Tree herdado com 16 sensores **não é corrigido nem aprovado** por esse passo.

Os próximos requisitos antes de colocar essa estrutura em `tsens_table` são: verificar inicialização SROT, controle de clocks, calibração e eventual influência do QFPROM, interrupções críticas, thresholds e thermal zones/cooling, contagem 15 com IDs 1–15 e o novo DTS. A [quarentena de placas PR #28](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/28) continua separada e bloqueia probe do controlador herdado.

Workflow host-only: testes negativos da nova descrição e da proteção #17, compilação ARM64 de `tsens.o` e `tsens-v2.o` com LLVM18 Full LTO/CFI, artefatos limitados a logs e hashes. Não ativa firmware, não cria `Image` nem `boot.img` e não toca o telefone.

**Gates:** `TYPE3_HW_ID_LIST=15_SOURCE_ONLY`, `TYPE3_DATA_BINDING=DISABLED`, `TSENS_INIT_CALIBRATION=HOLD`, `THERMAL_RUNTIME=HOLD`, `CPU_DVFS=HOLD`, `BOOT/FLASH/MERGE=HOLD`. Mesmo CI verde não autoriza merge automático ou uso térmico em hardware.
