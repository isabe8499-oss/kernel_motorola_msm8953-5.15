# Deen C100 — integração Kconfig host-only SMEM, SMD/RPMsg e clocks RPM

Data: 2026-11-19. Base da branch: [PR #12](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/12), commit `0f8081c46fa3cd707119bc158bf6504fb035c72a`. Hardware alvo: Motorola One deen, MSM8953, candidatos C100/PVT1 e C200/PVT2. **Não é um defconfig final nem um kernel aprovado para inicialização.**

## Fontes verificadas nesta revisão

- `arch/arm64/configs/gki_defconfig`: base ACK 5.15 Android 14, com `CONFIG_LTO_CLANG_FULL=y` e `CONFIG_CFI_CLANG=y`. Não substituir por configuração genérica ou por `deen_defconfig` 4.19.
- `arch/arm64/configs/deen-msm8953-base.fragment`: **20 símbolos** revisados previamente, incluindo `ARCH_QCOM`, MSM8953 GCC/pinctrl, `QCOM_SMD_RPM`, `QCOM_RPMPD`, SPMI/PMIC, SDHCI e GPIO keys. O arquivo **permanece intacto**.
- `drivers/soc/qcom/Kconfig`: `QCOM_SMEM` depende de `HWSPINLOCK`, `QCOM_SMD_RPM` depende de `RPMSG`.
- `drivers/rpmsg/Kconfig`: `RPMSG_QCOM_SMD` depende de `MAILBOX` e `QCOM_SMEM`.
- `drivers/clk/qcom/Kconfig`: `QCOM_CLK_SMD_RPM` depende de `QCOM_SMD_RPM` e seleciona `QCOM_RPMCC`.
- `drivers/hwspinlock/Kconfig`: `HWSPINLOCK_QCOM` depende de `ARCH_QCOM` ou `COMPILE_TEST`; `HWSPINLOCK` habilita o framework.
- O DTSI Deen atual usa `qcom,smem`, `qcom,rpm-msm8953`, filhos RPMCC/RPMPD e PMIC; isso cria **dependências de software**, mas a prova de layout real SMEM/firmware/hwlocks/doorbell/RPM ACK segue pendente.

## Hipótese isolada: cinco opções adicionais

`arch/arm64/configs/deen-msm8953-smem-rpm-host.fragment` foi criado **somente para CI**:

```text
CONFIG_HWSPINLOCK=y
CONFIG_HWSPINLOCK_QCOM=y
CONFIG_QCOM_SMEM=y
CONFIG_RPMSG_QCOM_SMD=y
CONFIG_QCOM_CLK_SMD_RPM=y
```

As cinco opções não são incorporadas ao fragmento de 20 nem consideradas aprovadas para ROM. O teste resolve em sequência `gki_defconfig`, `gki + Deen20` e `gki + Deen20 + host5`, sempre com `olddefconfig` sob **LLVM 18**, e gera JSON com as diferenças de Kconfig. Todas as 25 seleções devem resolver como `y`; qualquer nova ativação de remoteproc, SMP2P, TSENS, WLAN/USB/DRM, NFC ou USB-C resultante especificamente do fragmento host rejeita o gate.

## Objetos do teste de compilação

O workflow tenta compilar individualmente, em AArch64/LLVM 18 e na configuração candidata, **13 objetos**:

1. `drivers/hwspinlock/hwspinlock_core.o`
2. `drivers/hwspinlock/qcom_hwspinlock.o`
3. `drivers/soc/qcom/smem.o`
4. `drivers/rpmsg/qcom_smd.o`
5. `drivers/soc/qcom/smd-rpm.o`
6. `drivers/soc/qcom/rpmpd.o`
7. `drivers/clk/qcom/clk-smd-rpm.o`
8. `drivers/clk/qcom/gcc-msm8953.o`
9. `drivers/pinctrl/qcom/pinctrl-msm8953.o`
10. `drivers/spmi/spmi-pmic-arb.o`
11. `drivers/regulator/qcom_smd-regulator.o`
12. `drivers/regulator/qcom_spmi-regulator.o`
13. `drivers/mmc/host/sdhci-msm.o`

Também compila os DTBs PVT1/C100 e PVT2/C200 e exige hashes **idênticos** aos anteriores; não gera `Image`, módulos, `boot.img` ou ZIP flashável. Os 11 diagnósticos de schema por DTB são preservados e revisados pelo gate já existente. Se o compilador/versão da ferramenta causar erro, o workflow deve falhar sem declarar prontidão.

## Distinção entre progresso e bootabilidade

**Um PASS significa apenas:**

- A base GKI e o fragmento Deen20 resolvem Kconfig;
- As cinco opções extra foram aceitas como um conjunto isolado por Kconfig;
- Os objetos e DTBs selecionados compilam;
- A árvore binária e os gates térmicos anteriores não foram afrouxados.

**Ainda NÃO significa:** SMEM inicializado pelo SBL, integridade de partições, mensagens RPMsg/RPM atendidas, relógios e reguladores funcionando, MMC/eMMC iniciando, kernel completo linkável, AOSPA Android14 compatível, board PVT runtime confirmada, TSENS 15 IDs validado, segurança térmica, memória stock plenamente conciliada, firmware aprovado ou boot.img correto.

Kconfig de fonte não substitui provas do FDT stock nem testes de integração. O `main`, o fragmento Deen20 e as fontes doadoras 3.18/4.19 ficam sem alteração. O PR deve continuar **draft** até auditoria dos resultados.

## Próximos gates após este CI

1. Reconciliar a seleção efetiva do caminho SMEM → RPMSG_QCOM_SMD → RPMCC com os modelos driver/OF e a propriedade de memória reservada/hwspinlocks.
2. Examinar o delta real GKI→Deen20→host5, evitando módulos inesperados e divergências de CFI/LTO.
3. Validar objetos faltantes e necessidades de console/early clock/power/eMMC, sem declarar `FULL_DEEN_DEFCONFIG_PASS`.
4. Concluir TSENS TYPE3, CPU thermal, memória/SMEM, GCC/SPMI/USB/APCS e a compatibilidade de ROM/vendor.
5. Só após aceite dos contratos de boot, DTB/PVT e recuperação, considerar uma imagem experimental. **Sem flash, merge, firmware ou habilitação de remoteproc nesta branch.**

Status: `SMEM_RPM_HOST_CONFIG=PENDING_CI`, `DEEN_FULL_DEFCONFIG=HOLD`, `GLOBAL_SCHEMA=REVIEW_REQUIRED`, `THERMAL_RUNTIME=HOLD`, `BOOT/FLASH/MERGE=HOLD`.
