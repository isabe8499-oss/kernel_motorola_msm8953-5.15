# Motorola One Deen / ACK 5.15 — limite dos itens de memória compartilhada SMSM

Escopo: proteção de memória de `drivers/soc/qcom/smsm.c`, empilhada no [PR #25](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/25), **não** em drivers/Device Tree/firmware experimental. Data: 19/11/2026.

## Risco demonstrado pelo código

O driver `qcom_smsm_probe()` obtém `num_entries` e `num_hosts` de `SMEM_SMSM_SIZE_INFO` (item **419**, se existir com 16 bytes), ou usa valores padrão `8` e `3`. Esses números são usados para definir:

- `SMEM_SMSM_SHARED_STATE`, item **85**: `num_entries × sizeof(u32)` bytes, vetor de estados.
- `SMEM_SMSM_CPU_INTR_MASK`, item **333**: `num_entries × num_hosts × sizeof(u32)` bytes, matriz de assinaturas.

O código-base chama `qcom_smem_alloc()` mas aceita `-EEXIST`: regiões previamente criadas pelo firmware podem ter dimensão diferente da esperada. O código chamava `qcom_smem_get(..., NULL)`, ignorando o **comprimento real** dos itens, e depois usava os ponteiros para estado local e linhas/colunas da matriz. Se a região existente tiver comprimento insuficiente, o uso pode sair dos limites.

## Correção mínima e independente

1. `check_mul_overflow()` em `size_t` calcula as duas necessidades, rejeitando contagens zero ou dimensões que extrapolem o espaço de endereço.
2. O tamanho recebido de **cada** `qcom_smem_get(..., &size)` precisa ser pelo menos o comprimento requerido, **antes de qualquer indexação** em `states` ou `intr_mask`; em caso de incompatibilidade o driver retorna `-EINVAL` pela limpeza já existente `out_put`.
3. As multiplicações usadas para encontrar a linha local e a linha remota da matriz passam a ser feitas em `size_t`, impedindo truncamento intermediário em `u32`.

**Não modifica** valores padrão 8×3, conteúdo do item 419, ID de host, porta `qcom,ipc-3`, IRQ, DTS, firmware ou configurações do telefone. Não força modificação de SMEM; em caso de inconsistência rejeita o probe.

## Verificações

`scripts/test_qcom_smsm_shared_item_bounds.py` verifica a ordenação exata dos acessos, os dois tamanhos, a aritmética para casos válidos/negativos, e preservação do limite `qcom,local-host` do PR #25. O teste anterior foi atualizado somente para reconhecer `qcom_smem_get(..., &size)`. `.github/workflows/deen-ack515-smsm-smem-bounds.yml` executa 8 testes novos + 6 regressivos, compila o objeto real `smsm.o` ARM64 LLVM18 com LTO Full/CFI no runner e publica apenas logs/hashes.

**Limites:** o CI não pode verificar o conteúdo da SMEM do Motorola One em runtime. A evidência stock disponível é um **FDT no boot original**, e não a memória compartilhada inicializada após o bootloader. O valor **real** de `SMEM_SMSM_SIZE_INFO` (419), a existência e tamanho dos itens 85/333, os processadores remotos e a entrega de IRQs permanecem **desconhecidos**. Não habilitar SMSM/remoteproc para testar essa correção. `SMSM_RUNTIME=HOLD`, `RPM_ACK=HOLD`, `CPU_CLOCK=HOLD`, `TSENS=HOLD`, `BOOT/FLASH=HOLD`.

O próximo passo de integração real é decidir **quais drivers podem ser necessários no primeiro boot** sem inventar a topologia dos hosts; não atribuir os bits 13/19 a host IDs 1/3 somente pelo FDT stock.
