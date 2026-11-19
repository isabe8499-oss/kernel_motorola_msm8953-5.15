# Motorola One Deen — link integral ThinLTO/CFI com SMSM isolado (host6)

Data: 19/11/2026. Base exata: [PR #23](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/23), commit `546d3356cb4c60a0aad342ec51fc8d079b65d6d2`. Não é configuração de produção, nem prova de boot, firmware ou controle térmico.

## Ponto de partida comprovado

- [Push #44630740037](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44630740037) e [pull_request #44630808425](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44630808425): ambos **SUCCESS**, `vmlinux` e `Image` ARM64 vinculados com Clang18/ThinLTO **e CFI habilitado**, PVT1/PVT2 hashes idênticos, `PASS_THINLTO_CFI_LINK_ONLY_GKI_FULL_LTO_NOT_YET_VALIDATED`.
- O [PR #18](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/18) já comprovou **apenas a compilação de objetos** SMEM/RPM/SMSM quando `QCOM_SMSM=y` e `QCOM_APCS_IPC=n`; não provou incorporação do SMSM num `vmlinux` ThinLTO/CFI nem entrega de interrupções reais.
- O DTB candidato contém `/smsm/apps@0` e três `qcom,ipc`, mas não descreve os filhos remotos inbound `interrupt-controller` do stock modem/ADSP/WCNSS. Não adicionar essas entradas por inferência.

## Experiência CI: incluir SMSM como símbolo host6

O novo workflow `.github/workflows/deen-ack515-thinlto-cfi-smsm-host6.yml` aplica, em ordem, `gki_defconfig`, 20 opções mínimas Deen, 5 opções host-only SMEM/SMD/RPM e **uma única opção adicional** do fragmento já auditado:

```text
CONFIG_QCOM_SMSM=n -> y
CONFIG_QCOM_APCS_IPC=n -> n
```

O teste chama `config_gate()` do [PR #18](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/18) para exigir delta **exatamente de um símbolo**, preservando `CONFIG_QCOM_SMEM_STATE=y`, `CONFIG_CFI_CLANG=y` e `CONFIG_LTO_CLANG_FULL=y` na etapa antes da mudança de LTO. Nenhum remoteproc, SMP2P, TSENS, WLAN ou firmware é habilitado.

Em seguida, o CI realiza a mesma mudança temporária **apenas** de `CONFIG_LTO_CLANG_FULL=y→n` e `CONFIG_LTO_CLANG_THIN=n→y` já aprovada no PR #23. Confere `CONFIG_CFI_CLANG=y` e que `QCOM_SMSM=y` se mantém; executa a compilação e link completos `-j2 Image`, exige o objeto real `drivers/soc/qcom/smsm.o`, gera `vmlinux` ELF AArch64 e verifica os hashes exatos de ambos os DTBs experimentais.

O único resultado aprovável é `PASS_THINLTO_CFI_SMSM_HOST6_FULL_LINK_ONLY_RUNTIME_HOLD`. O artefato GitHub inclui **somente logs, hashes e configurações**: nenhum `Image`, `vmlinux`, `boot.img` ou FDT original.

## Próximo bloqueador funcional: plataforma/clock

O FDT stock C100 contém `qcom,8953-l2ccc` em `0x0b011000`, e o driver original `drivers/clk/msm/clock-cpu-8953.c` configura o CPU clock nos offsets `0x50/0x54/0x58`. No candidato ACK, há `qcom,msm8953-apcs-kpss-global` e o RPM/SMEM usa o bit doorbell no offset `0x8`. O `gcc-msm8953.c` do ACK cobre o GCC, **não é por si prova de implementação do clock da CPU/CPUSS**. As oito CPUs candidatas não contêm `clocks`, `cpu-supply` ou `operating-points-v2` próprios, portanto a paridade de controle de frequência/voltagem com o stock ainda não é demonstrada.

Não adicionar driver CPU-clk, cpufreq, OPP ou votos de regulador até reconciliar registradores, clocks e suporte à plataforma. Também não ligar SMSM inbound nem modem/ADSP/WCNSS sem provas do firmware. Esses são **bloqueadores de hardware**, não condições para aceitar um link sintético.

## GATES

`FULL_HOST_LINK_THINLTO_CFI=PASS_PR23`; `SMSM_FULL_LINK=IN_CI`; `STOCK_SMEM_MAILBOX=REVIEW_REQUIRED`; `CPU_CLOCK_CPUSS=HOLD`; `TSENS_15_IDS_VS_DT_16=HOLD`; `FULL_LTO_GKI=HOLD`; `FIRMWARE/DEVICE_BOOT/FLASH/MERGE=HOLD`. Sem modificações em C, DTS/DTSI ou defconfig de produção.
