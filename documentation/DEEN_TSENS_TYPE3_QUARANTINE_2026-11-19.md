# Deen C100/C200 — quarentena térmica TYPE3 no DTB, não uma solução térmica

## Evidência de origem

O FDT stock C100/C200 auditado diretamente do `boot_b-original.img` (SHA-256 `6e8ec0eafec86e50b8895f81fc1c4809f0c1e0c674ea82a8640e7a3ace7a9765`) descreve `qcom,msm8953-tsens`, **15 sensores com IDs de hardware 1..15**, janelas físicas `0x4a8000/0x2000` e `0x0a4000/0x1000`, IRQs SPI184/314. A fonte Motorola 3.18 `msm-tsens.c` mapeia MSM8953 para **TSENS_TYPE3** e `TSENS_CALIB_FUSE_MAP_NONE`.

O DTSI herdado da árvore ACK-derived 5.15 descreve, diferentemente, `compatible = "qcom,msm8953-tsens", "qcom,tsens-v2"` e **16 sensores**, com TM `0x4a9000/0x1000` e SROT `0x4a8000/0x1000`. O binding 5.15 `qcom-tsens.yaml` não enumera `qcom,msm8953-tsens` como compatível v2 validado.

## Alteração deliberadamente mínima

O arquivo **somente da placa Deen**, `arch/arm64/boot/dts/qcom/msm8953-motorola-deen-common.dtsi`, ganha uma sobrescrita:

```dts
&tsens0 {
    status = "disabled";
};
```

Isso afeta exclusivamente os DTBs candidatos **Deen PVT1/C100 e PVT2/C200**; não altera o DTSI genérico do SoC, os 16 sensores herdados, registradores/IRQs, limites térmicos, firmware, Kconfig ou drivers. A quarentena impede probe inadvertido dessa descrição v2 não verificada caso `CONFIG_QCOM_TSENS=y` seja habilitado futuramente.

**CRÍTICO:** desabilitar o sensor também significa que **não existe proteção térmica comprovada** fornecida por esse driver. Este DTB não está aprovado para inicialização real ou flash. O estado correto é `TSENS_RUNTIME=HOLD`, `THERMAL_SAFETY=HOLD`, `BOOT/FLASH=HOLD`.

## CI de prova, não de execução em hardware

`scripts/deen_tsens_type3_quarantine_gate.py` consulta com `fdtget` os **DTBs compilados**, exigindo `status="disabled"`, o `compatible` experimental explicitamente mantido, contagem ainda 16 (não fingir que foi portada para TYPE3) e IDs de placa exatos C100/C200. `scripts/test_deen_tsens_type3_quarantine_gate.py` tem 7 testes, incluindo negativos para status ausente/okay, troca de placa e tentativa de mudar contagem sem driver. O workflow `.github/workflows/deen-tsens-type3-quarantine.yml` recompila ambos os DTBs com cross-compiler ARM64, publica **somente logs/hashes** e não produz `Image` ou `boot.img`.

Os hashes dos novos DTBs **não serão iguais aos candidatos anteriores**; a diferença de status é deliberada. Isso **não** implica igualdade com o firmware stock. Até existir prova de registradores TYPE3, calibração/IRQ, mapeamento dos IDs, governor/cooling e DVFS, a interface térmica permanece bloqueada.

Nenhum merge de hardware, habilitação de firmware, distribuição de kernel ou flash está autorizado por este PR.
