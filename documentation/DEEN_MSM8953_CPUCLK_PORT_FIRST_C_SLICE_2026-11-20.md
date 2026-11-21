# Motorola One Deen 5.15 — primeiro trecho C do port CPUCLK MSM8953

Data: 20/11/2026. Base imutável: PR #31, commit `92dff9a3e542cd0dc4a7297c5fee0ff928fd401b`. Fonte OEM: `drivers/clk/msm/clock-cpu-8953.c` em `isabe8499-oss/kernel_motorola_msm8953` / `lineage-18.1`, SHA blob `8add43967bbc6fac12f04f3b91117c9462161915`.

## O que foi implementado

`drivers/clk/qcom/clk-cpu-msm8953-preflight.c` é **código kernel C efetivo, mas ainda não é driver funcional**:
- verifica os nomes e tamanhos mínimos dos **sete recursos físicos** exigidos pelo controlador OEM dos dois clusters, rejeitando qualquer recurso ausente, insuficiente ou com sobreposição;
- implementa a extração do *speed bin* conforme o legado (`efuse[10:8]`), sem efetuar leitura do eFuse;
- valida a forma dos pares u32 de frequência/tensão em propriedades `qcom,speedN-bin-v0-cl` e `qcom,speedN-bin-v0-cci`, sem configurá-las no hardware.

É compilado somente com `CONFIG_QCOM_MSM8953_CPUCLK_PREFLIGHT=y` e `COMPILE_TEST=y`, num `.config` temporário do GitHub Actions. Não há `platform_driver_register`, `of_clk_add_hw_provider`, driver OF ativável, Kconfig habilitado na defconfig Deen, MMIO read/write, programação de PLL, manipulação de reguladores ou alteração de OPP.

O arquivo não tenta ser uma solução artificial de boot: o port verdadeiro ainda precisará de callbacks Common Clock Framework, controle de tensão/CCI e sequenciamento de PLL, todos validados contra o FDT original, antes de uma habilitação funcional.

## Testes e evidências

O `scripts/test_deen_msm8953_cpuclk_preflight.py` tem oito testes que fixam os recursos stock e a ausência de operações de runtime/registro de clocks. O workflow `.github/workflows/deen-msm8953-cpuclk-preflight.yml` roda também os oito testes de referência do PR #31, compila o arquivo C com Clang/LLVM18 para ARM64 e armazena apenas logs e hashes do objeto. Não produz `Image`, `boot.img` nem permite acesso ao dispositivo.

Referência original: `Deen_Boot_B_Audit.zip`, `boot_b-original.img`, SHA256 `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`. A imagem original e os FDTs stock brutos **não** são publicados no GitHub. O CI valida a referência derivada, não os bytes stock diretamente.

## Próximos critérios para um port realmente funcional

1. Relacionar precisamente os muxes c0/c1 e CCI, os acessos `APCS_ALIAS1` e a janela APCS SMD/RPM de `0x0B011000`.
2. Portar a sequência segura de Clock Framework/PLL com dependências de XO, `vdd-mx`, `vdd-cl`, *speed bin* e limitações de frequência/tensão.
3. Validar que nenhuma operação de clock se sobreponha aos bits de comunicação com RPM e que falhas/defer sejam tratadas.
4. Resolver TSENS TYPE3 stock de 15 sensores e SMEM/RPM antes de permitir boot com DVFS.

**Gates:** `CPUCLK_SOURCE_PREP=IN_CI`; `CPU_CLK_PROVIDER=NOT_IMPLEMENTED`; `DVFS/CCI/PLL=HOLD`; `TSENS_RUNTIME=HOLD`; `SMEM/RPM_RUNTIME=HOLD`; `BOOT/FLASH/MERGE=HOLD`.

Nenhuma alteração de firmware ou Device Tree, e nenhum merge.
