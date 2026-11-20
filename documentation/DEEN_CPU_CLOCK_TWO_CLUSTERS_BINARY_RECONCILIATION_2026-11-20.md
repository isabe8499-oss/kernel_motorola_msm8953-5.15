# Motorola One Deen — controladora CPU_CLOCK_8953 stock C100/C200 × ACK 5.15

**Data:** 20/11/2026. Origem: `Deen_Boot_B_Audit.zip` enviado pelo usuário, `boot_b-original.img`, SHA256 `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`. O FDT C100 (offset `0x00b7820a`) tem SHA256 `537dc8c3f0a75fbe0b27d8d32b067c7efa8472dccd86b33698700e7e4022408a` e o C200 (offset `0x00abe4f6`) tem `f1bd9bb41f203ebb443b79bfd38564e6203fb858be3d53d8ad132792952c9a16`. **Inspeção binária real executada localmente e read-only.** Nenhum raw boot, FDT ou firmware publicado no repositório.

## Descoberta principal (FDT stock original)

Ambos os FDTs contêm `/soc/qcom,cpu-clock-8953@b116000`, `compatible="qcom,cpu-clock-8953"`, `qcom,num-clusters=<2>`, `#clock-cells=<1>`. Os **sete recursos MMIO** e nomes reais da propriedade `reg-names`:

| Região stock | Endereço | Tamanho |
|---|---|---|
| `rcgwr-c0-base` | `0x0B114000` | `0x68` |
| `rcgwr-c1-base` | `0x0B014000` | `0x68` |
| `c0-pll` | `0x0B116000` | `0x400` |
| `c0-mux` | `0x0B111050` | `0x8` |
| `c1-mux` | `0x0B011050` | `0x8` |
| `cci-mux` | `0x0B1D1050` | `0x8` |
| `efuse` | `0x000A4124` | `0x8` |

Os blocos `/soc/clock-controller@b111000` e `/soc/clock-controller@b011000` usam `qcom,8953-l2ccc`, com janelas de `0x1000` bytes. Os muxes CPU c0 e c1 residem no **offset +0x50** das duas janelas respectivamente. O registro `0x0B011008` usado pela sinalização RPM/SMSM é **outro offset dentro da segunda janela**, mas isso não prova a arbitração ou coexistência segura dos drivers.

O stock anuncia `clock-frequency=<2016000000>` para os oito nós Cortex-A53 (IDs `0..3` e `0x100..0x103`). O controlador descreve `vdd-mx-supply`, `vdd-cl-supply`, um clock `xo_a`, e tabelas `qcom,speed{0,2,6,7}-bin-v0-{cl,cci}`. **A frequência declarada não é medida de clock em execução e não é uma configuração segura para aplicar automaticamente.** As tabelas são metadados OEM de frequência/tensão, não OPPs validadas do novo kernel.

## Diferenças para o candidato ACK 5.15

A base `deen/c100-schema-reconcile-v2` contém oito CPUs A53 e método PSCI, mas os nós CPU compilados não apresentam `clocks`, `cpu-supply` ou `operating-points-v2`; não existe `qcom,cpu-clock-8953` no DTB candidato. Seu `mailbox@b011000`, `compatible="qcom,msm8953-apcs-kpss-global","syscon"`, cobre `0x0B011000/0x1000`.

A fonte do driver OEM 3.18 `drivers/clk/msm/clock-cpu-8953.c` implementa A53 Power, Performance e CCI e contém `cpu_clock_pwr_init()` usando `APCS_ALIAS1_CMD_RCGR=0x0B011050`. Já a árvore 5.15 contém drivers `apcs-msm8916.c` e `clk-cpu-8996.c`, específicos dos respectivos SoCs, e `qcom-cpufreq-nvmem.c` sem entrada OF MSM8953. **Não reaproveitar nenhum deles só por nome semelhante**; os requisitos de clock/reset/PLL e reguladores precisam ser conciliados.

## Gate do GitHub Actions

Os arquivos `documentation/DEEN_STOCK_CPU_CLOCK_TWO_CLUSTERS_2026-11-20.json`, `scripts/deen_stock_cpu_clock_two_cluster_gate.py` e oito testes fixam as regiões stock como referência derivada e conferem **nos dois DTBs candidatos compilados**: oito CPUs e board IDs, ausência de CPU OPP/clock provider sem port validado, presença da janela APCS e hashes de DTBs pinados.

**O GitHub Actions não lê o boot original**: ele usa apenas a referência derivada já inspecionada localmente. Resultado esperado `PASS_REFERENCE_ONLY_CPU_DVFS_PORT_HOLD` significa auditoria correta, e **não** que o clock funciona, que a CPU usa 2016 MHz ou que exista uma imagem flashável.

## Port mínimo futuro — requisitos para autorizar alterações funcionais

Reconciliar as sete janelas com o legacy 3.18; mapear nomes físicos Power/Performance/CCI, fonte XO, seleção de PLL, speed bins e reguladores, sem substituição automática do clock stock pelo mailbox APCS. Estabelecer dependências e compatibilidade DT binding/Kconfig/driver 5.15, revisar init de bootloader e método PSCI. Depois validar separadamente tensão e política térmica TSENS_TYPE3 antes de expor cpufreq/OPPs. O uso da memória compartilhada para SMD-RPM continua condicionado ao item SMEM 419 e aos contratos de IRQ.

**Status:** `CPU_CLOCK_TWO_CLUSTER_STOCK_READ=PASS_LOCAL`, `CANDIDATE_NO_CPU_DVFS_DRIVER=CONFIRMED`, `CPU_DVFS_DRIVER_PORT=HOLD`, `THERMAL_RUNTIME=HOLD`, `SMEM/RPM_RUNTIME=HOLD`, `BOOT/FLASH/MERGE=HOLD`.
