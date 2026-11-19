# Deen ACK 5.15 — ThinLTO + CFI, diagnóstico de link completo em CI

Data: 19/11/2026. Base: [PR #22](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/22), commit `ce011eb2367dd76974613d7424f544586791076e`. Somente workflow e documentação; nenhum driver, DTS, defconfig versionado ou firmware alterado.

## Resultado já comprovado

No PR #22, os dois checks no mesmo SHA passaram: [push #44623911112](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44623911112) e [pull_request #44623921194](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44623921194). O arquivo `vmlinux` ELF ARM64 e `arch/arm64/boot/Image` foram gerados no runner e seus hashes registrados, com os DTBs C100/C200 intactos. **A configuração temporária desse teste desabilitou LTO e CFI**. O gatilho do runner no teste Full LTO anterior [#44614603381](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/actions/runs/44614603381) ocorreu em `LTO vmlinux.o`, e o log indica desligamento externo do runner (`SIGTERM`, exit 143); a causa exata não foi verificada.

## O teste isolado nesta branch

O novo workflow `.github/workflows/deen-ack515-thinlto-cfi-full-link.yml` mantém os mesmos passos de preparação e compila `Image` com o Clang 18 e `-j2`. A diferença experimental é **somente**:

```text
CONFIG_LTO_CLANG_FULL=y -> n
CONFIG_LTO_CLANG_THIN=n -> y
CONFIG_CFI_CLANG=y      -> y (preservado)
```

- O `host5.config` original (GKI+Deen20+5 símbolos SMEM/SMD/RPM) é salvo sem modificações.
- O novo `thinlto-cfi.config` existe somente no runner e passa por `olddefconfig`; o teste exige delta exatamente de dois símbolos LTO, mantendo `CFI_CLANG`, Deen20 e host5.
- O script continua proibindo novas habilitações de `QCOM_Q6V5_MSS`, `QCOM_Q6V5_PAS`, `QCOM_WCNSS_PIL`, `QCOM_SMP2P`, `QCOM_SMSM` e `QCOM_TSENS`.
- Exige `vmlinux`, `arch/arm64/boot/Image`, ELF AArch64, e hashes idênticos dos DTBs candidatos PVT1 e PVT2.
- Publica **somente logs, `.config` e hashes**, não `Image`, `vmlinux`, `boot.img` nem o boot original do usuário.

**Interpretação:** aprovação deste teste significará `PASS_THINLTO_CFI_LINK_ONLY_GKI_FULL_LTO_NOT_YET_VALIDATED`, não aprovação do GKI original com Full LTO. O aparelho continua sem prova de boot, TSENS seguro (stock 15 sensores versus candidato 16), paridade de clocks/SMEM/APCS, firmware e configuração final Deen.

Se o CI voltar a cair por motivo externo, revisar a mensagem exata do runner e não tratar `143` como erro de C. Não atribuir memória insuficiente sem a prova correspondente.

`GKI_FULL_LTO_LINK=HOLD`, `DEVICE_RUNTIME=HOLD`, `THERMAL_PROTECTION=HOLD`, `FIRMWARE/BOOT/FLASH/MERGE=HOLD`.
