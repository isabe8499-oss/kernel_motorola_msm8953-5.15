# Deen C100/PVT1 e C200/PVT2 — experiência SMSM sem driver APCS mailbox

Data: 19/11/2026. Origem: [PR #13](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/13), SHA `c63329c6f9b710f42302f76f685ec3bb3624d504`. Comparação com [PR #15](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/15), que testou simultaneamente `QCOM_SMSM` e `QCOM_APCS_IPC` no host.

## Hipótese limitada

As árvores **candidatas** PVT1/C100 e PVT2/C200 descrevem o envio RPM através de `/smd/rpm` / `qcom,ipc=<&apcs 8 0>` e SMSM por `qcom,ipc-1=<&apcs 8 13>` e `qcom,ipc-3=<&apcs 8 19>`. No kernel ACK 5.15, `drivers/rpmsg/qcom_smd.c` contém o fallback `qcom,ipc` via `syscon_node_to_regmap` e `drivers/soc/qcom/smsm.c` usa `qcom,ipc-%d` via syscon. A presença de um provedor `qcom,msm8953-apcs-kpss-global` com função mailbox **não comprova** que seja necessário selecionar seu driver mailbox quando o Device Tree já escolhe o caminho legado syscon.

A hipótese testável em CI é **apenas**: os objetos SMEM, SMD/RPM, SMSM e clocks RPM compilam com `QCOM_APCS_IPC=n`, mantendo os três `qcom,ipc` candidatos corretos e sem alteração nos DTBs. Um PASS **não** demonstra que a entrega de doorbell/interrupção, ACK RPM ou memória SMEM em hardware funcione sem mailbox.

## Fronteira de Kconfig

A ordem do CI é `gki_defconfig → Deen20 → host5 → SMSM-only`, cada fragmento seguido por `olddefconfig`. O arquivo novo `arch/arm64/configs/deen-msm8953-smsm-only-host.fragment` contém **somente**:

```text
CONFIG_QCOM_SMSM=y
```

O verificador exige:
- Delta exato `QCOM_SMSM=n→y`, nenhum outro símbolo novo;
- `QCOM_APCS_IPC=n` antes **e depois**, e `QCOM_SMP2P` e remoteproc não habilitados por esta experiência;
- `QCOM_SMEM_STATE=y`, `CONFIG_CFI_CLANG=y` e `CONFIG_LTO_CLANG_FULL=y` mantidos;
- opções anteriores Deen20/host5 permanecendo `y`;
- cinco objetos AArch64 compilados e DTBs candidatos imutáveis.

O fragmento original Deen20 e o host5 não foram alterados. Isto **não** é uma recomendação de configuração final para a ROM nem substitui a medição real da entrega dos bits APCS.

## Testes de Device Tree

O parser FDT já existente verifica que os três `qcom,ipc` referenciam o mesmo phandle APCS do candidato e preservam a tupla (offset, bit) `(8,0)`, `(8,13)` e `(8,19)`, `qcom,smd-edge=<15>`, identidade PVT e ausência de `mboxes` no SMD. As fixtures negativas rejeitam troca de phandle, bit/offset errado, caminho mailbox inesperado e habilitação acidental de `QCOM_APCS_IPC` ou remoteproc.

Hashes esperados, idênticos ao PR #13:
- PVT1 `fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a`;
- PVT2 `9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05`.

**Nenhuma comparação direta binária com o FDT stock C100 ocorre nesse CI.** Documentos históricos em `main` registram um FDT stock C100 com 1.471 nós / 253.704 bytes contra DTB candidato inicial muito menor; o pacote atual do projeto não contém os bytes originais `boot_b-original.img` ou o FDT de 253.704 bytes. Portanto, a equivalência dos três IPCs com stock permanece **HOLD**; valores de candidato não devem ser apresentados como hardware comprovado.

## Aceite e próximas decisões

O workflow `.github/workflows/deen-c100-smsm-only-no-apcs.yml` compila 5 objetos de transporte, 2 DTBs candidatos, executa testes negativos, preserva o inventário de configuração e gera JSON `PASS_HOST_ONLY_WITH_RUNTIME_HOLD` se tudo passar. Não cria Image, boot.img, flashable ZIP, firmware ou módulos de ativação.

Se a experiência passar, a interpretação é **SMSM configurável/compilável sem o driver APCS mailbox nessa árvore e nesse Kconfig**, e não que `QCOM_APCS_IPC` jamais seja necessário em outra função, board ou em runtime. Continuam `STOCK_FDT=HOLD`, `SMEM_RUNTIME=HOLD`, `SMD_RPM_ACK=HOLD`, `TSENS_RUNTIME=HOLD`, `FULL_DEEN_DEFCONFIG=HOLD`, `GLOBAL_SCHEMA=REVIEW_REQUIRED`, `BOOT/FLASH/FIRMWARE/MERGE=HOLD`.

Próximo gate com evidência necessária: obter o **FDT stock C100 original, com SHA/verificação de origem**, e confrontar os nós/apps/ADSP/WCNSS/modem, o SMP2P remoto e consumidores de SMEM com a árvore ACK, sem habilitar firmware nem inventar reserva de memória. Esse trabalho não foi realizado nesta proposta.
