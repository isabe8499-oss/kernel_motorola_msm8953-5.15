# Deen C100/PVT1 — APCS, SMSM e SMD/RPM: contrato de IPC em ACK 5.15

Data: 19/11/2026. Branch de auditoria: `audit/deen-c100-apcs-smsm-ipc-20261119`; base exata [PR #13](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/13) no SHA `c63329c6f9b710f42302f76f685ec3bb3624d504`. Item: [issue #14](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/issues/14).

**ESCOPO:** ler a árvore binária candidata PVT1/C100 e PVT2/C200, Kconfig/driver e compilar os objetos em CI. **Não testar hardware, ativar firmware, modificar DTS/driver, compilar Image ou gerar artefato flashável.** O FDT *stock* C100 completo não está disponível no material desta etapa; os contratos abaixo são dos DTBs **candidatos**, não prova binária stock.

## 1. Topologia real extraída dos DTBs candidatos

Os dois DTBs anteriores, SHA256 PVT1 `fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a` e PVT2 `9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05`, contêm a mesma geometria:

| Função | Nó e propriedades candidatas | Significado no driver 5.15 |
|---|---|---|
| Provedor APCS/syscon | `/soc@0/mailbox@b011000`, `reg=<0xb011000 0x1000>`, `compatible="qcom,msm8953-apcs-kpss-global", "syscon"`, `#mbox-cells=<1>` | Nó com interface mailbox possível **e** syscon; phandle do candidato = `0x0d` |
| RPM via SMD | `/smd/rpm`, `qcom,smd-edge=<15>`, `interrupts=<0 168 1>`, `qcom,ipc=<&apcs 8 0>` | Doorbell **legacy syscon**: offset `8`, bit `0`; não um `mboxes` |
| SMSM host1 | `/smsm` `qcom,ipc-1=<&apcs 8 13>` | Regmap de syscon, offset `8`, bit `13` |
| SMSM host3 | `/smsm` `qcom,ipc-3=<&apcs 8 19>` | Regmap de syscon, offset `8`, bit `19` |
| SMSM local | `/smsm/apps@0`, `reg=<0>`, `#qcom,smem-state-cells=<1>` | Registro do estado local, não nó de IRQ de outro processador |
| SMEM | `/smem`: `memory-region=<0x47>`, `qcom,rpm-msg-ram=<0x48>`, `hwlocks=<0x49 3>` | Referencia reserva em `0x86300000`, SRAM RPM em `0x60000` e `qcom,tcsr-mutex` |
| HW spinlock | `/soc@0/hwlock@1905000`: `compatible="qcom,tcsr-mutex"`, `#hwlock-cells=<1>` | Driver `qcom_hwspinlock.c`; mutex 3 do SMEM |

**Atenção ao parsing:** `#mbox-cells=<1>` é do provedor mailbox. Já `qcom,ipc` e `qcom,ipc-1/3` são **triplas legadas independentes** (phandle do syscon, offset, número do bit). Não confundir os três itens com `mbox-cells` ou declarar uma incompatibilidade fictícia pelo tamanho da propriedade.

## 2. Caminho confirmado nos fontes — sem presumir comunicação funcional

- `drivers/rpmsg/qcom_smd.c:qcom_smd_parse_edge()`: solicita canal via `mbox_request_channel()`. Quando não existe `mboxes` e retorna `-ENODEV`, **usa o fallback** `of_parse_phandle(node, "qcom,ipc", 0)` → `syscon_node_to_regmap()` → `of_property_read_u32_index(..., 1/2)`; também requer `irq_of_parse_and_map()`. Os DTBs atuais usam **este fallback**, não o caminho de mailbox consumer.
- `drivers/soc/qcom/smsm.c:smsm_parse_ipc()`: monta `qcom,ipc-%d`, obtém o syscon, extrai offset e bit e faz envio por regmap. `qcom_smsm_probe()` consulta `SMEM_SMSM_SIZE_INFO`, com fallback para contagem padrão em sistemas antigos; depois obtém/aloca `SMEM_SMSM_SHARED_STATE` e `SMEM_SMSM_CPU_INTR_MASK`. A estrutura real dessas entradas **depende do conteúdo SMEM presente**, não é estabelecida apenas pela existência dos phandles.
- `drivers/mailbox/qcom-apcs-ipc-mailbox.c` tem match OF para `qcom,msm8953-apcs-kpss-global`, usando dados de `msm8994_apcs_data` com offset `8`. Seu suporte de mailbox é uma capacidade possível do mesmo bloco, **mas não foi demonstrado como necessário ao caminho legado SMD atual**. Selecionar `QCOM_APCS_IPC` não prova que a escrita de doorbell ou resposta RPM funcionem; possíveis interações entre o provedor de mailbox e syscon requerem cuidado no futuro.
- `drivers/soc/qcom/smd-rpm.c` contém o match OF `qcom,rpm-msm8953`, já corrigido isoladamente anteriormente. Isso não é evidência de que algum canal SMD remoto exista ou responda em runtime.
- `drivers/hwspinlock/qcom_hwspinlock.c` possui o match `qcom,tcsr-mutex`; a posse/estado do lock e a inicialização SMEM dependem de hardware/bootloader.

**Não extrapolar:** os nodes PVT1/PVT2 são árvores candidatas experimentalmente compiladas, não a configuração validada em runtime ou cópia original do stock.

## 3. Teste isolado Kconfig: Deen20 + host5 + host2

O fragmento adicional `arch/arm64/configs/deen-msm8953-apcs-smsm-host.fragment` possui **somente**:

```text
CONFIG_QCOM_APCS_IPC=y
CONFIG_QCOM_SMSM=y
```

- Base GKI resolve a configuração inicial com Clang18 e Full LTO/CFI.
- O fragmento de **20 símbolos** Deen e os **5 símbolos host** do PR #13 continuam inalterados.
- Em outro passo host, as duas novas opções são mescladas com `merge_config.sh` e `olddefconfig`. O script exige **exatamente duas diferenças**, sem nova seleção de remoteproc, SMP2P, TSENS, USB/DRM/NFC ou outra função não auditada.
- `QCOM_SMSM` seleciona `QCOM_SMEM_STATE`, mas esta já estava `y` no host5; a checagem rejeita qualquer mudança adicional inesperada.
- Os dois símbolos são **experimentos de compilação e configuração**, **não recomendação de ativá-los** na imagem do aparelho. Os drivers e a base Deen20 não são modificados.

## 4. Testes estáticos e CI

`scripts/deen_c100_apcs_smsm_ipc_gate.py`:
1. Lê os dois DTBs e exige hashes exatos, board-IDs, compatibilidade do APCS, `reg`, phandles, offset e bits do SMD+SMSM, 15/SPI168, `apps@0` e as referências SMEM/hwlocks; impede `mboxes` novo não auditado.
2. Compara fontes reais para `qcom_smd_parse_edge()`, `smsm_parse_ipc()`, tabela OF de APCS/SMSM/RPM e Kconfig.
3. Verifica delta dos `.config` host5→host7, preservação de Full LTO/CFI e proibição de remoteproc/SMP2P acidental.
4. Exige que os **11 diagnósticos de schema por DTB** permaneçam idênticos aos do PR #13, inclusive TSENS.
5. Retorna `PASS_HOST_ONLY_WITH_RUNTIME_HOLD`, nunca `RPM_RUNTIME_PASS`.

`scripts/test_deen_c100_apcs_smsm_ipc_gate.py` inclui fixtures negativas (phandle trocado por hwlock, offset errado, índice de bit ilegal, mboxes prematuro, alteração do SMSM state, remoteproc inesperado) e fixture positiva **sintética**. Isso testa a detecção de regressões, não simula hardware.

`.github/workflows/deen-c100-apcs-smsm-ipc-host.yml` monta o Kconfig GKI+Deen20+host5+host2, recompila os **13 objetos** anteriores **mais** `drivers/mailbox/qcom-apcs-ipc-mailbox.o` e `drivers/soc/qcom/smsm.o` (15 no total), DTBs PVT1/PVT2 e schema completo; guarda relatórios/objetos **sem kernel Image, boot.img, ZIP flashável ou firmware**.

## 5. Bloqueadores e a próxima decisão

- `APCS_MAILBOX_RUNTIME=HOLD`, `SMSM_STATE_MEMORY=HOLD`, `SMD_RPM_CHANNEL_ACK=HOLD`: nenhuma transação foi feita em hardware.
- `STOCK_C100_FDT_BINARY=HOLD`: binário stock original não está entre as fontes atualmente disponíveis; configurações remotas/offsets ainda requerem comparação direta.
- `SMEM_BOOTLOADER_LAYOUT=HOLD`: um phandle não prova que a memória já foi inicializada ou é partilhada corretamente.
- `TSENS_TYPE3=HOLD`, `FULL_DEEN_DEFCONFIG=HOLD`, `GLOBAL_DT_SCHEMA=REVIEW_REQUIRED`.
- `MERGE=HOLD`, `BOOT_IMAGE=HOLD`, `FLASH=HOLD`, `FIRMWARE_ENABLEMENT=HOLD`.

Após o CI, decidir em auditoria separada se o kernel candidato realmente precisa de `QCOM_APCS_IPC` como driver mailbox (o fallback syscon pode dispensá-lo) e quais dependências SMSM do boot/vendor são demonstráveis. **Não ativar por suposição, nem esconder os 11 diagnósticos restantes.**

## 6. Primeiro CI — bloqueio proposital de escopo herdado do PR #13

[Run #44583154288](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44583154288) **falhou no teste sintético host5→host7**, antes de executar Kconfig/compilação. A regra `NO_NEW_ENABLEMENT` herdada do PR #13 ainda incluía `QCOM_SMSM` — apropriado ao escopo anterior, mas incompatível com a proposta nova de medir explicitamente `QCOM_SMSM=y` como segunda opção host-only.

A correção da auditoria **não removeu SMSM da política geral anterior**: apenas neste teste, `if name in NEW: continue` admite `QCOM_APCS_IPC` e `QCOM_SMSM`, que já estão cobertos pelas condições de delta **exatamente de dois símbolos**. Remoteproc, SMP2P, TSENS e periféricos continuam proibidos. Os testes negativos exigem falha caso `QCOM_Q6V5_MSS` seja habilitado. O CI posterior precisa provar que a condicional funciona; o resultado inicial não foi reclassificado como sucesso.
