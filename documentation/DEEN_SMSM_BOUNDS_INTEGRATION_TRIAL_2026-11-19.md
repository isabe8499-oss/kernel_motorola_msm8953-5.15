# Ensaio de integração — SMSM protegido + ThinLTO/CFI, somente CI

**Objetivo:** testar se o kernel ACK 5.15 inteiro continua compilando/vinculando com **as duas proteções SMSM** do [PR #25](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/25) e do [PR #26](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/26) combinadas, além da configuração experimental de SMSM com CFI do [PR #24](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/24).

Esta branch parte do SHA `82514669475f136d69d3c3a1176bfe1ff1e3161a` do PR #24. Foi confirmado previamente que seu `smsm.c` tinha SHA blob `3e8994d6110e68ddaa1fcc4a59c8eb4f0b7c62de`, **idêntico ao ACK de origem**, sem nenhuma das duas guardas. O arquivo `smsm.c` da branch recebeu a versão **exata** da branch do PR #26, depois das guardas. Foram adicionados os testes de código das duas correções.

`.github/workflows/deen-ack515-smsm-bounds-full-link.yml` reaproveita a configuração e link já testados no PR #24: GKI + Deen20 + host5, alteração **somente no runner** `QCOM_SMSM=n→y`, `QCOM_APCS_IPC=n`, e `LTO_CLANG_FULL→LTO_CLANG_THIN`, mantendo `CFI_CLANG=y`. Executa **14 testes** (6 locais + 8 de dimensão/itens SMEM), depois produz `vmlinux` e `Image` no executor e valida os dois DTBs candidatos. Publica apenas logs e checksums, **sem distribuir Image, boot.img ou firmware**.

**Esta é uma branch de ensaio, não um destino de merge.** As proteções continuam para avaliação nos PRs #25 e #26 em sequência, independentemente de testes dessa combinação. O link integral comprovará exclusivamente integração da fonte e do Kconfig experimental, e **não** o conteúdo dos itens 85/333/419 na SMEM stock, a execução de código em modem/ADSP/WCNSS, nem a segurança de boot.

**Bloqueadores P0 que permanecem:** CPU clock/CPUSS 3.18→5.15; host SMSM/SMEM item 419 e IRQ inbound; SMD-RPM ACK; TSENS stock 15 sensores com calibração/IRQ não conciliados com V2 de 16; configuração final Deen; Full LTO original; Android bootloader/AVB/boot. **Nada deve ser instalado no Motorola.**
