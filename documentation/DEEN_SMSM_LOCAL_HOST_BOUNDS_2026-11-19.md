# ACK 5.15 Deen — validação dos índices locais de SMSM

Esta correção é independente do firmware do Motorola One e parte da árvore `deen/c100-schema-reconcile-v2`. É uma proteção genérica no driver `drivers/soc/qcom/smsm.c`, **não uma habilitação de SMSM em produção**.

## Problema encontrado no driver

O driver lê as dimensões `num_entries` e `num_hosts` de uma estrutura SMEM opcional (ID 419) ou usa valores padrão `8` e `3`. A propriedade `qcom,local-host` do Device Tree é um índice `u32` (padrão 0). Antes desta mudança, o driver **não verificava** esse índice antes de utilizá-lo para:

- `smsm->local_state = states + smsm->local_host`, indexado por `num_entries`;
- `smsm->subscription = intr_mask + smsm->local_host * smsm->num_hosts`, com uma matriz de `num_entries × num_hosts` elementos;
- entradas `entry->subscription + smsm->local_host`, cujo índice de coluna deve caber em `num_hosts`.

Assim, `local_host >= num_entries` ou `local_host >= num_hosts` poderia levar a acessos fora dos limites em dados de memória compartilhada; a correção rejeita a configuração antes do registro de estado ou uso dos ponteiros.

## Correção mínima

Após ler `qcom,local-host`, rejeita-se o índice se exceder **qualquer** uma das duas dimensões, retornando `-EINVAL` pelo caminho de limpeza já existente `out_put:`.

O ramo `local_host=0`, as dimensões padrão e os valores válidos existentes não mudam. Não são alteradas a disposição de SMEM, a lógica de interrupção, as IRQs, as propriedades `qcom,ipc`, a base APCS, o Device Tree, a configuração de produção ou o firmware.

## Validação

`scripts/test_qcom_smsm_local_host_bounds.py`: seis testes de localização e ordem da proteção no código-fonte, de casos válidos/inválidos e do caminho de limpeza. O workflow `.github/workflows/deen-ack515-smsm-local-host-guard.yml` ativa `CONFIG_QCOM_SMSM=y` **apenas no `.config` temporário do runner**, com `QCOM_APCS_IPC=n`, compila o objeto `smsm.o` em ARM64 com LLVM 18 e preserva logs e SHA-256. Sem `Image`, `boot.img` ou binário flashável.

**Limitações:** esses testes não demonstram que o bootloader tenha criado a estrutura SMEM, não determinam a existência de `SMEM_SMSM_SIZE_INFO` no Deen, não validam o mapeamento remoto de hosts e não ativam SMSM/firmware. Mesmo depois de CI verde, `SMSM_RUNTIME`, `RPM_ACK`, `CPU_CLOCK`, `TSENS_15_vs_16` e `BOOT/FLASH` continuam **HOLD**. A eventual integração em uma branch ACK requer revisão técnica independente.

A experiência de link completo com SMSM no [PR #24](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/24) continua separada desta proteção genérica.
