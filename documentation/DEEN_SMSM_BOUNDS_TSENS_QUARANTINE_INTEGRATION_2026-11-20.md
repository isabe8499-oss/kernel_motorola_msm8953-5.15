# Deen C100/C200 — Integração host-only: SMSM bounds + TSENS quarantine

Data: 20/11/2026. Base: [PR #27](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/27) (`0b5b12c1e010f17f1dfd2777760eae570c40304f`), cuja compilação completa com **ThinLTO+CFI** e os **14 testes SMSM** passou em push e pull_request. Contenção térmica reproduzida **apenas na DTS do Deen** a partir do [PR #28](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/28), que também passou no CI.

## Propósito e escopo mínimo

Este ramo de CI comprova se o kernel experimental compila em conjunto com duas mudanças **já aprovadas isoladamente**:
- Guardas SMSM de `drivers/soc/qcom/smsm.c` dos [PRs #25](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/25) e [#26](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/26), trazidas pela base #27; testam limites de `local_host`, tamanhos de itens SMEM 85/333 e overflow dos vetores;
- No `msm8953-motorola-deen-common.dtsi`, **somente** a inclusão `&tsens0 { status = "disabled"; };` e seu comentário técnico do PR #28, sem alterar `msm8953.dtsi`, drivers térmicos, reguladores ou os `qcom,board-id`.

**O nó TSENS herdado é inseguro para ativação:** o stock FDT C100/C200 identifica **15 sensores TYPE3** enquanto o DTSI ACK herdado descreve **16 sensores v2**. Manter o nó em `disabled` evita o probe acidental do driver incorreto, mas um telefone **não pode ser considerado seguro para boot sem proteção térmica validada**. O descritor provisório de 15 IDs do [PR #29](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/pull/29) permanece separado e não entrou nesta combinação.

## Testes e validações obrigatórias

O novo workflow `.github/workflows/deen-ack515-smsm-tsens-quarantine-full-link.yml`:
- Resolve `gki_defconfig → Deen20 → SMEM/RPM host5 → SMSM-only`, sem ativar `QCOM_APCS_IPC`, `QCOM_SMP2P`, remoteproc ou TSENS.
- Executa os 6 testes SMSM de host, 8 testes SMSM de itens compartilhados e 7 testes negativos de quarentena térmica.
- Alterna **somente para o CI** Full LTO → ThinLTO, preserva CFI=y, compila e linka `vmlinux` e `Image` ARM64 e exige o objeto `smsm.o`.
- Reconstrói os dois DTBs PVT1/PVT2, verifica `status="disabled"`, preservação dos IDs `0x4d/C100` e `0x4d/C200`, mantém o count herdado 16 **sem fingir que foi corrigido**, e verifica que os DTBs são diferentes do candidato anterior (que tinha TSENS habilitado).
- Publica apenas logs e hashes, nunca `boot.img`, `Image`, `vmlinux`, partições stock ou firmware.

**O CI dos PRs #27/#28, isoladamente, não basta para afirmar que a combinação passou.** Somente os checks novos podem validar a interação, e mesmo um resultado verde significa apenas `PASS_SMSM_BOUNDS_AND_TSENS_QUARANTINE_LINK_ONLY_RUNTIME_HOLD`.

## Bloqueadores inalterados

`TSENS_TYPE3_PORT=HOLD`; `SAFE_THERMAL_MANAGEMENT=HOLD`; `CPU_CLOCK_CPUSS=HOLD`; `SMEM_FIRMWARE_ABI=HOLD`; `RPM_ACK=HOLD`; `GKI_FULL_LTO_LINK=HOLD`; `REMOTE_SMSM_INBOUND=HOLD`; `BOOT/FLASH/FIRMWARE_ENABLEMENT/MERGE=HOLD`.

Os DTBs com TSENS desativado **não devem ser distribuídos como imagens instaláveis**. O ramo experimental não é destino para merge de código enquanto as proteções térmicas e o boot não forem validados.
