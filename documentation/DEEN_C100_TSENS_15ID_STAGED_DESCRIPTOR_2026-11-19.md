# Motorola One Deen — descritor TSENS MSM8953 com 15 IDs, ainda NÃO ligado ao OF

Data: 19/11/2026. Base: PR #10, HEAD `54901d379be4436ac9efb38dd352066694b8ddec`. PR da etapa: branch `stage/deen-msm8953-tsens-15hwids-20261119`. Issue-mãe: [#8](https://github.com/isabe8499-oss/kernel_motorola_msm8953-5.15/issues/8).

## Mudança de código realmente implementada

`drivers/thermal/qcom/tsens-v2.c` acrescenta **21 linhas** com:

```c
static unsigned int tsens_msm8953_stage_hw_ids[] = {
    1, 2, 3, 4, 5, 6, 7, 8,
    9, 10, 11, 12, 13, 14, 15,
};

struct tsens_plat_data data_msm8953_stage_only = {
    .num_sensors = 15,
    .hw_ids = tsens_msm8953_stage_hw_ids,
    /* .ops / .feat / .fields intentionally NULL -- no probe readiness. */
};
```

O `struct tsens_plat_data` existe em `drivers/thermal/qcom/tsens.h` e o `tsens_probe()` no arquivo `tsens.c` usa `data->hw_ids[i]` quando a tabela é disponibilizada. A tabela numérica 1–15 vem da **auditoria anterior do FDT stock C100**, não de uma leitura direta do binário original nesta etapa.

A configuração é **incompleta de propósito**. Não se atribuiu `ops_generic_v2`, versão de IP, conversão térmica, EEPROM, calibração, limites, interrupções ou dados de registradores ao novo descriptor porque essas peças ainda não foram comprovadas em runtime. Se fosse ligado hoje, `tsens_probe()` abortaria em `if (!priv->ops || !priv->ops->init || !priv->ops->get_temp) return -EINVAL;`. A branch não faz essa ligação.

**Não foram alterados:** `drivers/thermal/qcom/tsens.c` (inclusive `tsens_table`), `tsens.h`, `msm8953.dtsi`, DTBs, `qcom-tsens.yaml`, `Makefile`, `Kconfig`, funções de acesso MMIO, reguladores ou firmware.

**Nota importante:** o DTS existente ainda contém `"qcom,msm8953-tsens", "qcom,tsens-v2"`. Logo o **caminho genérico v2 atual permanece exatamente como antes**; esta branch não ativa a nova tabela nem altera o comportamento de fallback herdado. Não confundir “nenhuma ativação nova” com “TSENS existente desabilitado”.

## BLOQUEADOR P0 novo: `#qcom,sensors` pode ultrapassar o array de 15 IDs

A implementação atual de `tsens_probe()` em `drivers/thermal/qcom/tsens.c` começa com `num_sensors = data->num_sensors`, mas em seguida executa `of_property_read_u32(np, "#qcom,sensors", &num_sensors)`. **O DTSI MSM8953 continua declarando 16 sensores.** Se a futura entrada OF selecionasse agora o novo descritor de 15 elementos, o loop `priv->sensor[i].hw_id = data->hw_ids[i]` iria acessar `hw_ids[15]` fora do array quando `i == 15`.

Por isso a ausência de OF match não é só uma preferência: **é condição de segurança obrigatória.** O novo teste `test_dt_count_override_would_overrun_unbound_fifteen_id_table` confirma em fonte essa dependência e impede apresentar o descritor como funcional. Antes de qualquer binding futuro, será necessário:
- reconciliar o DTB e a quantidade de sensores real com o FDT stock C100;
- garantir que o número efetivamente usado pelo probe nunca excede o tamanho da tabela `hw_ids` (incluindo regressões para DTs antigos);
- só então verificar callbacks/registradores, calibração, segurança térmica e IRQ reais.

**Nenhum valor no DTSI, nenhuma linha do `tsens_probe()` e nenhuma configuração de hardware foram alterados para ocultar essa condição.**

## Por que não ligar o descritor nesta etapa?

- O stock C100 documentado indica **15 sensores** (IDs de hardware 1 a 15, clientes 1–15, slopes 0xc80), enquanto o candidato 5.15 usa `#qcom,sensors = <16>`, com indexação default 0–15.
- O doador **3.18** tem `TSENS_TYPE3` e rotina compatível `qcom,msm8953-tsens`; o intermediário **4.19 WIP** usa `data_tsens2xxx` para MSM8953 e confirma uma ponte de conversão signed 12-bit ×100. A geometria dos 11 registradores e das oito zonas térmicas foi verificada estaticamente no PR #10; **nenhum doador comprova funcionamento no kernel 5.15 do Deen**.
- EEPROM/fuses, propriedade real da região térmica, versão SROT, limiares stock, IRQ/ACK em hardware e thermal zones seguem sem equivalência validada.
- O FDT stock completo binário anterior não consta do pacote recente; a auditoria existente foi usada como evidência secundária, não como prova direta.
- Não é seguro inventar `ops`, `feat` e `fields` com base apenas na equivalência de offsets, pois o sistema de proteção térmica precisa operar corretamente.

## Gate reproduzível no GitHub Actions

`.github/workflows/deen-msm8953-tsens-staged-15id.yml`:

1. Compila **o objeto real** `tsens-v2.o` e `tsens.o` (AArch64), confirma presença do símbolo `data_msm8953_stage_only` e do array `tsens_msm8953_stage_hw_ids` com `nm`, e ausência de referência ao descritor dentro de `tsens.o`.
2. Roda os novos testes `test_deen_msm8953_tsens_stage_only.py` (15 IDs únicos, ausência de callbacks, nenhum OF match, no DTS change, referência às oito zonas e schema sem falso PASS), mais regressões dos PRs #3–#10.
3. Executa `dtschema==2024.2` sobre o schema completo e ambos os DTBs, sem esconder os **11 erros de schema conhecidos por DTB** — inclusive TSENS.
4. Mantém os hashes de DTB idênticos aos do PR #10: PVT1 `fa9ca9966da457ee45b28fc3e2479ed145bc5cfb20e537faff45ca472b510d1a`; PVT2 `9d3291f5ee86799032efdf4c6bec0b5950a35170bcd88cc77bc1820fb08c2b05`.
5. Empacota logs, schema, relatório e arquivos **host-only**, sem kernel Image, boot.img ou pacote de flash.

## Próximos bloqueadores

`STAGE_15_IDS_COMPILED`: somente PASS quando CI verde.

`STOCK_FDT_DIRECT` = HOLD; `THERMAL_RUNTIME` = HOLD; `TEMPERATURE_CONVERSION` = HOLD; `EEPROM_CALIBRATION` = HOLD; `THRESHOLD_IRQ_SAFETY` = HOLD; `TSENS_COMPATIBLE_MATCH` = HOLD; `SCHEMA_GLOBAL` = REVIEW_REQUIRED; `BOOT`/`FIRMWARE`/`FLASH`/`MERGE` = HOLD.

Qualquer futura conclusão de sensor/temperatura deverá ser submetida a outro PR, sem extrapolar de “objeto compilou” para “thermal funciona”.
